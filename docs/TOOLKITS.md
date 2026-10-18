# GTK, Qt, cursors and font ownership

These are source settings for deployment. No running desktop settings were changed during this pass. The contract is [THEME.md](THEME.md): Catppuccin Mocha Pink, Iosevka Curly 10 for UI and monospace text, Papirus-Dark, Mocha Pink cursors at 24, 96 logical DPI and grayscale slight hinting. Output scaling belongs to Sway.

## What owns each setting

- GTK3/GTK4 settings select the installed `catppuccin-mocha-pink-standard+default` theme. GTK4 CSS and assets remain symlinks into `/usr/share/themes`; install the theme package before deploying. GTK3's empty `gtk.css` intentionally adds no override.
- `.gtkrc-2.0` and the two legacy `.config/gtkrc*` files use the same GTK2 choices. The missing `.gtkrc-2.0.mine` include was removed. They contain preferences, without generated ownership warnings or machine paths.
- Xsettings covers XWayland clients and agrees on fonts, cursor size, rendering and 96 × 1024 DPI. Both cursor default `index.theme` files select the same cursor.
- Fontconfig enables grayscale antialiasing and slight hinting without forcing a second DPI or LCD filter. It keeps support for the legacy `~/.fonts` directory.
- `nwg-look` can rewrite GTK settings, GTK2 and cursor defaults and apply GSettings immediately. Treat this repo as authoritative: after using it, review only intentional preference changes back into these files. Qt configuration GUIs similarly rewrite files; window geometry is intentionally excluded here.

## Qt5 and Qt6

`environment.d/qt.conf` uses `QT_QPA_PLATFORMTHEME=qt5ct`. The installed Qt6 `qt6ct` plugin advertises both `qt6ct` and the compatibility key `qt5ct`; Qt5 uses its native `qt5ct` plugin. Each reads its corresponding `qt5ct.conf` / `qt6ct.conf`. Both select `kvantum-dark`, the same fonts and Papirus-Dark. On a different distro/version, check that the Qt6 plugin supports the compatibility key before relying on it.

The global `QT_STYLE_OVERRIDE=kvantum` was removed: per-toolkit style selection is sufficient. No platform backend, scale factor or Qt Quick style is forced. An application with its own platform plugin/style or a sandbox may bypass these preferences.

Kvantum supplies its own palette; `custom_palette=false` prevents the old Frappé ct palette from overriding it. The obsolete absolute-path Qt6 `style-colors.conf` is removed. No machine-specific palette path is needed.

**Required packages:** `qt5ct`, `qt6ct`, `kvantum` for Qt6 and the matching Qt5 Kvantum style package (`kvantum-qt5` on Arch). The Qt5 style plugin is **absent on this machine**: `/usr/lib/qt/plugins/styles/` currently contains only `libqt5ct-style.so`. With that missing dependency Qt5 still receives the right fonts/icons, but falls back to a light widget style. This is not completed visual acceptance. Install that dependency before the real Qt5 check; no package installation was attempted here.

`environment.d` reaches systemd-managed applications, but this login manager starts `sway` directly; Sway does not inherit that user-manager environment. The shared shell environment now exports `QT_QPA_PLATFORMTHEME=${QT_QPA_PLATFORMTHEME:-qt5ct}`. Sway launches Fuzzel through `~/.local/bin/launch-app`, which sources the shared defaults before executing it, so applications launched by Fuzzel inherit the variable even in an already-running bare Sway session. An `exec_always` command also syncs that default into D-Bus/systemd activation. Explicit per-app overrides are preserved.

Restart existing Qt apps which were launched without the variable. A compositor reload cannot change an existing application's environment. For a terminal opened before this fix, start a new shell, source `~/.config/shell/environment.sh`, or run `~/.local/bin/launch-app qpwgraph`. The important check is the environment of a new app launched through this normal path; a Qt probe with the variable manually injected cannot verify session propagation.

## Kvantum asset provenance and translucency

The managed Mocha Pink SVG and original configuration came from the installed `kvantum-theme-catppuccin-git r21.71105d2-1`, official [catppuccin/kvantum](https://github.com/catppuccin/kvantum/tree/71105d2). This is an actual Mocha asset, replacing the old `catppuccin-frappe-pink#` override. The upstream [MIT license](https://raw.githubusercontent.com/catppuccin/kvantum/71105d2/LICENSE) is saved beside the asset as `LICENSE`.

Original installed SHA-256:

```text
c0d32dd8f19a78841ce59367ffa91095ca850e68938ee16d55e41d7b4eccce32  catppuccin-mocha-pink.kvconfig
4d4507fc281d31bb1d67491eb5fe238a769a463f42f96778cdd513f5fead04a1  catppuccin-mocha-pink.svg
```

Local configuration changes enable `translucent_windows=true`, `reduce_window_opacity=20` and `reduce_menu_opacity=20` for roughly 80% background opacity, matching Kitty's preference. `composite=true` is retained. Kvantum's [official Theme-Config documentation](https://raw.githubusercontent.com/tsujan/Kvantum/master/Kvantum/doc/Theme-Config.pdf) defines these as reductions to the theme's window/menu background drawing. This does not set compositor opacity on the entire window. Text remains opaque. The upstream list of applications requiring opaque windows is retained; do not remove safety exceptions just to force translucency.

Kvantum's KDE-specific blur requests are disabled (`blurring=false`, `popup_blurring=false`); actual SwayFX blur is a compositor decision. GTK3/4 and libadwaita apps keep readable opaque backgrounds: there is no reliable common background-only alpha setting across their widgets, custom CSS and application style ownership. This pass deliberately adds no broad GTK CSS patch. Qt Quick, Electron, embedded web views and app-rendered surfaces may also remain opaque. Check transparency over bright/dark wallpaper after deployment; offscreen palette tests cannot establish compositor alpha or glyph clarity.

## Validation on 18 October 2026

- Config INI/XML parsing and all three GTK4 theme link targets passed.
- `fc-match` with `XDG_CONFIG_HOME` pointing to the repo configs resolves Noto Sans and Iosevka Curly to their actual families.
- Built a temporary minimal QApplication probe against installed Qt **5.15.19** and **6.12.0**, run with `QT_QPA_PLATFORM=offscreen`, `QT_QPA_PLATFORMTHEME=qt5ct`, repo `XDG_CONFIG_HOME` and **QT_STYLE_OVERRIDE unset**. Both loaded their matching ct plugin and returned Noto Sans 10 / Papirus-Dark. Qt6 returned Window `#1e1e2e` and Highlight `#f5c2e7`. Qt5 initially returned a fallback palette because its Kvantum plugin was missing. The user installed `kvantum-qt5 1.1.8-1`; the repeated probe now returns Window `#1e1e2e` / Highlight `#f5c2e7` for Qt5 as well, with Noto Sans 10 and Papirus-Dark.
- Vendored SVG is byte-identical to the package asset and parses as XML. Kvantum's config intentionally repeats some sections; do not reject that valid upstream format with a strict INI parser.

Still required after deployment: GTK2/3/4, Qt5, Qt6 and XWayland app inspection after fresh login, normal/selection/disabled states, cursor transitions, scaled output changes and actual background opacity. libadwaita apps may constrain theme application independently of GTK settings.

## Monospace follow-up

The user selected Iosevka Curly for all desktop text. GTK2/3/4, Xsettings and Qt5/6 now name it explicitly. Generic Fontconfig text families also select it with Noto Color Emoji fallback; first-family matching leaves explicit icon fonts alone. GSettings UI/document/monospace values are applied with `scripts/apply-ui-fonts.py --apply`, which saves their previous values privately. New Qt offscreen probes verify the font change; earlier Noto Sans measurements above describe the initial migration. Restart apps which retain their fonts at launch.
