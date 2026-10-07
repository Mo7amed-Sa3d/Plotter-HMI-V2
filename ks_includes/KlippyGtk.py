"""Central widget factory for the HMI.

Every widget in every panel is built through this class. Sizing is
computed from the actual screen dimensions at startup, so the same
code renders correctly on any display. Styling comes from CSS files
in styles/<theme>/.
"""

import os
import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class KlippyGtk:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height

        # Scale factor relative to a 480x800 reference.
        self.scale = min(width / 480.0, height / 800.0)

        # Base font sizes, in points.
        self.font_ratio = [12, 18, 24]

        self._css_provider = None
        self._load_css()

    # ------------------------------------------------------------------
    # CSS
    # ------------------------------------------------------------------

    def _load_css(self):
        provider = Gtk.CssProvider()
        css_dir = os.path.join(os.path.dirname(__file__),
                               "..", "styles", "default")
        for name in ("base.css", "style.css"):
            path = os.path.abspath(os.path.join(css_dir, name))
            if os.path.exists(path):
                try:
                    provider.load_from_path(path)
                except Exception as e:
                    logging.error(f"CSS load failed for {path}: {e}")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._css_provider = provider

    def reload_css(self):
        self._load_css()

    # ------------------------------------------------------------------
    # Sizing helpers
    # ------------------------------------------------------------------

    def px(self, reference_px):
        v = int(round(reference_px * self.scale))
        return max(v, 1)

    # ------------------------------------------------------------------
    # Widget builders
    # ------------------------------------------------------------------

    def Button(self, label, style=None, icon=None,
               width=None, height=None, font=None):
        btn = Gtk.Button()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=self.px(6))
        if icon:
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DND)
            img.set_pixel_size(self.px(28))
            box.pack_start(img, False, False, 0)
        if label:
            lbl = Gtk.Label(label=label)
            lbl.set_line_wrap(True)
            if font:
                lbl.get_style_context().add_class(font)
            box.pack_start(lbl, True, True, 0)
        btn.add(box)
        if style:
            btn.get_style_context().add_class(style)
        if width or height:
            btn.set_size_request(
                self.px(width) if width else -1,
                self.px(height) if height else -1,
            )
        return btn

    def Label(self, text, style=None, font=None, wrap=False):
        lbl = Gtk.Label(label=text)
        lbl.set_line_wrap(wrap)
        if style:
            lbl.get_style_context().add_class(style)
        if font:
            lbl.get_style_context().add_class(font)
        return lbl

    def Image(self, icon, size=None):
        img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
        if size:
            img.set_pixel_size(self.px(size))
        return img

    def Slider(self, min_val, max_val, value):
        adj = Gtk.Adjustment(value=value, lower=min_val, upper=max_val,
                             step_increment=1, page_increment=10)
        s = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        s.set_draw_value(False)
        s.set_size_request(-1, self.px(48))
        return s

    def ProgressBar(self):
        pb = Gtk.ProgressBar()
        pb.set_size_request(-1, self.px(20))
        return pb

    def Scroll(self, child):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(child)
        return sw

    def Dialog(self, title, parent):
        d = Gtk.Dialog(title=title, transient_for=parent,
                       modal=True, destroy_with_parent=True)
        d.set_default_size(self.px(400), self.px(300))
        return d