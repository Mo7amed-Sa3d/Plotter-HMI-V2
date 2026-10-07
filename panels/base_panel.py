"""Base class for all panels. Provides the title bar and lifecycle.

The screen manager constructs a panel with Panel(screen, title, **kwargs)
and adds it to the window. The panel is responsible for building its own
content into self.content.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class Panel(Gtk.Box):
    def __init__(self, screen, title="", **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._screen = screen
        self.gtk = screen.gtk
        self._config = screen.config
        self.title = title
        self.kwargs = kwargs

        if title:
            self._build_title_bar(title)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content.set_margin_top(self.gtk.px(8))
        self.content.set_margin_bottom(self.gtk.px(8))
        self.content.set_margin_start(self.gtk.px(8))
        self.content.set_margin_end(self.gtk.px(8))
        self.pack_start(self.content, True, True, 0)

        self.show_all()
        self.activate()

    # ------------------------------------------------------------------
    # Title bar
    # ------------------------------------------------------------------

    def _build_title_bar(self, title):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        bar.get_style_context().add_class("title_bar")
        bar.set_size_request(-1, self.gtk.px(64))

        back = self.gtk.Button("", style="ghost", icon="go-previous",
                                width=56, height=56)
        back.connect("clicked", lambda w: self._screen.show_panel(
            self._screen.prev_panel_name()))
        bar.pack_start(back, False, False, self.gtk.px(6))

        lbl = self.gtk.Label(title, font="title")
        bar.pack_start(lbl, True, True, 0)

        spacer = Gtk.Box()
        spacer.set_size_request(self.gtk.px(56), -1)
        bar.pack_start(spacer, False, False, self.gtk.px(6))

        self.pack_start(bar, False, False, 0)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def activate(self):
        pass

    def deactivate(self):
        pass

    def process_update(self, data):
        pass