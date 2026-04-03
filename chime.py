"""
chime.py -- Looping xylophone chime for Jarvis thinking state.
Plays ascending then descending notes repeatedly until stopped.
"""
import numpy as np
import soundfile as sf
import subprocess
import threading
import os
import time

SAMPLE_RATE = 44100

# Xylophone-style note frequencies (C major pentatonic, two octaves)
NOTES_UP   = [523, 659, 784, 1047, 1319]   # C5 E5 G5 C6 E6
NOTES_DOWN = [1319, 1047, 784, 659, 523]   # back down

def _generate_note(freq, duration=0.18, volume=0.35):
    t    = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    wave = volume * np.sin(2 * np.pi * freq * t)
    # Add a slight harmonic for xylophone timbre
    wave += (volume * 0.3) * np.sin(2 * np.pi * freq * 2 * t)
    wave += (volume * 0.1) * np.sin(2 * np.pi * freq * 3 * t)
    # Sharp attack, exponential decay
    decay = np.exp(-t * 8)
    return (wave * decay).astype(np.float32)

def _play_wav(data):
    path = "/tmp/jarvis_note.wav"
    sf.write(path, data, SAMPLE_RATE)
    subprocess.run(["aplay", "-q", path], capture_output=True)


class ThinkingChime:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread     = None
        # Pre-generate all notes
        self._notes = [_generate_note(f) for f in NOTES_UP + NOTES_DOWN[1:-1]]

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        while not self._stop_event.is_set():
            for note in self._notes:
                if self._stop_event.is_set():
                    return
                _play_wav(note)
                time.sleep(0.02)  # tiny gap between notes


# Singleton
_chime = ThinkingChime()

def start_chime():
    _chime.start()

def stop_chime():
    _chime.stop()


def ready_chime():
    """Single low note -- Jarvis is now listening for wake word."""
    note = _generate_note(440, duration=0.12, volume=0.3)  # A4
    _play_wav(note)

def wake_chime():
    """Two quick ascending notes -- wake word detected."""
    note1 = _generate_note(659, duration=0.10, volume=0.4)  # E5
    note2 = _generate_note(1047, duration=0.12, volume=0.4) # C6
    _play_wav(note1)
    time.sleep(0.02)
    _play_wav(note2)
