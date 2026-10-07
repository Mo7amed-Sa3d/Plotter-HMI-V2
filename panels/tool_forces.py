"""Tool forces panel: sliders for solenoid P0 and P1."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from panels.base_panel import Panel


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Tool Forces", **kwargs)

        self._val_labels = {}
        self._sliders = {}

        self.content.pack_start(self._channel_group(0, "Solenoid P0"),
                                True, True, 0)
        self.content.pack_start(self._channel_group(1, "Solenoid P1"),
                                True, True, 0)

    def _channel_group(self, channel: int, label: str):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=self.gtk.px(6))
        box.get_style_context().add_class("group")

        box.pack_start(self.gtk.Label(label, font="sub"), False, False, 0)

        val = self.gtk.Label("0", font="big")
        box.pack_start(val, False, False, 0)
        self._val_labels[channel] = val

        slider = self.gtk.Slider(0, 255, 0)
        slider.connect("value-changed", self._on_slider_changed, channel)
        box.pack_start(slider, False, False, 0)
        self._sliders[channel] = slider

        return box

    def _on_slider_changed(self, slider, channel):
        v = int(slider.get_value())
        self._val_labels[channel].set_text(str(v))
        self._screen.job.set_force(channel, v)