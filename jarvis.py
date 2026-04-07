import os
import sys
import time
import threading
import random
import subprocess

from speak      import Speaker, SpeakError
from transcribe import Transcriber, TranscribeError
from think      import Brain, ThinkError
from listen     import Listener, ListenError
from wake       import WakeWordDetector
from memory     import Memory
from chime      import start_chime, stop_chime, ready_chime, wake_chime
import server
import battery

THINKING_PHRASES = [
    "Let me see...",
    "Hmm, give me a moment...",
    "Good question, let me think...",
    "One moment...",
    "Ah, let me think about that...",
    "Right, so...",
    "Interesting, let me see...",
]

EXIT_PHRASES = ["nevermind", "never mind", "forget it", "stop", "cancel", "exit"]
MAX_EXCHANGES = 3


class Jarvis:
    def __init__(self):
        print("[jarvis] Initialising...")
        self.speaker     = Speaker()
        self.transcriber = Transcriber()
        self.brain       = Brain()
        self.listener    = Listener()
        self.memory      = Memory()
        self._busy       = False
        self._running    = True
        self.wake        = WakeWordDetector(on_wake=self._on_wake)

    def run(self) -> None:
        if not self.brain.is_available():
            print("[jarvis] ERROR: llama.cpp not running.")
            sys.exit(1)

        print("[jarvis] All systems ready.")
        server.start()

        def _battery_loop():
            while self._running:
                pct = battery.get_percent()
                if pct >= 0:
                    server.set_state('idle', battery=pct)
                time.sleep(60)

        threading.Thread(target=_battery_loop, daemon=True).start()

        server.set_tap_callback(self._on_wake)
        server.set_state("idle", "Listening for wake word...", 100)
        ready_chime()
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
        threading.Thread(target=self._conversation, daemon=True).start()

    def _conversation(self) -> None:
        try:
            self.wake.stop()
            server.set_state("listening", "Speak your question...")
            wake_chime()
            time.sleep(1.0)

            self.speaker.say("Yes?")
            time.sleep(0.3)

            exchanges = 0

            while exchanges < MAX_EXCHANGES:
                # Listen
                try:
                    wav_path = self.listener.record()
                except ListenError as e:
                    print(f"[jarvis] Listen error: {e}")
                    self.speaker.say("Sorry, I couldn't hear you.")
                    break

                # Transcribe
                try:
                    question = self.transcriber.transcribe(wav_path)
                except TranscribeError as e:
                    print(f"[jarvis] Transcribe error: {e}")
                    self.speaker.say("Sorry, I couldn't understand that.")
                    break
                finally:
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)

                if not question.strip():
                    self.speaker.say("I didn't catch that.")
                    break

                print(f"[jarvis] You said: {question!r}")

                # Check for exit phrase
                if any(p in question.lower() for p in EXIT_PHRASES):
                    self.speaker.say("Sure, let me know if you need anything.")
                    break

                # Check for app launch commands
                q = question.lower()
                if any(p in q for p in ["shut down", "shutdown", "power off", "poweroff", "turn off"]):
                    self.speaker.say("Shutting down. Goodbye.")
                    time.sleep(2)
                    subprocess.run(["sudo", "poweroff"])
                    break

                if any(p in q for p in ["reboot", "restart", "restart jarvis"]):
                    self.speaker.say("Rebooting now.")
                    time.sleep(2)
                    subprocess.run(["sudo", "reboot"])
                    break

                if any(p in q for p in ["close retroarch", "exit retroarch", "quit retroarch", "close games", "exit games", "close retro arc", "exit retro arc", "quit retro arc", "close the retro", "exit the retro"]):
                    self.speaker.say("Closing RetroArch.")
                    subprocess.run(["pkill", "retroarch"], stderr=subprocess.DEVNULL)
                    subprocess.Popen(
                        ["chromium", "--kiosk", "--password-store=basic",
                         "--disable-infobars", "--noerrdialogs",
                         "--disable-session-crashed-bubble", "http://localhost:8090"],
                        env={**os.environ, "DISPLAY": ":1"},
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    break

                if any(p in q for p in ["open retroarch", "launch retroarch", "open retro arch", "play games", "open games"]):
                    self.speaker.say("Opening RetroArch.")
                    server.set_state("idle", "RetroArch running...")
                    subprocess.run(["pkill", "chromium"], stderr=subprocess.DEVNULL)
                    subprocess.Popen(
                        ["retroarch"],
                        env={**os.environ, "DISPLAY": ":1"},
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    break

                # Thinking phrase + chime
                thinking = random.choice(THINKING_PHRASES)
                self.speaker.say(thinking)
                start_chime()
                server.set_state("thinking", "Let me think about that...")

                # Think
                self.memory.add("user", question)
                try:
                    response = self.brain.chat(self.memory.get_history())
                except ThinkError as e:
                    stop_chime()
                    print(f"[jarvis] Think error: {e}")
                    self.speaker.say("Sorry, I had trouble with that one.")
                    break
                finally:
                    stop_chime()

                print(f"[jarvis] Response: {response!r}")
                self.memory.add("assistant", response)

                # Speak
                try:
                    self.speaker.say(response)
                    server.set_state("speaking", response)
                except SpeakError as e:
                    print(f"[jarvis] Speak error: {e}")
                    break

                exchanges += 1

                if exchanges < MAX_EXCHANGES:
                    self.speaker.say("Anything else?")
                    time.sleep(0.3)
                else:
                    self.speaker.say("Let me know if you need anything else.")

        finally:
            time.sleep(0.3)
            self.wake.start()
            server.set_state("idle", "Listening for wake word...")
            self._busy = False


if __name__ == "__main__":
    Jarvis().run()
