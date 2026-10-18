# Captured configuration and reconstruction boundaries

Reviewed 18 October 2026 against the selected source under `home/`, the original audit, active Sway references, shell entrypoints and local user-service link names. This is a source/dependency review; it does not prove a fresh login or the desktop appearance. The deployment manifest is generated separately and must agree with the final source tree.

## Managed source

- Home-level Zsh and Bash startup files load the shared `shell/environment.sh`. Zsh's `.zshrc` is a relative symlink to `zshrc`. The three plugins/theme remain pinned Git submodules and need `git submodule update --init --recursive`; the OMZ Git helper is a separate managed file. Plugin companion files come from the whole submodule checkout, not just its top-level script.
- All active personal Sway snippets and the explicit `hp-envy.conf` profile are captured. The Swaybar configuration, Python status script, emoji picker, notes daemon and lock/suspend wrapper are source files. System `/etc/sway/config.d/*` snippets remain distribution/package dependencies and can differ on another installation.
- Kitty's included palette, Tofi, Dunst, Swaylock, Btop/Cava, Micro settings/bindings and its selected `catppuccin-mocha-transparent` scheme are captured. The wallpaper is now copied to the managed `home/.local/share/backgrounds/dotfiles/desktop.jpg`, matching the active Sway reference.
- Toolkit settings cover GTK2/3/4, qt5ct/qt6ct, environment.d, Xsettings, Fontconfig, both cursor defaults and Kvantum. Mocha Pink Kvantum SVG/config/license are vendored. GTK4 CSS and assets remain absolute symlinks into the installed GTK theme; the GTK package, Papirus icons, cursor theme and fonts remain required external assets.
- The PipeWire equalizer config uses PipeWire's built-in filter nodes; it has no personal impulse-response/audio asset dependency. The `psd-resync` timer drop-in and ckb-next autostart entry are selected source, subject to the optional requirements below.
- Git preferences and selected MIME associations are captured individually. App account/profile directories, browser extensions and per-app state are outside this capture.

## External, optional and machine-local dependencies

Package groups and install sources are described in [DEPENDENCIES.md](DEPENDENCIES.md). Do not confuse copied configuration with an installed or enabled service.

| Area | Boundary |
| --- | --- |
| GTK assets | `/usr/share/themes/catppuccin-mocha-pink-standard+default/gtk-4.0/{gtk.css,gtk-dark.css,assets}` must exist. These link targets resolve locally, but will fail until the theme package is installed on a new machine. |
| Wallpaper | The copied image came from the existing personal wallpaper. Original author/license is unestablished. Keep this repository private until provenance or replacement is settled. `wpaperd` is an inactive alternative and its `~/Pictures/Wallpapers` collection is deliberately uncaptured. |
| Notes | `~/sticky_notes.md` is deliberately untracked personal content. Kitty/Micro can open/create it on a new machine. Back up its contents privately if needed; do not import it into the source repo. |
| Emoji | The cache/list is generated outside the repo. Default first use fetches Unicode data; an offline build needs a privately retained list or `-f` list input. Typing/X11 tools are optional. |
| Shell aliases | `peaclock` is optional. Its custom `~/.config/peaclock` appearance is not captured; remove the alias or supply local preferences if used. `antidot` is guarded when unavailable. |
| ckb-next | A local `/usr/bin/ckb-next` exists but is not owned by a package in the local pacman database. The autostart entry uses `TryExec`; install the hardware tool deliberately if wanted. Device profiles are not captured. |
| Music services | Existing working enablement links select `mpd.service`, `mpDris2.service` and `mpd-rich-presence.service`. These are optional existing-machine choices, not reconstructed music-server configuration. MPD databases, music, account/integration settings and service enablement are deliberately not imported. |
| Profile sync | The one-minute timer drop-in is preserved, but does not install or enable Profile-sync-daemon. Its base timer was absent in the local review. Treat the drop-in as dormant unless deliberately reinstalling/configuring the service. |
| PipeWire | Existing user links enable `pipewire-pulse.service`/socket. Install the desktop audio packages and establish the target machine's user-service setup; a config-only deployment does not enable services. |
| Git | Identity/signing-key identifier and `/opt/flutter` safe-directory exception reflect this user. Private signing keys and credentials stay external. Signed commits require the existing keyring and an available agent; required LFS filters need `git-lfs`. Review these preferences for another account. |
| MIME apps | Package/application IDs must exist on the target machine. Generated local mail-launcher IDs and app-specific URI handlers should be selected locally rather than importing account profiles or arbitrary generated launchers. |

Optional overrides are `shell/environment.local.sh`, `shell/login.local.sh`, `shell/interactive.local.sh` and `sway/machines/local.conf`, as described in [PORTABILITY.md](PORTABILITY.md). Machine output/input identifiers are isolated in `hp-envy.conf`. Engineering paths and vendor installations remain opt-in local configuration.

## Reconstruction check

1. Initialise all three submodules and install required desktop/appearance packages. Verify GTK link targets and fonts before deploying.
2. Confirm the final manifest includes new source files and removes retired theme/palette references. Run deployment into a temporary home and run the doctor against it; a missing optional app/profile is not a core desktop failure.
3. Review the machine profile, optional service choices, Git identity/signing setup and local MIME applications. Restore private personal notes/assets separately when desired.
4. Use a fresh real session to check launch, clipboard/emoji, bar, notifications, audio, screenshot creation, notes, suspend/lock and representative toolkit windows. Installed binaries, source parsing and offscreen probes cannot establish session startup, hardware or translucent appearance.
