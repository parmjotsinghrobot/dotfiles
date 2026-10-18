#!/usr/bin/env python3
"""Import Tofi app-name usage counts into Fuzzel desktop-ID history."""
import argparse
import configparser
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def desktop_names(roots):
    names, seen = {}, set()
    for root in roots:
        for path in sorted((root / 'applications').rglob('*.desktop')):
            desktop_id = str(path.relative_to(root / 'applications')).replace('/', '-')
            if desktop_id in seen:
                continue
            seen.add(desktop_id)
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            parser.optionxform = str
            try:
                parser.read_string(path.read_text())
                entry = parser['Desktop Entry']
            except (OSError, UnicodeError, configparser.Error, KeyError):
                continue
            if entry.get('Type') != 'Application' or any(
                    entry.get(key, '').lower() == 'true' for key in ('Hidden', 'NoDisplay')):
                continue
            if entry.get('TryExec') and not shutil.which(entry['TryExec']):
                continue
            # Tofi saved display names, including localized names. Never guess
            # between multiple installed apps with the same display name.
            for key, value in entry.items():
                if key == 'Name' or key.startswith('Name['):
                    names.setdefault(value.strip(), set()).add(desktop_id)
    return names


def tofi_counts(text):
    counts = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        count, name = line.split(' ', 1)
        number = int(count)
        if number < 0 or not name.strip():
            raise ValueError('Invalid Tofi history entry')
        counts[name.strip()] = counts.get(name.strip(), 0) + number
    return counts


def fuzzel_counts(text):
    counts = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        desktop_id, count = line.rsplit('|', 1)
        number = int(count)
        if number < 0 or not desktop_id:
            raise ValueError('Invalid Fuzzel history entry')
        counts[desktop_id] = counts.get(desktop_id, 0) + number
    return counts


def plan(source, destination, names, imported):
    mapped, unmatched, ambiguous = {}, {}, {}
    for name, count in source.items():
        candidates = names.get(name, set())
        if len(candidates) == 1:
            desktop_id = next(iter(candidates))
            mapped[desktop_id] = mapped.get(desktop_id, 0) + count
        elif candidates:
            ambiguous[name] = sorted(candidates)
        else:
            unmatched[name] = count
    merged = dict(destination)
    new_imported = dict(imported)
    additions = {}
    for desktop_id, count in mapped.items():
        previous = imported.get(desktop_id, 0)
        delta = max(0, count - previous)
        new_imported[desktop_id] = max(previous, count)
        if delta:
            merged[desktop_id] = merged.get(desktop_id, 0) + delta
            additions[desktop_id] = delta
    return merged, new_imported, additions, unmatched, ambiguous


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            output.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    home = Path.home()
    state = Path(os.environ.get('XDG_STATE_HOME', str(home / '.local/state')))
    cache = Path(os.environ.get('XDG_CACHE_HOME', str(home / '.cache')))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--source', type=Path, default=state / 'tofi-drun-history')
    parser.add_argument('--destination', type=Path, default=cache / 'fuzzel')
    args = parser.parse_args()
    roots = [Path(os.environ.get('XDG_DATA_HOME', str(home / '.local/share')))]
    roots += [Path(p) for p in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if p]
    directory = state / 'dotfiles/history-import'
    ledger = directory / 'tofi-fuzzel.json'
    pending = directory / 'pending.json'
    if pending.exists():
        raise SystemExit('An interrupted import needs review: ' + str(pending))
    data = json.loads(ledger.read_text()) if ledger.exists() else {}
    if data and (data.get('source') != str(args.source.resolve()) or
                 data.get('destination') != str(args.destination.resolve())):
        raise SystemExit('Import ledger belongs to different history paths; no changes made')
    source = tofi_counts(args.source.read_text())
    original = args.destination.read_text() if args.destination.exists() else ''
    merged, imported, additions, unmatched, ambiguous = plan(
        source, fuzzel_counts(original), desktop_names(roots), data.get('imported', {}))
    print(f'{len(additions)} apps receive {sum(additions.values())} imported launches.')
    print(f'{len(unmatched)} unmatched names; {len(ambiguous)} ambiguous names left unchanged.')
    for desktop_id, count in sorted(additions.items(), key=lambda item: -item[1])[:10]:
        print(f'  +{count} {desktop_id}')
    if not args.apply:
        print('Preview only; use --apply to merge. Source history is never modified.')
        return
    if not additions:
        print('No new history to import; no files written.')
        return
    if subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'fuzzel'],
                      stdout=subprocess.DEVNULL).returncode == 0:
        raise SystemExit('Close the active Fuzzel menu before importing history')
    old_umask = os.umask(0o077)
    try:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        backup = directory / stamp
        backup.mkdir(parents=True, mode=0o700)
        (backup / 'fuzzel-before').write_text(original)
        (backup / 'ledger-before.json').write_text(json.dumps(data, indent=2) + '\n')
        report = {'source': str(args.source.resolve()), 'destination': str(args.destination.resolve()),
                  'unmatched': unmatched, 'ambiguous': ambiguous, 'additions': additions}
        (backup / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        next_ledger = {'source': str(args.source.resolve()),
                       'destination': str(args.destination.resolve()), 'imported': imported}
        # A pending transaction makes an interrupted import explicit; never
        # silently apply the same additions twice on the next invocation.
        atomic_write(pending, json.dumps({'backup': str(backup), 'next_ledger': next_ledger}) + '\n')
        atomic_write(args.destination, ''.join(f'{name}|{count}\n' for name, count in
                     sorted(merged.items(), key=lambda item: (-item[1], item[0]))))
        atomic_write(ledger, json.dumps(next_ledger, indent=2) + '\n')
        pending.unlink()
        print('Merged history. Backup and mapping report: ' + str(backup))
    finally:
        os.umask(old_umask)


if __name__ == '__main__':
    main()
