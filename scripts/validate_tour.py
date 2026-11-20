#!/usr/bin/env python3
"""Validate local tour data and resources; does not certify projection quality."""
import argparse
import json
import math
import re
import struct
import sys
import zipfile
from pathlib import Path


def image_size(path):
    with path.open('rb') as f:
        data = f.read(24)
        if data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
            return struct.unpack('>II', data[16:24])
        if data[:2] != b'\xff\xd8':
            raise ValueError('只接受 PNG 或 JPEG 图片')
        f.seek(2)
        while True:
            byte = f.read(1)
            if not byte:
                break
            if byte != b'\xff':
                continue
            marker = f.read(1)
            while marker == b'\xff':
                marker = f.read(1)
            if not marker or marker in (b'\xd9', b'\xda'):
                break
            if marker == b'\x00' or marker[0] in range(0xD0, 0xD8):
                continue
            length_bytes = f.read(2)
            if len(length_bytes) != 2:
                break
            length = struct.unpack('>H', length_bytes)[0]
            if length < 2:
                break
            if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                body = f.read(5)
                if len(body) == 5:
                    height, width = struct.unpack('>HH', body[1:])
                    return width, height
                break
            f.seek(length - 2, 1)
    raise ValueError('无法读取图片尺寸')


def local_path(root, value):
    if not isinstance(value, str) or not value or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', value) or value.startswith(('/', '\\')) or '\\' in value:
        raise ValueError('资源必须是工程内相对路径')
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError('资源路径越过工程目录')
    if not path.is_file():
        raise ValueError('资源不存在: ' + value)
    return path


def finite_number(value, low, high):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and low <= value <= high


def validate(root):
    root = Path(root).resolve()
    errors, warnings = [], []
    def error(message):
        errors.append(message)
    required = ('index.html', 'app.js', 'styles.css', 'tour.json', 'vendor/pannellum.js', 'vendor/pannellum.css', 'vendor/PANNELLUM-LICENSE.txt')
    for value in required:
        try:
            local_path(root, value)
        except ValueError as exc:
            error(str(exc))
    try:
        config = json.loads((root / 'tour.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return {'ok': False, 'errors': errors + [str(exc)], 'warnings': warnings}
    if not isinstance(config, dict) or not isinstance(config.get('scenes'), dict) or not config['scenes']:
        return {'ok': False, 'errors': errors + ['scenes 必须是非空对象'], 'warnings': warnings}
    scenes = config['scenes']
    if not isinstance(config.get('title'), str) or not config['title'].strip():
        error('缺少项目标题')
    if not isinstance(config.get('firstScene'), str) or config['firstScene'] not in scenes:
        error('firstScene 没有对应场景')
    for sid, scene in scenes.items():
        prefix = str(sid) + ': '
        if not isinstance(scene, dict):
            error(prefix + '场景必须是对象')
            continue
        if not isinstance(scene.get('title'), str) or not scene['title'].strip():
            error(prefix + '缺少标题')
        for key, low, high in [('yaw', -180, 180), ('pitch', -90, 90), ('hfov', 50, 110)]:
            if not finite_number(scene.get(key), low, high):
                error(prefix + key + ' 不在有效数值范围')
        for key in ('panorama', 'poster'):
            try:
                path = local_path(root, scene.get(key))
                width, height = image_size(path)
                if width <= 0 or height <= 0:
                    error(prefix + key + ' 图片尺寸无效')
                if key == 'panorama':
                    if width != 2 * height:
                        error(prefix + '完整等距柱状全景须为 2:1；不要直接拉伸修复')
                    if width > 4096:
                        warnings.append(prefix + '单图超过 4096px，需实测纹理上限或改用切片')
            except (ValueError, OSError, struct.error) as exc:
                error(prefix + key + ': ' + str(exc))
        provenance = scene.get('provenance')
        if not isinstance(provenance, dict) or provenance.get('kind') not in ('illustrative', 'generated', 'licensed', 'user-supplied') or not isinstance(provenance.get('statement'), str) or not provenance['statement'].strip():
            error(prefix + '需要 provenance.kind 和非空 statement')
        spots = scene.get('hotSpots')
        if not isinstance(spots, list):
            error(prefix + 'hotSpots 必须是数组')
            continue
        ids = set()
        for spot in spots:
            if not isinstance(spot, dict):
                error(prefix + '热点必须是对象')
                continue
            hid = spot.get('id')
            if not isinstance(hid, str) or not hid or hid in ids:
                error(prefix + '热点 id 缺失或重复')
            else:
                ids.add(hid)
            if not isinstance(spot.get('label'), str) or not spot['label'].strip():
                error(prefix + '热点缺少 label')
            if not finite_number(spot.get('yaw'), -180, 180) or not finite_number(spot.get('pitch'), -90, 90):
                error(prefix + '热点角度无效')
            if spot.get('kind') == 'scene':
                if not isinstance(spot.get('target'), str) or spot['target'] not in scenes:
                    error(prefix + '热点目标不存在')
            elif spot.get('kind') == 'info':
                if not all(isinstance(spot.get(k), str) and spot[k].strip() for k in ('title', 'body')):
                    error(prefix + '信息热点缺少 title / body')
            else:
                error(prefix + '热点 kind 必须是 scene 或 info')
    # Every reachable scene should also be able to return to the initial scene.
    first = config.get('firstScene')
    if isinstance(first, str) and first in scenes:
        edges = {sid: {h.get('target') for h in s.get('hotSpots', []) if isinstance(h, dict) and h.get('kind') == 'scene' and isinstance(h.get('target'), str) and h['target'] in scenes} if isinstance(s, dict) and isinstance(s.get('hotSpots'), list) else set() for sid, s in scenes.items()}
        def walk(start):
            seen, todo = set(), [start]
            while todo:
                sid = todo.pop()
                if sid not in seen:
                    seen.add(sid)
                    todo.extend(edges.get(sid, set()) - seen)
            return seen
        for sid in scenes:
            if sid not in walk(first) or first not in walk(sid):
                warnings.append(str(sid) + ': 热点路径不连通；外围目录仍可跳转，请确认叙事意图')
    for file in root.rglob('*'):
        if file.is_symlink():
            error('工程含符号链接，离线打包前请改为本地文件: ' + str(file.relative_to(root)))
    for name in ('index.html', 'styles.css'):
        path = root / name
        if not path.exists():
            continue
        content = path.read_text(encoding='utf-8')
        matches = re.findall(r'(?:src|href)=[\"\']([^\"\']+)', content) if name.endswith('html') else re.findall(r'url\([\"\']?([^\)\"\']+)', content)
        for ref in matches:
            if ref.startswith(('data:', '#')):
                continue
            try:
                local_path(root, ref)
            except ValueError as exc:
                error(name + ': ' + str(exc))
    return {'ok': not errors, 'scenes': len(scenes), 'errors': errors, 'warnings': warnings, 'limits': ['静态预检不证明投影、无缝、客户端交互或素材许可合格']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--zip', type=Path)
    args = parser.parse_args()
    result = validate(args.directory)
    if result['ok'] and args.zip:
        root = args.directory.resolve()
        target = args.zip.resolve()
        if target == root or root in target.parents:
            parser.error('ZIP 请写到工程目录外')
        if target.exists():
            parser.error('ZIP 已存在，拒绝覆盖')
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(root.rglob('*')):
                if path.is_file() and not any(p.startswith('.') or p == '__pycache__' for p in path.relative_to(root).parts):
                    bundle.write(path, path.relative_to(root))
        result['zip'] = str(target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
