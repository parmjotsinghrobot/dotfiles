#!/bin/sh
# Preview by default. Pass --apply to write links and private recovery backups.
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$repo_dir/scripts/deploy.py" "$@"
