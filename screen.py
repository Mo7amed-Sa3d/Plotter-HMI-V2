"""Screen manager — the top-level GTK window.

Owns:
  * the KlippyGtk widget factory
  * the panel hierarchy (stack of active panels)
  * the machine serial client
  * the job runner
  * the web server

Provides show_panel() for navigation and a periodic poll of the
machine state that is dispatched to the active panel's
process_update().
"""

import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from ks_includes.KlippyGtk import KlippyGtk
from machine import Machine
from job import Job
from web_server import start_server


class KlipperScreen(Gtk.Window):
    def __init__(self):
        super().__init__(title="Label Cutter HMI")
        self.set_decorated(False)
        self.set_resizable(False)

        # Fullscreen
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geo = monitor.get_geometry()
        self.width = geo.width
        self.height = geo.height
        self.fullscreen()

        # Widget factory
        self.gtk = KlippyGtk(self, self.width, self.height)

        # Config placeholder
        self.config = {}

        # Panel hierarchy
        self.panels = {}
        self.panel_stack = ["main_menu"]
        self.current_panel = None

        # Machine and job (headless, unchanged)
        self.machine = Machine(dispatch=self._dispatch_to_gtk)
        try:
            self.machine.open()
        except RuntimeError as e:
            logging.error(f"Serial: {e}")

        self.job = Job(self.machine, dispatch=self._dispatch_to_gtk)
        start_server(self.machine, self.job)

        # Machine callbacks
        self.machine.on_position(self._on_position)
        self.machine.on_sensors(self._on_sensors)
        self.job.on_state(self._on_job_state)
        self.job.on_progress(self._on_job_progress)

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_box)

        # Load initial panel
        self.show_panel("main_menu")

        # Periodic status poll (once per second)
        GLib.timeout_add(1000, self._poll_status)

        self.connect("destroy", Gtk.main_quit)

    # ------------------------------------------------------------------
    # Panel management
    # ------------------------------------------------------------------

    def show_panel(self, panel_name, **kwargs):
        """Replace the current panel with a new one."""
        logging.debug(f"Showing panel: {panel_name}")

        if self.current_panel is not None:
            self.current_panel.deactivate()
            self.main_box.remove(self.current_panel)

        panel_cls = self._load_panel(panel_name)
        if panel_cls is None:
            logging.error(f"Could not load panel: {panel_name}")
            return

        self.current_panel = panel_cls(self, **kwargs)
        self.panels[panel_name] = self.current_panel

        # Track hierarchy for back navigation
        if not self.panel_stack or self.panel_stack[-1] != panel_name:
            self.panel_stack.append(panel_name)

        self.main_box.pack_start(self.current_panel, True, True, 0)
        self.current_panel.show_all()

    def _load_panel(self, panel_name):
        """Dynamically import a module from panels/ and return its Panel class."""
        try:
            module = __import__(f"panels.{panel_name}", fromlist=["Panel"])
            return getattr(module, "Panel")
        except (ImportError, AttributeError) as e:
            logging.error(f"Panel {panel_name}: {e}")
            return None

    def prev_panel_name(self):
        if len(self.panel_stack) > 1:
            self.panel_stack.pop()
            return self.panel_stack[-1]
        return "main_menu"

    # ------------------------------------------------------------------
    # Machine state dispatch
    # ------------------------------------------------------------------

    def _dispatch_to_gtk(self, fn):
        """Schedule a callable to run on the GTK main thread."""
        GLib.idle_add(fn)

    def _poll_status(self):
        self.machine.refresh_status()
        return True

    def _on_position(self, pos):
        if self.current_panel is not None:
            self.current_panel.process_update({"position": pos})

    def _on_sensors(self, s):
        if self.current_panel is not None:
            self.current_panel.process_update({"sensors": s})

    def _on_job_state(self, job):
        if job.state.name == "RUNNING":
            self.show_panel("cutting")
        if self.current_panel is not None:
            self.current_panel.process_update({"job_state": job.state})

    def _on_job_progress(self, value):
        if self.current_panel is not None:
            self.current_panel.process_update({
                "progress": value,
                "job_index": self.job.current_index,
            })