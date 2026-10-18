# Dotfiles

SwayFX desktop with Catppuccin Mocha, Pink accents and translucent backgrounds. Kitty's 80% background opacity is the reference; text and controls stay opaque. GTK and other applications retain readable opaque surfaces where their toolkit does not support background transparency reliably.

The source repo belongs in `~/dotfiles`, separately from live application data. Only the paths named in `manifest.json` are deployed. Browser profiles, accounts, histories, caches and private keys do not belong here.

## Install or update

On this machine the source is already at `~/dotfiles`. For a new checkout:

```sh
git clone --recurse-submodules https://github.com/parmjotsinghrobot/dotfiles ~/dotfiles
cd ~/dotfiles
```

The public remote must contain this migration before that clone command can reproduce it. This work does not push changes.

Review [dependencies](docs/DEPENDENCIES.md), install the relevant packages, then:

```sh
cd ~/dotfiles
python3 scripts/doctor.py
./install.sh
./install.sh --apply
```

The first installer command previews the changes. Apply backs up existing individual files privately, then links them to this checkout. Reapplying keeps existing managed links. It does not install packages, reload the compositor, restart services or log you out.

The source checkout must stay at its deployed location. Preview against an isolated home with `./install.sh --target-home /tmp/dotfiles-preview`; use an empty directory outside this checkout.

## Recovery

Each apply prints its recovery run ID. Review and restore it with:

```sh
./install.sh --rollback RUN_ID
./install.sh --rollback RUN_ID --apply
```

Rollback refuses to overwrite files that have changed ownership since deployment. See [deployment details](docs/DEPLOYMENT.md) and the [original setup recovery note](docs/RECOVERY.md). Keep recovery copies private: they can contain personal settings and the original Git state.

## Layout and ownership

| Path | Purpose |
| --- | --- |
| `home/` | Selected files, arranged relative to `$HOME` |
| `manifest.json` | Explicit deployment allowlist |
| `theme/palette.json` | Shared Mocha Pink colour roles and opacity policy |
| `packages/` | Required, optional and machine-specific dependencies |
| `scripts/` | Deployment and read-only diagnostics |
| `tests/` | Isolated deployment regression checks |
| `docs/` | Theme, toolkit, portability, migration and validation notes |

Edit managed files here after deployment. Some graphical settings tools, including `nwg-look`, can replace symlinks or overwrite settings; review Git changes and preview deployment afterwards. Do not run `git add` over the live `.config` tree.

Theme policy and component coverage are in [THEME.md](docs/THEME.md). Machine-specific input/output and toolchain settings are described in [PORTABILITY.md](docs/PORTABILITY.md). Changes requiring a real desktop check remain listed in [the task list](docs/DOTFILES_TASKS.md).

## Launcher and fonts

[Fuzzel and emoji history](docs/FUZZEL.md) describes the active launcher, clipboard and emoji menus. Tofi remains an optional fallback. Iosevka Curly is the default UI/document/monospace family; apply session GSettings on a fresh machine with `python3 scripts/apply-ui-fonts.py --apply`.

## Desktop basics

Super+Space launches Fuzzel, Super+Q opens Kitty, Super+B opens the browser, Super+V opens clipboard history, and Super+F1 opens the emoji picker. Super+Shift+C reloads Sway. Super+Escape locks and suspends. Read the managed keybind config for the full list.

The active bar is native Swaybar with a Python status script. SwayFX and swaylock-effects are required for configured visual effects. Swaybar controls, tray behaviour and limitations are documented alongside its files.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/doctor.py
git diff --check
```

Static checks and isolated deployment tests do not establish physical display, suspend/resume or lock-screen behaviour. Check those in a real graphical session before treating a rebuild as fully verified.
