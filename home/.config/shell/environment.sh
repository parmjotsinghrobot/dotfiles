# POSIX shell syntax: shared by Bash and Zsh, including noninteractive shells.
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
# Login-manager sessions need not inherit systemd's environment.d values.
# qt6ct accepts this compatibility key too, while Qt5 needs qt5ct.
export QT_QPA_PLATFORMTHEME="${QT_QPA_PLATFORMTHEME:-qt5ct}"
# Preserve the existing keyring location, including signing keys.
export GNUPGHOME="${GNUPGHOME:-$HOME/.local/share/gnupg}"
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) PATH="$HOME/.local/bin:$PATH" ;;
esac
export PATH
# No manual parsing/eval of environment.d: its quoting/expansion belongs to systemd.
# Shell-only and engineering setup is opt-in, in a trusted local shell file.
[ ! -r "$XDG_CONFIG_HOME/shell/environment.local.sh" ] || . "$XDG_CONFIG_HOME/shell/environment.local.sh"
