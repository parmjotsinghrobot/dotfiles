# Earphone equalizer

The ten-band filter lives in `home/.config/pipewire/pipewire.conf.d/sink-eq6.conf`, linked to the corresponding path under `~/.config`. The old earphone curve was reset to **0 dB on every band** on 4 November 2026. Existing frequency/Q values and filter types are placeholders for the new curve, not a Galaxy Buds tuning recommendation. The old config is backed up under `~/.local/state/dotfiles-cleanup/20261104T010222Z/source/`.

## Routing

```text
App playback -> effect_input.eq6 -> ten-band EQ -> effect_output.eq6 -> Galaxy Buds 3 FE
```

The capture side uses WirePlumber's `filter.smart` policy, named `earphone-eq`, with a target matching `node.description = "Galaxy Buds 3 FE"` and `media.class = "Audio/Sink"`. Leave the real earphones selected as the output. WirePlumber inserts the EQ when clients select that device, including clients explicitly targeting it. Other output devices are outside this earphone-specific rule. If the headphones' node description changes, update the match.

This uses the [upstream WirePlumber smart-filter policy](https://pipewire.pages.freedesktop.org/wireplumber/policies/smart_filters.html). It requires WirePlumber 0.5; the installed version was 0.5.18 at validation. The persistent playback-side `node.dont-fallback` and `node.linger` settings keep the filter waiting if its target is absent, instead of falling back to another device or being destroyed.

## Tuning

Edit each band's `Freq`, `Q` and `Gain` in the managed file. Use headroom when adding boosts; this setup does not include a separate preamp stage.

Config edits are loaded at the next PipeWire start. If applying immediately with `systemctl --user restart pipewire pipewire-pulse wireplumber`, expect an audio interruption and possible application reconnection. This restart was **not** performed during the setup: the existing filter's gains were flattened with `pw-cli set-param`, and equivalent smart routing was enabled through the `filters` metadata object. The on-disk configuration makes those choices persistent after restart.

A live, temporary band adjustment can be made with `pw-cli set-param NODE_ID Props '{ params = [ "eq_band_1:Gain" -2.0 ] }'`. Get the current `effect_input.eq6` node ID from `wpctl status`; IDs change across server restarts. Live controls alone do not save the curve: keep the managed file in sync.

## Verification

On 4 November 2026:

- PipeWire's recursively merged configuration parsed as JSON and contained exactly one filter chain, ten zero-gain bands and the smart-filter target.
- The existing graph changed from direct app-to-headphone links to app-to-EQ-to-headphone links for both visible application streams.
- Newly created silent `pw-cat` streams entered the EQ when using the default output and when explicitly targeting the headphones; test streams were terminated afterwards.
- Querying live filter parameters confirmed all ten gains were 0 dB.
- The default output remained the headphones. MPD, mpDris2 and MPD rich presence retained their original process IDs and active state; their configuration and enablement were not changed.

This verifies routing and running control values, not listening quality or a calibrated earphone response. A full audio-server restart and physical Bluetooth disconnect/reconnect were not tested in this session.
