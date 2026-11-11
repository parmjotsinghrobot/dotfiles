#!/usr/bin/env python3
"""Swap the focused workspace with the next numbered slot (1–10)."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def sway(*args):
    result = subprocess.run(
        ["swaymsg", "-r", *args], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def swap_commands(workspaces, direction):
    current = next(ws for ws in workspaces if ws["focused"])
    number = current["num"]
    target = number + direction
    if not (1 <= number <= 10 and 1 <= target <= 10):
        return []

    neighbours = [ws for ws in workspaces if ws["num"] == target]
    # Ambiguous numbering should not silently select a workspace.
    if len(neighbours) > 1 or sum(ws["num"] == number for ws in workspaces) > 1:
        raise ValueError("Workspace numbers must be unique")
    neighbour = neighbours[0] if neighbours else None

    def numbered_name(ws, new_number):
        # Keep labels such as '3: browser' attached to their workspace.
        return str(new_number) + ws["name"][len(str(ws["num"])):]

    def rename(old, new):
        return f"rename workspace {json.dumps(old)} to {json.dumps(new)}"

    if neighbour is None:
        return [rename(current["name"], numbered_name(current, target))]

    temporary = "__workspace_swap_" + uuid.uuid4().hex
    return [
        rename(current["name"], temporary),
        rename(neighbour["name"], numbered_name(neighbour, number)),
        rename(temporary, numbered_name(current, target)),
    ]


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("left", "right"):
        raise ValueError("Usage: shift-workspace.py left|right")
    # Serialise key repeats so each swap reads the previous swap's result.
    lock_path = Path(os.environ["XDG_RUNTIME_DIR"]) / "sway-workspace-swap.lock"
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        commands = swap_commands(
            sway("-t", "get_workspaces"), -1 if sys.argv[1] == "left" else 1
        )
        if commands:
            replies = sway("; ".join(commands))
            for reply in replies:
                if not reply.get("success"):
                    raise RuntimeError(reply.get("error", "Workspace swap failed"))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Workspace swap: {error}", file=sys.stderr)
        sys.exit(1)
