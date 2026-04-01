"""
transcribe.py -- Whisper.cpp wrapper for Jarvis.

Transcribes a WAV file to text using the local whisper-cli binary.
Input must be 16kHz mono WAV -- conversion handled automatically via ffmpeg.

Usage:
    from transcribe import Transcriber
    t = Transcriber()
    text = t.transcribe("/tmp/recording.wav")
    print(text)
"""

import subprocess
import os
import re
import tempfile

WHISPER_BIN   = "/home/kailash/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = "/home/kailash/whisper.cpp/models/ggml-base.en.bin"


class TranscribeError(Exception):
    pass


class Transcriber:
    def __init__(
        self,
        whisper_bin: str = WHISPER_BIN,
        model: str = WHISPER_MODEL,
        threads: int = 4,
    ):
        self.whisper_bin = whisper_bin
        self.model       = model
        self.threads     = threads

        if not os.path.exists(whisper_bin):
            raise TranscribeError(f"whisper-cli not found: {whisper_bin}")
        if not os.path.exists(model):
            raise TranscribeError(f"Whisper model not found: {model}")

    def transcribe(self, wav_path: str) -> str:
        """
        Transcribe a WAV file. Returns cleaned text string.
        Converts to 16kHz mono automatically if needed.
        Returns empty string if nothing was detected.
        """
        if not os.path.exists(wav_path):
            raise TranscribeError(f"Audio file not found: {wav_path}")

        converted = self._ensure_16k_mono(wav_path)

        try:
            result = subprocess.run(
                [
                    self.whisper_bin,
                    "-m", self.model,
                    "-f", converted,
                    "-t", str(self.threads),
                    "--no-prints",
                    "-nt",          # no timestamps
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise TranscribeError(f"Whisper failed: {result.stderr}")

            return self._clean(result.stdout)

        except subprocess.TimeoutExpired:
            raise TranscribeError("Whisper timed out")
        finally:
            if converted != wav_path and os.path.exists(converted):
                os.unlink(converted)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_16k_mono(self, wav_path: str) -> str:
        """
        Convert to 16kHz mono WAV using ffmpeg if needed.
        Returns the original path if already correct format,
        otherwise returns path to a temp converted file.
        """
        tmp = tempfile.mktemp(suffix=".wav")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", wav_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-f", "wav",
                    tmp,
                ],
                capture_output=True,
                timeout=30,
                check=True,
            )
            return tmp
        except subprocess.CalledProcessError as e:
            raise TranscribeError(f"ffmpeg conversion failed: {e.stderr.decode()}")

    @staticmethod
    def _clean(text: str) -> str:
        """Strip timestamps, brackets, and extra whitespace."""
        # Remove [BLANK_AUDIO] and similar markers
        text = re.sub(r"\[.*?\]", "", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text


if __name__ == "__main__":
    t = Transcriber()
    sample = "/home/kailash/whisper.cpp/samples/jfk.wav"
    print(f"Transcribing: {sample}")
    result = t.transcribe(sample)
    print(f"Result: {result!r}")
    print("transcribe.py smoke test complete.")
