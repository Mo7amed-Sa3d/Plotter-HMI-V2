"""Cutting progress panel: filename, progress, preview, pause/resume."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from panels.base_panel import Panel


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Cutting", **kwargs)

        # Filename
        self.file_label = self.gtk.Label("No file", font="title")
        self.content.pack_start(self.file_label, False, False, 0)

        # Preview area (drawn with a drawing area later; for now a
        # simple placeholder label).
        self.preview = Gtk.DrawingArea()
        self.preview.set_size_request(-1, self.gtk.px(220))
        self.content.pack_start(self.preview, True, True, 0)

        # Percent
        self.percent = self.gtk.Label("0.0 %", font="big")
        self.content.pack_start(self.percent, False, False, 0)

        # Progress bar
        self.bar = self.gtk.ProgressBar()
        self.content.pack_start(self.bar, False, False, 0)

        # Control buttons
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                      spacing=self.gtk.px(8))
        self.pause_btn = self.gtk.Button("Pause", style="primary", height=56)
        self.resume_btn = self.gtk.Button("Resume", style="success", height=56)
        settings_btn = self.gtk.Button("Settings", height=56)
        cancel_btn = self.gtk.Button("Cancel", style="danger", height=56)

        self.pause_btn.connect("clicked", lambda w: self._screen.job.pause())
        self.resume_btn.connect("clicked", lambda w: self._screen.job.resume())
        settings_btn.connect("clicked", lambda w: self._open_settings())
        cancel_btn.connect("clicked", lambda w: self._cancel())

        row.pack_start(self.pause_btn, True, True, 0)
        row.pack_start(self.resume_btn, True, True, 0)
        row.pack_start(settings_btn, True, True, 0)
        row.pack_start(cancel_btn, True, True, 0)

        self.content.pack_start(row, False, False, 0)

        self.resume_btn.hide()

        self._total_moves = 0

    # ---- Public ----

    def set_file(self, path):
        self.file_label.set_text(path.split("/")[-1])

    def set_job(self, job):
        self._total_moves = len(job.moves) if job else 0

    # ---- Handlers ----

    def _cancel(self):
        self._screen.job.cancel()
        self._screen.show_panel("main_menu")

    def _open_settings(self):
        d = self.gtk.Dialog("Cutting Settings", self._screen)

        grid = Gtk.Grid(column_spacing=self.gtk.px(8),
                        row_spacing=self.gtk.px(8))
        grid.attach(self.gtk.Label("Speed (mm/s)"), 0, 0, 1, 1)
        speed = Gtk.SpinButton.new_with_range(1, 200, 1)
        speed.set_value(int(self._screen.job.speed_override))
        grid.attach(speed, 1, 0, 1, 1)

        grid.attach(self.gtk.Label("Force P0"), 0, 1, 1, 1)
        fa = Gtk.SpinButton.new_with_range(0, 255, 1)
        fa.set_value(self._screen.job.force_a)
        grid.attach(fa, 1, 1, 1, 1)

        grid.attach(self.gtk.Label("Force P1"), 0, 2, 1, 1)
        fb = Gtk.SpinButton.new_with_range(0, 255, 1)
        fb.set_value(self._screen.job.force_b)
        grid.attach(fb, 1, 2, 1, 1)

        d.get_content_area().pack_start(grid, True, True, 0)
        d.add_button("Cancel", Gtk.ResponseType.CANCEL)
        d.add_button("OK", Gtk.ResponseType.OK)

        r = d.run()
        if r == Gtk.ResponseType.OK:
            self._screen.job.set_speed(float(speed.get_value()))
            self._screen.job.set_force(0, int(fa.get_value()))
            self._screen.job.set_force(1, int(fb.get_value()))
        d.destroy()

    # ---- Data updates ----

    def process_update(self, data):
        if "progress" in data:
            v = data["progress"]
            self.bar.set_fraction(v)
            self.percent.set_text(f"{v * 100:.1f} %")
        if "job_state" in data:
            from job import JobState
            st = data["job_state"]
            if st == JobState.PAUSED:
                self.pause_btn.hide()
                self.resume_btn.show()
            elif st == JobState.RUNNING:
                self.resume_btn.hide()
                self.pause_btn.show()