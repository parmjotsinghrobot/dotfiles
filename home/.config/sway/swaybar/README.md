# Swaybar

Native workspace buttons on the left, restricted to the current monitor.
The bar and tray appear on all monitors and remain visible across workspaces.
The bar is 26 pixels tall with workspace buttons at least 36 pixels wide.
Tray padding is 6 pixels, preserving the smaller tray icon size.
Catppuccin Mocha colours use a translucent Base background, Pink filled
focused workspace, Pink outlined workspaces visible on other monitors,
Subtext0 inactive labels and Red urgency highlights.
The status line contains, in order: playing media, a `|` separator,
Bluetooth icon, memory-chip icon and
percentage, volume, brightness, battery, time, short date. Each icon sits beside
its value, with spacing between groups. The native tray is at the far right;
its nm-applet icon provides network status.

Media shows title and artist, capped at 48 characters (24 when the bar needs
the shorter label). It and its separator disappear when nothing is playing.
The window title remains omitted.

Uses the existing Python 3/PyGObject and wpctl installations. Media properties
are queried directly over D-Bus with a 600 ms timeout per player, so a hung
browser is skipped without libplayerctl aborting the status process. No additional
status-bar package. Each module refreshes independently.

Only native workspace buttons and tray icons respond to clicks. Workspace
scrolling is disabled. All status blocks are display-only: no media controls,
brightness/volume scrolling, mixer launcher or Bluetooth toggle.

The broken audio idle inhibitor is disabled in autostart and omitted here.
Stock swaybar has no status-block hover tooltips, CSS rounded workspace
buttons, or independent left/centre/right module positioning. Calendar and
device/network hover details are therefore unavailable. No substitute popup
actions have been added.

## Apply

The running session has not been changed automatically. From a terminal:

```sh
sway -C -c ~/.config/sway/config && swaymsg reload && pkill -x waybar
```

Check the bar on each monitor, tray menus, Bluetooth state, memory percentage,
mute/output changes, brightness readings and battery state.
Reloading does not stop an already-running sway-audio-idle-inhibit process;
stop it separately if needed.

Inspect the status data independently:

```sh
python3 ~/.config/sway/swaybar/status.py --once
```

This prints module failures to stderr and one JSON snapshot to stdout.

## Previous alternatives

Swaybar is the managed bar. Waybar configuration was already staged for deletion in the original checkout; it is preserved in the private recovery snapshot and Git history, not deployed by this source tree. The old launch-waybar helper is retired by the optional legacy cleanup. wpaperd and GTKlock are also not part of the active desktop.
