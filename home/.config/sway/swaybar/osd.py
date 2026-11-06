#!/usr/bin/env python3
"""Small, non-interactive layer-shell overlay fed by sway-osd.socket."""

import configparser
import os
from pathlib import Path
import queue
import sys
import threading

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("PangoCairo", "1.0")
from gi.repository import GLib, Gtk, GtkLayerShell, Pango, PangoCairo


def parse_reading(line):
    value, style = line.split()
    percent = int(value)
    if not 0 <= percent <= 100 or style not in ("volume", "brightness", "muted"):
        raise ValueError(f"invalid overlay reading: {line!r}")
    return percent, style


def colour(value):
    text = value.removeprefix("#")
    if len(text) not in (6, 8):
        raise ValueError(f"invalid colour: {value!r}")
    rgba = [int(text[i:i + 2], 16) / 255 for i in range(0, len(text), 2)]
    return (*rgba, 1.0) if len(rgba) == 3 else tuple(rgba)


def feedback_reading(kind, controls):
    if kind == "volume":
        percent, muted = controls.read_volume()
        style = "muted" if muted else "volume"
    else:
        percent, style = controls.read_brightness(), "brightness"
    return f"{max(0, min(100, percent))} {style}"


def refresh_worker(overlay, controls):
    while True:
        kind = overlay.refresh_requests.get()
        # Percentage queries may lag behind a held key. Only query the newest
        # requested control; adjustments run directly in the Sway shortcuts.
        while True:
            try:
                kind = overlay.refresh_requests.get_nowait()
            except queue.Empty:
                break
        try:
            reading = feedback_reading(kind, controls)
        except Exception as error:
            print(f"osd refresh: {error}", file=sys.stderr, flush=True)
            continue
        GLib.idle_add(overlay.update, reading)


class Overlay:
    def __init__(self):
        config = configparser.ConfigParser()
        with Path(__file__).with_name("osd.ini").open() as source:
            config.read_file(source)
        self.settings = config["overlay"]
        self.percent, self.style = 0, "volume"
        self.timer = None
        self.fade_timer = None
        self.opacity = 1.0
        self.pending = b""
        self.refresh_requests = queue.SimpleQueue()
        self.window = Gtk.Window()
        self.window.set_app_paintable(True)
        self.window.set_accept_focus(False)
        self.window.set_visual(self.window.get_screen().get_rgba_visual())
        GtkLayerShell.init_for_window(self.window)
        GtkLayerShell.set_namespace(self.window, "hardware-osd")
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.BOTTOM,
                                self.settings.getint("margin"))
        GtkLayerShell.set_exclusive_zone(self.window, 0)
        self.window.connect("realize", lambda window:
                            window.get_window().input_shape_combine_region(cairo.Region(), 0, 0))
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(self.settings.getint("width"), self.settings.getint("height"))
        self.area.connect("draw", self.draw)
        self.window.add(self.area)

    def draw(self, area, context):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        context.save()
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.set_source_rgba(0, 0, 0, 0)
        context.paint()
        context.restore()
        context.push_group()
        context.set_source_rgba(*colour(self.settings["background"]))
        context.paint()
        context.set_source_rgba(*colour(self.settings["border"]))
        context.set_line_width(1)
        context.rectangle(0.5, 0.5, width - 1, height - 1)
        context.stroke()
        bar_width = width - 56
        context.set_source_rgba(*colour(self.settings["track"]))
        context.rectangle(6, 6, bar_width, height - 12)
        context.fill()
        context.set_source_rgba(*colour(self.settings[self.style]))
        context.rectangle(6, 6, bar_width * self.percent / 100, height - 12)
        context.fill()
        layout = PangoCairo.create_layout(context)
        layout.set_font_description(Pango.FontDescription(self.settings["font"]))
        layout.set_text(f"{self.percent}%", -1)
        text_width, text_height = layout.get_pixel_size()
        context.set_source_rgba(*colour(self.settings["foreground"]))
        context.move_to(width - text_width - 7, (height - text_height) / 2)
        PangoCairo.show_layout(context, layout)
        context.pop_group_to_source()
        context.paint_with_alpha(self.opacity)
        return False

    def update(self, line):
        self.percent, self.style = parse_reading(line)
        if self.timer is not None:
            GLib.source_remove(self.timer)
        if self.fade_timer is not None:
            GLib.source_remove(self.fade_timer)
            self.fade_timer = None
        self.opacity = 1.0
        self.window.show_all()
        self.area.queue_draw()
        self.timer = GLib.timeout_add(self.settings.getint("timeout"), self.begin_fade)

    def begin_fade(self):
        self.timer = None
        if self.settings.getint("fade", fallback=180) <= 0:
            return self.hide()
        self.fade_started = GLib.get_monotonic_time()
        self.fade_timer = GLib.timeout_add(16, self.fade_step)
        return GLib.SOURCE_REMOVE

    def fade_step(self):
        duration = self.settings.getint("fade", fallback=180) * 1000
        elapsed = GLib.get_monotonic_time() - self.fade_started
        progress = min(1.0, max(0.0, elapsed / duration))
        self.opacity = 1 - progress * progress * (3 - 2 * progress)
        self.area.queue_draw()
        if progress >= 1:
            self.fade_timer = None
            return self.hide()
        return GLib.SOURCE_CONTINUE

    def hide(self):
        self.window.hide()
        self.timer = None
        return GLib.SOURCE_REMOVE

    def read_input(self, fd, condition):
        try:
            data = os.read(fd, 4096)
        except BlockingIOError:
            return GLib.SOURCE_CONTINUE
        if not data:
            Gtk.main_quit()
            return GLib.SOURCE_REMOVE
        self.pending += data
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            try:
                if line in (b"refresh volume", b"refresh brightness"):
                    self.refresh_requests.put(line.decode("ascii").split()[1])
                else:
                    self.update(line.decode("ascii"))
            except ValueError as error:
                print(f"osd: {error}", file=sys.stderr, flush=True)
        # Do not retain an unbounded partial line from a broken writer.
        if len(self.pending) > 128:
            self.pending = b""
        return GLib.SOURCE_CONTINUE


def main():
    import status as controls
    overlay = Overlay()
    threading.Thread(target=refresh_worker, args=(overlay, controls), daemon=True).start()
    fd = sys.stdin.fileno()
    os.set_blocking(fd, False)
    GLib.io_add_watch(fd, GLib.IO_IN | GLib.IO_HUP, overlay.read_input)
    Gtk.main()


if __name__ == "__main__":
    main()
