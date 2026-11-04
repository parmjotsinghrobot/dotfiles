# Desktop runtime and deployment audit

Reviewed live on 4 November 2026 (Pacific/Auckland). Scope: every entry in the current deployment manifest, Sway startup commands and keybinds, user services/sockets/timers, XDG autostart entries, running system services, and desktop package lists. This is a current-session snapshot, not an application-usage history or proof that a disconnected device is never used. No other candidate was removed, disabled or stopped during this audit.

## Change applied

Removed the dormant `.config/xsettingsd/xsettingsd.conf` source and manifest entry, plus its owned live symlink. xsettingsd is not installed, running or configured to start; there was no daemon to kill. Updated current toolkit/font documentation. Original config and link are recoverable under `~/.local/state/dotfiles-cleanup/20261104T005640Z`.

There are now **67 manifest entries** in the working tree. The existing, uncommitted low-memory notification additions are included in that count and were preserved.

## Suggested next decisions, in priority order

| Priority | Candidate | Current evidence | Recommendation and consequence |
| --- | --- | --- | --- |
| 1 | Profile-sync-daemon timer override | `.config/systemd/user/psd-resync.timer.d/frequency.conf` is deployed, but `profile-sync-daemon` is not installed and neither `psd.service` nor `psd-resync.timer` exists. | Remove the drop-in from source/deployment. It currently changes nothing; this does not remove browser profiles. |
| 1 | ckb-next autostart entry | `.config/autostart/ckb-next.autostart.desktop` points to `/usr/bin/ckb-next`, which is absent. No ckb process or currently attached Corsair keyboard was found. | Remove the dead autostart entry. Retain the separate Corsair input rule if the keyboard is still used when docked; today's absence cannot settle that. |
| 2 | Legacy wpaperd config | `.config/wpaperd/config.toml` remains tracked and exists live, but is outside the manifest. wpaperd is not running; its Sway start/keybind lines are commented. Sway already runs swaybg. | Remove the unused source/live config if wallpaper rotation is no longer wanted. Keep swaybg. |
| 2 | PipeWire equalizer | `sink-eq6.conf` is deployed and its ten-band `effect_input.eq6` / `effect_output.eq6` nodes exist. The output is linked to the Bluetooth sink, but the visible Zen and MPD streams connect directly to that sink; no source is linked into the EQ input in this snapshot. | Decide whether EQ is wanted. If not, remove its config next turn and arrange an audio restart separately. If yes, fix routing instead. Loaded does not mean it is processing the app audio. |
| 3 | Peaclock alias/package suggestion | Installed; not running. Zsh has an alias specifying `.config/peaclock`, but no Peaclock config is deployed. | Optional utility, not a background cost. Drop the alias/package-list suggestion if unused, or configure it deliberately. |
| 3 | Engineering example and deployed README files | `.config/shell/engineering.example.sh`, `.config/zsh/README.md` and `.config/sway/swaybar/README.md` are documentation/sample files, not runtime services. | Keep these in the repo; optionally stop linking them into the live home directory. Never remove plugin companion files merely because they are not separate manifest entries. |

## What is actually running from desktop startup

Exactly one of each expected startup helper was observed, except the intentionally separate text and image clipboard watchers. No duplicated notification daemon, notes daemon, bar or idle daemon was found.

| Component | Live evidence | Review |
| --- | --- | --- |
| SwayFX | One Sway process; active eDP-1 output | Keep: compositor/session. |
| Swaybar + Python status | One bar and one `status.py` process | Keep: current bar. |
| swaybg | Running; compositor reports a wallpaper layer | Keep: active wallpaper renderer. |
| Dunst | One running daemon | Keep: notifications, including the memory monitor. |
| swayidle | One process with 300-second suspend and before-sleep pause/lock hooks | Keep if this idle/suspend policy is wanted. Do not remove the before-sleep hooks as incidental cleanup. No lock/suspend was triggered. |
| sway-audio-idle-inhibit | Running, connected to PipeWire/Pulse compatibility, and holds an `idle` inhibitor with reason “Audio is playing”; Zen has active audio | Keep for now: live evidence supports its purpose. An older audit called it broken; that is not sufficient to remove the now-running helper. This check does not prove every resume/idle transition works. |
| udiskie | One process | Optional convenience: removable-drive mounting/tray. Keep unless manual mounting is preferred. |
| nm-applet | One process | Optional network tray UI; NetworkManager itself is separately required. No duplicate applet was found. |
| Clipboard watchers | Two `wl-paste --watch cliphist store` processes, one text and one image | Keep both for clipboard history; these are not accidental duplicates. `cliphist` runs per clipboard event, so it need not appear persistently. |
| autotiling | One process | Optional layout automation, independent of Sway's ability to tile. Remove only if manual split selection is preferred. |
| Sticky notes | Kitty + Micro notes window and one `sticky-notes-daemon.py` | Optional feature with a real startup cost. Keep if the automatically hidden/shown note is wanted. Removing startup must preserve `~/sticky_notes.md`. |
| Low-memory notification | Enabled/active user unit; compiled monitor process running | Keep: current working-tree addition, not dormant configuration. No test notification was sent. |
| Qt environment synchronization | Sway and sampled apps have `QT_QPA_PLATFORMTHEME=qt5ct` | Keep shared environment, `launch-app` and activation synchronization. The synchronization command exits after setting state; no permanent process is expected. |

System XDG autostart entries also exist for nm-applet, mpDris2, keyring, accessibility and user-directory setup. An entry on disk is not proof a Sway session executes it. The live count, not the number of entry files, was used when checking duplicates.

## On-demand components: absence from the process list is normal

| Managed component | Why keep / current boundary |
| --- | --- |
| Fuzzel, emoji picker, clipboard picker | Bound to Super+Space, Super+F1 and Super+V; launch for a menu and exit. Separate native usage caches remain untouched. |
| Swaylock and lock-and-suspend | Used by idle/before-sleep hooks and Super+Escape. A running locker is not expected in an unlocked session. No locking or suspension was tested. |
| grim, slurp, brightnessctl, wpctl, playerctl | Referenced by screenshot, brightness, audio and media bindings; short-lived tools. |
| Zsh startup/plugins/theme | Selected shell setup, not daemons. Plugins are sourced in an interactive shell; autocomplete/highlighting do not need separate processes. |
| GTK2/3/4 settings and theme assets | Read by compatible toolkit clients, rather than run as services. Existing files do not prove every toolkit/version was exercised during this session. |
| qt5ct/qt6ct + Kvantum | Apps read the configured platform/style plugins; their settings GUIs need not remain open. Keep both for mixed Qt5/Qt6 support unless a separate application audit establishes one is unnecessary. |
| Fontconfig + GSettings fonts | Font queries resolve correctly; all three live GSettings font values are Iosevka Curly 10. These are separate consumers/settings mechanisms. |
| Cursor defaults | The two default-theme locations support different lookup paths. They are not duplicate background services. |
| Git config and MIME associations | Read when Git or file/URI handling is used; no daemon needed. |
| Vendored theme license | Attribution accompanying the theme asset, not dead runtime configuration. Retain it while retaining the asset. |

GTK2 compatibility settings are repeated across conventional lookup locations. That alone is not evidence of a running-service problem; assess whether GTK2 applications are still used before removing compatibility paths.

## Active user services outside the managed startup

| Service/group | Observation | Recommendation |
| --- | --- | --- |
| MPD | Enabled/running and connected to PipeWire | Keep if local music playback is still wanted. Music-server settings/database are not rebuilt by this dotfiles manifest. |
| mpDris2 | Enabled/running | MPD's desktop media-control bridge; useful for media keys/bar. Keep with MPD. |
| mpd-rich-presence | Enabled/running; about 9.7 MiB systemd-accounted memory at capture | Optional music-presence integration. Candidate to disable next turn if no longer wanted; do not confuse it with MPD playback or mpDris2. Its service exists even though a package named exactly `mpd-rich-presence` is not installed. |
| daily-nonsense timer | Enabled/active, scheduled for 19:00 local; last service result successful | Existing personal email automation, outside dotfiles deployment. Keep unless explicitly cancelled. It was not executed or edited during the audit. |
| PipeWire + pipewire-pulse + WirePlumber | All running; real application streams and connected Bluetooth headphones | Keep all three: audio server, PulseAudio compatibility, and session/device policy serve separate roles. |
| XDG portals (core, wlr, GTK), document/permission portals | Running | Keep for application integration/file dialogs/screen sharing. Multiple portal backends are not inherently duplicates. |
| D-Bus, dconf, GNOME Keyring, accessibility bus | Running or activation-backed | Keep infrastructure; process presence alone does not justify removing credential/accessibility support. |
| GVfs, device/phone monitors, Thunar | Running | File-manager integration; phone/removable-media helpers are optional, but no evidence here establishes them as unwanted. |
| GnuPG/GCR/p11-kit sockets | Present, several associated services inactive until requested; a separate GPG agent is running | Socket activation is normal. Keep signing/key storage; do not remove an agent merely because another key-management socket exists. |

There were **zero failed user units**. `pulseaudio.service` and `pipewire-media-session.service` appeared as inactive/not-found references, not running duplicate audio servers; there is no demonstrated service file to delete.

## System services checked (outside dotfiles ownership)

Running services included NetworkManager/wpa_supplicant, Bluetooth, auto-cpufreq, UPower, chronyd, ly, Polkit, rtkit, udisks2, fwupd, bolt, Avahi, CUPS, Docker/containerd, libvirt networking, systemd-machined, and normal system/user D-Bus, logging, login and device-management services.

- **Keep Bluetooth**: headphones are connected and carrying audio.
- **Keep CUPS for now**: three printers are configured. An idle print spooler is not evidence printing is unused.
- **Docker/containerd**: Docker is enabled/running, with zero running containers in this snapshot. Consider disabling automatic startup if containers are only used occasionally; keep installed tooling if needed for coursework. Today's zero count is not usage history.
- **Virtualization**: libvirt sockets/networking are enabled; no running QEMU/VirtualBox VM process was observed. Review auto-started networking separately from keeping VM tools/images. This audit does not establish that VM use has ended.
- **Avahi**: enabled/running local discovery. It may support printers/device discovery; decide alongside those uses.
- **bolt**: Thunderbolt support; dormant hardware use cannot be inferred from a running daemon alone.
- **auto-cpufreq, UPower, NetworkManager, time sync, login, Polkit and firmware/device infrastructure**: keep unless reviewing an actual replacement/conflict. These are not unused dotfile leftovers.

No system package, service, socket or timer was disabled or removed.

## Reconstruction/documentation gaps

- The deployed generic wallpaper is a fallback. The active laptop profile overrides it with `~/Downloads/20261024_103410.jpg`; that file exists today but is outside the repo. A new machine will not reproduce the current laptop wallpaper from dotfiles alone.
- Only eDP-1 is connected today. Lab/TV/headless output rules and disconnected hardware input rules are portability preferences, not dead daemons. Review device ownership before deleting them.
- Current documentation still mentions managed Btop settings, but Btop is absent from both the working manifest and tracked home files. It is installed as an optional utility. Reconcile the documentation next turn; no Btop files were recreated here.
- `git-lfs` remains an optional package-list suggestion but is not installed. Package lists are not a live package inventory; historical `installed-snapshot.json` is intentionally not rewritten as though it were current.
- Music services, the email automation and other per-app account/data settings are running outside the manifest. Do not silently absorb credentials, music databases, browser profiles or personal note contents into Git.
- Engineering package lists and toolchain example settings are opt-in; they are not all desktop-login requirements.

## Verification and limits

Used live process counts, systemd user services/sockets/timers and system running-service lists, Sway outputs/input IDs/window classes (without window titles), selected process environment keys, PipeWire nodes/links, package presence, deployed-link ownership, and the repo's read-only doctor. Doctor reported zero required checks missing. All 67 remaining manifest destinations are the expected repo links; deployment preview requires zero changes.

This is not a resource benchmark or a historical usage study. No private application content, credentials or notes were copied into this report. No GUI, notification, lock, suspend, email job or audio restart was triggered for verification. Removal candidates other than xsettingsd remain intact for the next turn.

## Complete remaining deployment allowlist

All entries below were checked for their expected live link. Runtime roles and removal candidates are reviewed above.

```text
.config/Kvantum/catppuccin-mocha-pink/LICENSE
.config/Kvantum/catppuccin-mocha-pink/catppuccin-mocha-pink.kvconfig
.config/Kvantum/catppuccin-mocha-pink/catppuccin-mocha-pink.svg
.config/Kvantum/kvantum.kvconfig
.config/autostart/ckb-next.autostart.desktop
.config/dunst/dunstrc
.config/environment.d/qt.conf
.config/fontconfig/fonts.conf
.config/fuzzel/fuzzel.ini
.config/git/config
.config/gtk-3.0/gtk.css
.config/gtk-3.0/settings.ini
.config/gtk-4.0/assets
.config/gtk-4.0/gtk-dark.css
.config/gtk-4.0/gtk.css
.config/gtk-4.0/settings.ini
.config/gtkrc
.config/gtkrc-2.0
.config/kitty/current-theme.conf
.config/kitty/kitty.conf
.config/micro/bindings.json
.config/micro/colorschemes/catppuccin-mocha-transparent.micro
.config/micro/settings.json
.config/mimeapps.list
.config/pipewire/pipewire.conf.d/sink-eq6.conf
.config/qt5ct/qt5ct.conf
.config/qt6ct/qt6ct.conf
.config/shell/engineering.example.sh
.config/shell/environment.sh
.config/sway/config
.config/sway/config.d/00-variables.conf
.config/sway/config.d/10-autostart.conf
.config/sway/config.d/20-inputs.conf
.config/sway/config.d/20-outputs.conf
.config/sway/config.d/30-keybinds.conf
.config/sway/config.d/40-bar.conf
.config/sway/config.d/40-visuals.conf
.config/sway/config.d/50-miscellaneous.conf
.config/sway/config.d/99-swayfx.conf
.config/sway/machines/hp-envy.conf
.config/sway/swaybar/README.md
.config/sway/swaybar/bar.conf
.config/sway/swaybar/status.py
.config/swaylock/config
.config/systemd/user/default.target.wants/low-memory-notify.service
.config/systemd/user/low-memory-notify.service
.config/systemd/user/psd-resync.timer.d/frequency.conf
.config/zsh/.zshrc
.config/zsh/README.md
.config/zsh/plugins/omz-lib/git.zsh
.config/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
.config/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
.config/zsh/themes/passion/passion.zsh-theme
.config/zsh/zshrc
.gtkrc-2.0
.icons/default/index.theme
.local/bin/clipboard-picker
.local/bin/emoji-picker
.local/bin/launch-app
.local/bin/lock-and-suspend
.local/bin/low-memory-notify
.local/bin/sticky-notes-daemon.py
.local/share/backgrounds/dotfiles/desktop.jpg
.local/share/icons/default/index.theme
.local/share/low-memory-notify/monitor.c
.zprofile
.zshenv
```
