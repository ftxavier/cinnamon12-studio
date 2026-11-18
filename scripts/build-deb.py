#!/usr/bin/env python3
"""Build the passive, architecture-independent Debian package of Cinnamon12 Studio.

* Installs only files under /usr (themes, icons, wallpapers, xlets, CLI, docs).
* NO maintainer scripts: nothing touches any user's GSettings on install/remove.
  Each user activates with `cinnamon12 apply light|dark` and reverts with
  `cinnamon12 restore` (run it before `apt remove` to clear the theme names).
* Removing the package removes every file it installed; Cinnamon/GTK fall back to
  their default themes on the next reload/login if the theme was still active.

Usage: python3 scripts/build-deb.py   ->  dist/cinnamon12-studio_<ver>_all.deb
"""
import gzip, hashlib, os, shutil, subprocess, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
PKG = 'cinnamon12-studio'
UPSTREAM = '0.3.0'
REVISION = '1'
VERSION = f'{UPSTREAM}-{REVISION}'
MAINTAINER = 'Cinnamon12 Studio Maintainer <maintainer@example.invalid>'  # placeholder
SHARE = Path('usr/share')
EXCLUDE_SUFFIXES = ('-original.png',)          # wallpaper masters stay in the repo only
EXCLUDE_NAMES = ('.cinnamon12-studio-owned', '__pycache__')


def copy_tree(src: Path, dst: Path):
    for path in sorted(src.rglob('*')):
        rel = path.relative_to(src)
        if any(part in EXCLUDE_NAMES for part in rel.parts):
            continue
        if path.is_file() and path.name.endswith(EXCLUDE_SUFFIXES):
            continue
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def gz(src_text: str, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=9, mtime=0) as f:
            f.write(src_text.encode())


def main():
    DIST.mkdir(exist_ok=True)
    stamp = time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())
    with tempfile.TemporaryDirectory(prefix='c12-deb-') as t:
        root = Path(t) / PKG
        for name in ('Cinnamon12-Light', 'Cinnamon12-Dark'):
            copy_tree(ROOT / 'themes' / name, root / SHARE / 'themes' / name)
        copy_tree(ROOT / 'icons' / 'Cinnamon12-Icons', root / SHARE / 'icons' / 'Cinnamon12-Icons')
        copy_tree(ROOT / 'assets' / 'wallpapers', root / SHARE / 'backgrounds' / PKG)
        for kind in ('applets', 'desklets'):
            for p in sorted((ROOT / kind).iterdir()):
                copy_tree(p, root / SHARE / 'cinnamon' / kind / p.name)
        # Cinnamon Settings > Backgrounds lists /usr/share/gnome-background-properties/*.xml
        walls = sorted((ROOT / 'assets' / 'wallpapers').glob('*-2560x1440.jpg'))
        xml = ['<?xml version="1.0"?>', '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">', '<wallpapers>']
        for w in walls:
            title = 'Cinnamon12 ' + w.stem.split('-')[1].capitalize()
            xml += ['  <wallpaper deleted="false">', f'    <name>{title}</name>',
                    f'    <filename>/usr/share/backgrounds/{PKG}/{w.name}</filename>',
                    '    <options>zoom</options>', '  </wallpaper>']
        xml.append('</wallpapers>')
        props = root / SHARE / 'gnome-background-properties' / 'cinnamon12.xml'  # shown as 'Cinnamon12'
        props.parent.mkdir(parents=True, exist_ok=True)
        props.write_text('\n'.join(xml) + '\n')
        # CLI (apply / restore / panel / doctor) for every user, no root needed to run it.
        cli_home = root / SHARE / PKG / 'scripts'
        cli_home.mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts' / 'manage.py', cli_home / 'manage.py')
        (root / 'usr' / 'bin').mkdir(parents=True)
        (root / 'usr' / 'bin' / 'cinnamon12').write_text(
            '#!/bin/sh\nexec /usr/bin/python3 /usr/share/cinnamon12-studio/scripts/manage.py "$@"\n')
        # Documentation
        doc = root / SHARE / 'doc' / PKG
        doc.mkdir(parents=True)
        for n in ('README.md', 'docs/COMPATIBILITY.md'):
            shutil.copyfile(ROOT / n, doc / Path(n).name)
        gz(f'''{PKG} ({VERSION}) noble; urgency=medium

  * Shell theme imports the installed Cinnamon stylesheet.
  * GTK3 built on Adwaita; also styles Muffin server-side title bars.
  * Dedicated GTK4 stylesheet; reversible 48 px centered panel profile.
  * CLI installed as /usr/bin/cinnamon12; no maintainer scripts.

 -- {MAINTAINER}  {stamp}
''', doc / 'changelog.Debian.gz')
        (doc / 'copyright').write_text(f'''Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Cinnamon12 Studio
Source: local project

Files: *
Copyright: 2026 Cinnamon12 Studio contributors
License: Cinnamon12-Studio
 {(ROOT / 'LICENSE.md').read_text().strip().replace(chr(10) + chr(10), chr(10) + ' .' + chr(10)).replace(chr(10), chr(10) + ' ')}
''')
        # Permissions
        for p in root.rglob('*'):
            os.chmod(p, 0o755 if p.is_dir() else 0o644)
        os.chmod(root / 'usr' / 'bin' / 'cinnamon12', 0o755)
        os.chmod(cli_home / 'manage.py', 0o755)
        # control + md5sums
        size_kb = sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) // 1024
        md5 = []
        for p in sorted(root.rglob('*')):
            if p.is_file():
                md5.append(f'{hashlib.md5(p.read_bytes()).hexdigest()}  {p.relative_to(root)}')
        deb = root / 'DEBIAN'
        deb.mkdir()
        (deb / 'md5sums').write_text('\n'.join(md5) + '\n')
        (deb / 'control').write_text(f'''Package: {PKG}
Version: {VERSION}
Section: x11
Priority: optional
Architecture: all
Maintainer: {MAINTAINER}
Installed-Size: {size_kb}
Depends: cinnamon, python3
Recommends: yaru-theme-icon | adwaita-icon-theme
Description: Cinnamon12 light and dark desktop theme for Cinnamon
 Original blue light/dark theme for the Cinnamon desktop: shell theme,
 GTK 3/4 themes (also used for window title bars), icon theme, wallpapers
 and optional applets/desklets.
 .
 Installing the package does not change any user's appearance. Each user
 activates it with "cinnamon12 apply light" (or dark) and reverts with
 "cinnamon12 restore"; "cinnamon12 panel apply|restore" manages an optional
 centered 48 px panel layout with backup.
''')
        os.chmod(deb / 'md5sums', 0o644)
        os.chmod(deb / 'control', 0o644)
        out = DIST / f'{PKG}_{VERSION}_all.deb'
        subprocess.run(['dpkg-deb', '--build', '--root-owner-group', '-Zxz', str(root), str(out)], check=True)
    print('Criado:', out, f'({out.stat().st_size // 1024} KiB)')


if __name__ == '__main__':
    main()
