# Zsh startup

`~/.zshenv` sets `ZDOTDIR=${XDG_CONFIG_HOME:-$HOME/.config}/zsh`; Zsh then reads `.zshrc`, the managed symlink to `zshrc`. No extra source line is needed in a home `.zshrc`.

Startup works offline. Weather runs only when you call `weather`. Package checks run only when you call `dotfiles-refresh-updates`; a failed check keeps the old cache. Set `DOTFILES_GREETING=1` in `shell/environment.local.sh` to show a greeting and the existing update count. Refresh the count manually; it can be stale.

History and completion dumps live under `${XDG_CACHE_HOME:-$HOME/.cache}/zsh`. Plugin and theme files resolve through the real `zshrc` path, so deployment symlinks do not break plugin companion files. The upstream passion prompt remains intact. Missing optional theme/plugins are skipped; initialise the repo submodules to enable them.

Shared XDG defaults, local-bin PATH and the existing GPG key location are in `shell/environment.sh`. Local personal setup belongs in `shell/environment.local.sh`, `shell/login.local.sh` (Zsh login only) or `shell/interactive.local.sh` (Bash and Zsh interactive; use compatible syntax). These files are not deployed from this repository. See [portability](../../../docs/PORTABILITY.md) in the repository for optional course toolchains.
