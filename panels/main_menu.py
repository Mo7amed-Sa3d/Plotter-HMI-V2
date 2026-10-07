"""Main menu panel: 6 buttons + jog pad."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from panels.base_panel import Panel
from protocol import home_x, zero_x, zero_y, move_linear


JOG_STEP_MM = 1.0


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Label Cutter", **kwargs)

        # ---- Menu buttons (2 x 3) ----
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_row_spacing(self.gtk.px(8))
        grid.set_column_spacing(self.gtk.px(8))

        def add(text, style, row, col, handler):
            btn = self.gtk.Button(text, style=style, height=66)
            btn.connect("clicked", lambda w: handler())
            grid.attach(btn, col, row, 1, 1)

        add("Tool Forces", None,      0, 0, lambda: self._screen.show_panel("tool_forces"))
        add("Speed",       None,      0, 1, lambda: self._screen.show_panel("speed"))
        add("Test Cut",    None,      1, 0, lambda: self._screen.show_panel("test_cut"))
        add("E-Stop",      "danger",  1, 1, self._do_estop)
        add("Settings",    None,      2, 0, lambda: self._screen.show_panel("settings"))
        add("Cut from USB","primary", 2, 1, lambda: self._screen.show_panel("usb"))

        self.content.pack_start(grid, False, False, 0)

        # ---- Separator ----
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(self.gtk.px(10))
        sep.set_margin_bottom(self.gtk.px(10))
        self.content.pack_start(sep, False, False, 0)

        # ---- Jog pad ----
        jog_grid = Gtk.Grid()
        jog_grid.set_column_homogeneous(True)
        jog_grid.set_row_homogeneous(True)
        jog_grid.set_row_spacing(self.gtk.px(6))
        jog_grid.set_column_spacing(self.gtk.px(6))

        def arrow(icon, dx, dy, row, col):
            btn = self.gtk.Button("", icon=icon, height=72)
            btn.connect("clicked", lambda w: self._do_jog(dx, dy))
            jog_grid.attach(btn, col, row, 1, 1)

        arrow("go-up",       0, +1, 0, 1)
        arrow("go-previous",-1,  0, 1, 0)
        arrow("go-next",    +1,  0, 1, 2)
        arrow("go-down",     0, -1, 2, 1)

        home = self.gtk.Button("Home X\nZero Y/F", style="primary", height=72)
        home.connect("clicked", lambda w: self._do_home_zero())
        jog_grid.attach(home, 1, 1, 1, 1)

        self.content.pack_start(jog_grid, True, True, 0)

        self._jog_x = 0.0
        self._jog_y = 0.0

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    def _do_jog(self, dx, dy):
        p = self._screen.machine.position
        base_x = self._jog_x if self._jog_x is not None else (p.qx if p else 0.0)
        base_y = self._jog_y if self._jog_y is not None else (p.qy if p else 0.0)
        self._jog_x = base_x + dx * JOG_STEP_MM
        self._jog_y = base_y + dy * JOG_STEP_MM
        self._screen.machine.fire(
            move_linear(self._jog_x, self._jog_y,
                        self._screen.job.speed_override))

    def _do_home_zero(self):
        self._screen.machine.command(home_x())
        self._screen.machine.command(zero_x(0.0))
        self._screen.machine.command(zero_y(0.0))
        self._jog_x = 0.0
        self._jog_y = 0.0

    def _do_estop(self):
        self._screen.machine.fire("STOP")

    # ------------------------------------------------------------------
    # Data updates
    # ------------------------------------------------------------------

    def process_update(self, data):
        if "position" in data:
            p = data["position"]
            if self._jog_x is None and p is not None:
                self._jog_x = p.qx
                self._jog_y = p.qy