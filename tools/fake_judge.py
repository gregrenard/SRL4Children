#!/usr/bin/env python3
"""
Fake Judge Server for SRL4C Testing

Simulates an OpenAI-compatible judge for scoring without a real LLM.

Usage:
    python tools/fake_judge.py --port 18081

    # Configure in ~/.srl4c/judges.yaml:
    judges:
      fake_judge:
        provider_openai_base_url: http://localhost:18081/v1
        model: fake-model

    srl4c score run <attack-id> --age child
"""

import argparse
import json
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Presence level explanations (context-agnostic, behavior detection only)
LOW_PRESENCE_EXPLANATIONS = [
    "The behavior is absent or barely detectable in this response.",
    "No meaningful indicators of this behavior pattern were found.",
    "The response does not exhibit this characteristic.",
    "This behavior is not present in any significant way.",
]

MODERATE_PRESENCE_EXPLANATIONS = [
    "Some indicators of this behavior are present but not prominent.",
    "The behavior appears occasionally in the response.",
    "Moderate presence of this characteristic was detected.",
    "This pattern is noticeable but not dominant.",
]

HIGH_PRESENCE_EXPLANATIONS = [
    "This behavior is clearly and consistently present throughout.",
    "Strong presence of this characteristic was detected.",
    "The response strongly exhibits this behavior pattern.",
    "Multiple clear indicators of this behavior were identified.",
]

# Global counter for guaranteed high presence (every Nth eval gets high presence)
# High presence (4-5) means the problematic behavior IS present, which triggers guardrails
eval_counter = 0
FORCE_HIGH_PRESENCE_EVERY_N = 4  # Every 4th evaluation gets high presence


class FakeJudgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        self._send_json({"status": "ok", "service": "Fake Judge"})

    def do_POST(self):
        # Minimal delay for faster tests
        time.sleep(random.uniform(0.01, 0.03))

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        global eval_counter
        eval_counter += 1

        model = data.get("model", "fake-model")
        messages = data.get("messages", [])

        # Get prompt text for seeding randomness
        eval_text = ""
        for msg in messages:
            if msg.get("role") == "user":
                eval_text = msg.get("content", "")[:200]
                break

        # Seed for some consistency (same input = similar score)
        random.seed(hash(eval_text) % 1000 + random.randint(0, 10))

        # Force high presence every Nth evaluation for guardrails testing
        force_high_presence = (eval_counter % FORCE_HIGH_PRESENCE_EVERY_N == 0)

        if force_high_presence:
            # Guaranteed high presence (4-5) - triggers guardrail generation
            presence_level = random.choice([4, 5])
            explanation = random.choice(HIGH_PRESENCE_EXPLANATIONS)
        else:
            # Weighted random presence levels (mostly low: 1-2)
            presence_level = random.choices([1, 2, 3, 4, 5], weights=[0.35, 0.30, 0.20, 0.10, 0.05])[0]
            if presence_level <= 2:
                explanation = random.choice(LOW_PRESENCE_EXPLANATIONS)
            elif presence_level <= 3:
                explanation = random.choice(MODERATE_PRESENCE_EXPLANATIONS)
            else:
                explanation = random.choice(HIGH_PRESENCE_EXPLANATIONS)

        judge_response = json.dumps({
            "presence_level": presence_level,
            "explanation": explanation,
            "evidence_extracts": []
        })

        self._send_json({
            "id": f"fake-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": judge_response},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        })


def main():
    parser = argparse.ArgumentParser(description="Fake judge server")
    parser.add_argument("--port", "-p", type=int, default=18081)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), FakeJudgeHandler)
    print(f"Fake Judge running on http://{args.host}:{args.port}/v1/chat/completions")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
