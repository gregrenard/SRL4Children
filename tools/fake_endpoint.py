#!/usr/bin/env python3
"""
Fake Endpoint Server for SRL4C Testing

Simulates a target chatbot for running attacks without a real LLM.

Usage:
    python tools/fake_endpoint.py --port 8080

    srl4c endpoint add simple --name fake-bot --url http://localhost:8080/chat
    srl4c attack run --endpoint fake-bot --dataset test_single
"""

import argparse
import json
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

FAKE_RESPONSES = [
    "I'm here to help! What would you like to know?",
    "That's a great question! Let me think about that...",
    "I understand you're curious. Here's what I can tell you...",
    "Thanks for asking! I'd be happy to help with that.",
    "Interesting question! Let me share my thoughts...",
    "I appreciate you reaching out. Here's my response...",
    "Great topic! I'll do my best to explain...",
    "I'm glad you asked! Here's what I know...",
    "That's something I can help with. Let me explain...",
    "Good question! Here's a thoughtful answer for you...",
]


class FakeEndpointHandler(BaseHTTPRequestHandler):
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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self._send_json({"status": "ok", "service": "Fake Endpoint"})

    def do_POST(self):
        # Add realistic delay (100-500ms)
        time.sleep(random.uniform(0.1, 0.5))

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        message = data.get("message", "")
        response_text = random.choice(FAKE_RESPONSES)

        if message and len(message) > 20:
            response_text += f" Regarding '{message[:30]}...'"

        self._send_json({"response": response_text})


def main():
    parser = argparse.ArgumentParser(description="Fake endpoint server")
    parser.add_argument("--port", "-p", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), FakeEndpointHandler)
    print(f"Fake Endpoint running on http://{args.host}:{args.port}/chat")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
