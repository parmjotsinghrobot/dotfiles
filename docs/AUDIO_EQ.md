# Galaxy Buds 3 FE equalizer

The managed filter is `home/.config/pipewire/pipewire.conf.d/sink-eq6.conf`. The current preset preserves the original bass for EDM and brings the treble closer to the [SoundGuys preference curve](https://www.soundguys.com/product/samsung-galaxy-buds-3-fe/), using its B&K 5128 measurement. It is a preference adjustment based on that chart, not an acoustic measurement of this particular pair or the user's ears.

## Current preset (4 November 2026)

| Node | Filter | Frequency | Q | Gain |
| --- | --- | --- | --- | --- |
| `eq_band_2` | Peak | 822 Hz | 1.144 | +2.16 dB |
| `eq_band_3` | Peak | 1538 Hz | 2.500 | -1.05 dB |
| `eq_band_4` | Peak | 6275 Hz | 1.560 | -3.35 dB |
| `eq_band_5` | Peak | 9759 Hz | 2.014 | +8.00 dB |
| `eq_band_7` | Peak | 12341 Hz | 3.314 | -4.51 dB |
| `eq_band_8` | Peak | 15300 Hz | 2.301 | +5.87 dB |
| `eq_band_10` | High shelf | 18360 Hz | 0.707 | -4.50 dB |

The preamp is **−7.9 dB** (`preamp:Mult=0.402717034`, `Add=0`). This is inside the DSP graph, independent of the headphone volume slider. The three unused bands (1, 6 and 9) are at 0 dB. Compared with the previous conservative preset, the lower preamp reduces overall level by another 5 dB; bass is retained in the response shape, rather than made louder through the hardware volume control.

Full parameters and metrics: [audio/galaxy-buds-3-fe-preset.json](audio/galaxy-buds-3-fe-preset.json).

The source contains 241 numerical measurement points extracted directly from the public page; its pink target was reconstructed from the SVG path (approximately 0.006 dB vertical quantization). The target keeps the original measured bass below 150 Hz and blends logarithmically to the SoundGuys target by 350 Hz. Above that, full target correction was fitted across the chart's 20 Hz–20 kHz range, with extra weight above 4 kHz. The fit uses bounded gains/Q and rounded controls. Original bass shape changes by less than 0.06 dB below 150 Hz. Predicted treble error against the target is about 0.49 dB RMS above 4 kHz on a log-frequency grid.

The strongest combined boost is about 6.90 dB; the −7.9 dB preamp leaves at least 1 dB of spectral headroom at 44.1, 48 and 96 kHz. All rounded filters have poles inside the unit circle at those rates. These are numerical checks, not a listening-quality guarantee. High-treble matching is less certain because the source is an averaged artificial-ear measurement; the stronger fit is an auditionable preset, not proof of a more accurate response at the user's eardrum.

Source CSVs remain under `~/Documents/Audio/galaxy-buds-3-fe-soundguys/`. The current fit script, JSON, Equalizer APO-style export and plot are in `fitted-edm/`; the previous conservative artifacts remain in `fitted/`. Reproduction uses NumPy, SciPy and Matplotlib in an isolated environment, not desktop runtime dependencies.

## Routing

```text
App -> effect_input.eq6 -> preamp -> EQ -> effect_output.eq6 -> Galaxy Buds 3 FE
```

WirePlumber's `filter.smart` policy inserts `earphone-eq` for an `Audio/Sink` whose `node.description` is `Galaxy Buds 3 FE`. Leave the real earphones selected as the output. Explicit client selections of those headphones also pass through the filter; other output devices are outside the rule. Update the match if the node description changes. Playback-side `node.dont-fallback` and `node.linger` make the filter wait for its target rather than falling back or being destroyed.

Policy reference: [WirePlumber smart filters](https://pipewire.pages.freedesktop.org/wireplumber/policies/smart_filters.html). DSP reference: [PipeWire Filter-Chain](https://docs.pipewire.org/page_module_filter_chain.html). Requires WirePlumber 0.5 and PipeWire's builtin biquad/linear plugins.

## Applying adjustments and rollback

Edit band `Freq`, `Q`, `Gain` in the managed file; recompute preamp headroom if adding boosts. Live band controls can be updated with `pw-cli set-param NODE_ID Props '{ params = [ "eq_band_1:Gain" -2.0 ] }'`. The preamp control is `preamp:Mult`, using linear amplitude rather than dB. Obtain the current `effect_input.eq6` ID from `wpctl status`; IDs change after restarts. Live adjustments do not save themselves to the source file.

Graph-structure edits need an audio restart or fresh session. `systemctl --user restart pipewire.service wireplumber.service pipewire-pulse.service` interrupts audio. During this setup the restart brought Bluetooth back in hands-free/mSBC mode with the A2DP connection initially unavailable. Reconnecting its A2DP profile and selecting `a2dp-sink` restored **AAC**, verified on the live node. Do not infer the codec just from the profile name: on this installation `a2dp-sink` denotes AAC, while `a2dp-sink-sbc` denotes SBC. No global microphone/autoswitch policy was changed.

The previous conservative preset is backed up at `/home/parmjot/.local/state/dotfiles-eq/20261104T012418Z/conservative-config.conf` (and `conservative-preset.json`). The prior flat config is backed up at `~/.local/state/dotfiles-eq/20261104T011607Z/flat-config.conf`. To disable the curve live without a restart, set `preamp:Mult` to 1 and every `eq_band_1:Gain` through `eq_band_10:Gain` to 0 in the filter's Props params. For persistent flat rollback, copy the backup's contents into the managed source file and reload audio when convenient. The even older earphone curve remains in `~/.local/state/dotfiles-cleanup/20261104T010222Z/source/`.

## Verification

- Updated the existing live graph through Props controls without restarting any audio or music service.
- Queried live preamp and all seven active bands; values match the saved preset. Bands 1, 6 and 9 are flat.
- The persistent configuration parses through PipeWire and a private PipeWire instance loads the complete graph.
- AAC/A2DP remained active; app links still enter the EQ and only its output connects to the headphones.
- Rounded-filter stability and full-band headroom were checked at 44.1/48/96 kHz. The plot is a predicted, level-aligned response.

No physical earphone response was measured. Final bass/treble balance needs listening evaluation.
