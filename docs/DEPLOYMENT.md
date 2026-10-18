# Deployment and recovery

The repository is source; `home/` mirrors selected paths below your home directory.
`manifest.json` is the complete deployment allowlist:

```json
{"version": 1, "paths": [".zshenv", ".config/tofi/config"]}
```

Only named files and symlinks are deployed. Real directories cannot be entries;
list their files individually so app databases, sessions and unrelated preferences
stay untouched. Duplicate, overlapping and traversing paths are rejected. Keep
credentials, browser profiles, caches and histories out of the repository.

## Preview and apply

Python 3.9+ is required. Initialise the documented Git submodules and install the
documented dependencies before deployment. No packages or services are modified
by this script.

```sh
cd ~/dotfiles
./install.sh
./install.sh --target-home /tmp/dotfiles-test-home
./install.sh --target-home /tmp/dotfiles-test-home --apply
# After reviewing that preview and test home:
./install.sh --apply
```

Default operation is a dry run, including rollback. It writes nothing. `KEEP`
means an existing link already points to this checkout; `LINK` creates a link;
`BACKUP+LINK` moves an existing file or symlink into recovery storage first.
Each destination links to its absolute path in this checkout: do not move or
delete the checkout after deploying it. Repeating apply makes no changes when
all links are already correct.

The complete manifest and destination parents are checked before any writes.
Destination-parent symlinks and real directory conflicts cause an error. The
tool never links an entire app directory unless the source entry is itself an
explicit asset symlink. Source symlinks must resolve within `home/`, or within
`/usr/share/themes` or `/usr/share/icons` for installed theme assets. Missing
sources, missing system themes and dangling nested asset links cause an error.
The `.local/state/dotfiles-deploy` location is reserved for recovery metadata.

## Rollback

Every changing apply prints a recovery run ID. Originals and its journal live
under `~/.local/state/dotfiles-deploy/<RUN_ID>/`; new run directories are mode
0700, journals 0600, and original file permissions are retained. These backups
are local and must never be committed or published.

```sh
./install.sh --rollback RUN_ID
./install.sh --rollback RUN_ID --apply
# For a temporary home, pass the same --target-home used when applying.
```

Rollback restores original files/symlinks and removes links created by that run.
It checks every destination before proceeding and refuses to remove a link or
file changed since deployment. Resolve conflicts manually while preserving the
saved originals, then retry. Existing correct links were not modified by the
run and are not rollback entries. Roll back multiple deployments in reverse
order. Recovery journals are retained; empty directories created for deployed
files are retained too.

The journal is written before file operations, so an interrupted apply can
usually be recovered using the printed run directory or latest recovery run.
Run one deployment/rollback process at a time and avoid editing destinations
during it; this is a local workstation tool, not a concurrent transactional
filesystem manager. If the operating system fails between an original being
restored and the journal update, inspect the remaining originals manually.

## Isolated verification

```sh
python3 -m unittest discover -s tests -p 'test_deploy.py' -v
sh -n install.sh
python3 -m py_compile scripts/deploy.py
```

Tests use temporary repositories and homes, covering dry runs, backup/restore,
unmanaged-file preservation, reapply, rollback conflicts, symlink parents,
malformed allowlists and dangling dependencies. They do not validate the actual
desktop appearance or reload services.

## Filesystem boundary

Backups use atomic rename. The target files and recovery storage must support rename between their locations. A sandbox overlay can report `EXDEV` even when stat device IDs match; restore the printed journal and rerun outside that overlay. Do not replace this with an unverified copy/delete. The private recovery snapshot remains the first fallback.
