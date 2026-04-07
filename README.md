# Jarvis

A fully local, offline voice assistant running on Raspberry Pi 5 8GB. No cloud. No API keys. No subscriptions.

## Hardware

- Raspberry Pi 5 8GB
- Waveshare 4" 720x720 HDMI capacitive touchscreen
- Waveshare UPS HAT (E) with 4x Samsung 21700 50E cells (I2C at 0x2d)
- SunFounder USB microphone (hw:3,0)
- USB speaker (hw:2,0)

## Stack

| Component | Role |
|---|---|
| OpenWakeWord (hey_jarvis_v0.1) | Wake word detection |
| Whisper.cpp (base.en) | Speech to text (~2.6s) |
| Qwen2.5-1.5B Q4 via llama.cpp | Language model (~11.6 tok/s) |
| Piper TTS (lessac medium) | Text to speech |
| SQLite | Conversation memory |
| WebSocket server | UI state bridge |
| Chromium kiosk | Fullscreen touch UI |

## How it works

Say "Hey Jarvis" or tap the orb:

1. Records until silence
2. Transcribes with Whisper
3. Checks for voice commands first
4. Falls through to Qwen if no command matched
5. Speaks the response via Piper
6. Back to listening

## Voice commands

To add a new command: add a function to `actions.py`, add a dict entry to `commands.py`. No changes to `jarvis.py` needed.

| Phrase | Action |
|---|---|
| "open games" | Launch RetroArch, hide UI |
| "close games" | Close RetroArch, restore UI |
| "volume up" | +10% volume |
| "volume down" | -10% volume |
| "shut down" | Graceful poweroff |
| "reboot" | Graceful reboot |
| "nevermind" | Exit current conversation |

## UI

Fullscreen dark kiosk UI with animated pulsing orb:

- Purple -- idle, listening for wake word
- Green -- recording
- Amber -- thinking
- Pink -- speaking

Battery % from UPS HAT feeds into the UI indicator. Tap the orb to talk without saying "Hey Jarvis".

WebSocket server on port 8765. UI served on port 8090.

## Key paths

| Path | Purpose |
|---|---|
| ~/jarvis/jarvis.py | Main loop |
| ~/jarvis/commands.py | Voice command phrase registry |
| ~/jarvis/actions.py | Voice command implementations |
| ~/jarvis/server.py | WebSocket UI bridge |
| ~/jarvis/web/index.html | Kiosk UI |
| ~/jarvis/battery.py | UPS HAT I2C reader |
| ~/jarvis/wake.py | Wake word detector |
| ~/jarvis/listen.py | Mic recording with silence detection |
| ~/jarvis/transcribe.py | Whisper STT |
| ~/jarvis/think.py | llama.cpp HTTP client |
| ~/jarvis/speak.py | Piper TTS |
| ~/jarvis/memory.py | SQLite conversation history |
| /etc/systemd/system/jarvis.service | systemd service |
| /etc/systemd/system/llama.service | llama.cpp service |
| ~/.asoundrc | ALSA device config |

## External binaries

| Binary | Path |
|---|---|
| llama-server | ~/llama.cpp/build/bin/llama-server |
| whisper-cli | ~/whisper.cpp/build/bin/whisper-cli |
| piper | ~/piper/piper |

## Models

| Model | Path |
|---|---|
| Qwen2.5-1.5B Q4 | ~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf |
| Whisper base.en | ~/whisper.cpp/models/ggml-base.en.bin |
| Piper lessac medium | ~/piper/voices/en_US-lessac-medium.onnx |
| Hey Jarvis | ~/.local/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx |

## Running

Manual:

    cd ~/jarvis && python3 jarvis.py

Service:

    sudo systemctl start jarvis.service
    sudo systemctl stop jarvis.service
    sudo systemctl status jarvis.service

Logs:

    sudo journalctl -u jarvis.service -f

Jarvis and llama.cpp start automatically on boot. llama starts first with a 15s head start.

## Conversation memory

Jarvis remembers the last 20 messages within and across sessions. To reset:

    python3 -c "from memory import Memory; Memory().clear()"

## ALSA notes

The USB mic (hw:3,0) is not enumerated by PortAudio by default. ~/.asoundrc exposes it. If the mic stops working after a reboot:

    arecord -l
    python3 -c "import sounddevice as sd; print(sd.query_devices())"
