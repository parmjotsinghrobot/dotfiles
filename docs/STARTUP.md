# Startup and legacy cleanup

Sway's session configuration owns the desktop startup commands. The notes daemon
holds a nonblocking `flock` in `$XDG_RUNTIME_DIR/sticky-notes-daemon.lock`, or
`~/.cache/dotfiles/sticky-notes-daemon.lock` when that variable is unset. A duplicate
exits before connecting to Sway. The descriptor remains open for the daemon's
lifetime; a crash releases the lock automatically. The stale lock file itself is
harmless.

An already running copy of the old, unguarded daemon cannot acquire this guard
retroactively. Deploy the source and use the next fresh login to start a single
guarded copy. Do not blindly kill desktop processes during the migration. Testing
with a mocked Sway connection verifies duplicate prevention, not actual window
behaviour in a logged-in Sway session.

The `psd-resync.timer.d/frequency.conf` override resyncs every minute; its description
now agrees with that interval. Installing source does not reload the running user
service manager or alter an active timer.

## Review and retire stale entries

From the repository root:

```sh
python3 scripts/cleanup_legacy.py
python3 scripts/cleanup_legacy.py --apply
```

The first command only reports matches and makes no files or directories. The
second moves each matching file or symlink into a private directory under
`~/.local/state/dotfiles/legacy-cleanup/`. It prints that run's rollback command.
It does not stop services, send D-Bus calls, reload systemd or end the session.
Use `--target-home /path/to/fixture` to inspect a separate home.

The scope is deliberately narrow:

- Broken links in user `*.wants` directories for `mpd-notification.service`,
  `gamemoded.service`, `modprobed-db.service`, `yams.service`, and
  `spotblock.service`. Working links and regular files remain.
- `firefox-profile@.service` only when its `ExecStart` uses the known
  `%h/.local/bin/firefox-sync.sh` and that helper is absent.
- `cameractrlsd.service` only when its `ExecStart` is exactly the known
  `/usr/lib/python3.14/site-packages/CameraCtrls/cameractrlsd.py` and that path
  is absent. An updated executable path is retained.
- `lunarclient.desktop` only when `Exec` starts from `/tmp/.mount_`.
- The known `launch-waybar` watcher only when its old configuration and stylesheet
  are both absent. Replaced helpers and restored configuration remain.

No application directories, caches or existing backups are removed. Symbolic
links are moved themselves, without moving their targets. Symlinked parent
directories are rejected to prevent cleanup outside the selected home.

## Restore a cleanup run

Substitute the printed run ID:

```sh
python3 scripts/cleanup_legacy.py --rollback RUN_ID
python3 scripts/cleanup_legacy.py --rollback RUN_ID --apply
```

Rollback is also read-only by default. It restores saved entries by rename and
refuses to overwrite newly created files. Move conflicting new entries aside,
then repeat. Repeating a completed rollback is harmless. The private
`journal.json` records the target home, original relative paths and backup names;
intent is recorded before each move so an interrupted cleanup remains restorable.
Leave this recovery directory in place until the new session has been checked.

## Fixture verification

```sh
python3 -m unittest discover -s tests -p test_session_cleanup.py -v
```

These tests exercise broken versus working links, unrelated-file retention,
read-only preview, backup permissions, rollback/conflicts, exact stale command
matching, parent-symlink rejection, and real cross-process notes-lock contention
before any Sway socket is opened. They do not prove startup on a real login.
