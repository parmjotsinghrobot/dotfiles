# Zsh startup

`~/.zshenv` sets `ZDOTDIR=${XDG_CONFIG_HOME:-$HOME/.config}/zsh`; Zsh then reads `.zshrc`, the managed symlink to `zshrc`. No extra source line is needed in a home `.zshrc`.

Startup works offline. Weather runs only when you call `weather`. Package checks run only when you call `dotfiles-refresh-updates`; a failed check keeps the old cache. Set `DOTFILES_GREETING=1` in `shell/environment.local.sh` to show a greeting and the existing update count. Refresh the count manually; it can be stale.

History and completion dumps live under `${XDG_CACHE_HOME:-$HOME/.cache}/zsh`. Plugin and theme files resolve through the real `zshrc` path, so deployment symlinks do not break plugin companion files. Missing optional theme/plugins are skipped; initialise the repo submodules to enable them.

Editing uses Emacs bindings with Delete, Home/End, Insert, Page Up/Down, Ctrl+Left/Right and Ctrl+Delete. Both common escape sequences and the terminal's terminfo entries are bound. Up/Down retain prefix history search. Passion's alarm-driven prompt refresh is disabled to avoid signal-triggered redraws during editing and completion; its clock updates with each new prompt.

Tab completion prefers prefixes, then separator abbreviations (`r.pdf` → `report.pdf`), then substrings (`13` → `Folder 13`). Completion also works at the cursor inside a word. If ordinary completion fails, a missing path section can be filled: `~/.local/sh|daily-nonsense` → `~/.local/share/daily-nonsense/`, where `|` marks the cursor. Shorter forms work too: from your home directory, `.loca|daily` completes to `.local/share/daily-nonsense/`. This fallback matches the directory prefix before the cursor and the remaining path after it, allowing the final name to be abbreviated. It searches up to three directory levels and stops at the nearest level with matches. It considers at most 512 directories and leaves multiple matches ambiguous.

Shared XDG defaults, local-bin PATH and the existing GPG key location are in `shell/environment.sh`. Local personal setup belongs in `shell/environment.local.sh`, `shell/login.local.sh` (Zsh login only) or `shell/interactive.local.sh` (Bash and Zsh interactive; use compatible syntax). These files are not deployed from this repository. See [portability](../../../docs/PORTABILITY.md) in the repository for optional course toolchains.
