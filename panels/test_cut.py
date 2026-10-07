"""Test cut panel: draw a small calibration pattern."""

import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from panels.base_panel import Panel
from gcode_parser import parse_text


TEST_PATTERNS = {
    "Square 20x20": """
G21
G90
G1 X20 Y0 F40
G1 X20 Y20
G1 X0 Y20
G1 X0 Y0
""",
    "Circle 20 mm": """
G21
G90
G1 X20 Y10 F40
G1 X19.7 Y13.9
G1 X18.9 Y17.7
G1 X17.4 Y21.2
G1 X15.3 Y24.4
G1 X12.6 Y27.0
G1 X9.5 Y29.0
G1 X6.2 Y30.2
G1 X2.7 Y30.7
G1 X-0.8 Y30.3
G1 X-4.1 Y29.1
G1 X-7.1 Y27.2
G1 X-9.6 Y24.7
G1 X-11.5 Y21.6
G1 X-12.6 Y18.2
G1 X-13.0 Y14.7
G1 X-12.4 Y11.2
G1 X-11.1 Y7.9
G1 X-9.1 Y5.0
G1 X-6.5 Y2.6
G1 X-3.4 Y0.8
G1 X0 Y0
""",
}


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Test Cut", **kwargs)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=self.gtk.px(6))
        row.pack_start(self.gtk.Label("Pattern:", font="sub"), False, False, 0)
        self.combo = Gtk.ComboBoxText()
        for name in TEST_PATTERNS:
            self.combo.append_text(name)
        self.combo.set_active(0)
        row.pack_start(self.combo, True, True, 0)
        self.content.pack_start(row, False, False, 0)

        run = self.gtk.Button("Run Test Cut", style="primary", height=80)
        run.connect("clicked", lambda w: self._run())
        self.content.pack_start(run, True, True, 0)

    def _run(self):
        name = self.combo.get_active_text()
        gcode = TEST_PATTERNS[name].strip()
        job = parse_text(gcode)
        self._screen.cutting.set_file("test_cut")
        self._screen.job.job = job
        self._screen.job.total_moves = len(job.moves)
        self._screen.job.current_index = 0
        from job import JobState
        self._screen.job.state = JobState.RUNNING
        self._screen.show_panel("cutting")
        threading.Thread(target=self._screen.job._run, daemon=True).start()