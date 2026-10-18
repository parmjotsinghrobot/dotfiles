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

During the initial migration no compositor reload, logout, service restart, screen lock or suspend was triggered. The later Fuzzel/monospace pass validated and reloaded Sway and Dunst, with no logout, lock or suspend. A fresh graphical login is needed for environment.d changes and to retire any old notes-daemon instance. Inspect Tofi launch/clipboard/emoji menus, notifications, bar/tray, toolkit apps, transparency over bright/dark wallpaper, font fallback and scaled monitors. Test lock/suspend/resume directly. GTK/libadwaita, Qt Quick and app-rendered surfaces can remain opaque. Browser/editor/chat/music-app theme preferences are not comprehensively migrated by this desktop pass.

Post-staging checks include Git submodule registration and staged whitespace checks; three copied settings files had extra blank EOF lines, corrected before commit.

The original `.config` Git metadata was archived out of the live configuration directory, then a full copy was reused for `~/dotfiles` at the user's request. Original refs/reflogs/hooks/configuration/objects are retained. Both old and current repositories shared original HEAD `4eddbe874a62d70152f3e3e41075915a1aecd6ec` and 27 reachable commits before the migration commit. Registered submodules resolve all three original pinned SHAs.

## Active Fuzzel and monospace follow-up

All 40 regression/integration tests pass with the 69-entry deployment manifest. Fuzzel is now the default app/clipboard/emoji backend; clipboard tests cover binary data and cancellation. Generic Fontconfig families resolve to Iosevka, with emoji and icon families verified separately. Fresh Qt5 and Qt6 offscreen applications both report Iosevka Curly 10. GSettings UI/document/monospace values were changed with private original-value backups and verified by readback. SwayFX validation and Sway/Dunst reloads succeeded.

The Tofi app-history import merged 4,849 prior launches across 56 exact installed-app matches while retaining existing Fuzzel counts; a second preview proposed zero additions. The original Tofi history is unchanged; 115 unmatched old display names are recorded in the private mapping report. No private usage files are committed.

## Qt session propagation fix

The user-manager environment contained QT_QPA_PLATFORMTHEME=qt5ct, but login-manager-started Sway and qpwgraph did not. environment.d alone therefore did not cover normal GUI launches. The shared shell defaults now export the compatibility key, and the Sway Fuzzel command uses a deployed launch-app helper before spawning the launcher. D-Bus/systemd activation is synchronized on reload.

SwayFX validation and reload passed. Invisible Qt5 and Qt6 programs were then launched by the real Sway session through this helper, with no manually injected Qt theme variable. Both reported `qt5ct|Iosevka Curly|#1e1e2e|#f5c2e7`. Regression tests exercise an absent inherited variable and preserve explicit per-app overrides and argument boundaries. All 42 tests pass. Existing qpwgraph/Qt settings processes must be closed and reopened; their environments cannot change through a compositor reload.
