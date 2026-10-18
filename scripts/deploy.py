#!/usr/bin/env python3
"""Deploy explicit files only; preview by default, with guarded rollback."""
import argparse
import datetime
import json
import os
from pathlib import Path, PurePosixPath
import sys
import uuid

REPO = Path(__file__).resolve().parents[1]
STATE = PurePosixPath('.local/state/dotfiles-deploy')
SYSTEM_ASSETS = (Path('/usr/share/themes'), Path('/usr/share/icons'))


def exists(path):
    return os.path.lexists(path)


def safe_paths(raw):
    if not isinstance(raw, list):
        raise ValueError('paths must be a list')
    result = []
    for item in raw:
        if not isinstance(item, str) or not item or '\\' in item:
            raise ValueError(f'invalid manifest path: {item!r}')
        path = PurePosixPath(item)
        if path.is_absolute() or any(p in ('', '.', '..') for p in item.split('/')):
            raise ValueError(f'path must be a normal relative path: {item!r}')
        if path == STATE or STATE in path.parents or path in STATE.parents:
            raise ValueError(f'path overlaps recovery state: {item}')
        if any(path == p or path in p.parents or p in path.parents for p in result):
            raise ValueError(f'duplicate or overlapping path: {item}')
        result.append(path)
    return result


def check_parents(target, relative):
    """Never follow a destination-parent symlink or overwrite a real directory."""
    if target.is_symlink() or (exists(target) and not target.is_dir()):
        raise ValueError(f'target home must be a real directory: {target}')
    current = target
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink() or (exists(current) and not current.is_dir()):
            raise ValueError(f'unsafe destination parent: {current}')


def check_source(root, relative):
    source = root / relative
    try:
        resolved = source.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(f'missing or dangling source: {source}: {error}') from error
    def allowed(path):
        return path.is_relative_to(root.resolve()) or any(path.is_relative_to(p) for p in SYSTEM_ASSETS)
    if not allowed(resolved):
        raise ValueError(f'source escapes home subtree: {source}')
    if source.is_dir() and not source.is_symlink():
        raise ValueError(f'manifest must name individual files or symlinks: {source}')
    if not (resolved.is_file() or resolved.is_dir()):
        raise ValueError(f'unsupported source type: {source}')
    # Directory symlink assets can contain further dependencies. Do not deploy a
    # theme whose nested symlink will escape the repository or be dangling.
    if resolved.is_dir():
        for directory, dirs, files in os.walk(resolved, followlinks=False):
            for name in dirs + files:
                dependency = Path(directory) / name
                if dependency.is_symlink():
                    try:
                        linked = dependency.resolve(strict=True)
                    except (OSError, RuntimeError) as error:
                        raise ValueError(f'dangling asset dependency: {dependency}') from error
                    if not allowed(linked):
                        raise ValueError(f'asset dependency escapes home subtree: {dependency}')
    return source


def managed_link(destination, source):
    return destination.is_symlink() and os.readlink(destination) == str(source)


def save_journal(directory, data):
    temporary = directory / 'journal.json.tmp'
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    os.chmod(temporary, 0o600)
    temporary.replace(directory / 'journal.json')


def deploy(repo, target, apply=False):
    if target.resolve().is_relative_to(repo.resolve()):
        raise ValueError('target home must not be inside the source checkout')
    manifest = json.loads((repo / 'manifest.json').read_text())
    if not isinstance(manifest, dict) or manifest.get('version') != 1:
        raise ValueError('manifest must be an object with version 1')
    paths = safe_paths(manifest.get('paths'))
    changes = []
    for relative in paths:
        check_parents(target, relative)
        source = check_source(repo / 'home', relative)
        destination = target / relative
        if destination.is_dir() and not destination.is_symlink():
            raise ValueError(f'refusing to replace a real directory: {destination}')
        if managed_link(destination, source):
            print(f'KEEP    {relative}')
            continue
        backup = exists(destination)
        print(f'{"BACKUP+LINK" if backup else "LINK"} {relative}')
        changes.append({'path': str(relative), 'source': str(source), 'backup': backup})
    check_parents(target, STATE / 'run')
    if not apply:
        print(f'Dry run: {len(changes)} change(s); no files written. Use --apply to deploy.')
        return None
    if not changes:
        print('Already deployed; no files written.')
        return None
    old_umask = os.umask(0o077)
    try:
        run = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        directory = target / STATE / run
        directory.mkdir(parents=True, mode=0o700)
        data = {'version': 1, 'target_home': str(target), 'entries': changes}
        save_journal(directory, data)
        for entry in changes:
            relative = PurePosixPath(entry['path'])
            check_parents(target, relative)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if entry['backup']:
                saved = directory / 'originals' / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                destination.replace(saved)
            destination.symlink_to(entry['source'])
        print(f'Recovery journal: {directory}')
        print(f'Rollback preview: ./install.sh --target-home {str(target)!r} --rollback {run}')
        return directory
    finally:
        os.umask(old_umask)


def rollback(target, run, apply=False):
    if not run or '/' in run or '\\' in run or run in ('.', '..'):
        raise ValueError('rollback expects the recovery run ID, not a path')
    check_parents(target, STATE / run / 'journal.json')
    directory = target / STATE / run
    journal = directory / 'journal.json'
    if journal.is_symlink():
        raise ValueError('recovery journal must not be a symlink')
    data = json.loads(journal.read_text())
    if data.get('version') != 1 or data.get('target_home') != str(target):
        raise ValueError('recovery journal version or target home mismatch')
    entries = data.get('entries')
    if not isinstance(entries, list):
        raise ValueError('invalid recovery entries')
    safe_paths([entry['path'] for entry in entries])
    actions = []
    for entry in reversed(entries):
        relative = PurePosixPath(entry['path'])
        check_parents(target, relative)
        check_parents(directory, PurePosixPath('originals') / relative)
        destination = target / relative
        saved = directory / 'originals' / relative
        owned = managed_link(destination, entry['source'])
        if exists(destination) and not owned:
            if entry.get('restored'):
                print(f'KEEP restored {relative}')
                continue
            # An interrupted deployment may not yet have touched this entry.
            if entry['backup'] and not exists(saved):
                print(f'KEEP unchanged {relative}')
                continue
            raise ValueError(f'rollback conflict; destination changed: {destination}')
        if entry['backup'] and not exists(saved):
            if owned:
                raise ValueError(f'missing original backup: {saved}')
            continue
        print(f'{"RESTORE" if entry["backup"] else "UNLINK"} {relative}')
        actions.append((entry, destination, saved, owned))
    if not apply:
        print(f'Dry run: {len(actions)} rollback action(s); use --apply to restore.')
        return
    for entry, destination, saved, owned in actions:
        check_parents(target, PurePosixPath(entry['path']))
        if owned:
            destination.unlink()
        if entry['backup']:
            saved.replace(destination)
        entry['restored'] = True
        save_journal(directory, data)
    print('Rollback complete; recovery journal retained.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='write changes (default: dry run)')
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--rollback', metavar='RUN_ID', help='preview or restore one recovery run')
    args = parser.parse_args()
    target = args.target_home.expanduser().absolute()
    try:
        if args.rollback:
            rollback(target, args.rollback, args.apply)
        else:
            deploy(REPO, target, args.apply)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
