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
percentage, volume, brightness, battery, coffee toggle, time, short date. Each icon sits beside
its value, with spacing between groups. The native tray is at the far right;
its nm-applet icon provides network status.

Media shows title and artist, capped at 48 characters (24 when the bar needs
the shorter label). It and its separator disappear when nothing is playing.
The window title remains omitted.

Uses the existing Python 3/PyGObject and wpctl installations. Media properties
are queried directly over D-Bus with a 600 ms timeout per player, so a hung
browser is skipped without libplayerctl aborting the status process. No additional
status-bar package. Each module refreshes independently.
Polling failures clear that module's stale reading and retry automatically;
unexpected exceptions cannot permanently stop a module's worker. Repeated
identical errors are logged once until the error changes or the module recovers.
Volume readings remain available when only the optional device-icon lookup fails.

The volume keys invoke `wpctl` directly, sharing the bar's
`@DEFAULT_AUDIO_SINK@` target. WirePlumber resolves it on every command and
reading, so default-output changes to Bluetooth or USB need no config reload.
Steps remain 5%, raising is capped at 100%, and mute toggles without changing
the volume. This follows the default output, not a separately routed app stream.
The shortcuts adjust the device before requesting feedback from the existing
overlay over its FIFO. There is no Python startup before the adjustment.
Percentage queries run on the overlay's background worker, with queued refreshes
coalesced to the newest request. They cannot delay an adjustment or the fade.
The overlay starts once at Sway login to avoid loading GTK on the first press.
The manual `status.py --volume up|down|mute` and `--brightness up|down` commands
remain available. D-Bus loads only for the bar itself.

Volume, mute and brightness keys also update one small GTK overlay (220 × 28 px,
bottom centre, 900 ms hold then 180 ms fade), with a bar and percentage label.
Volume is Pink, brightness Yellow and muted volume is
dimmed while retaining the stored level. Brightness steps remain 5%. This adds
no Dunst notifications or history entries. Configure size, position, colours
and timeout in `~/.config/sway/swaybar/osd.ini`. The `sway-osd.socket` user unit owns
`$XDG_RUNTIME_DIR/sway-osd.fifo` and starts the overlay on demand. After deploying new
files, run `systemctl --user daemon-reload` and
`systemctl --user enable --now sway-osd.socket`. For later overlay config edits,
restart `sway-osd.service`.
The renderer handles fading because SwayFX 0.6 does not animate layer-shell
surfaces. Another keypress cancels the fade and restores full opacity; setting
`fade = 0` disables it.

Left-click `☕ OFF` to keep the session awake; `☕ ON` is Pink while active.
Click again to release it. The bar holds a logind `idle` inhibitor, respected
by the existing swayidle configuration. Closing/restarting the status provider
also releases it; it starts off. It does not block explicit suspend or lid-close
actions. Failure to acquire the inhibitor leaves it off and logs the error.
Native workspace buttons and tray menus still work. Workspace scrolling is
disabled. Other status blocks remain display-only: no media controls,
brightness/volume scrolling, mixer launcher or Bluetooth toggle.

Audio idle inhibition runs separately from the bar via
`sway-audio-idle-inhibit`. Active playback or recording blocks the five-minute
idle suspend; stopping it starts a fresh idle countdown. Keep swayidle's
`before-sleep` hooks: timeout-only invocations on swayidle 1.9.1 can fail to
connect to logind and ignore the inhibitor. See
<https://github.com/swaywm/swayidle/issues/198>.
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
mute/output changes, brightness readings and battery state. Toggle coffee and
check `systemd-inhibit --list` for `swaybar coffee`; toggle off to release it.
Reloading does not stop an already-running sway-audio-idle-inhibit process;
stop it separately if needed.

Inspect the status data independently:

```sh
python3 ~/.config/sway/swaybar/status.py --once
```

This prints module failures to stderr and one JSON snapshot to stdout.

## Previous alternatives

Swaybar is the managed bar. Waybar configuration was already staged for deletion in the original checkout; it is preserved in the private recovery snapshot and Git history, not deployed by this source tree. The old launch-waybar helper is retired by the optional legacy cleanup. wpaperd and GTKlock are also not part of the active desktop.
