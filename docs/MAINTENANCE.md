# Maintenance and retained alternatives

Swaybar is the supported bar, started by `sway/config.d/40-bar.conf`. Its
configuration and status script live in `home/.config/sway/swaybar/`.
The original checkout already had the Waybar files staged for deletion; the
private recovery snapshot and original Git history preserve them. The old
`launch-waybar` helper belongs to the retired setup.

wpaperd is a dormant alternative: Sway uses its configured wallpaper directly.
GTKlock is also dormant; the active lock command uses Swaylock Effects. Its old
CSS depends on `/tmp/lockscreen.png`, which is temporary state, not a managed
asset. Neither alternative should be added to autostart without deliberately
replacing and testing the current wallpaper/lock workflow.

## Old files and recovery storage

The private snapshot described in [RECOVERY.md](RECOVERY.md) preserves original
files and Git metadata, including the index and staged/unstaged changes. Old
`gtk-3.0.backup`, `gtk-4.0.old`, `kitty.conf.bak` and similar copies are not source
dependencies. Keep the snapshot until deployment and the real desktop have
been checked. This cleanup does not delete live app caches or personal app
state; those files are simply outside the deployment allowlist.

The original `.git` was about 1.5 GiB, although objects reachable from refs
occupied about 5 MiB. At the user's request, `~/dotfiles` now directly reuses
the full original metadata, including reflogs, hooks, local settings and loose
objects; no old data was pruned. The preliminary smaller clone metadata and
complete original snapshots are retained privately. Investigate storage only
with those recovery copies available; do not assume unreachable objects are
disposable.

## Application associations

`home/.config/mimeapps.list` contains only locally resolvable desktop IDs.
[MIME_CLEANUP.json](MIME_CLEANUP.json) records removed associations. The audit
checked desktop IDs in `~/.local/share/applications`,
`/usr/local/share/applications`, and `/usr/share/applications`, including IDs
derived from nested directories.

The only installed application removed from an association was Chromium for
`application/octet-stream`: arbitrary binary data should not default to a web
browser. Other valid choices, including the generated Evolution/Thunderbird
mail handlers, were retained. Missing image-viewer defaults were removed
without inventing a replacement preference; the desktop may ask for a viewer
until one is chosen. On another machine, install the intended apps and review
these associations rather than assuming generated desktop IDs are portable.

## Copied upstream code

`home/.config/zsh/plugins/omz-lib/git.zsh` was already a copied Oh My Zsh Git
library, with its upstream URL in the first line:
[ohmyzsh/ohmyzsh, lib/git.zsh](https://github.com/ohmyzsh/ohmyzsh/blob/master/lib/git.zsh).
Its exact historical upstream commit was not recorded; the migration preserves
the existing file rather than claiming it matches today's upstream revision.
Its SHA-256 at migration is
`26dfed1d098632d05185a4c18a19fec9b40a65d4d15c14856a8e5ee480c84c02`.

The upstream MIT notice is retained verbatim in
[licenses/oh-my-zsh-MIT.txt](licenses/oh-my-zsh-MIT.txt), retrieved on 18 October
2026 from the project's
[official LICENSE.txt](https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/LICENSE.txt).
Keep this copyright and permission notice with redistributed copies. The
separate Zsh submodules retain their own upstream licenses and histories.

## Routine changes

Edit managed source under `home/`, add new individual paths to `manifest.json`,
and preview deployment using [DEPLOYMENT.md](DEPLOYMENT.md). Keep credentials,
profiles, histories, caches, recovery backups and generated files outside Git.
Update dependency and theme docs when introducing an external asset. A syntax
check or temporary-home deployment cannot replace a real login, lock/unlock,
suspend/resume and visual check on the intended displays.
