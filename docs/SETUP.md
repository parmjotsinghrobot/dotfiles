# Package and feature setup

Plain `./install.sh` remains a links-only preview. Use the guided flow in a terminal:

```sh
./install.sh --setup
./install.sh --setup --apply
```

The second command asks the questions again; it does not remember the first
selection. To repeat an exact selection, use explicit flags instead:

```sh
# Desktop + appearance packages, including foreign packages via an existing helper:
./install.sh --install-packages all --aur-helper paru
./install.sh --install-packages all --aur-helper paru --apply

# Official packages + everyday utilities + Bluetooth:
./install.sh --install-packages official --feature utilities --feature bluetooth
# Enable the existing mail timer for future user sessions:
./install.sh --feature mail
# Add --apply to either command after reviewing its output.
```

`--aur-helper yay` is also supported. The installer does not bootstrap an AUR
helper or bypass package/build confirmation prompts. Official-only installation
leaves foreign packages for manual review; the configured SwayFX desktop and GTK
assets still require their foreign packages. Foreign lists were captured using
`pacman -Qm`, so some entries may be locally built rather than available in AUR.

| Feature flag | Action |
| --- | --- |
| `utilities` | Add `packages/optional-*` to the package selection |
| `engineering` | Add `packages/engineering-*`; vendor tools/licenses remain separate |
| `emoji-typing` | Add `wtype` for the existing emoji picker's Wayland typing mode |
| `bluetooth` | Enable and start system `bluetooth.service`; with packages also install `bluez-utils` |
| `network` | Enable and start system `NetworkManager.service`; choose only if it should manage this machine's network |
| `ui-fonts` | Run the existing UI font helper, which saves previous GSettings values |
| `mail` | Enable existing `daily-nonsense.timer` without starting or restarting it |

Repeat `--feature` for multiple selections. Package features require
`--install-packages official` or `all`. Omitting/declining a feature leaves its
current state alone; this is an additive setup flow, not an uninstall manager.
Existing mandatory deployment entries (including memory warnings and the OSD)
retain their existing behaviour.

## Order and boundaries

Setup displays the command plan and deploys in this order: packages, dotfile
links, then selected service/font actions. Package operations run only on Arch
or distributions declaring Arch in `/etc/os-release`'s `ID_LIKE`. Apply must run
as the normal user against their current home. `sudo` is used only for official
packages and system services; AUR builds run as the user. Alternate target homes
can be previewed, but cannot apply package/feature setup.

Official installation uses `sudo pacman -Syu --needed`, which includes a full
system upgrade to avoid a partial upgrade. Read Arch news and the proposed
transaction before accepting it. See [Arch system maintenance](https://wiki.archlinux.org/title/System_maintenance#Partial_upgrades_are_unsupported).
Package availability is resolved by the target's configured repositories and
helper, rather than assumed from the historical snapshot. Missing names or
failed builds stop setup; later deployment/features are not run. All package
commands retain their normal confirmation prompts.

Without `--apply`, no package manager, service manager or font helper is invoked
and no files are written. Missing external theme assets may be marked `PENDING`
in a package preview. Missing repository sources, unsafe destination parents and
real-directory conflicts still fail before package changes. Initialise the Git
submodules first. Apply checks external assets after package installation.

Package upgrades, service enablement and GSettings changes are outside dotfile
rollback. A later failure can leave earlier operations applied. Retry after
resolving the error; managed dotfile links and `--needed` package installs are
safe to repeat. Font backups have their own restore option.

## Daily-nonsense mail

This feature uses the **existing personal installation** under
`~/.local/share/daily-nonsense/` and existing user units under
`~/.config/systemd/user/`. It requires the Python script, settings, email template,
memo library, private `config.json`, `recipients.json`, service and timer to be
present. On a new machine, restore/setup that application separately before
selecting mail. The dotfiles repo does not copy credentials, recipients, message
history or the personal mail application into Git.

Selecting mail reloads user unit definitions and runs
`systemctl --user enable daily-nonsense.timer`. It deliberately omits `--now`:
the existing persistent timer could send catch-up mail immediately if started.
The selection changes enablement for future user sessions and leaves the current
timer's running/stopped state unchanged. Future scheduled emails follow the
existing application settings; no test email or send command is executed.
See [systemctl enable](https://man.archlinux.org/man/systemctl.1.en).

To stop and disable scheduled sending yourself:

```sh
systemctl --user disable --now daily-nonsense.timer
```

## Checks

Run `python3 -m unittest discover -s tests -v`. Setup tests use temporary homes
and mocked command execution; they never install packages, enable units or send
email. A real clean-machine rebuild remains a separate validation step.
