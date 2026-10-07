"""HMI entry point using the KlipperScreen-style framework.

Initializes GTK, creates the KlipperScreen window, and enters the GTK
main loop. Also installs a SIGINT handler so Ctrl+C from an SSH session
terminates the app cleanly.
"""

import sys
import signal
import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from screen import KlipperScreen


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    win = KlipperScreen()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())