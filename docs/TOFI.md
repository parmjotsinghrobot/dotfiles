# Tofi

`home/.config/tofi/config` gives the application launcher, clipboard picker and emoji picker the same Catppuccin Mocha Pink appearance. It targets the locally installed **Tofi 0.9.1**; option names and values were checked against its `tofi(5)` manual.

The background is Mocha Base `#1e1e2ecc`: 80% opaque, matching Kitty. Foregrounds stay opaque. Pink marks the prompt, cursor, border and selected result. Selected text is Base on a filled Pink row, with matching characters in Surface1 so a search remains readable. Other results use Text; the placeholder uses Subtext0. Tofi 0.9.1 exposes match highlighting for the selected result only. The window and selection have square corners; blur is a separate SwayFX effect.

The menu retains the original centred 640 × 640 square, with 24 logical pixels of outer padding. The selection background has 12 pixels of horizontal padding on each side and 4 pixels vertically. `clip-to-padding = false` allows the left highlight padding to extend before the text instead of being clipped at its starting position. `scale = true` follows output scaling; unusually small logical displays can use a per-invocation dimension override.

The font is named through Pango instead of pointing directly to one font file, preserving fallback for emoji and symbols. Test actual glyph coverage after installation. The existing emoji script invokes plain `tofi`, and the clipboard pipeline passes newline-separated labels to it. Substring matching, required selection and explicit confirmation remain enabled; these pipelines and their data/output formats are unchanged. `tofi-drun --drun-launch=true` keeps its existing launch behaviour.

## SwayFX namespace

The visible surface namespace is **`launcher`**, not `tofi`. This is set in [Tofi v0.9.1 `src/main.c`](https://github.com/philj56/tofi/blob/v0.9.1/src/main.c#L1490-L1495), and `launcher` is present in the installed binary. Its temporary output-discovery surface uses `dummy`; do not style that surface. Configure launcher blur in SwayFX using `layer_effects "launcher" ...`; check the compositor configuration separately. A background alpha does not itself enable blur.

## Validation and desktop checks

The config was parsed by the installed binary against an intentionally absent Wayland display and an isolated temporary runtime directory. Its only diagnostic was the expected connection failure; a deliberately invalid option produced an extra parser error, confirming that this method reaches the parser. This checks supported keys and value syntax without opening a menu or touching the desktop. It does not test geometry, glyph rendering, matching colours, transparency or selection behaviour.

After deployment, check these on the laptop and each scaled external output:

1. Open the normal application launcher; type a substring and move the selection. Check the Pink row, matching text, cursor and placeholder.
2. Open clipboard history using its existing binding; check long labels and confirm the selected clipboard item still decodes correctly.
3. Open the emoji picker; search by name and check emoji/symbol fallback, selection and copy/type behaviour.
4. Repeat over bright and dark windows or wallpaper. Confirm that blur affects the `launcher` surface and the opaque text remains readable. If contrast is poor, raise background alpha before making text translucent.
5. Check long input and labels, narrow outputs and output scaling. Override dimensions per invocation if an unusual display needs it.
