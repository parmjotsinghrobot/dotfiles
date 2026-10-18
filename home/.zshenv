# Shared shell paths; desktop environment.d is loaded by the login session.
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
[ ! -r "$XDG_CONFIG_HOME/shell/environment.sh" ] || . "$XDG_CONFIG_HOME/shell/environment.sh"
export ZDOTDIR="$XDG_CONFIG_HOME/zsh"
