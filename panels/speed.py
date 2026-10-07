"""Speed panel: slider for machine feed rate."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from panels.base_panel import Panel


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Speed", **kwargs)

        self.content.pack_start(Gtk.Box(), True, True, 0)

        self.value_label = self.gtk.Label("40 mm/s", font="big")
        self.content.pack_start(self.value_label, False, False, 0)

        self.slider = self.gtk.Slider(1, 200, 40)
        self.slider.connect("value-changed", self._on_changed)
        self.content.pack_start(self.slider, False, False, 0)

        self.content.pack_start(Gtk.Box(), True, True, 0)

    def _on_changed(self, slider):
        v = int(slider.get_value())
        self.value_label.set_text(f"{v} mm/s")
        self._screen.job.set_speed(float(v))