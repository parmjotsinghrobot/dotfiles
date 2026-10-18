#!/usr/bin/env python3
"""Apply shared UI fonts to GSettings; preview by default, save original values."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'org.gnome.desktop.interface'
KEYS = ('font-name', 'document-font-name', 'monospace-font-name')


def gsettings(*arguments):
    return subprocess.check_output(['gsettings', *arguments], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--restore', type=Path, help='restore an original-values JSON backup')
    args = parser.parse_args()
    if args.restore:
        data = json.loads(args.restore.read_text())
        if data.get('schema') != SCHEMA or set(data.get('original', {})) != set(KEYS):
            raise SystemExit('Invalid font backup')
        values = data['original']
    else:
        font = json.loads((ROOT / 'theme/palette.json').read_text())['fonts']['ui']
        # GVariant string syntax; the managed family has no shell interpretation.
        name = f"{font['family']} {font['size_pt']}"
        value = "'" + name.replace('\\', '\\\\').replace("'", "\\'") + "'"
        values = dict.fromkeys(KEYS, value)
    current = {key: gsettings('get', SCHEMA, key) for key in KEYS}
    changes = {key: value for key, value in values.items() if current[key] != value}
    for key, value in changes.items():
        print(f'{key}: {current[key]} -> {value}')
    if not changes:
        print('UI font settings already match.')
        return
    if not args.apply:
        print('Preview only; use --apply to write.')
        return
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
    directory = state / 'dotfiles/fonts'
    old_umask = os.umask(0o077)
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup = directory / (stamp + '-' + uuid.uuid4().hex[:8] + '.json')
        backup.write_text(json.dumps({'schema': SCHEMA, 'original': current}, indent=2) + '\n')
    finally:
        os.umask(old_umask)
    print(f'Original values: {backup}')
    for key, value in changes.items():
        subprocess.run(['gsettings', 'set', SCHEMA, key, value], check=True)
        if gsettings('get', SCHEMA, key) != value:
            raise SystemExit(f'Font setting did not apply: {key}')


if __name__ == '__main__':
    main()
