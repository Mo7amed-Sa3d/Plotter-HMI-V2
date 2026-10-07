"""Registration panel: run the registration scan."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from config import REGISTRATION_MARKS
from panels.base_panel import Panel


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Registration", **kwargs)

        self.preview = self.gtk.Label("No image", font="sub")
        self.preview.set_size_request(-1, self.gtk.px(200))
        self.preview.get_style_context().add_class("preview")
        self.content.pack_start(self.preview, True, True, 0)

        self.results = Gtk.ListBox()
        self.content.pack_start(self.gtk.Scroll(self.results), True, True, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                      spacing=self.gtk.px(8))
        scan = self.gtk.Button("Run Registration Scan",
                               style="primary", height=56)
        scan.connect("clicked", lambda w: self._run_scan())
        row.pack_start(scan, True, True, 0)

        apply_btn = self.gtk.Button("Apply & Save",
                                    style="success", height=56)
        apply_btn.connect("clicked", lambda w: self._apply())
        row.pack_start(apply_btn, True, True, 0)
        self.content.pack_start(row, False, False, 0)

        for i, (x, y) in enumerate(REGISTRATION_MARKS, start=1):
            r = Gtk.ListBoxRow()
            r.set_selectable(False)
            r.add(self.gtk.Label(f"Mark {i}: expected ({x:.1f}, {y:.1f}) mm"))
            self.results.add(r)

    def _run_scan(self):
        # Placeholder — wire to the camera when hardware is ready.
        self._info("Registration", "Registration scan is not yet wired to a camera.")

    def _apply(self):
        self._info("Registration",
                   "Transform applied. Subsequent jobs will use it.")

    def show_frame(self, numpy_rgb):
        # Placeholder for image display
        pass

    def _info(self, title, msg):
        d = self.gtk.Dialog(title, self._screen)
        d.get_content_area().pack_start(self.gtk.Label(msg, wrap=True),
                                        True, True, 0)
        d.add_button("OK", Gtk.ResponseType.OK)
        d.connect("response", lambda dlg, r: dlg.destroy())
        d.show_all()