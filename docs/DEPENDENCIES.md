# Dependencies and rebuild notes

Recorded 18 October 2026 from active configs and local `pacman` databases. The target is Catppuccin Mocha with Pink accent. This is a selected desktop manifest, not an export of every installed package or a replacement for installing Arch itself.

## Package groups

`packages/*-official.txt` contain installed packages known to the local sync databases. `*-aur-local.txt` contain installed **foreign** packages (`pacman -Qm`), normally AUR or locally built packages. Foreign status alone does not prove an AUR origin. Review build instructions and sources before rebuilding. Lists contain one package per line with comments; package names and availability may change.

| Group | Purpose |
| --- | --- |
| `desktop-*` | Active Sway session, shell, bindings, launchers and scripts |
| `appearance-*` | Fonts, theme assets, icons and toolkit configuration tools |
| `optional-*` | Everyday utilities and optional shell/update features |
| `engineering-*` | Selected installed coursework tools; never prerequisites for desktop login |

`packages/installed-snapshot.json` records installed versions and upstream URLs read from installed package metadata. It is evidence of this machine on the recorded date, not a lockfile. Do not downgrade a rolling Arch installation to these versions piecemeal. Package dependencies resolve through the package manager; there is no need to copy every transitive library into these lists. Standard Arch command-line utilities (`sh`, coreutils, sed, grep, awk, systemd) are assumed.

The compositor must be **SwayFX** (`swayfx 0.6-0` in the snapshot), because the config uses blur, shadows, rounded corners, dimming and layer effects. Stock Sway cannot consume all of it. The locker must be **swaylock-effects**, currently `swaylock-effects-git r470.496059a-1`, for screenshots, blur and fade support. Their executables remain named `sway` and `swaylock`.

The bar uses Python, PyGObject and the **Playerctl 2.0 GI namespace** (`python`, `python-gobject`, `playerctl`). Sticky notes require `python-i3ipc`. The bar reads memory/backlight/battery from Linux `/proc` and `/sys`, Bluetooth through the system D-Bus BlueZ service, MPRIS through the user D-Bus session and audio through `wpctl`/WirePlumber. Installed binaries and imports do not prove these services are running.

## Fonts and visual assets

| Asset | Installed package/source | Setting |
| --- | --- | --- |
| Monospace | `ttc-iosevka-curly`; [Iosevka](https://typeof.net/Iosevka/) | Iosevka Curly |
| UI/documents/monospace | `ttc-iosevka-curly` | Iosevka Curly; notifications retain 13 pt, UI defaults use 10 pt |
| Emoji fallback | `noto-fonts-emoji` | Noto Color Emoji |
| Bar icons | `ttf-font-awesome-5` (foreign) | Font Awesome 5 Free / Brands; Font Awesome 7 is not the same family |
| Additional bar symbols | `ttf-nerd-fonts-symbols`, `ttf-nerd-fonts-symbols-mono` | Symbols Nerd Font / Symbols Nerd Font Mono |
| GTK | `catppuccin-gtk-theme-mocha`; [upstream](https://github.com/catppuccin/gtk) | `catppuccin-mocha-pink-standard+default` |
| Cursor | `catppuccin-cursors-mocha`; [upstream](https://github.com/catppuccin/cursors) | `catppuccin-mocha-pink-cursors`, size 24 |
| Qt palette/style | `kvantum-theme-catppuccin-git`; [upstream](https://github.com/catppuccin/Kvantum) | `catppuccin-mocha-pink` |
| Icons | `papirus-icon-theme`; [upstream](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) | Papirus-Dark |
| Optional folder tint | `papirus-folders-catppuccin-git`; [upstream](https://github.com/catppuccin/papirus-folders) | Mocha Pink if enabled deliberately |

These URLs come from installed package metadata; current upstream availability was not checked. Exact installed versions are in the JSON snapshot. GTK4 CSS/assets symlinks require the corresponding `/usr/share/themes/.../gtk-4.0` files. Kitty's palette is managed source (`home/.config/kitty/current-theme.conf`), not a separate runtime package.

**Qt5/Qt6:** `kvantum` supplies the Qt6 plugin and `kvantum-qt5` supplies `/usr/lib/qt/plugins/styles/libkvantum.so`. Both are required and listed in `appearance-official.txt`. The user installed `kvantum-qt5 1.1.8-1` during migration; both Qt offscreen probes now return Mocha Window and Pink Highlight colours.

The wallpaper was copied from `~/Pictures/Wallpapers/leo-auckland-harbour-catppuccin.jpg` to managed `home/.local/share/backgrounds/dotfiles/desktop.jpg`. Its original source/license is not established; keep this checkout private until provenance is resolved before publication, or choose a replacement. It is not automatically downloaded. The screenshot binding creates the configured XDG pictures `Screenshots` directory when used. Sticky notes use `~/sticky_notes.md`; its personal contents are not part of these dependencies.

## Optional features and local toolchains

`checkupdates` comes from `pacman-contrib`. It is optional and can contact mirrors when explicitly used by the shell; the doctor never runs it. `antidot` is currently provided by `antidot-bin` and is sourced during shell initialization. Peaclock is an optional shell alias.

The emoji script defaults to the Wayland clipboard (`fuzzel`, `wl-copy`). Wayland typing additionally needs `wtype`; X11 clipboard/typing need `xclip`/`xdotool`. All three are absent in the snapshot and are **not** core desktop requirements. The picker stores lists under `${BEMOJI_DB_LOCATION:-${XDG_DATA_HOME:-$HOME/.local/share}/bemoji}` and uses `curl` to fetch Unicode emoji data on first use. For an offline rebuild, retain a local list or pass `-f /path/to/list.txt`; doctor only checks for cached lists and never fetches them.

Engineering manifests list only locally installed, relevant tools: C/C++ builds, debugging, serial access, FPGA loading, SPIM, circuit simulation, MATLAB installer tooling, Pylon and Typst. They are examples for this user's coursework, not a universal course environment. Quartus/Nios II, MATLAB itself, PSoC tools and Basler camera support can require separate vendor installations, licenses, udev rules and target hardware. `matlab-mpm` is an installer, not proof MATLAB is installed. The recorded `QSYS_ROOTDIR` in old startup files pointed into a missing Paru build cache; never recreate that cache path as an installation strategy. Select the installed Quartus version and its `quartus/sopc_builder/bin` explicitly in a machine-local profile. ARM embedded compiler packages are not installed in this snapshot. Configure serial-device permissions and validate USB/JTAG access separately.

## Rebuild sequence

1. Install Arch and establish graphics drivers, network access, a login/session mechanism and normal user permissions for the target machine. These are outside the selected dotfile manifests.
2. Review `desktop-official.txt` and `appearance-official.txt`, then install those packages using the machine's package manager. Review/rebuild their `aur-local` counterparts from trusted package sources. Keep optional applications and engineering tools separate. Do not install stock Sway or stock swaylock alongside their conflicting forks.
3. Initialise the repository's pinned Zsh submodules from its root: `git submodule update --init --recursive`. The three upstreams are [passion](https://github.com/ChesterYue/ohmyzsh-theme-passion), [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions), and [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting). The small OMZ git library is a managed file, not one of those submodules.
4. Follow the repository deployment guide and inspect its dry run before deploying. Supply the private wallpaper or a local replacement, screenshot directory, optional emoji cache, machine outputs and any required engineering paths.
5. Run `python3 scripts/doctor.py` from the repository (or use its absolute path from any working directory). `--home /path/to/test-home` checks deployment files in a temporary home while commands, fonts and system theme assets remain checks of the current machine. Exit status is 1 for missing required checks and 0 otherwise; optional omissions do not fail it.
6. Start a fresh session, test launch/clipboard/emoji/notifications, Bluetooth/audio, screenshots, sticky notes, lock/suspend/resume and scaled screens. Confirm representative GTK3, GTK4, Qt5, Qt6 and XWayland windows visually. Import/font/path checks cannot validate appearance or hardware behavior.

The diagnostic performs only local read queries and Python import checks, suppresses Python bytecode writing, does not invoke the shell configuration, and does not start services or change packages/settings. It deliberately does not execute Sway, a locker, GUI applications or network requests.

## Selected local settings

Git enables an LFS filter, so `git-lfs` is included as an optional Git feature dependency; signed commits also require GnuPG and the user's existing private signing key, which is never deployed. The captured ckb-next autostart relies on a locally installed, unowned `/usr/bin/ckb-next` executable; reinstall that hardware app deliberately on another machine or omit the autostart entry. Generated Thunderbird/Evolution mail-handler associations were removed because their application executables are absent; choose an installed mail client locally. Optional MPD service enablement is documented in CAPTURE.md and is not enabled automatically.

Fuzzel is the active desktop requirement; Tofi is optional fallback. `gsettings-desktop-schemas` supplies shared UI/document/monospace preferences. Run `python3 scripts/apply-ui-fonts.py --apply` after deployment to set these session values; previous values are saved under XDG state storage.
