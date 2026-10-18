# Catppuccin Mocha Pink

This is the appearance contract for the managed desktop. `theme/palette.json` records the shared values; application configs remain the files their applications read. There is no theme generator or automatic synchronisation. A changed shared value needs a review of the coverage table below.

The flavour is **Mocha**, with **Pink** as the interactive accent. Body text stays Text. Frappé, blue and mauve are not alternate UI accents; colours with a specific meaning remain available for terminals, syntax and status.

## Palette and states

| Role | Colour | Use |
| --- | --- | --- |
| Base | `#1e1e2e` | Normal background |
| Mantle | `#181825` | Recessed panels and inactive tabs |
| Surface0 | `#313244` | Raised controls and subtle highlights |
| Surface1 | `#45475a` | Inactive boundaries |
| Text | `#cdd6f4` | Normal readable text |
| Subtext0 | `#a6adc8` | Secondary labels, still readable |
| Pink | `#f5c2e7` | Focus, selection, active tab/workspace, borders |
| Red | `#f38ba8` | Error, urgency, authentication failure |
| Yellow | `#f9e2af` | Warning, low battery, caps lock |
| Green | `#a6e3a1` | Success, charging, diff additions |
| Blue | `#89b4fa` | Information and semantic syntax |
| Teal | `#94e2d5` | Verification in progress |

Use Base text on a filled Pink selection. A highlighted match can use Pink on Base; make the selected row distinguishable with a fill or outline as well. Disabled controls should not look selected. Critical notifications and lock failures must differ from ordinary focus. Never replace all terminal ANSI colours or syntax colours with Pink: their distinctions carry information.

## Fonts, scale and transparency

- UI: **Noto Sans 10 pt**, explicitly named in GTK, Qt and Xsettings.
- Monospace: **Iosevka Curly 10 pt**, including Kitty. Tofi deliberately uses 14 pt for scanning a launcher; Swaybar uses 9 pt to fit its 26-pixel bar. Icon/emoji fallback may use the installed symbol and emoji fonts.
- Icons: **Papirus-Dark**. It is an intentional complete icon set, so every icon need not be Pink.
- Cursor: **catppuccin-mocha-pink-cursors**, size **24**, in Sway, GTK, Xsettings and both user cursor defaults.
- Logical DPI: **96**; GTK/Xsettings encode this as **98304** (96 × 1024). Use Sway per-output scaling for physical display size, recorded in the machine's output configuration. Avoid a second forced Fontconfig DPI such as 143.
- Rendering: antialiasing on, slight hinting, no subpixel rendering. This avoids conflicting RGB assumptions across differently scaled outputs.
- Use Kitty's **0.8 background opacity** as the reference: Mocha Base with `cc` alpha for Tofi, Swaybar and Dunst; supported Kvantum window/menu backgrounds reduce opacity by 20%. Keep text and controls opaque. GTK/libadwaita and application-rendered surfaces may need opaque backgrounds; do not fade whole windows to force the effect. Swaylock retains its blurred screenshot with translucent indicator surfaces because its native effects do not provide a full-screen Mocha tint. Check all transparency over bright and dark wallpaper. Blur is a compositor effect, not a replacement for contrast.

Noto Sans and Iosevka Curly both resolved to the named families with local `fc-match` on 18 October 2026. The current GTK request for Source Sans Pro falls back to Noto Sans; the contract names the actual installed family directly.

## Assets and provenance

| Asset | Installation/source evidence on this machine | Required handling |
| --- | --- | --- |
| GTK | `/usr/share/themes/catppuccin-mocha-pink-standard+default`, owned by `catppuccin-gtk-theme-mocha` | Install the package; preserve GTK4 CSS/assets links to this theme |
| Cursor | `/usr/share/icons/catppuccin-mocha-pink-cursors`, owned by `catppuccin-cursors-mocha` | Install the package and align all cursor selectors |
| Icons | `/usr/share/icons/Papirus-Dark`, owned by `papirus-icon-theme` | Install the package; use the same name in Qt/GTK/bar |
| Kitty | Existing `kitty/current-theme.conf` credits Catppuccin's Kitty Mocha port, MIT | Keep attribution; override UI accents with Pink while preserving ANSI semantics |
| Micro | Existing `micro/colorschemes/catppuccin-mocha-transparent.micro` | Preserve custom scheme with selected settings |
| Qt/Kvantum | Genuine `catppuccin-mocha-pink` assets copied from installed official port, with MIT license | Managed under `.config/Kvantum`; both toolkit style plugins are required |
| Wallpaper | Existing personal image copied to managed `.local/share/backgrounds/dotfiles/desktop.jpg` | Source/license not established; keep private until provenance is resolved before any publication |

This specification uses local files and package ownership as evidence. Exact package lists and installation steps belong to the dependency inventory. Do not copy complete application profiles to capture an appearance preference.

## Config ownership and coverage

Paths below are relative to `$HOME`; managed copies live under the repo's `home/` tree. They are review targets, not a claim that every target has already been implemented or visually verified.

| Component | Settings to own | Target and verification |
| --- | --- | --- |
| SwayFX | `.config/sway/config.d/40-visuals.conf`, `50-miscellaneous.conf`, `99-swayfx.conf` | Pink focus where exposed, Mocha surfaces, consistent cursor; effects remain deliberate |
| Displays | `.config/sway/config.d/20-outputs.conf` or its machine-profile replacement | Per-output scale; check laptop/external display transitions |
| Swaybar | `.config/sway/swaybar/bar.conf`, `status.py` | Preserve existing Mocha/Pink workspace states; semantic status colours; inspect tray and glyph fallback |
| Tofi | `.config/tofi/config` | Explicit background, foreground, selected row, match, prompt, placeholder and border; check launch, clipboard and emoji menus |
| GTK3/4 | `.config/gtk-3.0/settings.ini`, `.config/gtk-4.0/settings.ini`, GTK4 CSS/assets links | Mocha Pink, Noto Sans, Papirus-Dark, cursor 24; inspect one app per toolkit |
| GTK2 | `.gtkrc-2.0`, selected `.config/gtkrc` if actually consumed | Same asset/font choices; resolve missing includes |
| Xsettings | `.config/xsettingsd/xsettingsd.conf` | Same GTK/font/cursor values and logical DPI; inspect XWayland app |
| Qt5/Qt6 | `.config/qt5ct/qt5ct.conf`, `.config/qt6ct/qt6ct.conf`, selected palette files, `.config/environment.d/qt.conf` | Same fonts/icons/Mocha palette; verify platform-theme selection separately for both versions |
| Kvantum | `.config/Kvantum/kvantum.kvconfig`, selected Mocha Pink theme assets | Mocha Pink style for Qt widgets; validate assets exist |
| Cursor defaults | `.icons/default/index.theme`, `.local/share/icons/default/index.theme` | Both inherit Mocha Pink; inspect crossing toolkit/window boundaries |
| Fontconfig | `.config/fontconfig/fonts.conf` | 96 logical DPI policy, slight hinting, grayscale antialiasing; no conflicting forced DPI |
| Kitty | `.config/kitty/kitty.conf`, `current-theme.conf` | Pink selection/cursor/active tab/border, preserved ANSI palette, 10 pt, opacity 0.8 |
| Dunst | `.config/dunst/dunstrc` | Mocha surfaces/Text; Pink normal accent, Red critical; inspect short/long notifications |
| Swaylock | `.config/swaylock/config` | Mocha/Pink idle, Teal verifying, Red failure, Yellow warning; check actual lock interaction |
| Micro | `.config/micro/settings.json`, selected colour scheme | Preserve syntax/diff semantics and Pink UI accent |
| Btop/Cava | Selected `.config/btop/btop.conf` and theme; `.config/cava/config` | Mocha backgrounds, Pink primary accent, semantic alerts; inspect terminal rendering |
| Browser/editor/chat/music | Selected theme preferences or extension list only | Later application pass: Mocha Pink where supported; document any app limitation |

GUI tools such as `nwg-look`, `qt5ct` and `qt6ct` can rewrite their settings. Treat the repo files as authoritative: after using a GUI, review and copy only intentional preference changes back to the repo, excluding window geometry and session state. Do not let a second tool silently own the same choice. The shared JSON is reference data; editing it alone does not update GTK or Qt.

## Acceptance on the actual desktop

After deploying and starting a fresh login, check normal/focused/inactive/selected/error states, toolkit cursor transitions, notification urgency and lock verification/failure. Run the three Tofi uses with long labels and emoji. Check text and transparency over bright/dark wallpaper on the laptop and scaled external displays. Repeat a compositor reload and check that appearance remains consistent. Screenshot review and direct lock/suspend testing remain necessary; parsing config files cannot establish these results.
