"""
think.py -- llama.cpp client for Jarvis.

Sends conversation history to the local llama.cpp server
and returns the assistant response.

Usage:
    from think import Brain
    brain = Brain()
    response = brain.chat([
        {"role": "user", "content": "What is the capital of France?"}
    ])
"""

import json
import urllib.request
import urllib.error

LLAMA_URL    = "http://localhost:8080/v1/chat/completions"
MAX_TOKENS   = 300
TIMEOUT_SECS = 60

SYSTEM_PROMPT = """You are Jarvis, a concise and helpful personal assistant running locally on a Raspberry Pi 5. 
You give short, direct answers suitable for text-to-speech output. 
Avoid markdown, bullet points, and long lists. Speak in plain sentences."""


class ThinkError(Exception):
    pass


class Brain:
    def __init__(self, url: str = LLAMA_URL):
        self.url = url

    def chat(self, messages: list[dict]) -> str:
        """
        Send a list of messages and return the assistant reply.
        messages format: [{"role": "user"|"assistant"|"system", "content": "..."}]
        """
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        payload = json.dumps({
            "messages": full_messages,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.URLError as e:
            raise ThinkError(f"Cannot reach llama.cpp: {e}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ThinkError(f"Unexpected response from llama.cpp: {e}")

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(
                "http://localhost:8080/health", method="GET"
            )
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False


if __name__ == "__main__":
    brain = Brain()
    print("Checking llama.cpp...")
    if not brain.is_available():
        print("ERROR: llama.cpp not reachable on port 8080.")
        raise SystemExit(1)
    print("Server reachable. Testing chat...")
    response = brain.chat([
        {"role": "user", "content": "What is 2 + 2? Answer in one sentence."}
    ])
    print(f"Response: {response!r}")
    print("think.py smoke test complete.")
