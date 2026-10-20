#!/usr/bin/env python3
"""Display-only system status for swaybar."""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading

import gi

gi.require_version("Playerctl", "2.0")
from gi.repository import Gio, GLib, Playerctl


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          timeout=3, env={**os.environ, "LC_ALL": "C"}).stdout.strip()


def block(name, text):
    return {"name": name, "full_text": str(text), "separator": False,
              "separator_block_width": 10, "markup": "none"}


def media():
    for name in Playerctl.list_players():
        if name.name == "playerctld":
            continue
        try:
            player = Playerctl.Player.new_from_name(name)
            if player.props.playback_status != Playerctl.PlaybackStatus.PLAYING:
                continue
            metadata = player.props.metadata.unpack() if player.props.metadata else {}
        except GLib.Error:
            continue
        title = metadata.get("xesam:title", "")
        artist = ", ".join(metadata.get("xesam:artist", []))
        text = " - ".join(part for part in (title, artist) if part)
        text = " ".join((text or player.props.player_name).split())
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


def volume():
    text = run("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@")
    percent = int(float(text.split()[1]) * 100 + 0.5)
    muted = "MUTED" in text
    properties = run("wpctl", "inspect", "@DEFAULT_AUDIO_SINK@")
    device = re.search(r'device.id\s*=\s*"?(\d+)', properties)
    if device:
        properties += "\n" + run("wpctl", "inspect", device[1])
    form = re.search(r'device.form-factor\s*=\s*"([^"]+)"', properties)
    icons = {"headphone": "", "hands-free": "", "headset": "",
             "phone": "", "portable": "", "car": ""}
    factor = form[1].lower() if form else ""
    icon = next((value for key, value in icons.items() if key in factor),
                ["", "", ""][min(2, percent * 3 // 100)])
    return [block("volume", " MM" if muted else f"{icon} {percent}")]


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
           ("clock", clock, 10)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="print a single JSON snapshot")
    args = parser.parse_args()
    cache, lock, changed = {}, threading.Lock(), threading.Event()
    stop = threading.Event()

    def collect(name, function):
        try:
            result = function()
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, GLib.Error) as error:
            # A missing player/device must not take the rest of the bar down.
            result = []
            if args.once:
                print(f"{name}: {error}", file=sys.stderr)
        with lock:
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
    print('{"version":1,"click_events":false}', flush=True)
    print("[", flush=True)
    for name, function, interval in MODULES:
        threading.Thread(target=worker, args=(name, function, interval), daemon=True).start()
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


if __name__ == "__main__":
    main()
