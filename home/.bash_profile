# Login shells share the same portable environment as interactive Bash.
[[ ! -r "$HOME/.bashrc" ]] || . "$HOME/.bashrc"
