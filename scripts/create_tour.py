#!/usr/bin/env python3
"""Copy the self-contained tour; optionally replace the initial panorama."""
import argparse
import json
import shutil
from pathlib import Path
from validate_tour import image_size, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--title', default='点亮洞窟')
    parser.add_argument('--panorama', type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / 'assets' / 'starter'
    target = args.output.expanduser().resolve()
    if target == source or source in target.parents:
        parser.error('输出目录不能位于模板内部')
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        parser.error('目标非空，拒绝覆盖: ' + str(target))
    if not args.title.strip():
        parser.error('标题不能为空')
    if args.panorama:
        try:
            width, height = image_size(args.panorama.expanduser())
            if width != height * 2:
                parser.error('全景须为 2:1；请检查投影后再提供，不要直接拉伸')
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
    shutil.copytree(source, target, dirs_exist_ok=True)
    config = json.loads((target / 'tour.json').read_text(encoding='utf-8'))
    config['title'] = args.title.strip()
    if args.panorama:
        panorama = args.panorama.expanduser().resolve()
        suffix = '.png' if panorama.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n' else '.jpg'
        relative = 'panoramas/user-main' + suffix
        shutil.copy2(panorama, target / relative)
        first = config['scenes'][config['firstScene']]
        first.update(panorama=relative, poster=relative)
        first['provenance'] = {'kind': 'user-supplied', 'statement': '用户提供素材；来源、许可和真实/虚构属性待填写。'}
    (target / 'tour.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = validate(target)
    print(json.dumps({'directory': str(target), **result}, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
