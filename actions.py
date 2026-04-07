"""
actions.py -- Command actions for Jarvis.
Each function receives (speaker, srv) and executes a system action.
"""

import os
import time
import subprocess

DISPLAY = ":1"
CHROMIUM_CMD = [
    "chromium", "--kiosk", "--password-store=basic",
    "--disable-infobars", "--noerrdialogs",
    "--disable-session-crashed-bubble", "http://localhost:8090"
]


def poweroff(speaker, srv):
    speaker.say("Shutting down. Goodbye.")
    time.sleep(2)
    subprocess.run(["sudo", "poweroff"])


def reboot(speaker, srv):
    speaker.say("Rebooting now.")
    time.sleep(2)
    subprocess.run(["sudo", "reboot"])


def retroarch_open(speaker, srv):
    speaker.say("Opening RetroArch.")
    srv.set_state("idle", "RetroArch running...")
    subprocess.run(["pkill", "chromium"], stderr=subprocess.DEVNULL)
    subprocess.Popen(
        ["retroarch"],
        env={**os.environ, "DISPLAY": DISPLAY},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def retroarch_close(speaker, srv):
    speaker.say("Closing RetroArch.")
    subprocess.run(["pkill", "retroarch"], stderr=subprocess.DEVNULL)
    subprocess.Popen(
        CHROMIUM_CMD,
        env={**os.environ, "DISPLAY": DISPLAY},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def volume_up(speaker, srv):
    subprocess.run(["amixer", "-c", "2", "sset", "PCM", "10%+"], stdout=subprocess.DEVNULL)
    speaker.say("Volume up.")


def volume_down(speaker, srv):
    subprocess.run(["amixer", "-c", "2", "sset", "PCM", "10%-"], stdout=subprocess.DEVNULL)
    speaker.say("Volume down.")
