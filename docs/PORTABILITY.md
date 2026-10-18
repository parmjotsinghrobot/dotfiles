# Portable defaults and machine settings

The shared Sway defaults contain generic input repeat settings, app bindings and the deployed wallpaper at `~/.local/share/backgrounds/dotfiles/desktop.jpg`. `sway/config` explicitly includes `machines/hp-envy.conf` after the shared snippets to retain this laptop's existing behaviour. That file owns its touchpad, Corsair keyboard, Logitech mouse, eDP panel, remembered lab/TV modes and the optional HEADLESS-1 tablet placement/workspace. HEADLESS-1 is configured but never created automatically.

On a different machine, remove that include or replace it with a reviewed profile. `machines/local.conf` is an optional final include for local adjustments. Do not commit personal display identifiers unnecessarily. Input names come from `swaymsg -t get_inputs`; output names come from `swaymsg -t get_outputs`. These queries are read-only; test a changed mode on the physical desktop before retaining it.

## Shell paths and engineering tools

`~/.zshenv` and Bash source `shell/environment.sh`. It establishes XDG defaults without overriding existing values, adds `~/.local/bin` once and preserves `GNUPGHOME=~/.local/share/gnupg` unless explicitly set. Existing signing keys stay where they are. The terminal TTY is set interactively; gpg-agent is socket activated.

Systemd owns parsing `environment.d` files. Shell startup does not run `export $(generator)` or evaluate environment-generator output. Such word splitting corrupts values containing spaces and treats shell-like data incorrectly. Start a fresh login session after changing session environment; an existing terminal inherits its session's values. For shells launched outside that session, put explicit trusted shell exports in `shell/environment.local.sh`, rather than sourcing environment.d as a shell program.

Course toolchains are optional. Source `$XDG_CONFIG_HOME/shell/engineering.example.sh` from your untracked `shell/environment.local.sh` if required. Its Qsys lookup uses the installed `qsys` command's real path; no Quartus installation was found on this machine during the audit, so no guessed or package-cache path is exported. If Qsys is installed outside PATH, set `QSYS_ROOTDIR` locally to its existing `quartus/sopc_builder/bin` directory. The Rockchip compiler path is added only if its executable exists. This compiler directory was found locally, but is not required for desktop startup.

The previous Ruby 3.0 gem path, `$HOME/gems` and a versioned Wine-GE path are no longer inserted globally. No matching Ruby/gem executable was found in the audit. Use an installed runtime's own environment setup or an explicit checked local PATH when a project needs one. This removes stale assumptions without deleting any runtimes or project files.

Shell startup is offline by default. `weather` explicitly fetches a short forecast with a two-second timeout. `dotfiles-refresh-updates` refreshes the update-count cache explicitly. `DOTFILES_GREETING=1` displays a short greeting and cached count; it performs no update check. History/completion files use the XDG cache, outside the repo.

## Audio and suspend

Volume keys use `wpctl` against `@DEFAULT_AUDIO_SINK@`, matching the status bar's PipeWire target; volume-up is capped at 100%. Bluetooth/USB output selection still needs a physical session check.

`Mod+Escape` calls `~/.local/bin/lock-and-suspend`. The installed swaylock-effects supports `--daemonize` (`-f`), which detaches only after locking; it does not provide `--ready-fd`. The wrapper stops on a locking failure and requests suspend only after readiness. Both the wrapper and swayidle's before-sleep hook disable grace with `--grace 0`; resume requires authentication. No fixed sleep guesses lock readiness. The existing idle suspend delay remains five minutes; before-sleep pauses media and waits for the locker. No suspend, lock, reload or live session action was run during implementation.

The sticky-notes daemon remains `exec_always ~/.local/bin/sticky-notes-daemon.py`; its own single-instance guard handles reloads. Visual alpha is managed by application backgrounds; whole-window opacity is not added here.

## Local overrides

These optional local files are intentionally absent from the managed file manifest: `shell/environment.local.sh`, `shell/login.local.sh`, `shell/interactive.local.sh` and `sway/machines/local.conf`. Create them in your live XDG config directory. In any such file, use `$HOME`, checked directories and explicit quoting instead of another account's absolute paths. Never put credentials into a tracked profile.

GUI launches use `~/.local/bin/launch-app` to source the same environment defaults as shells. This matters for Qt because login-manager-started Sway does not inherit systemd user-manager variables. Fuzzel inherits the bridge environment and passes it to apps it launches; D-Bus activation is synchronized on each Sway reload. Explicit per-app theme overrides are preserved.
