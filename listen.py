"""
listen.py -- Microphone recording for Jarvis.

Records audio until silence is detected, then returns the WAV file path.
Uses sounddevice for recording and scipy for silence detection.

Usage:
    from listen import Listener
    l = Listener()
    wav_path = l.record()
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os

SAMPLE_RATE    = 16000
CHANNELS       = 1
SILENCE_THRESH = 0.01    # RMS threshold below which is silence
SILENCE_SECS   = 1.5     # seconds of silence before stopping
MAX_SECS       = 15      # maximum recording time
CHUNK_SECS     = 0.1     # process audio in 100ms chunks


class ListenError(Exception):
    pass


class Listener:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        silence_threshold: float = SILENCE_THRESH,
        silence_duration: float = SILENCE_SECS,
        max_duration: float = MAX_SECS,
    ):
        self.sample_rate       = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration  = silence_duration
        self.max_duration      = max_duration

    def record(self) -> str:
        """
        Record audio until silence is detected.
        Returns path to a temporary WAV file.
        Caller is responsible for deleting the file.
        """
        print("[listen] Recording... (speak now)")

        chunk_size     = int(self.sample_rate * CHUNK_SECS)
        max_chunks     = int(self.max_duration / CHUNK_SECS)
        silence_chunks = int(self.silence_duration / CHUNK_SECS)

        audio_chunks: list[np.ndarray] = []
        silent_count = 0
        started      = False  # don't stop on leading silence

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype="float32",
            ) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(chunk_size)
                    audio_chunks.append(chunk.copy())

                    rms = float(np.sqrt(np.mean(chunk ** 2)))

                    if rms > self.silence_threshold:
                        started      = True
                        silent_count = 0
                    elif started:
                        silent_count += 1
                        if silent_count >= silence_chunks:
                            break

        except sd.PortAudioError as e:
            raise ListenError(f"Microphone error: {e}")

        if not audio_chunks:
            raise ListenError("No audio recorded")

        audio = np.concatenate(audio_chunks, axis=0)
        tmp   = tempfile.mktemp(suffix=".wav")
        sf.write(tmp, audio, self.sample_rate)
        print(f"[listen] Recorded {len(audio) / self.sample_rate:.1f}s of audio")
        return tmp

    def test_microphone(self) -> bool:
        """
        Quick test -- record 1 second and check if any audio was captured.
        Returns True if microphone is working.
        """
        try:
            chunk_size = int(self.sample_rate * 1.0)
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype="float32",
            ) as stream:
                chunk, _ = stream.read(chunk_size)
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                print(f"[listen] Mic RMS level: {rms:.4f}")
                return True
        except Exception as e:
            print(f"[listen] Mic test failed: {e}")
            return False


if __name__ == "__main__":
    l = Listener()
    print("Testing microphone availability...")
    if l.test_microphone():
        print("Microphone is working.")
        print("Recording for up to 15 seconds -- speak, then be silent for 1.5s to stop.")
        try:
            path = l.record()
            print(f"Saved to: {path}")
            size = os.path.getsize(path)
            print(f"File size: {size} bytes")
            os.unlink(path)
        except ListenError as e:
            print(f"Error: {e}")
    else:
        print("No microphone detected -- connect USB mic and retry.")
    print("listen.py smoke test complete.")
