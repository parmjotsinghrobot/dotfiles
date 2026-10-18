# Original setup recovery

Private snapshot: `~/.local/state/dotfiles-backups/20261018T011646Z`. Contains original Git metadata and index, staged/unstaged binary patches, selected live files and `inventory.json`. The old live Git directory is archived as `original-live-git`; original submodule pointer files are under `original-submodule-pointers`. The live `.config` directory is no longer a repository.

The canonical `~/dotfiles` checkout reuses a complete copy of the **original Git metadata**, retaining the original commits, refs, reflogs, hooks, repo configuration and object store. Only the worktree layout, relocated submodule worktree paths, migration index and new work branch change. Existing `main` stays at its original commit. New staged objects were retained during metadata reuse. No original objects were pruned. The original Git index is separately preserved in the snapshot.

The preliminary clone's metadata is also retained as `clone-metadata-before-original-reuse`. `migration-full-git` is another preserved metadata copy; its read-only `git fsck --full --no-reflogs` passed with expected dangling objects. Do not replace `.git` or replay patches over modified files blindly.

Managed-file deployment rollback and legacy-cleanup restoration are documented in VALIDATION.md and STARTUP.md. Restore live files from the private snapshot only after reviewing their current owners and backing up subsequent changes.
