#!/usr/bin/env python3
"""Render original schematic rooms into true spherical PNG test panoramas (stdlib)."""
import argparse
import math
import struct
import zlib
from pathlib import Path


def png(path, width, height, raw):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 7)) + chunk(b'IEND', b''))


def wall(u, v, mode, front=False):
    # Flat, deliberately schematic relief motifs; not archaeological reconstruction.
    color = [133, 104, 73]
    band = v > 3.8 or v < 0.65
    if band:
        pattern = math.sin(u * 8) * math.sin(v * 13)
        return [91 + pattern * 13, 106 + pattern * 10, 89 + pattern * 7]
    spacing = 2.5
    c = (u + spacing / 2) % spacing - spacing / 2
    arch = (c / 0.96) ** 2 + ((v - 2.5) / 1.3) ** 2
    inside = abs(c) < .96 and 0.74 < v < 2.5 or arch < 1 and v >= 2.5
    if not inside:
        # Mineral-pigment waves are original decoration.
        wave = abs(math.sin(u * 1.35 + math.sin(v * 1.7)))
        if wave < .05:
            color = [92, 113, 101]
        return color
    color = [65, 53, 39]
    if arch > .83 and v > 2.5 or abs(c) > .86:
        return [172, 144, 98]
    if mode == 'rest' and front:
        body = (u / 3.1) ** 2 + ((v - 1.6) / .55) ** 2
        head = ((u + 2.5) / .42) ** 2 + ((v - 1.9) / .45) ** 2
        if body < 1 or head < 1:
            return [192, 163, 119] if math.sin(u * 9 + v * 14) > -.85 else [151, 119, 78]
        return [71, 60, 46]
    head = (c / .28) ** 2 + ((v - 2.78) / .34) ** 2
    halo = (c / .57) ** 2 + ((v - 2.78) / .68) ** 2
    body = .95 < v < 2.47 and abs(c) < .43 + (2.47 - v) * .17
    legs = (c / .74) ** 2 + ((v - 1.02) / .26) ** 2 < 1
    if .9 < halo < 1.08:
        return [181, 153, 103]
    if head < 1 or body or legs:
        color = [193, 164, 120]
        if body and abs(math.sin(c * 12 + v * 9)) < .12:
            color = [138, 119, 90]
        if head < 1 and 2.73 < v < 2.77 and .06 < abs(c) < .21:
            color = [83, 70, 51]
    return color


def render(path, width, mode):
    height = width // 2
    longitudes = [((x + .5) / width - .5) * 2 * math.pi for x in range(width)]
    sn, cs = [math.sin(a) for a in longitudes], [math.cos(a) for a in longitudes]
    raw = bytearray()
    for j in range(height):
        pitch = (.5 - (j + .5) / height) * math.pi
        cp, dy = math.cos(pitch), math.sin(pitch)
        raw.append(0)
        for i in range(width):
            dx, dz = cp * sn[i], cp * cs[i]
            tx, tz = 4.5 / abs(dx) if abs(dx) > 1e-9 else 1e12, 5.4 / abs(dz) if abs(dz) > 1e-9 else 1e12
            ty = 3.5 / dy if dy > 0 else -1.7 / dy
            t = min(tx, ty, tz)
            x, y, z = dx * t, 1.7 + dy * t, dz * t
            is_pillar = False
            if mode == 'pillar' and dz > 0:
                # Front face of a pillar inside the room, with real spherical occlusion.
                pt = 2.4 / dz
                if pt < t and abs(dx * pt) < 1.08 and 0 < 1.7 + dy * pt < 4.8:
                    x, y, z, t, is_pillar = dx * pt, 1.7 + dy * pt, 2.4, pt, True
            if is_pillar:
                color = wall(x, y * .91, 'main')
                shade = 1.18
            elif t == ty:
                if dy > 0:
                    lattice = abs(math.sin(x * 1.8) * math.sin(z * 1.8))
                    color = [142, 109, 70] if lattice > .23 else [77, 91, 78]
                    shade = .67
                else:
                    grout = abs(x % 1.5) < .025 or abs(z % 1.5) < .025
                    color = [73, 63, 48] if grout else [116, 99, 74]
                    shade = .85
            else:
                color = wall(x if t == tz else z, y, mode, front=t == tz and dz > 0)
                shade = 1.06 if dz > 0 and t == tz else .82
            noise = 1 + .028 * math.sin(x * 63 + y * 81 + z * 49) + .022 * math.sin(x * 17 - y * 29 + z * 13)
            light = 1 + .1 * max(0, dz)
            raw.extend(max(0, min(255, round(c * shade * noise * light))) for c in color)
    png(path, width, height, raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--width', type=int, default=2048)
    args = parser.parse_args()
    if args.width < 256 or args.width > 4096 or args.width % 2:
        parser.error('width 必须是 256–4096 之间的偶数')
    args.output.mkdir(parents=True, exist_ok=True)
    if any((args.output / (name + '.png')).exists() for name in ('main', 'rest', 'pillar')):
        parser.error('示意图片已存在，拒绝覆盖')
    for name in ('main', 'rest', 'pillar'):
        render(args.output / (name + '.png'), args.width, name)
        print('Rendered ' + name, flush=True)


if __name__ == '__main__':
    main()
