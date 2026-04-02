import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os

SAMPLE_RATE    = 44100
CHANNELS       = 1
SILENCE_SECS   = 1.5
MAX_SECS       = 15
CHUNK_SECS     = 0.1
VOICE_THRESH   = 0.008   # RMS above this = voice
SILENCE_THRESH = 0.006   # RMS below this = silence


class ListenError(Exception):
    pass


class Listener:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        voice_threshold: float = VOICE_THRESH,
        silence_threshold: float = SILENCE_THRESH,
        silence_duration: float = SILENCE_SECS,
        max_duration: float = MAX_SECS,
    ):
        self.sample_rate       = sample_rate
        self.voice_threshold   = voice_threshold
        self.silence_threshold = silence_threshold
        self.silence_duration  = silence_duration
        self.max_duration      = max_duration

    def record(self) -> str:
        print("[listen] Recording... (speak now)")

        chunk_size     = int(self.sample_rate * CHUNK_SECS)
        max_chunks     = int(self.max_duration / CHUNK_SECS)
        silence_chunks = int(self.silence_duration / CHUNK_SECS)

        audio_chunks: list[np.ndarray] = []
        silent_count = 0
        started      = False

        try:
            with sd.InputStream(
                device=1,
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype="float32",
            ) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(chunk_size)
                    audio_chunks.append(chunk.copy())
                    rms = float(np.sqrt(np.mean(chunk ** 2)))

                    if rms > self.voice_threshold:
                        started      = True
                        silent_count = 0
                    elif started and rms < self.silence_threshold:
                        silent_count += 1
                        if silent_count >= silence_chunks:
                            print("[listen] Silence detected, stopping.")
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
        try:
            chunk_size = int(self.sample_rate * 1.0)
            with sd.InputStream(
                device=1,
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
            print(f"File size: {os.path.getsize(path)} bytes")
            os.unlink(path)
        except ListenError as e:
            print(f"Error: {e}")
    else:
        print("No microphone detected -- connect USB mic and retry.")
    print("listen.py smoke test complete.")
