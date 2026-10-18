export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
[ ! -r "$XDG_CONFIG_HOME/shell/environment.sh" ] || . "$XDG_CONFIG_HOME/shell/environment.sh"
[[ $- == *i* ]] || return
command -v eza >/dev/null 2>&1 && alias ls='eza'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '
[[ ! -r "$XDG_CONFIG_HOME/shell/interactive.local.sh" ]] || . "$XDG_CONFIG_HOME/shell/interactive.local.sh"
