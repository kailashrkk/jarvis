"""
jarvis.py -- Main loop for Jarvis voice assistant.

Flow:
    WakeWordDetector hears "Hey Jarvis"
        -> Listener records until silence
        -> Transcriber converts speech to text
        -> Brain sends to llama.cpp with conversation history
        -> Speaker plays the response
        -> back to listening

Run:
    python3 jarvis.py
"""

import os
import sys
import time
import threading

from speak      import Speaker, SpeakError
from transcribe import Transcriber, TranscribeError
from think      import Brain, ThinkError
from listen     import Listener, ListenError
from wake       import WakeWordDetector
from memory     import Memory


class Jarvis:
    def __init__(self):
        print("[jarvis] Initialising...")
        self.speaker    = Speaker()
        self.transcriber = Transcriber()
        self.brain      = Brain()
        self.listener   = Listener()
        self.memory     = Memory()
        self._busy      = False
        self._running   = True

        self.wake = WakeWordDetector(on_wake=self._on_wake)

    def run(self) -> None:
        if not self.brain.is_available():
            print("[jarvis] ERROR: llama.cpp not running. Start with: sudo systemctl start llama")
            sys.exit(1)

        print("[jarvis] All systems ready.")
        self.speaker.say("Jarvis online. Say hey Jarvis to begin.")

        self.wake.start()

        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.wake.stop()
            print("[jarvis] Shutdown.")

    def _on_wake(self) -> None:
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=self._handle_query, daemon=True).start()

    def _handle_query(self) -> None:
        try:
            # Acknowledge wake word
            self.speaker.say("Yes?")

            # Record question
            try:
                wav_path = self.listener.record()
            except ListenError as e:
                print(f"[jarvis] Listen error: {e}")
                self.speaker.say("Sorry, I couldn't hear you.")
                return

            # Transcribe
            try:
                question = self.transcriber.transcribe(wav_path)
            except TranscribeError as e:
                print(f"[jarvis] Transcribe error: {e}")
                self.speaker.say("Sorry, I couldn't understand that.")
                return
            finally:
                if os.path.exists(wav_path):
                    os.unlink(wav_path)

            if not question.strip():
                self.speaker.say("I didn't catch that.")
                return

            print(f"[jarvis] You said: {question!r}")

            # Add to memory
            self.memory.add("user", question)

            # Think
            try:
                history  = self.memory.get_history()
                response = self.brain.chat(history)
            except ThinkError as e:
                print(f"[jarvis] Think error: {e}")
                self.speaker.say("Sorry, I had trouble thinking of a response.")
                return

            print(f"[jarvis] Response: {response!r}")

            # Add response to memory
            self.memory.add("assistant", response)

            # Speak
            try:
                self.speaker.say(response)
            except SpeakError as e:
                print(f"[jarvis] Speak error: {e}")

        finally:
            self._busy = False


if __name__ == "__main__":
    Jarvis().run()
