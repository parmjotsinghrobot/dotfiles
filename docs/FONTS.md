# Iosevka Curly desktop defaults

Iosevka Curly is the UI, document and monospace default at 10 pt. Dunst uses 13 pt, restoring the original notification font size. The launcher stays at 14 pt and Swaybar at 9 pt. Icon fonts and Noto Color Emoji remain dedicated glyph fallbacks.

Managed settings cover GTK2/3/4, Qt5/6, Xsettings, Dunst and Fontconfig. Fontconfig first-family rules select Iosevka for generic sans-serif, serif, monospace and system-ui requests, with Noto Color Emoji as fallback. Explicit icon families are left alone. Apps or web content that explicitly request another named font can override generic defaults.

## Session settings

GTK/libadwaita applications can also read GSettings instead of settings.ini. The helper applies `font-name`, `document-font-name` and `monospace-font-name` under `org.gnome.desktop.interface` using the shared palette's UI font:

```sh
cd ~/dotfiles
python3 scripts/apply-ui-fonts.py
python3 scripts/apply-ui-fonts.py --apply
```

Preview is read-only. Apply saves the original serialized values privately under `${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles/fonts/`, then verifies each changed key. A repeated apply writes nothing if values already agree. To restore a selected backup:

```sh
python3 scripts/apply-ui-fonts.py --restore /absolute/path/to/backup.json
python3 scripts/apply-ui-fonts.py --restore /absolute/path/to/backup.json --apply
```

This restores session settings only; managed config files are versioned separately in Git. Session writes require the normal user session D-Bus/dconf environment. In this desktop tool sandbox, use the approved outside-sandbox execution rather than interpreting its read-only runtime errors as a font problem.

## Verification

All four generic families resolve to Iosevka, `sans-serif:charset=1f600` falls back to Noto Color Emoji, and Font Awesome 5 Free still resolves to its named font. When checking system-ui with the CLI, use `fc-match ':family=system-ui'`; an unescaped hyphen in the positional shorthand is parsed as a font-pattern separator.

Minimal offscreen Qt5 and Qt6 applications both report `Iosevka Curly 10`. These probes verify toolkit font selection, not on-screen layout. GSettings values were applied and read back. SwayFX configuration validation passed, Sway reloaded its bindings and Dunst reloaded its font. Some existing applications cache fonts and need reopening; a full logout was not forced.
