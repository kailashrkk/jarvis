"""
commands.py -- Phrase-to-action mapping for Jarvis.
To add a new command: add an entry here and a matching function in actions.py.
"""

COMMANDS = [
    {
        "phrases": ["shut down", "shutdown", "power off", "poweroff", "turn off"],
        "action": "poweroff",
    },
    {
        "phrases": ["reboot", "restart", "restart jarvis"],
        "action": "reboot",
    },
    {
        "phrases": ["open retroarch", "launch retroarch", "open retro arch", "play games", "open games"],
        "action": "retroarch_open",
    },
    {
        "phrases": ["close retroarch", "exit retroarch", "quit retroarch", "close games", "exit games",
                    "close retro arc", "exit retro arc", "quit retro arc", "close the retro", "exit the retro"],
        "action": "retroarch_close",
    },
    {
        "phrases": ["volume up", "louder", "turn it up"],
        "action": "volume_up",
    },
    {
        "phrases": ["volume down", "quieter", "turn it down"],
        "action": "volume_down",
    },
]
