# Fuzzel trial and emoji usage sorting

Fuzzel 1.15.0 is installed for comparison. Tofi remains the default for Super+Space, clipboard history and Super+F1; the trial does not replace those bindings.

```sh
# Applications
fuzzel

# Existing emoji picker, with native Fuzzel usage history; copies the choice
~/.config/tofi/scripts/emoji-picker.sh --picker fuzzel

# Print the choice instead of copying
~/.config/tofi/scripts/emoji-picker.sh --picker fuzzel --echo
```

The Fuzzel config keeps Iosevka Curly, Mocha Pink, an 80% background, square corners and no icons. Its approximate square geometry is expressed in characters/rows rather than Tofi's exact pixel dimensions. Up, Down, Tab and Shift+Tab stop at the list ends. Enter accepts; Escape cancels. The counter shows matching entries versus total entries, not page numbers.

## Native usage counts

Fuzzel's `--cache=PATH` explicitly enables usage tracking in dmenu mode. Its own manual recommends separate files for different menu types, including emoji. The script now supplies:

```text
${XDG_CACHE_HOME:-$HOME/.cache}/bemoji/fuzzel-history
```

Frequent selections rise in Fuzzel's ordering; typed matching still influences filtered results. Counts refer to the full input label (emoji plus description), so changing descriptions can create new history entries. Application usage remains in Fuzzel's separate default cache. The script does not maintain a second counter or write usage state into Git. `BEMOJI_FUZZEL_CACHE` overrides the emoji cache path; `BEMOJI_PICKER=fuzzel` selects this backend without a flag. Other picker backends retain their existing behaviour.

The original plain Tofi emoji invocation did not pass a history file; its run/drun app counts are separate. This change does not import app counts or invent emoji usage from them.

## Checks

The installed `fuzzel --check-config` validates all options, including the deployed config. All 32 regression/integration tests pass. Integration tests stub the UI to check picker selection, dedicated cache arguments with spaces, combined Unicode emoji output, cancellation and no change to default Tofi selection. These tests do not claim to measure latency or implement Fuzzel's native sorting.

For a direct check, choose an emoji twice, reopen with an empty search, and check its position. Compare app/emoji startup responsiveness to Tofi. Existing SwayFX effects target the `launcher` namespace, also Fuzzel's default. See the installed `fuzzel(1)` cache documentation or [packaged upstream manual](https://manpages.debian.org/unstable/fuzzel/fuzzel.1.en.html).

## Relaunch checks

The relaunch completed without a reported failure. Still check Super+V and Super+F1, audio/brightness keys, screenshot creation, toolkit cursor/font transitions and a normal lock/suspend/resume when convenient. Uniform Iosevka Curly across notifications and toolkit apps is a requested follow-up after this trial; no font changes were made as part of the Fuzzel trial.
