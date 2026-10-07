"""Full-screen jog panel with larger arrows and a step selector."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from panels.base_panel import Panel
from protocol import home_x, zero_x, zero_y, move_linear


STEPS = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Manual Jog", **kwargs)

        # Step selector
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=self.gtk.px(6))
        row.pack_start(self.gtk.Label("Step", font="sub"), False, False, 0)
        self.step_combo = Gtk.ComboBoxText()
        for s in STEPS:
            self.step_combo.append_text(str(s))
        self.step_combo.set_active(2)   # 1.0 mm
        row.pack_start(self.step_combo, True, True, 0)
        row.pack_start(self.gtk.Label("mm", font="sub"), False, False, 0)
        self.content.pack_start(row, False, False, 0)

        # Jog pad
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_row_spacing(self.gtk.px(6))
        grid.set_column_spacing(self.gtk.px(6))

        def arrow(icon, dx, dy, row, col):
            btn = self.gtk.Button("", icon=icon, height=90)
            btn.connect("clicked", lambda w: self._do_jog(dx, dy))
            grid.attach(btn, col, row, 1, 1)

        arrow("go-up",       0, +1, 0, 1)
        arrow("go-previous",-1,  0, 1, 0)
        arrow("go-next",    +1,  0, 1, 2)
        arrow("go-down",     0, -1, 2, 1)

        home = self.gtk.Button("Home X\nZero Y/F", style="primary", height=90)
        home.connect("clicked", lambda w: self._do_home_zero())
        grid.attach(home, 1, 1, 1, 1)

        self.content.pack_start(grid, True, True, 0)

        self._jog_x = None
        self._jog_y = None

    def _do_jog(self, dx, dy):
        step = float(self.step_combo.get_active_text() or "1.0")
        p = self._screen.machine.position
        if self._jog_x is None:
            self._jog_x = p.qx if p else 0.0
            self._jog_y = p.qy if p else 0.0
        self._jog_x += dx * step
        self._jog_y += dy * step
        self._screen.machine.fire(
            move_linear(self._jog_x, self._jog_y,
                        self._screen.job.speed_override))

    def _do_home_zero(self):
        self._screen.machine.command(home_x())
        self._screen.machine.command(zero_x(0.0))
        self._screen.machine.command(zero_y(0.0))
        self._jog_x = 0.0
        self._jog_y = 0.0

    def process_update(self, data):
        if "position" in data and self._jog_x is None:
            p = data["position"]
            self._jog_x = p.qx
            self._jog_y = p.qy