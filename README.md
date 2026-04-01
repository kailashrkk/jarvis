# Jarvis

A fully local, offline voice assistant running on Raspberry Pi 5 8GB.
No cloud. No API keys. No subscriptions.

## Stack

| Component | Role |
|---|---|
| OpenWakeWord | Wake word detection ("Hey Jarvis") |
| Whisper.cpp (base.en) | Speech to text |
| Qwen2.5-1.5B via llama.cpp | Language model |
| Piper TTS (lessac medium) | Text to speech |
| SQLite | Conversation memory |

## Hardware

- Raspberry Pi 5 8GB
- USB microphone
- USB powered speaker (3.5mm audio + USB power)

## How it works
```
Say "Hey Jarvis"
    -> Records until silence
    -> Transcribes speech to text
    -> Sends to local LLM with conversation history
    -> Speaks the response
    -> Back to listening
```

## Setup

### Dependencies
```bash
sudo apt-get install -y python3-pyaudio portaudio19-dev ffmpeg sox libsox-fmt-all
pip install openwakeword pyaudio sounddevice soundfile numpy --break-system-packages
```

### External binaries

| Binary | Path |
|---|---|
| llama.cpp server | ~/llama.cpp/build/bin/llama-server |
| whisper-cli | ~/whisper.cpp/build/bin/whisper-cli |
| piper | ~/piper/piper |

### Models

| Model | Path |
|---|---|
| Qwen2.5-1.5B Q4 | ~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf |
| Whisper base.en | ~/whisper.cpp/models/ggml-base.en.bin |
| Piper lessac medium | ~/piper/voices/en_US-lessac-medium.onnx |
| Hey Jarvis | ~/.local/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx |

## Running manually
```bash
python3 ~/jarvis/jarvis.py
```

## Running as a systemd service
```bash
sudo systemctl start jarvis
sudo systemctl status jarvis
sudo systemctl stop jarvis
```

Jarvis starts automatically on boot. Logs:
```bash
journalctl -u jarvis -f
```

## Module overview

| File | Role |
|---|---|
| jarvis.py | Main loop and state machine |
| wake.py | Wake word detection |
| listen.py | Microphone recording with silence detection |
| transcribe.py | Whisper speech to text |
| think.py | llama.cpp HTTP client |
| speak.py | Piper TTS |
| memory.py | SQLite conversation history |

## Conversation memory

Jarvis remembers the last 20 messages within and across sessions.
To reset memory:
```bash
python3 -c "from memory import Memory; Memory().clear()"
```
