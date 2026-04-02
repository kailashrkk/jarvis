import threading
import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly
from openwakeword.model import Model

WAKE_WORD_MODEL = "/home/kailash/.local/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
RECORD_RATE     = 44100   # what the mic supports
TARGET_RATE     = 16000   # what OpenWakeWord needs
CHUNK_SECS      = 0.08    # 80ms chunks
THRESHOLD       = 0.5


class WakeWordDetector:
    def __init__(self, on_wake, threshold: float = THRESHOLD):
        self.on_wake   = on_wake
        self.threshold = threshold
        self._running  = False
        self._thread   = None
        self._model    = Model(wakeword_model_paths=[WAKE_WORD_MODEL])

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[wake] Listening for 'Hey Jarvis'...")

    def stop(self) -> None:
        self._running = False

    def _listen_loop(self) -> None:
        chunk_size = int(RECORD_RATE * CHUNK_SECS)
        try:
            with sd.InputStream(
                device=1,
                samplerate=RECORD_RATE,
                channels=1,
                dtype="int16",
                blocksize=chunk_size,
            ) as stream:
                while self._running:
                    chunk, _ = stream.read(chunk_size)
                    audio = chunk.flatten()

                    # Resample from 44100 to 16000
                    resampled = resample_poly(audio, TARGET_RATE, RECORD_RATE)
                    resampled = resampled.astype(np.int16)

                    scores = self._model.predict(resampled)
                    for name, score in scores.items():
                        if score >= self.threshold:
                            print(f"[wake] Detected '{name}' with score {score:.2f}")
                            if self._running:
                                self.on_wake()
                            self._model.reset()
                            break

        except sd.PortAudioError as e:
            print(f"[wake] Audio error: {e}")
        except Exception as e:
            print(f"[wake] Error: {e}")


if __name__ == "__main__":
    import time

    detected = []

    def on_wake():
        print("*** WAKE WORD DETECTED ***")
        detected.append(True)

    w = WakeWordDetector(on_wake=on_wake)
    try:
        w.start()
        print("Say 'Hey Jarvis' -- listening for 10 seconds...")
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        w.stop()

    print(f"Detections: {len(detected)}")
    print("wake.py smoke test complete.")
