# Desktop appearance

The managed desktop uses the palette and asset choices in [THEME.md](THEME.md). Pink identifies focus and selection; Text remains the normal text colour. Red errors, Yellow warnings, Teal verification, terminal ANSI colours and syntax distinctions retain their meaning.

## Translucency

Kitty is the reference: its background is 80% opaque and its text is opaque. Dunst and Swaybar use Base `#1e1e2ecc`; `cc` is 204/255, exactly 80%. Swaybar's inactive workspace backgrounds and raised active backgrounds use the same alpha, while selected workspace fills stay solid Pink for contrast. Native Sway title/background surfaces also have 80% alpha; the existing borderless layout stays in place.

SwayFX blurs the `panel`, `launcher` and `notifications` layers. Launcher is the verified Tofi layer namespace. These effects do not lower whole-window opacity, which would fade text and icons too. Existing inactive-window dimming remains separate from background translucency.

Micro's default background is unset. Btop selects the managed `catppuccin-mocha-pink` theme with `theme_background = false`. Cava leaves its background unset in gradient mode, as the installed sample configuration requires; its Mauve-to-Pink bars inherit Kitty's background. All three therefore inherit terminal translucency when run in Kitty. Selected rows and status surfaces can still use opaque fills to identify state.

Swaylock retains its blurred screenshot background and its existing lock startup behaviour. The ring, interior, key highlights and keyboard-layout background are intentionally invisible; the clock and status text remain visible. Text uses Mocha Text normally, Teal during verification, Red for failure and Yellow for clearing/caps lock. The installed swaylock-effects does not offer a background overlay/tint setting: `color=000000` supplies the original black fallback, rather than tinting screenshots.

## Managed files

- Kitty: concise `kitty.conf` retaining every active preference, plus the attributed complete Mocha ANSI palette in `current-theme.conf`. Pink now covers cursor, selection, active border, active tab and hovered URLs.
- Dunst: explicit low/normal/critical backgrounds, text and frames. Normal uses Pink; critical uses Red. Low priority uses a subtle Surface1 frame.
- Swaybar: existing font fallback, glyph layout and command are preserved. The status script owns semantic status colours separately.
- Micro: selected custom scheme is retained with Pink selections/search/current-line numbers. Syntax and diffs keep semantic colours.
- Btop: `themes/catppuccin-mocha-pink.theme` is a required companion to `btop.conf`. Load/temperature/used-resource gradients progress through Green, Yellow and Red.
- Cava: selected gradient and terminal background inheritance are explicit; existing sensitivity, frequency range and mono output are retained.

## Application extensions

Browser, editor, chat and music apps need their own appearance settings. Record a selected Mocha/Pink theme or extension identifier individually after choosing it; keep accounts, browser profiles, session storage and caches out of the repository. GTK/Qt asset ownership and translucent surfaces are covered by the toolkit task. Some application content, web pages, video and custom widgets provide no background alpha setting and require a separate app-specific choice. Whole-window opacity is unsuitable for matching Kitty because it also fades their content.

## Validation and remaining visual checks

The invisible-indicator correction passed the installed Swaylock configuration parser up to the expected missing-compositor error using an isolated, absent Wayland socket. A temporary Grim capture of the active eDP-1 output succeeded through the same wlr screencopy protocol used by Swaylock and contained nonuniform image data; the capture was removed. No lock was started for this check, so final Swaylock rendering still needs a manual visual check. The existing `30x4` blur can make mostly uniform windows appear solid.

The installed Kitty configuration parser loads the shortened config and included theme with no bad lines and reports opacity `0.8`. Dunst/Cava INI structure and Micro JSON parse successfully; Swaylock option names and hex colour widths match installed `--help`. Micro colour-link and Btop theme records pass structural checks. These structural checks do not establish rendering or full application-parser acceptance. Sway/SwayFX validation belongs to the combined compositor pass.

After deployment, inspect over bright and dark wallpaper: Kitty text and ANSI colours, launcher selection, normal/low/critical notifications including progress bars, each workspace state, tray icons, Micro selections and syntax, Btop high-temperature/load states and Cava gradients. Test actual lock entry, verification, failure, clearing and caps lock in the session. Confirm the screenshot remains obscured by blur and text remains readable. Repeat on laptop and external displays. No running desktop or lock screen was changed or visually checked during this source pass.
