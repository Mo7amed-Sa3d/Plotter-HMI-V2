"""USB file browser panel."""

from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from config import USB_MOUNT_POINTS
from panels.base_panel import Panel


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Cut from USB", **kwargs)

        # Refresh button row
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bar.pack_start(Gtk.Box(), True, True, 0)
        refresh_btn = self.gtk.Button("Refresh", style="ghost", height=44)
        refresh_btn.connect("clicked", lambda w: self.refresh())
        bar.pack_start(refresh_btn, False, False, 0)
        self.content.pack_start(bar, False, False, 0)

        # File list
        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-activated", self._on_activate)
        self.content.pack_start(self.gtk.Scroll(self.listbox), True, True, 0)

        # Start button
        start = self.gtk.Button("Start Cutting", style="primary", height=56)
        start.connect("clicked", lambda w: self._start())
        self.content.pack_start(start, False, False, 0)

        self.refresh()

    def _mount(self):
        for mp in USB_MOUNT_POINTS:
            p = Path(mp)
            if p.exists() and any(p.iterdir()):
                return p
        return None

    def refresh(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        mp = self._mount()
        if mp is None:
            row = Gtk.ListBoxRow()
            row.set_selectable(False)
            row.add(self.gtk.Label("No USB drive detected", font="sub"))
            self.listbox.add(row)
            self.listbox.show_all()
            return

        for path in sorted(mp.rglob("*")):
            if path.is_file() and path.suffix.lower() in (
                    ".gcode", ".nc", ".txt", ".plt"):
                row = Gtk.ListBoxRow()
                row.add(self.gtk.Label(str(path.relative_to(mp))))
                row.path = str(path)
                self.listbox.add(row)
        self.listbox.show_all()

    def _on_activate(self, listbox, row):
        if hasattr(row, "path"):
            self._screen.machine.wait_drain(timeout=5.0)
            self._screen.job.start(row.path)
            self._screen.show_panel("cutting")

    def _start(self):
        row = self.listbox.get_selected_row()
        if row is None or not hasattr(row, "path"):
            return
        self._screen.machine.wait_drain(timeout=5.0)
        self._screen.job.start(row.path)
        self._screen.show_panel("cutting")