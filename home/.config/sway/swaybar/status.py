#!/usr/bin/env python3
"""System status, volume shortcuts and an idle-inhibit toggle for swaybar."""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import threading

DEFAULT_SINK = "@DEFAULT_AUDIO_SINK@"
Gio = GLib = None


def load_dbus():
    # Hardware keys only need subprocesses and the FIFO. Loading GI for every
    # keypress adds substantial latency, especially while a key is repeating.
    global Gio, GLib
    from gi.repository import Gio, GLib


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          timeout=3, env={**os.environ, "LC_ALL": "C"}).stdout.strip()


def block(name, text):
    return {"name": name, "full_text": str(text), "separator": False,
              "separator_block_width": 10, "markup": "none"}


def media():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    names = bus.call_sync(
        "org.freedesktop.DBus", "/org/freedesktop/DBus",
        "org.freedesktop.DBus", "ListNames", None,
        GLib.VariantType.new("(as)"), Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
    for name in sorted(names):
        if not name.startswith("org.mpris.MediaPlayer2.") or name.endswith(".playerctld"):
            continue
        try:
            # libplayerctl can abort the whole process on a hung player's timeout.
            # Query D-Bus directly so failures stay bounded and recoverable.
            properties = bus.call_sync(
                name, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties",
                "GetAll", GLib.Variant("(s)", ("org.mpris.MediaPlayer2.Player",)),
                GLib.VariantType.new("(a{sv})"), Gio.DBusCallFlags.NO_AUTO_START,
                600, None).unpack()[0]
            if properties.get("PlaybackStatus") != "Playing":
                continue
            metadata = properties.get("Metadata", {})
        except GLib.Error:
            continue
        title = metadata.get("xesam:title", "")
        artist = ", ".join(metadata.get("xesam:artist", []))
        text = " - ".join(part for part in (title, artist) if part)
        text = " ".join((text or name.removeprefix("org.mpris.MediaPlayer2.")).split())
        label = text if len(text) <= 48 else text[:47] + "…"
        result = block("mpris", f"♪ {label}")
        result["short_text"] = "♪ " + (text if len(text) <= 24 else text[:23] + "…")
        return [result, block("media-separator", "|")]
    return []


def bluetooth():
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    objects = bus.call_sync(
        "org.bluez", "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects",
        None, GLib.VariantType.new("(a{oa{sa{sv}}})"), Gio.DBusCallFlags.NONE,
        3000, None).unpack()[0]
    adapters = [interfaces["org.bluez.Adapter1"] for interfaces in objects.values()
                if "org.bluez.Adapter1" in interfaces]
    if not adapters:
        return []
    powered = any(adapter.get("Powered", False) for adapter in adapters)
    return [block("bluetooth", "" if powered else "󰂲")]


def memory():
    info = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        info[key] = int(value.split()[0])
    percent = int(100 * (info["MemTotal"] - info["MemAvailable"]) / info["MemTotal"])
    return [block("memory", f" {percent}%")]


def read_volume():
    text = run("wpctl", "get-volume", DEFAULT_SINK)
    match = re.fullmatch(r"Volume:\s+(\d+(?:\.\d+)?)\s*(\[MUTED\])?", text)
    if match is None:
        raise ValueError(f"unexpected wpctl volume response: {text!r}")
    percent = int(float(match[1]) * 100 + 0.5)
    muted = match[2] is not None
    return percent, muted


def volume():
    percent, muted = read_volume()
    # Device metadata is optional: reconnecting a headset can invalidate its ID
    # between these queries. Keep displaying the volume with a generic icon.
    properties = ""
    try:
        properties = run("wpctl", "inspect", DEFAULT_SINK)
        device = re.search(r'device.id\s*=\s*"?(\d+)', properties)
        if device:
            properties += "\n" + run("wpctl", "inspect", device[1])
    except (OSError, subprocess.SubprocessError):
        pass
    form = re.search(r'device.form-factor\s*=\s*"([^"]+)"', properties)
    icons = {"headphone": "", "hands-free": "", "headset": "",
             "phone": "", "portable": "", "car": ""}
    factor = form[1].lower() if form else ""
    icon = next((value for key, value in icons.items() if key in factor),
                ["", "", ""][min(2, percent * 3 // 100)])
    return [block("volume", " MM" if muted else f"{icon} {percent}")]


def adjust_volume(action):
    # Resolve the default on every invocation, including after USB/BT changes.
    commands = {
        "up": ("set-volume", "-l", "1.0", DEFAULT_SINK, "5%+"),
        "down": ("set-volume", DEFAULT_SINK, "5%-"),
        "mute": ("set-mute", DEFAULT_SINK, "toggle"),
    }
    run("wpctl", *commands[action])


def adjust_brightness(action):
    steps = {"up": "5%+", "down": "5%-"}
    text = run("brightnessctl", "--machine-readable", "set", steps[action])
    return parse_brightness(text)


def read_brightness():
    return parse_brightness(run("brightnessctl", "--machine-readable", "info"))


def parse_brightness(text):
    fields = text.split(",")
    if len(fields) != 5 or not re.fullmatch(r"\d+%", fields[3]):
        raise ValueError(f"unexpected brightnessctl response: {text!r}")
    return int(fields[3][:-1])


def show_osd(percent, style):
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        raise OSError("XDG_RUNTIME_DIR is not set")
    # Nonblocking writes keep a stopped/absent overlay from delaying the keys.
    fd = os.open(Path(runtime) / "sway-osd.fifo", os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        if not stat.S_ISFIFO(os.fstat(fd).st_mode):
            raise OSError("sway-osd.fifo is not a FIFO")
        os.write(fd, f"{max(0, min(100, percent))} {style}\n".encode())
    finally:
        os.close(fd)


class IdleInhibitor:
    def __init__(self):
        self.fd = None
        self.lock = threading.Lock()

    def toggle(self):
        with self.lock:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
                return
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            reply, descriptors = bus.call_with_unix_fd_list_sync(
                "org.freedesktop.login1", "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager", "Inhibit",
                GLib.Variant("(ssss)", ("idle", "swaybar coffee",
                                       "Keep awake from swaybar", "block")),
                GLib.VariantType.new("(h)"), Gio.DBusCallFlags.NONE,
                3000, None, None)
            # get() duplicates the descriptor; closing it releases our lock.
            self.fd = descriptors.get(reply.unpack()[0])

    def blocks(self):
        with self.lock:
            active = self.fd is not None
        result = block("coffee", "☕ ON" if active else "☕ OFF")
        result["color"] = "#f5c2e7" if active else "#a6adc8"
        return [result]

    def close(self):
        with self.lock:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None


inhibitor = IdleInhibitor()


def handle_click(event):
    if isinstance(event, dict) and event.get("name") == "coffee" and event.get("button") == 1:
        inhibitor.toggle()
        return True
    return False


def read_clicks(refresh):
    # Swaybar sends an opening '[' followed by one JSON object per line,
    # with commas preceding subsequent objects.
    for line in sys.stdin:
        line = line.strip().lstrip(",")
        if line in ("", "[", "]"):
            continue
        try:
            if handle_click(json.loads(line)):
                refresh()
        except (ValueError, OSError, GLib.Error) as error:
            print(f"click: {error}", file=sys.stderr, flush=True)


def backlight():
    devices = sorted(Path("/sys/class/backlight").glob("*"))
    if not devices:
        return []
    device = devices[0]
    maximum = int((device / "max_brightness").read_text())
    actual = device / "actual_brightness"
    current = int((actual if actual.exists() else device / "brightness").read_text())
    percent = int(current * 100 / maximum + 0.5)
    return [block("backlight", f" {percent}%")]


def battery():
    # Ignore mouse/touchpad batteries: Waybar's battery module is the laptop battery.
    devices = [p for p in sorted(Path("/sys/class/power_supply").glob("*"))
               if (p / "type").read_text().strip() == "Battery"
               and (not (p / "scope").exists() or (p / "scope").read_text().strip() != "Device")]
    if not devices:
        return []
    device = devices[0]
    capacity = int((device / "capacity").read_text())
    status = (device / "status").read_text().strip()
    icon = ["", "", "", "", ""][min(4, capacity * 5 // 100)]
    if status == "Charging":
        icon = ""
    elif status == "Full":
        icon = ""
    value = "FULL" if status == "Full" else f"{capacity}%"
    return [block("battery", f"{icon} {value}")]


def clock():
    now = datetime.datetime.now().astimezone()
    date = block("date", now.strftime("%a %d/%m"))
    # The date is next to the tray; use a smaller gap here.
    date["separator_block_width"] = 6
    return [block("clock", now.strftime("%H:%M")), date]


MODULES = [("mpris", media, 5), ("bluetooth", bluetooth, 20),
           ("memory", memory, 15), ("volume", volume, 2),
           ("backlight", backlight, 2), ("battery", battery, 10),
           ("coffee", inhibitor.blocks, 2), ("clock", clock, 10)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="print a single JSON snapshot")
    mode.add_argument("--volume", choices=("up", "down", "mute"),
                      help="adjust the same default output that the bar reports")
    mode.add_argument("--brightness", choices=("up", "down"),
                      help="adjust brightness by 5% and show the overlay")
    args = parser.parse_args()
    if args.volume or args.brightness:
        try:
            if args.volume:
                adjust_volume(args.volume)
            else:
                percent = adjust_brightness(args.brightness)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            parser.exit(1, f"adjustment: {error}\n")
        # Feedback is best-effort: a missing OSD must not fail an adjustment.
        try:
            if args.volume:
                percent, muted = read_volume()
                style = "muted" if muted else "volume"
            else:
                style = "brightness"
            show_osd(percent, style)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            print(f"osd: {error}", file=sys.stderr)
        return
    load_dbus()
    cache, lock, changed = {}, threading.Lock(), threading.Event()
    errors = {}
    stop = threading.Event()

    def collect(name, function):
        error = None
        try:
            result = function()
        except Exception as exception:
            # This is the worker boundary: an unexpected parser error must not
            # kill polling and leave the last cached value frozen indefinitely.
            result = []
            error = f"{type(exception).__name__}: {exception}"
        with lock:
            if error is not None and errors.get(name) != error:
                print(f"{name}: {error}", file=sys.stderr, flush=True)
            errors[name] = error
            cache[name] = result
        changed.set()

    def worker(name, function, interval):
        while not stop.is_set():
            collect(name, function)
            stop.wait(interval)

    def snapshot():
        with lock:
            return [b for name, _, _ in MODULES for b in cache.get(name, [])
                    if b["full_text"]]

    if args.once:
        threads = [threading.Thread(target=collect, args=(name, function))
                   for name, function, _ in MODULES]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        print(json.dumps(snapshot(), ensure_ascii=False))
        return

    def terminate(*_):
        stop.set()
        changed.set()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    print('{"version":1,"click_events":true}', flush=True)
    print("[", flush=True)
    for name, function, interval in MODULES:
        threading.Thread(target=worker, args=(name, function, interval), daemon=True).start()
    threading.Thread(target=read_clicks,
                     args=(lambda: collect("coffee", inhibitor.blocks),), daemon=True).start()
    first = True
    previous = None
    try:
        while not stop.is_set():
            changed.wait()
            changed.clear()
            current = snapshot()
            if current != previous:
                print(("" if first else ",") + json.dumps(current, ensure_ascii=False), flush=True)
                first, previous = False, current
    except BrokenPipeError:
        pass
    finally:
        stop.set()
        inhibitor.close()


if __name__ == "__main__":
    main()
