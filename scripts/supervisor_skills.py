#!/usr/bin/env python3
"""Offline, namespaced installation and portable access to Supervisor-Skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PREFIX = (REPO.parent.parent.parent if (REPO.parent / 'manifest.json').is_file()
                  else Path.home() / '.local/share/supervisor-skills')
PAYLOAD = ('skills', 'others', 'handbook', 'handbook-en', 'assets', 'scripts',
           'README.md', 'README.en.md', 'LICENSE', 'CHANGELOG.md',
           'CONTRIBUTING.md', 'llms.txt', 'requirements-lint.txt', 'INSTALL.md')
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', '.git', '.venv')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def skill_sources(source):
    return sorted(p for group in ('skills', 'others')
                  for p in (source / group).glob('*/SKILL.md'))


def installed_name(name):
    return name if name == 'supervisor' else 'supervisor-' + name


def namespace(text, names):
    # Only skill identifiers / relative links change; citations and external URLs stay intact.
    for old in sorted(names, key=len, reverse=True):
        new = installed_name(old)
        text = re.sub(r'(?m)^name: ' + re.escape(old) + r'\s*$', 'name: ' + new, text)
        text = text.replace('`' + old + '`', '`' + new + '`')
        text = text.replace('skill: ' + old, 'skill: ' + new)
        text = re.sub(r'\$' + re.escape(old) + r'(?![a-z0-9-])', '$' + new, text)
        text = text.replace('../' + old + '/SKILL.md', '../' + new + '/SKILL.md')
        text = text.replace('../../others/' + new + '/SKILL.md', '../' + new + '/SKILL.md')
        text = text.replace('../../others/' + old + '/SKILL.md', '../' + new + '/SKILL.md')
    return text


def build(source, destination):
    raw = destination / 'source'
    raw.mkdir(parents=True)
    for name in PAYLOAD:
        src = source / name
        if src.is_dir():
            shutil.copytree(src, raw / name, ignore=IGNORE)
        elif src.is_file():
            shutil.copy2(src, raw / name)
    entries = skill_sources(raw)
    names = [p.parent.name for p in entries]
    if 'supervisor' not in names or len(names) != len(set(names)):
        raise ValueError('Source must include supervisor and unique skill directory names')
    for entry in entries:
        name = installed_name(entry.parent.name)
        target = destination / 'skills' / name
        shutil.copytree(entry.parent, target, ignore=IGNORE)
        for p in target.rglob('*'):
            if p.suffix in ('.md', '.yaml'):
                value = namespace(p.read_text(encoding='utf-8'), names)
                if name == 'supervisor':
                    for resource in ('handbook/', 'handbook-en/', 'README.md'):
                        value = value.replace('../../' + resource, '../../source/' + resource)
                p.write_text(value, encoding='utf-8')
        if not (target / 'LICENSE').exists():
            shutil.copy2(raw / 'LICENSE', target / 'LICENSE')
    (destination / 'NOTICE.md').write_text(
        '# Supervisor-Skills local distribution\n\n'
        'Source: https://github.com/HKUSTDial/Supervisor-Skills\n'
        'Authors: Yuyu Luo / HKUST DIAL and contributors.\n'
        'License: CC BY-NC-SA 4.0; Draw.io reconstruction retains its MIT license.\n'
        'Local adaptations: supervisor router, CLI, namespaced skill identifiers and links.\n'
        'Original material is preserved under source/.\n', encoding='utf-8')
    return sorted(installed_name(n) for n in names)


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def managed_link(path, expected):
    return path.is_symlink() and os.readlink(path) == str(expected)


def preflight_link(path, target):
    if os.path.lexists(path) and not managed_link(path, target):
        raise ValueError(f'Refusing to replace existing path: {path}')


def install(args):
    prefix = args.prefix
    current = prefix / 'current'
    if os.path.lexists(current) and not current.is_symlink():
        raise ValueError(f'Refusing to replace existing path: {current}')
    previous = read_json(current / 'manifest.json') if (current / 'manifest.json').is_file() else None
    if current.is_symlink() and not previous:
        raise ValueError(f'Unrecognized installation: {current}')
    targets = [Path(t).expanduser().absolute() for t in args.target] if args.target else (
        [Path(t) for t in previous['targets']] if previous else [
            Path.home() / '.agents/skills', Path.home() / '.claude/skills'])
    if previous:
        targets.extend(Path(t) for t in previous['targets'])
    targets = sorted(set(targets))
    bin_dir = (args.bin_dir or (Path(previous['command']).parent if previous else
                              Path.home() / '.local/bin')).expanduser().absolute()
    executable = bin_dir / 'supervisor-skills'
    entrypoint = current / 'source/scripts/supervisor_skills.py'
    with tempfile.TemporaryDirectory(prefix='supervisor-build-') as temp:
        stage = Path(temp) / 'package'
        names = build(args.source.resolve(), stage)
        removed = set(previous['skills']) - set(names) if previous else set()
        if removed:
            raise ValueError('Source removed installed skills; preserving current installation: '
                             + ', '.join(sorted(removed)))
        for target in targets:
            for name in names:
                preflight_link(target / name, current / 'skills' / name)
        preflight_link(executable, entrypoint)
        hashes = inventory(stage)
        release_id = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
        print(f'{len(names)} skills; release {release_id}; prefix {prefix}')
        for target in targets:
            print(f'  Skill links: {target}')
        print(f'  Command: {executable}')
        if args.dry_run:
            print('Dry run: no installation paths modified.')
            return
        if (previous and previous['hashes'] == hashes
                and previous['targets'] == [str(t) for t in targets]
                and previous['command'] == str(executable)
                and not doctor(current, previous)):
            print('Already up to date; no new release created.')
            return
        # A fresh version is fully built before exposing it. Old versions remain available.
        releases = prefix / 'releases'
        releases.mkdir(parents=True, exist_ok=True)
        release = releases / (release_id + '-' + uuid.uuid4().hex[:8])
        shutil.copytree(stage, release)
        manifest = {'schema': 1, 'release': release.name, 'source': str(args.source.resolve()),
                    'targets': [str(t) for t in targets], 'skills': names, 'hashes': hashes,
                    'command': str(executable)}
        write_json(release / 'manifest.json', manifest)
        (release / 'source/scripts/supervisor_skills.py').chmod(0o755)
        created = []
        next_link = prefix / ('.current-' + uuid.uuid4().hex)
        try:
            for target in targets:
                target.mkdir(parents=True, exist_ok=True)
                for name in names:
                    path = target / name
                    if not os.path.lexists(path):
                        path.symlink_to(current / 'skills' / name, target_is_directory=True)
                        created.append(path)
            bin_dir.mkdir(parents=True, exist_ok=True)
            if not os.path.lexists(executable):
                executable.symlink_to(entrypoint)
                created.append(executable)
            next_link.symlink_to(release, target_is_directory=True)
            os.replace(next_link, current)
        except BaseException:
            for path in reversed(created):
                path.unlink()
            if next_link.is_symlink():
                next_link.unlink()
            raise
        print('Installed. Use: supervisor-skills doctor')


def package(prefix):
    root = prefix / 'current'
    if not (root / 'manifest.json').is_file():
        raise ValueError(f'No installation at {prefix}; run install first')
    return root, read_json(root / 'manifest.json')


def resolve_skill(root, manifest, name):
    if name not in manifest['skills']:
        name = installed_name(name)
    if name not in manifest['skills']:
        raise ValueError(f'Unknown skill: {name}; use list')
    return root / 'skills' / name


def doctor(root, manifest):
    errors = []
    for rel, checksum in manifest['hashes'].items():
        p = root / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != checksum:
            errors.append(f'Missing or changed: {p}')
    for target in manifest['targets']:
        for name in manifest['skills']:
            p = Path(target) / name
            if not managed_link(p, root / 'skills' / name) or not (p / 'SKILL.md').is_file():
                errors.append(f'Broken skill link: {p}')
    if not managed_link(Path(manifest['command']), root / 'source/scripts/supervisor_skills.py'):
        errors.append('Command link is missing or changed')
    for error in errors:
        print(error, file=sys.stderr)
    print(f'{len(manifest["skills"])} skills, {len(manifest["hashes"])} files, '
          f'{len(manifest["targets"])} discovery directories: ' + ('FAIL' if errors else 'OK'))
    drawio = shutil.which('drawio') or Path('/Applications/draw.io.app/Contents/MacOS/draw.io').exists()
    print('Optional Draw.io renderer: ' + ('available' if drawio else 'not installed; needed for PNG export'))
    return bool(errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, default=DEFAULT_PREFIX)
    sub = parser.add_subparsers(dest='action', required=True)
    command = sub.add_parser('install', help='Install / update from a local repository; no network')
    command.add_argument('--source', type=Path, default=REPO)
    command.add_argument('--target', action='append', default=[], help='Skill discovery directory; repeatable')
    command.add_argument('--bin-dir', type=Path)
    command.add_argument('--dry-run', action='store_true')
    sub.add_parser('list', help='List installed names and original names')
    sub.add_parser('doctor', help='Verify installed files and discovery links')
    sub.add_parser('handbook', help='Print paths to the complete bilingual handbook')
    for verb in ('show', 'path', 'export'):
        command = sub.add_parser(verb)
        command.add_argument('skill', nargs='?', default='supervisor')
        if verb == 'show':
            command.add_argument('--file', default='SKILL.md', help='Relative resource path in this skill')
    args = parser.parse_args()
    args.prefix = args.prefix.expanduser().absolute()
    if args.action == 'install':
        install(args)
        return 0
    root, manifest = package(args.prefix)
    if args.action == 'doctor':
        return int(doctor(root, manifest))
    if args.action == 'list':
        for name in manifest['skills']:
            print(name)
        return 0
    if args.action == 'handbook':
        for name in ('handbook', 'handbook-en'):
            print((root / 'source' / name).resolve())
        return 0
    skill = resolve_skill(root, manifest, args.skill)
    if args.action == 'path':
        print((skill / 'SKILL.md').resolve())
    elif args.action == 'show':
        path = (skill / args.file).resolve()
        if not path.is_relative_to(skill.resolve()):
            raise ValueError('--file must stay inside the skill directory')
        print(path.read_text(encoding='utf-8'))
    else:
        print('# Portable Supervisor-Skills context\n')
        print((root / 'NOTICE.md').read_text(encoding='utf-8'))
        print('Embedded references follow. Tool capabilities and binary assets are not included.\n')
        print(f'Skill location (local installation): {skill.resolve()}\n')
        for path in [skill / 'SKILL.md', *sorted((skill / 'references').rglob('*.md'))]:
            print(f'\n---\n\n## File: {path.relative_to(skill)}\n')
            print(path.read_text(encoding='utf-8'))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)
