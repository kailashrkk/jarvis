"""
wake.py -- OpenWakeWord wake word detection for Jarvis.

Continuously listens for "Hey Jarvis" and calls a callback when detected.
Runs in a background thread so the main loop stays responsive.

Usage:
    from wake import WakeWordDetector
    w = WakeWordDetector(on_wake=lambda: print("Wake word detected!"))
    w.start()
    # ... main loop ...
    w.stop()
"""

import threading
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

WAKE_WORD_MODEL = "/home/kailash/.local/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
SAMPLE_RATE     = 16000
CHUNK_SIZE      = 1280   # 80ms at 16kHz -- openwakeword requirement
THRESHOLD       = 0.5    # confidence threshold


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
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=CHUNK_SIZE,
            ) as stream:
                while self._running:
                    chunk, _ = stream.read(CHUNK_SIZE)
                    audio    = chunk[:, 0] if chunk.ndim > 1 else chunk.flatten()
                    scores   = self._model.predict(audio)

                    for name, score in scores.items():
                        if score >= self.threshold:
                            print(f"[wake] Detected '{name}' with score {score:.2f}")
                            if self._running:
                                self.on_wake()
                            # Reset model state after detection
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
