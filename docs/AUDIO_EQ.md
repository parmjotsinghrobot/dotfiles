# Galaxy Buds 3 FE equalizer

The managed filter is `home/.config/pipewire/pipewire.conf.d/sink-eq6.conf`. It applies a conservative fit towards the SoundGuys preference curve, using the [Galaxy Buds 3 FE measurement](https://www.soundguys.com/product/samsung-galaxy-buds-3-fe/) on a B&K 5128. This is an experimental preference adjustment, not a measured calibration of this particular pair or the user's ears.

## Current preset (4 November 2026)

| Filter | Frequency | Q | Gain |
| --- | --- | --- | --- |
| Low shelf | 90 Hz | 0.707 | −3.24 dB |
| Peak | 764 Hz | 1.422 | +1.90 dB |
| Peak | 1544 Hz | 1.500 | −0.31 dB |
| Peak | 6000 Hz | 1.500 | −1.41 dB |

A separate builtin `linear` stage supplies **−2.9 dB preamp** (`Mult=0.716143410`, `Add=0`). The remaining six biquads are flat spare bands. Preamp attenuation is inside the DSP graph, independent of the headphone volume slider. The peak calculated EQ boost is 1.85 dB or less at 44.1/48/96 kHz, leaving at least 1 dB of frequency-response headroom after preamp.

Full parameters and fit metrics: [audio/galaxy-buds-3-fe-preset.json](audio/galaxy-buds-3-fe-preset.json).

The input contained 241 measurement points directly from the public page's `labCharts.frequency.points`. Its displayed pink target was reconstructed from SVG coordinates, with approximately 0.006 dB vertical quantization. Both series use the same fixture/chart reference; no unrelated measurement-rig target was substituted.

Fitting used log-spaced frequencies from 20 Hz to 6 kHz, smoothed target-minus-measurement, 85% correction strength, bounded gains and broad Q values. Frequencies above 6 kHz were excluded from the fit; no boost was added to fill the large 10 kHz dip. Filter tails still extend beyond 6 kHz. Rounded controls were checked again after optimization. Predicted level-aligned target error over the fitted log-frequency grid falls from 2.02 dB RMS to 0.67 dB RMS. That is a calculation against this chart, not an independently measured acoustic improvement.

The source CSVs, fitting script, Equalizer APO-style export and plot are under `~/Documents/Audio/galaxy-buds-3-fe-soundguys/` on this machine. Reproduction uses NumPy, SciPy and Matplotlib in an isolated environment, not desktop runtime dependencies. The fitting script is `fitted/fit.py`; it expects that data directory. Plot: `fitted/eq-fit.png`.

## Routing

```text
App -> effect_input.eq6 -> preamp -> EQ -> effect_output.eq6 -> Galaxy Buds 3 FE
```

WirePlumber's `filter.smart` policy inserts `earphone-eq` for an `Audio/Sink` whose `node.description` is `Galaxy Buds 3 FE`. Leave the real earphones selected as the output. Explicit client selections of those headphones also pass through the filter; other output devices are outside the rule. Update the match if the node description changes. Playback-side `node.dont-fallback` and `node.linger` make the filter wait for its target rather than falling back or being destroyed.

Policy reference: [WirePlumber smart filters](https://pipewire.pages.freedesktop.org/wireplumber/policies/smart_filters.html). DSP reference: [PipeWire Filter-Chain](https://docs.pipewire.org/page_module_filter_chain.html). Requires WirePlumber 0.5 and PipeWire's builtin biquad/linear plugins.

## Applying adjustments and rollback

Edit band `Freq`, `Q`, `Gain` in the managed file; recompute preamp headroom if adding boosts. Live band controls can be updated with `pw-cli set-param NODE_ID Props '{ params = [ "eq_band_1:Gain" -2.0 ] }'`. The preamp control is `preamp:Mult`, using linear amplitude rather than dB. Obtain the current `effect_input.eq6` ID from `wpctl status`; IDs change after restarts. Live adjustments do not save themselves to the source file.

Graph-structure edits need an audio restart or fresh session. `systemctl --user restart pipewire.service wireplumber.service pipewire-pulse.service` interrupts audio. During this setup the restart brought Bluetooth back in hands-free/mSBC mode with the A2DP connection initially unavailable. Reconnecting its A2DP profile and selecting `a2dp-sink` restored **AAC**, verified on the live node. Do not infer the codec just from the profile name: on this installation `a2dp-sink` denotes AAC, while `a2dp-sink-sbc` denotes SBC. No global microphone/autoswitch policy was changed.

The prior flat config is backed up at `~/.local/state/dotfiles-eq/20261104T011607Z/flat-config.conf`. To disable the curve live without a restart, set `preamp:Mult` to 1 and every `eq_band_1:Gain` through `eq_band_10:Gain` to 0 in the filter's Props params. For persistent flat rollback, copy the backup's contents into the managed source file and reload audio when convenient. The even older earphone curve remains in `~/.local/state/dotfiles-cleanup/20261104T010222Z/source/`.

## Verification

- A private PipeWire instance loaded the complete graph and exposed the preamp and filter controls before changing live audio.
- The real audio restart loaded the persistent graph; queried controls matched the saved preset.
- Live headphone input links came only from `effect_output.eq6`, and application streams entered `effect_input.eq6`.
- AAC/A2DP was restored after the restart and the EQ route was verified again.
- MPD configuration, enablement and services were not changed or restarted. MPD and rich presence retained their process IDs. The media bridge was already inactive before this audio restart (its recorded stop time was 14:02:56); it was left alone.

No microphone recording or acoustic measurement was performed. Listening quality and physical Bluetooth reconnect behaviour still need user evaluation; the graph and numerical fit cannot establish those.
