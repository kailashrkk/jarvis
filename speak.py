"""
speak.py -- Piper TTS wrapper for Jarvis.

Converts text to speech using the local Piper binary.
Audio plays via aplay to the default ALSA device (USB speaker).

Usage:
    from speak import Speaker
    s = Speaker()
    s.say("Hello, I am Jarvis.")
"""

import subprocess
import tempfile
import os

PIPER_BIN    = "/home/kailash/piper/piper"
VOICE_MODEL  = "/home/kailash/piper/voices/en_US-lessac-medium.onnx"
TMP_WAV      = "/tmp/jarvis_tts.wav"


class SpeakError(Exception):
    pass


class Speaker:
    def __init__(
        self,
        piper_bin: str = PIPER_BIN,
        voice_model: str = VOICE_MODEL,
    ):
        self.piper_bin   = piper_bin
        self.voice_model = voice_model

        if not os.path.exists(piper_bin):
            raise SpeakError(f"Piper binary not found: {piper_bin}")
        if not os.path.exists(voice_model):
            raise SpeakError(f"Voice model not found: {voice_model}")

    def say(self, text: str) -> None:
        """
        Synthesise text and play it through the speaker.
        Blocks until playback is complete.
        """
        if not text.strip():
            return

        self._synthesise(text, TMP_WAV)
        self._play(TMP_WAV)

    def synthesise_to_file(self, text: str, path: str) -> None:
        """Synthesise text to a WAV file without playing it."""
        self._synthesise(text, path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _synthesise(self, text: str, output_path: str) -> None:
        try:
            result = subprocess.run(
                [self.piper_bin, "--model", self.voice_model, "--output_file", output_path],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise SpeakError(f"Piper failed: {result.stderr.decode()}")
        except subprocess.TimeoutExpired:
            raise SpeakError("Piper timed out")
        except FileNotFoundError:
            raise SpeakError(f"Piper binary not found: {self.piper_bin}")

    def _play(self, wav_path: str) -> None:
        try:
            result = subprocess.run(
                ["aplay", "-D", "plughw:2,0", wav_path],
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise SpeakError(f"aplay failed: {result.stderr.decode()}")
        except subprocess.TimeoutExpired:
            raise SpeakError("aplay timed out")
        except FileNotFoundError:
            raise SpeakError("aplay not found -- install with: sudo apt install alsa-utils")


if __name__ == "__main__":
    s = Speaker()
    print("Synthesising test phrase...")
    s.synthesise_to_file("Hello, I am Jarvis, your personal assistant.", TMP_WAV)
    print(f"WAV saved to {TMP_WAV}")
    print(f"File size: {os.path.getsize(TMP_WAV)} bytes")
    print("Attempting playback -- will fail until speaker is connected.")
    try:
        s._play(TMP_WAV)
        print("Playback complete.")
    except SpeakError as e:
        print(f"Playback skipped: {e}")
    print("speak.py smoke test complete.")
