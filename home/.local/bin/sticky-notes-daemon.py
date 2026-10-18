#!/usr/bin/env python3

import i3ipc
import fcntl
import os
from pathlib import Path

# Keep the lock descriptor open for this process; Sway reloads use exec_always.
_runtime = Path(os.environ.get("XDG_RUNTIME_DIR", str(Path.home() / ".cache/dotfiles")))
_runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
_lock_fd = os.open(_runtime / "sticky-notes-daemon.lock", os.O_CREAT | os.O_RDWR, 0o600)
try:
    fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(0)

APP_ID = "sticky-notes"

i3 = i3ipc.Connection()

hidden = False


def find_note():
    for con in i3.get_tree().leaves():
        if con.app_id == APP_ID:
            return con
    return None


def count_tiled():
    tree = i3.get_tree()
    ws = tree.find_focused().workspace()

    count = 0

    for con in ws.leaves():
        if con.app_id == APP_ID:
            continue

        # Ignore floating windows
        if con.floating in ("user_on", "auto_on"):
            continue

        count += 1

    return count


def update():
    global hidden

    note = find_note()
    if note is None:
        return

    tiled = count_tiled()

    if tiled > 0 and not hidden:
        note.command("move scratchpad")
        hidden = True

    elif tiled == 0 and hidden:
        i3.command(f'[app_id="{APP_ID}"] scratchpad show')
        hidden = False


def handler(i3, event):
    update()


for ev in (
    "window::new",
    "window::close",
    "window::move",
    "window::floating",
    "window::focus",
    "workspace::focus",
):
    i3.on(ev, handler)

update()
i3.main()
