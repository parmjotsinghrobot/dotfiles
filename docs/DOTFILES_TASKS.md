# Dotfiles audit and prioritised task list

Audited 18 October 2026. Target: **Catppuccin Mocha, Pink accent**, throughout the desktop and supported applications.

## Implementation update

The source now lives at `~/dotfiles` on `codex/dotfiles-mocha-pink`, with 69 explicitly deployed home files/links, reusing the full original Git metadata including reflogs and object store. Private original snapshot and per-file deployment/legacy-cleanup rollback journals exist. All 40 tests, live dependency diagnostics, SwayFX configuration validation, and Qt5/Qt6 offscreen palette probes pass. The later Fuzzel/monospace pass reloaded Sway and Dunst and applied the session font preferences. No logout, lock or suspend was forced. Actual display, fresh-login and hardware checks remain unchecked below. Broader browser/editor/chat/music-app themes remain a later pass.

The findings below describe the original audit; checked items record completed implementation.

## What the audit found

The repo lives directly in `~/.config`, has no `.gitignore`, and currently has only 26 index entries, including three Zsh submodules. Its scope misses both home-level startup files and many important settings inside `.config`. Simply moving Git to `$HOME` would widen that problem; the useful change is an explicit list of managed files and a reproducible deployment process.

The current working tree also differs substantially from the committed setup: Waybar's two files are staged for deletion, while its Swaybar replacement is untracked. Kitty includes an untracked theme. A fresh clone would therefore reproduce neither the committed desktop nor the current one reliably.

Read-only review covered tracked configs and changes, home startup files, local helper scripts, user services/autostart, theme/font/icon settings, selected application preferences, relevant installed packages, and referenced paths. Browser profiles, credentials, histories, and personal documents were not audited internally. This is a configuration audit, not a visual inspection of the running desktop; the available process view did not expose the graphical session.

## Ordered work

### 1. Preserve the current working setup before reorganising anything — P0

- [x] Make a private recovery copy of the repo, including its index, untracked desktop files, home startup files and selected local scripts. Preserve staged versus unstaged changes.
- [x] Review the existing modifications together with the staged Waybar deletions. Do not reset or blindly stage all of `.config`.
- [x] Capture the new `sway/config.d/40-bar.conf`, `sway/swaybar/bar.conf`, `sway/swaybar/status.py`, its README, `kitty/current-theme.conf`, and `~/.local/bin/sticky-notes-daemon.py` in that recovery copy.

**Why first:** the current bar and terminal appearance depend on files outside the index. Existing changes must survive the migration.

**Done when:** there is a restorable snapshot of the actual setup, with an inventory of what was saved.

### 2. Separate the source repo from live application data — P0

- [x] Use a standalone source directory, suggested `~/dotfiles`, with a `home/` subtree mirroring destinations under `$HOME`.
- [x] Add an explicit deployment map/script that links selected files. It must support a dry run, detect existing destinations, back them up before replacement, and support rollback.
- [x] Preserve repository history and the three Zsh submodules when migrating. Keep the existing checkout available until the new layout has been verified.
- [x] Add exclusions for generated state, completion dumps, histories, caches, editor backups, browser profiles, application databases, and credentials. Manage individual settings files where an application mixes preferences with state.
- [x] Stop tracking `zsh/.zcompdump`; let Zsh regenerate it, preferably under the cache directory.

Suggested layout:

```text
~/dotfiles/
  home/
    .zshenv
    .zprofile
    .config/
      sway/
      tofi/
      kitty/
      ...selected settings...
    .local/bin/
      ...selected personal scripts...
  packages/
  docs/
  install.sh
```

**Done when:** Git status concerns managed source files, a dry run shows every destination, and a second deployment makes no unnecessary changes. Do not make all of `$HOME` or `.config` the tracking scope.

### 3. Include the files needed to reconstruct the desktop — P1

- [x] Include `~/.zshenv` and `~/.zprofile`; review whether Bash's `.bashrc` and `.bash_profile` are also needed. `.zshenv` is what directs Zsh to the tracked config directory.
- [x] Include the Swaybar replacement and Kitty theme identified in task 1.
- [x] Include selected settings under `environment.d`, `gtk-3.0`, `gtk-4.0`, `qt5ct`, `qt6ct`, `Kvantum`, `xsettingsd`, and `fontconfig`.
- [x] Include personal helper scripts actually used by the desktop. Start with the sticky-notes daemon; review the other scripts individually before publishing them.
- [x] Include selected `systemd/user` definitions, `pipewire/pipewire.conf.d/sink-eq6.conf`, `micro/settings.json`, `micro/bindings.json`, and the custom Micro colour scheme.
- [x] Review `git/config`, `mimeapps.list`, autostart entries, and custom desktop launchers for inclusion, splitting personal/machine-specific values from portable preferences.
- [x] Record wallpaper and theme assets as dependencies, with a source or private backup. The active wallpaper exists locally but is outside the repo.

**Done when:** every active include, sourced file, personal executable and visual asset is either managed or documented as an external dependency. Avoid importing entire app directories with backups, session state or accounts.

### 4. Write down one Mocha Pink theme specification — P1

- [x] Define a small shared palette: Base `#1e1e2e`, Mantle `#181825`, Surface0 `#313244`, Text `#cdd6f4`, Subtext0 `#a6adc8`, Pink `#f5c2e7`, and Red `#f38ba8` for errors/urgency.
- [x] Standardise the GTK theme on `catppuccin-mocha-pink-standard+default`, the cursor on `catppuccin-mocha-pink-cursors` at size 24, and icons on the currently installed `Papirus-Dark` unless intentionally changed later.
- [x] Choose one installed UI font and one monospace font. Iosevka Curly resolves correctly. `Source Sans Pro`, requested by GTK, currently resolves to Noto Sans instead.
- [x] Document intentional differences such as terminal font size and transparency. Pink is the accent; ordinary body text should stay readable Mocha Text, with semantic colours retained for warnings and errors.
- [x] Keep this specification beside the configs. If synchronising palettes becomes repetitive, add a small generator later; do not build a theme framework before fixing the existing files.

**Done when:** each component has a documented theme, accent, font and asset source, with no unexplained alternate flavour.

### 5. Fix Tofi's appearance and selection states — P1

**Evidence:** `tofi/config` currently uses black with alpha, white input, `#abf` results, `#aff` alternate results, and no explicit `selection-color`. The installed Tofi 0.9.1 manual gives its default selection colour as `#F92672`, outside the intended palette.

- [x] Set Mocha background, text, Pink selection, match highlights, prompt, placeholder and border colours explicitly.
- [x] Remove the blue/cyan alternating-result treatment or replace it with a deliberate Mocha treatment that leaves selection obvious.
- [ ] Review the fixed 640×640 window and percentage padding on the laptop and scaled external displays.
- [x] Check SwayFX's `layer_effects "launcher"` selector against Tofi's actual layer namespace before relying on its blur/shadows.
- [ ] Verify app launching, clipboard selection and emoji selection, including cancellation, long labels and emoji font fallback.

**Done when:** the selected result is obvious in all three menus, their colours match the specification, and layout works on each relevant display.

### 6. Align GTK, Qt, cursor and font settings — P1

**Confirmed mismatches:**

| Component | Current setting | Work needed |
| --- | --- | --- |
| GTK 3/4 | Mocha Pink; Source Sans Pro | Use the chosen installed font and preserve required theme assets |
| Qt5 | Fusion, Tela-black-dark, IBM Plex fonts | Align style, icons, palette and fonts |
| Qt6 | kvantum-dark, Papirus-Dark, Noto Sans/Iosevka | Align with the same chosen Kvantum theme |
| Kvantum | `catppuccin-frappe-pink#` | Replace with a Mocha Pink theme; the current oddly named directory does exist |
| Cursor defaults | `~/.icons/default` uses Mocha Pink; `~/.local/share/icons/default` uses Breeze_Snow | Make both agree with Sway and GTK |
| Font rendering | Fontconfig forces DPI 143; GTK sets 96 DPI | Choose a deliberate scaling policy and verify it visually |

- [x] Reconcile `QT_QPA_PLATFORMTHEME=qt6ct` and `QT_STYLE_OVERRIDE=kvantum` in `environment.d/qt.conf` with the intended Qt5 and Qt6 setup. Test both toolkits rather than assuming one setting covers both.
- [x] Manage GTK 4's existing CSS/assets symlinks and their `/usr/share/themes/...` dependency. These links currently resolve, but are absent from the repo.
- [x] Reconcile older GTK2 Breeze settings in `.config/gtkrc` with home `.gtkrc-2.0` and the chosen theme. The latter includes a currently absent `.gtkrc-2.0.mine`.
- [x] Document which settings are generated by `nwg-look` so manual edits and GUI changes do not keep replacing each other.
- [x] Align font hinting: GTK/Xsettings currently request hintmedium/RGB while Fontconfig requests hintslight/no subpixel rendering.

**Done when:** representative GTK3, GTK4, Qt5, Qt6 and XWayland apps agree on the intended appearance after a fresh login, and cursors stay consistent across windows.

### 7. Finish the desktop-wide theme pass — P1

- [x] Preserve Kitty's existing Mocha theme and choose Pink for its relevant accent states. Its 2,341-line config currently contains only eight active setting lines; reduce the copied reference comments when convenient.
- [ ] Keep Swaybar's existing Mocha/Pink workspace colours and verify tray/font fallback on all monitors.
- [x] Give Dunst explicit Mocha foreground/background and Pink framing or accents, plus distinct critical urgency styling; its current config supplies a translucent black background without explicit foreground/urgency palettes.
- [x] Update Swaylock's white/yellow/cyan/red state colours to the shared palette while retaining visibly different verification/error states.
- [x] Review Micro, Btop and Cava next. Micro already selects a custom Mocha scheme, but that scheme is untracked; Btop currently selects `Default`.
- [ ] Treat editor, browser, chat and music-app themes as a later application pass. Save theme preferences or extension lists, not complete profiles and account data.

**Done when:** launcher, terminal, bar, notifications, lock screen and everyday tools form a coherent Mocha Pink desktop, including focused, inactive, selected and error states.

### 8. Record actual dependencies and a rebuild procedure — P1

- [x] Create separate lists for desktop requirements, optional applications, fonts/icons/themes, and machine/course-specific tools. Split official and AUR packages using local package ownership information.
- [x] Record **SwayFX**, not just Sway: the configs use blur, shadows, dimming, corners and layer effects. The installed compositor is `swayfx 0.6-0`.
- [x] Record **swaylock-effects**, since the lock config uses screenshots, blur, fade-in and other effects. The installed package is `swaylock-effects-git`.
- [x] Include the commands referenced by Sway and Zsh: Kitty, Zen, Tofi, Dunst, swayidle, udiskie, nm-applet, cliphist, wl-clipboard, autotiling, Micro, grim, slurp, brightnessctl, ALSA tools, playerctl, antidot, and the optional update checker.
- [x] Include Python/PyGObject and Playerctl GI bindings for the new bar, and `python-i3ipc` for sticky notes. All are locally present.
- [x] Document emoji picker's optional typing/X11 dependencies separately. `wtype`, `xclip`, and `xdotool` are absent here; the default Wayland clipboard path has its required commands.
- [x] Record theme/font installation sources and submodule setup, then add a diagnostic command that reports missing requirements without modifying the desktop.

**Done when:** a fresh-machine guide says what to install, what to deploy, what is optional, and what still needs local configuration.

### 9. Remove stale startup/service references and make reloads predictable — P2

- [x] Review five broken enabled-service links: `mpd-notification`, `gamemoded`, `modprobed-db`, `yams`, and `spotblock`. Disable stale entries or reinstall deliberately required services.
- [x] Fix or retire `firefox-profile@.service`, which calls missing `~/.local/bin/firefox-sync.sh`.
- [x] Fix or retire `cameractrlsd.service`, whose hard-coded Python 3.14 script path is absent. Prefer a package-provided executable/service where available.
- [x] Replace Lunar Client's autostart command referencing a temporary `/tmp/.mount_...` AppImage path with a persistent launcher if still wanted.
- [x] Reconcile the profile-sync timer description saying 10 minutes with its actual one-minute interval.
- [x] Ensure repeated Sway reloads do not spawn multiple sticky-notes daemons: it is launched with `exec_always` and the script has no single-instance guard.
- [ ] Review lock/suspend ordering and five-minute idle suspend behaviour through an actual session test. The manual shortcut uses a fixed two-second delay; this audit has not established a lock failure.

**Done when:** intended user services start cleanly, removed apps have no enabled remnants, and repeated reloads leave one instance of each intended daemon.

### 10. Split portable settings from this machine's overrides — P2

- [x] Separate Sway output modes/positions, named lab monitors, laptop touchpad, keyboard/mouse identifiers and headless-output setup into a machine profile.
- [x] Replace avoidable `/home/parmjot/...` paths with home-relative paths where the consuming program supports them; retain documented local overrides elsewhere.
- [x] Fix `QSYS_ROOTDIR`, duplicated in home startup files and pointing into a nonexistent package-build cache path. Resolve the installed tool location and keep course toolchains optional.
- [x] Review stale Ruby 3.0 and Wine/Proton paths in Zsh against what is still used.
- [x] Make shell greetings optional and fast: each interactive shell currently fetches weather, and an expired update cache triggers a foreground package-update check.
- [ ] Align audio controls: Sway shortcuts use ALSA `amixer`, while the new status bar reports the PipeWire default sink through `wpctl`. Verify they operate on the same output, especially with Bluetooth/USB audio.

**Done when:** the base config is usable without this laptop's devices, display names or engineering toolchains, and machine-specific additions are clearly named.

### 11. Clean old alternatives, associations and documentation — P2

- [x] Choose Swaybar as the documented current bar, or explicitly retain a supported Waybar alternative. Its README says the original Waybar files are preserved, but those files are currently staged for deletion, and `~/.local/bin/launch-waybar` still expects them.
- [x] Mark `wpaperd` as optional/retired or reconnect it intentionally: startup currently uses a fixed Sway wallpaper and the wpaperd launch is commented out.
- [x] Mark GTKlock as an unused alternative unless it is still needed. Sway currently selects Swaylock; GTKlock's CSS references `/tmp/lockscreen.png`.
- [x] Review `gtk-3.0.backup`, `gtk-4.0.old`, `kitty.conf.bak`, and other duplicates after the recovery copy exists. Distinguish useful custom assets from generated backups.
- [x] Audit MIME defaults and custom launchers. Examples worth checking: JPEG opens Firefox while other images use EOG; `application/octet-stream` opens Chromium; mail handlers reference generated `userapp-...` desktop files.
- [x] Replace the minimal README with setup, dependencies, deployment/rollback, keybindings, theme ownership, machine overrides, and troubleshooting. Restore or replace its missing desktop screenshot.
- [x] Fix the existing trailing whitespace in `sway/config`.
- [x] Investigate Git storage after migration is safe: `.git` is about 1.5 GiB, with 1.38 GiB of loose objects, while objects reachable from all refs account for roughly 4.9 MiB on disk. Inspect reflogs/unreachable objects before any pruning; do not assume the excess is disposable.

**Done when:** the docs describe the actual setup, retired alternatives are clearly labelled, and routine status/review is small and understandable.

### 12. Verify the rebuild and the appearance — P2, final acceptance

- [x] Run a deployment dry run against a temporary home; check links, conflicts, asset paths and submodule availability without overwriting live settings.
- [x] Validate configs with the installed tools, including SwayFX config validation. Check shell/Python syntax and dependency diagnostics.
- [ ] Test a real fresh login and repeated compositor reloads, then exercise launching, clipboard, emoji, notifications, audio, brightness, screenshots and sticky notes.
- [ ] Check the lock screen, suspend/resume, laptop/external screens and scaled outputs directly.
- [ ] Inspect representative toolkit apps and capture a screenshot/theme checklist after the desktop works.

**Done when:** the saved source reproduces the intended desktop and the Mocha Pink appearance has been checked on the actual display.

## Verification already performed

- Zsh config and emoji-picker shell syntax checks passed.
- Python parsing passed for the new Swaybar status script and sticky-notes daemon.
- Iosevka Curly resolves to its installed font; Source Sans Pro falls back to Noto Sans.
- Referenced wallpaper, screenshot directory, GTK4 theme links and Qt6 palette file exist.
- Core launch/bind commands are installed; optional emoji typing/X11 commands listed above are missing.
- `git diff --check` reports three existing trailing-whitespace lines in `sway/config`.
- The initial audit changed no settings and added only this task list. Subsequent implementation is recorded above; the user installed the missing Qt5 plugin, managed links were applied and nine stale startup entries were archived with rollback.

## Fuzzel and monospace follow-up

Fuzzel is now active for apps, clipboard and emoji with separate native usage caches. The emoji script retains a Tofi override. Iosevka Curly is the UI/document/monospace default across toolkit settings and generic Fontconfig families; Dunst restores its original 13 pt monospace font. Sway and Dunst were reloaded. Tofi app history was converted by exact installed desktop-name matching and merged into Fuzzel; private reports retain unmatched names. See FUZZEL.md, FONTS.md and HISTORY_IMPORT.md.
