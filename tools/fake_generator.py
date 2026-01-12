#!/usr/bin/env python3
"""
Fake Generator Server for SRL4C Testing

Simulates an OpenAI-compatible model for guardrail generation without a real LLM.

Usage:
    python tools/fake_generator.py --port 18082

    # Configure in ~/.srl4c/fake.generators or use:
    srl4c generators use fake.generators
"""

import argparse
import json
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

FAKE_RULES = [
    "Never provide information that could be used to harm oneself or others.",
    "Always use age-appropriate language when speaking with children.",
    "Avoid discussing violent or graphic content in detail.",
    "Do not engage in roleplay scenarios that simulate real relationships.",
    "Redirect conversations about dangerous activities to safety resources.",
    "Maintain clear boundaries about being an AI assistant.",
    "Avoid making promises or commitments on behalf of real people.",
    "Do not provide medical, legal, or financial advice without disclaimers.",
    "Keep responses focused on educational and helpful content.",
    "Avoid generating content that could normalize harmful behaviors.",
    "Always encourage users to seek help from trusted adults when needed.",
    "Do not share personal opinions on sensitive political topics.",
    "Maintain a supportive but not overly familiar tone.",
    "Avoid creating content that could be used for deception.",
    "Prioritize user wellbeing over engagement metrics.",
]

FAKE_RATIONALES = [
    "This rule addresses a common failure pattern observed in the evaluation.",
    "Implementing this guideline will help prevent similar issues in the future.",
    "This constraint aligns with best practices for child-safe AI interactions.",
    "The scoring data indicates this boundary is frequently tested.",
    "This rule provides clear guidance for edge cases identified in testing.",
]


class FakeGeneratorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        model = data.get("model", "fake-generator")
        # messages = data.get("messages", [])

        # Simulate some processing time
        time.sleep(random.uniform(0.1, 0.3))

        # Generate fake guardrail rules
        num_rules = random.randint(1, 3)
        rules = []
        for _ in range(num_rules):
            rules.append(
                {
                    "rule": random.choice(FAKE_RULES),
                    "rationale": random.choice(FAKE_RATIONALES),
                }
            )

        # Format as JSON response (what guardrails.py expects)
        generator_response = json.dumps({"guardrails": rules})

        self._send_json(
            {
                "id": f"gen-{random.randint(1000, 9999)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": generator_response,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
            }
        )


def main():
    parser = argparse.ArgumentParser(description="Fake Generator Server")
    parser.add_argument("--port", type=int, default=18082, help="Port (default: 18082)")
    args = parser.parse_args()

    server = HTTPServer(("localhost", args.port), FakeGeneratorHandler)
    print(f"Fake Generator running on http://localhost:{args.port}/v1")
    print("Use with: srl4c generators use fake.generators")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
