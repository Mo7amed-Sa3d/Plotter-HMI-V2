"""Settings panel: Wi-Fi and Ethernet configuration."""

import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from panels.base_panel import Panel


class Panel(Panel):
    def __init__(self, screen, **kwargs):
        super().__init__(screen, title="Settings", **kwargs)

        scroll = self.gtk.Scroll(Gtk.Box())
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=self.gtk.px(10))
        scroll.remove(scroll.get_child())
        scroll.add(inner)

        # Wi-Fi group
        wifi_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=self.gtk.px(6))
        wifi_box.get_style_context().add_class("group")
        wifi_box.pack_start(self.gtk.Label("Wi-Fi", font="sub"), False, False, 0)

        self.wifi_list = Gtk.ListBox()
        self.wifi_list.set_size_request(-1, self.gtk.px(140))
        wifi_box.pack_start(self.wifi_list, True, True, 0)

        scan_btn = self.gtk.Button("Scan", height=44)
        scan_btn.connect("clicked", lambda w: self._scan_wifi())
        wifi_box.pack_start(scan_btn, False, False, 0)

        grid = Gtk.Grid(column_spacing=self.gtk.px(6), row_spacing=self.gtk.px(6))
        grid.attach(self.gtk.Label("SSID", font="sub"), 0, 0, 1, 1)
        self.ssid_entry = Gtk.Entry()
        grid.attach(self.ssid_entry, 1, 0, 1, 1)

        grid.attach(self.gtk.Label("Password", font="sub"), 0, 1, 1, 1)
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        grid.attach(self.pass_entry, 1, 1, 1, 1)
        wifi_box.pack_start(grid, False, False, 0)

        connect_btn = self.gtk.Button("Connect", style="primary", height=44)
        connect_btn.connect("clicked", lambda w: self._connect_wifi())
        wifi_box.pack_start(connect_btn, False, False, 0)

        inner.pack_start(wifi_box, False, False, 0)

        # Ethernet group
        eth_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=self.gtk.px(6))
        eth_box.get_style_context().add_class("group")
        eth_box.pack_start(self.gtk.Label("Ethernet", font="sub"), False, False, 0)

        self.eth_status = self.gtk.Label("—", wrap=True)
        eth_box.pack_start(self.eth_status, False, False, 0)

        refresh_btn = self.gtk.Button("Refresh", height=44)
        refresh_btn.connect("clicked", lambda w: self._refresh_eth())
        eth_box.pack_start(refresh_btn, False, False, 0)

        inner.pack_start(eth_box, False, False, 0)

        self.content.pack_start(scroll, True, True, 0)

        GLib.idle_add(self._refresh_eth)

    # ---- Wi-Fi ----

    def _scan_wifi(self):
        for child in self.wifi_list.get_children():
            self.wifi_list.remove(child)
        try:
            out = subprocess.check_output(
                ["nmcli", "-t", "-f", "SSID,SIGNAL", "device", "wifi"],
                timeout=10).decode()
            for line in out.splitlines():
                parts = line.rsplit(":", 1)
                if len(parts) != 2:
                    continue
                ssid, signal = parts
                row = Gtk.ListBoxRow()
                row.add(self.gtk.Label(f"{ssid}   ({signal}%)"))
                row.ssid = ssid
                self.wifi_list.add(row)
            self.wifi_list.show_all()
        except Exception as e:
            self._error("Wi-Fi", f"Scan failed: {e}")

    def _connect_wifi(self):
        row = self.wifi_list.get_selected_row()
        ssid = row.ssid if row else self.ssid_entry.get_text()
        pwd = self.pass_entry.get_text()
        if not ssid:
            self._error("Wi-Fi", "Select or type an SSID.")
            return
        try:
            subprocess.check_call(
                ["nmcli", "device", "wifi", "connect", ssid, "password", pwd],
                timeout=30)
            self._info("Wi-Fi", f"Connected to {ssid}.")
        except Exception as e:
            self._error("Wi-Fi", f"Connect failed: {e}")

    # ---- Ethernet ----

    def _refresh_eth(self):
        try:
            out = subprocess.check_output(
                ["ip", "-brief", "addr", "show"], timeout=5).decode()
            lines = [l for l in out.splitlines()
                     if l.startswith(("eth", "en"))]
            self.eth_status.set_text("\n".join(lines) if lines else "No Ethernet")
        except Exception:
            self.eth_status.set_text("Unable to query interfaces")
        return False

    # ---- Message helpers ----

    def _info(self, title, msg):
        d = self.gtk.Dialog(title, self._screen)
        d.get_content_area().pack_start(self.gtk.Label(msg, wrap=True),
                                        True, True, 0)
        d.add_button("OK", Gtk.ResponseType.OK)
        d.connect("response", lambda dlg, r: dlg.destroy())
        d.show_all()

    def _error(self, title, msg):
        self._info(title, msg)