# Tofi to Fuzzel launch history

Tofi drun history uses `COUNT Display Name`; Fuzzel 1.15's native app cache uses `desktop-id.desktop|COUNT`. Copying or renaming the file directly does not transfer the history correctly.

```sh
cd ~/dotfiles
python3 scripts/import-tofi-history.py
python3 scripts/import-tofi-history.py --apply
```

The default input is `${XDG_STATE_HOME:-$HOME/.local/state}/tofi-drun-history`, and the output is `${XDG_CACHE_HOME:-$HOME/.cache}/fuzzel`. The source is never modified. Close any active Fuzzel menu before applying.

The importer indexes installed XDG desktop files, respecting user-directory precedence, hidden/NoDisplay entries, TryExec and localized names. Exact unique display-name matches map to desktop IDs. It does not guess between ambiguous entries or assign old names to unrelated apps. Unmatched entries remain in Tofi's history and are listed in the private mapping report.

Existing Fuzzel counts are retained and matched Tofi counts are added. A private ledger remembers imported counts, so repeated imports add only any further increase in the Tofi source. Repeating an unchanged import writes nothing. Do not delete the ledger to repeat an import unless you intentionally want counts added again; an emptied Fuzzel cache is not automatically re-seeded from an already-imported source.

Backups, the mapping report and the ledger live under `${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles/history-import/`. Before a write, the importer saves the previous native cache and ledger. An interrupted write leaves `pending.json` and requires review, preventing silent double counting. History and mapping data are private runtime state and are not tracked in this repository.

For immediate rollback before further Fuzzel use, review and restore the selected backup's `fuzzel-before` and `ledger-before.json` together. Preserve any new Fuzzel usage first: restoring an old cache directly discards uses recorded since that backup. The untouched Tofi source is also available for inspection.

Unit tests cover both native formats, preserving Fuzzel-only counts, idempotence, incremental imports, unknown/ambiguous names, user precedence, hidden entries and localized names. The actual import was followed by a second preview showing zero new additions. Executable-only `tofi-history` is not imported into the desktop-app cache; it has command names rather than desktop identities.
