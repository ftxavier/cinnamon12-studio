#!/usr/bin/env python3
"""Cinnamon12 Search - file name index of the user's home folder.

Writes one line per file or folder: <normalized name> TAB <f|d> TAB <absolute path>
(normalized = lower case without accents, so the applet can match with grep -P).
Runs as a separate low-priority process so the Cinnamon shell never walks the disk.
Skips hidden entries and heavy dependency/cache folders; never follows symlinks.

usage: indexer.py OUTPUT [MAX_ENTRIES] [EXCLUDED]
EXCLUDED: comma-separated folders relative to the home folder (e.g. "go,snap").
"""
import os
import sys
import unicodedata

SKIP_DIRS = {'node_modules', '__pycache__', 'vendor', 'target', 'site-packages',
             'venv', 'Trash', 'lost+found'}


def norm(s):
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def main():
    out = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 400000
    home = os.path.expanduser('~')
    excluded = sys.argv[3] if len(sys.argv) > 3 else ''
    skip_abs = {os.path.normpath(os.path.join(home, p.strip().strip('/')))
                for p in excluded.split(',') if p.strip().strip('/')}
    try:
        os.nice(10)
    except OSError:
        pass
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + '.tmp'
    count = 0
    stack = [home]
    with open(tmp, 'w', encoding='utf-8', errors='replace') as f:
        while stack and count < limit:
            d = stack.pop()
            try:
                it = os.scandir(d)
            except OSError:
                continue
            with it:
                for e in it:
                    name = e.name
                    if name.startswith('.') or '\n' in name or '\t' in name:
                        continue
                    try:
                        is_dir = e.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if is_dir and (name in SKIP_DIRS or e.path in skip_abs):
                        continue
                    f.write('%s\t%s\t%s\n' % (norm(name), 'd' if is_dir else 'f', e.path))
                    count += 1
                    if is_dir:
                        stack.append(e.path)
    os.replace(tmp, out)


if __name__ == '__main__':
    main()
