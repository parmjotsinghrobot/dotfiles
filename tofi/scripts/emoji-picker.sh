#!/bin/sh

# ripped from https://github.com/Speyll/dotfiles/blob/main/.local/bin/bemoji
# thanks <3

# Version and configuration
VERSION="0.4.1"
DB_DIR="${BEMOJI_DB_LOCATION:-${XDG_DATA_HOME:-$HOME/.local/share}/bemoji}"
# Default settings
ECHO_NEWLINE=${BEMOJI_ECHO_NEWLINE:-false}
DEFAULT_CMD=${BEMOJI_DEFAULT_CMD:-}

# Command lists
CMDS=""

# Picker command order
PICKERS="tofi fuzzel bemenu wofi rofi dmenu ilia"

usage() {
    cat >&2 <<EOF
Usage: ${0##*/} [OPTIONS]
Emoji picker with clipboard and typing support.

Options:
  -t, --type          Type selected emoji
  -c, --clip          Copy to clipboard (default)
  -e, --echo          Output emoji only
  -n, --newline       Add newline after output
  -f FILE             Custom emoji file/URL
  -D TYPES            Download lists (all,emoji,math,nerd)
  -v, --version       Show version
  -h, --help          Show this help
EOF
    exit $1
}

version() {
    echo "bemoji v$VERSION"
    echo "Database: $DB_DIR"
    exit 0
}

msg() { echo "$@" >&2; }

prepare_db() {
    [ -d "$DB_DIR" ] || mkdir -p "$DB_DIR"

    if [ -n "$BEMOJI_DOWNLOAD_LIST" ]; then
        if echo "$BEMOJI_DOWNLOAD_LIST" | grep -q 'none'; then return; fi

        for type in $(echo "$BEMOJI_DOWNLOAD_LIST" | tr ',' ' '); do
            case $type in
                all) download_emoji; download_math; download_nerd ;;
                emoji) download_emoji ;;
                math) download_math ;;
                nerd) download_nerd ;;
            esac
        done
    elif [ -z "$(ls -A "$DB_DIR" 2>/dev/null)" ]; then
        download_emoji
    fi
}

download_emoji() {
    curl -sSL "https://unicode.org/Public/emoji/latest/emoji-test.txt" |
    sed -nE 's/^.*; fully-qualified.*# (.[^ ]*) .*$/\1 \2/p' > "$DB_DIR/emojis.txt"
}

download_math() {
    curl -sSL "https://unicode.org/Public/math/latest/MathClassEx-15.txt" |
    awk -F';' '/^[^#]/{print $3 " " $7}' > "$DB_DIR/math.txt"
}

download_nerd() {
    curl -sSL "https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/css/nerd-fonts-generated.css" |
    sed -nE '/\.nf-/ {N;s/\.nf-(.*):before.*content: "\\?(.*)";/\2 \1/p}' > "$DB_DIR/nerd.txt"
}


select_emoji() {
    [ -n "$BEMOJI_CUSTOM_LIST" ] && {
        if [ -f "$BEMOJI_CUSTOM_LIST" ]; then
            emoji_data="$(cat "$BEMOJI_CUSTOM_LIST")"
        else
            emoji_data="$(curl -sSL "$BEMOJI_CUSTOM_LIST")"
        fi
    } || emoji_data="$emoji_data$(cat "$DB_DIR"/*.txt)"

    printf "%s" "$emoji_data" | sort -u | picker_command
}

picker_command() {
    for cmd in $PICKERS; do
        if command -v "$cmd" >/dev/null; then
            case $cmd in
                bemenu) exec bemenu -p 🔍 -i -l 20 ;;
                wofi) exec wofi -p 🔍 -i --show dmenu ;;
                rofi) exec rofi -p 🔍 -i -dmenu ;;
                dmenu) exec dmenu -p 🔍 -i -l 20 ;;
                ilia) exec ilia -n -p textlist -l Emoji ;;
                fuzzel) exec fuzzel -d -f 'monospace:size=14' -w 30 -l 10 -a bottom-right --x-margin 8 --y-margin 8 ;;
                tofi) exec tofi
            esac
        fi
    done
    msg "No suitable picker found" && exit 1
}

clipboard() {
    if [ -n "$WAYLAND_DISPLAY" ]; then
        wl-copy
    elif [ -n "$DISPLAY" ]; then
        xclip -selection clipboard
    else
        msg "No clipboard support" && exit 1
    fi
}

typer() {
    input=$(cat)
    [ -n "$WAYLAND_DISPLAY" ] && wtype -s 30 "$input" ||
    xdotool type --delay 30 "$input"
}

handle_selection() {
    selection=$(echo "$1" | awk '{print $1}')

    for cmd in $CMDS; do
        case $cmd in
            clip) printf "%s" "$selection" | clipboard ;;
            type) printf "%s" "$selection" | typer ;;
            echo) $ECHO_NEWLINE && echo "$selection" || printf "%s" "$selection" ;;
        esac
    done

    [ -z "$CMDS" ] && printf "%s" "$selection" | clipboard
}

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        -t|--type) CMDS="$CMDS type" ;;
        -c|--clip) CMDS="$CMDS clip" ;;
        -e|--echo) CMDS="$CMDS echo" ;;
        -n|--newline) ECHO_NEWLINE=true ;;
        -f|--file) BEMOJI_CUSTOM_LIST=$2; shift ;;
        -D) BEMOJI_DOWNLOAD_LIST=$2; shift ;;
        -v|--version) version ;;
        -h|--help) usage 0 ;;
        *) msg "Invalid option: $1"; usage 1 ;;
    esac
    shift
done

# Main flow
prepare_db
selection=$(select_emoji) || exit $?
[ -z "$selection" ] && exit 0

handle_selection "$selection"
