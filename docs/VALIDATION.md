# Migration validation — 18 October 2026

- All 27 unit/integration tests pass. Tests exercise the real 67-entry manifest through temporary-home preview, apply, idempotence and rollback, preserve unmanaged state, test conflict refusal and interrupted deployment recovery, load deployed shell plugins and verify duplicate-daemon exclusion.
- Live `scripts/doctor.py` reports 0 required checks missing. `wtype`, `xclip` and `xdotool` remain optional absent features.
- Live deployment preview reports 0 changes after apply.
- Installed SwayFX `sway --validate --config /home/parmjot/dotfiles/home/.config/sway/config` exits 0 with no diagnostics after deployment, run outside the sandbox. Inside the sandbox it could not access the display/DRM; headless fallback could not initialize the FX renderer. The first outside-sandbox check identified the not-yet-deployed wallpaper; the final check passes.
- Both Qt 5.15.19 and Qt 6.12.0 offscreen probes report Noto Sans 10, Papirus-Dark, Window `#1e1e2e`, Highlight `#f5c2e7`. The user installed `kvantum-qt5 1.1.8-1` to supply the missing Qt5 plugin. Offscreen palettes do not verify compositor alpha.
- Installed Kitty and Tofi config parsing passed. Shell syntax, structured theme/config checks and whitespace checks pass.
- The original metadata snapshot passed Git fsck with no corruption; dangling objects are retained privately.

## Applied changes and rollback

Deployment run: `20261018T012508Z-df63496b` under `~/.local/state/dotfiles-deploy/`.

```sh
cd ~/dotfiles
./install.sh --rollback 20261018T012508Z-df63496b
./install.sh --rollback 20261018T012508Z-df63496b --apply
```

Legacy startup cleanup run: `20261018T012603Z-d3c2c509` under `~/.local/state/dotfiles/legacy-cleanup/`. Nine verified stale entries were archived. See STARTUP.md for safe restore.

An initial apply failed at a sandbox overlay cross-device rename; its partial changes were rolled back using run `20261018T012418Z-660f8f69` before the successful outside-sandbox apply. No originals were discarded. The installer uses atomic rename and requires source/destination backup storage to permit it; real cross-filesystem homes need a same-filesystem backup location or a future copy-and-verify migration implementation.

## Remaining direct checks

No compositor reload, logout, service restart, screen lock or suspend was triggered. A fresh graphical login is needed for environment.d changes and to retire any old notes-daemon instance. Inspect Tofi launch/clipboard/emoji menus, notifications, bar/tray, toolkit apps, transparency over bright/dark wallpaper, font fallback and scaled monitors. Test lock/suspend/resume directly. GTK/libadwaita, Qt Quick and app-rendered surfaces can remain opaque. Browser/editor/chat/music-app theme preferences are not comprehensively migrated by this desktop pass.

Post-staging checks include Git submodule registration and staged whitespace checks; three copied settings files had extra blank EOF lines, corrected before commit.

The original `.config` Git metadata was archived out of the live configuration directory, then a full copy was reused for `~/dotfiles` at the user's request. Original refs/reflogs/hooks/configuration/objects are retained. Both old and current repositories shared original HEAD `4eddbe874a62d70152f3e3e41075915a1aecd6ec` and 27 reachable commits before the migration commit. Registered submodules resolve all three original pinned SHAs.
