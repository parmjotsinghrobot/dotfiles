#!/usr/bin/env python3
"""Read-only desktop dependency checks. No network, installs, or session actions."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'sway': 'swayfx (the FX fork is required)', 'swaymsg': 'swayfx',
    'swaybar': 'swayfx', 'swaybg': 'swaybg', 'swaylock': 'swaylock-effects-git',
    'swayidle': 'swayidle', 'kitty': 'kitty', 'zen-browser': 'zen-browser-bin',
    'tofi': 'tofi', 'tofi-drun': 'tofi', 'dunst': 'dunst', 'udiskie': 'udiskie',
    'nm-applet': 'network-manager-applet', 'cliphist': 'cliphist',
    'wl-copy': 'wl-clipboard', 'wl-paste': 'wl-clipboard', 'autotiling': 'autotiling',
    'micro': 'micro', 'grim': 'grim', 'slurp': 'slurp', 'brightnessctl': 'brightnessctl',
    'wpctl': 'wireplumber', 'playerctl': 'playerctl',
    'antidot': 'antidot-bin', 'zsh': 'zsh', 'git': 'git', 'curl': 'curl',
    'fc-match': 'fontconfig', 'xdg-user-dir': 'xdg-user-dirs', 'gpgconf': 'gnupg',
}
OPTIONAL = {'fuzzel': 'fuzzel; optional launcher/emoji trial',
            'checkupdates': 'pacman-contrib; optional update greeting',
            'wtype': 'wtype; emoji typing on Wayland',
            'xclip': 'xclip; emoji clipboard on X11',
            'xdotool': 'xdotool; emoji typing on X11',
            'btop': 'btop', 'cava': 'cava', 'peaclock': 'peaclock'}


def run(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=10,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(args, 1, '', str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(),
                        help='deployment target to inspect (default: current home)')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    missing = 0

    def check(ok, label, detail='', required=True):
        nonlocal missing
        if not ok and required:
            missing += 1
        print(f"{'OK' if ok else 'MISSING' if required else 'OPTIONAL'} {label}"
              + (f': {detail}' if detail else ''))

    print(f'Source: {ROOT}\nTarget home: {home}\nCommands use the current process PATH.')
    for name, package in REQUIRED.items():
        check(bool(shutil.which(name)), f'command {name}', package)
    for name, package in OPTIONAL.items():
        check(bool(shutil.which(name)), f'command {name}', package, False)
    # Inspect package ownership: a stock sway/swaylock executable is insufficient.
    if shutil.which('pacman'):
        for package in ('swayfx', 'swaylock-effects-git'):
            result = run('pacman', '-Q', package)
            check(result.returncode == 0, f'variant {package}', result.stdout.strip())
    else:
        print('REVIEW FX/effects variants manually; pacman unavailable.')
    for label, code in (
        ('PyGObject / Gio / GLib / Playerctl 2.0',
         "import gi; gi.require_version('Playerctl', '2.0'); from gi.repository import Gio, GLib, Playerctl"),
        ('i3ipc', 'import i3ipc'),
    ):
        result = run(sys.executable, '-B', '-c', code)
        check(result.returncode == 0, f'Python {label}', result.stderr.strip())
    for family in ('Iosevka Curly', 'Noto Sans', 'Noto Color Emoji',
                   'Font Awesome 5 Free', 'Font Awesome 5 Brands', 'Symbols Nerd Font'):
        result = run('fc-match', '-f', '%{family}', family)
        matched = result.stdout.strip()
        check(result.returncode == 0 and family.casefold() in matched.casefold(),
              f'font {family}', matched or result.stderr.strip())
    if shutil.which('qt5ct'):
        check(Path('/usr/lib/qt/plugins/styles/libkvantum.so').is_file(),
              'Qt5 Kvantum style plugin', 'kvantum-qt5')
    for asset in (
        '/usr/share/themes/catppuccin-mocha-pink-standard+default/gtk-3.0/gtk.css',
        '/usr/share/themes/catppuccin-mocha-pink-standard+default/gtk-4.0/gtk.css',
        '/usr/share/icons/catppuccin-mocha-pink-cursors/index.theme',
        '/usr/share/icons/Papirus-Dark/index.theme',
        '/usr/share/Kvantum/catppuccin-mocha-pink/catppuccin-mocha-pink.kvconfig',
    ):
        check(Path(asset).exists(), 'theme asset', asset)
    for relative in (
        '.zshenv', '.config/zsh/zshrc', '.config/kitty/current-theme.conf',
        '.config/sway/swaybar/status.py', '.local/bin/sticky-notes-daemon.py',
        '.config/tofi/scripts/emoji-picker.sh',
        '.config/zsh/themes/passion/passion.zsh-theme',
        '.config/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh',
        '.config/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh',
        '.config/zsh/plugins/omz-lib/git.zsh',
    ):
        check((home / relative).is_file(), 'deployed file', str(home / relative))
    # Read active output lines only; do not expand shell substitutions or run configs.
    config = ROOT / 'home/.config/sway'
    for path in sorted(config.rglob('*.conf')) if config.exists() else ():
        for line in path.read_text().splitlines():
            match = re.match(r'^\s*output\s+.*?\s+bg\s+(\S+)', line)
            if match and not match[1].startswith(('$', '#')):
                asset = Path(match[1].strip('"\'').replace('~/', str(home) + '/'))
                check(asset.is_file(), 'wallpaper', str(asset))
    picture_result = run('xdg-user-dir', 'PICTURES') if home == Path.home().resolve() else None
    pictures = Path(picture_result.stdout.strip()) if picture_result and picture_result.returncode == 0 and picture_result.stdout.strip() else home / 'Pictures'
    check((pictures / 'Screenshots').is_dir(), 'screenshot destination', str(pictures / 'Screenshots') + '; created by screenshot binding when used', False)
    data = Path(os.environ.get('XDG_DATA_HOME', str(home / '.local/share'))) if home == Path.home().resolve() else home / '.local/share'
    emoji = Path(os.environ.get('BEMOJI_DB_LOCATION', str(data / 'bemoji')))
    check(any(p.is_file() and p.stat().st_size for p in emoji.glob('*.txt')),
          'emoji database', str(emoji) + '; picker fetches on first use unless supplied locally', False)
    print(f'\n{missing} required check(s) missing. No files or settings changed.')
    print('Session services, visual appearance, audio routing and suspend require a real login test.')
    return bool(missing)


if __name__ == '__main__':
    sys.exit(main())
