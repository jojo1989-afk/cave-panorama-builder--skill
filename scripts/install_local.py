#!/usr/bin/env python3
"""Install this authored skill without overwriting other files."""
import argparse
import hashlib
import os
import shutil
from pathlib import Path


def manifest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, help='skills 根目录；默认 $CODEX_HOME/skills 或 ~/.codex/skills')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    base = args.dest or Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
    target = base.expanduser().resolve() / 'cave-panorama-builder'
    if target.exists() or target.is_symlink():
        parser.error('同名目录已存在，拒绝覆盖: ' + str(target))
    if target == source or source in target.parents:
        parser.error('不能安装到源 Skill 内部')
    if any(p.is_symlink() for p in source.rglob('*')):
        parser.error('源 Skill 含符号链接，请先审查并改为普通文件')
    if args.dry_run:
        print('安装目标: ' + str(target))
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
    if manifest(source) != manifest(target):
        raise RuntimeError('安装后文件校验不一致，请检查目标目录')
    print('已安装并校验: ' + str(target))
    print('下一轮对话可使用 $cave-panorama-builder。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
