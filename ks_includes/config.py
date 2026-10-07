"""Application config file parser (INI-style).

Currently a stub. The HMI reads its configuration from config.py.
This module exists so the framework has a place to load user
overrides from /etc/hmi.conf or ~/.config/hmi/hmi.conf in the future.
"""

import configparser
import os


def load(path=None):
    """Return a ConfigParser populated from the given file, or empty."""
    cp = configparser.ConfigParser()

    if path is None:
        candidates = [
            "/etc/hmi.conf",
            os.path.expanduser("~/.config/hmi/hmi.conf"),
        ]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break

    if path and os.path.exists(path):
        cp.read(path)
    return cp