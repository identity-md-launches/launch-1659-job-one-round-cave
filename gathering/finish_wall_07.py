#!/usr/bin/env python3
"""Keep Gathering 06 pixels and transfer only the new pigment from an image edit.

The image edit is first copied to artifacts/gathering/wall-v7.png. This script
fetches the exact previous wall by its public content hash, checks both rasters,
and replaces the edit's surrounding regenerated rock with the original pixels.
"""
import hashlib
from pathlib import Path
import struct
import sys
import urllib.request
import zlib

sys.path.insert(0, str(Path('shared/wall-thumbnail').resolve()))
import thumbnail

SOURCE_HASH = 'e9ca4c75f4acec13929f6d11546bb4a2da20bb55e3bb8b1c2baa93dabe78e4d8'
URL = 'https://api.imd.fun/artifacts/' + SOURCE_HASH
OUTPUT = Path('artifacts/gathering/wall-v7.png')


def source_bytes():
    request = urllib.request.Request(URL, headers={'User-Agent': 'Pepeolithic-Gathering-07/1.0'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=20) as response:
        raw = response.read(6_000_000)
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError('previous wall content hash changed')
    return raw


def png_rows(raw):
    # Reuse the shared, CRC-checking standard-library decoder without saving an
    # intermediate picture anywhere in the workspace.
    class InMemoryPNG:
        def read_bytes(self):
            return raw
    return thumbnail.png_rgb(InMemoryPNG())


def disk(x, y, cx, cy, radius, feather=5):
    distance = ((x - cx) ** 2 + (y - cy) ** 2) ** .5
    return max(0.0, min(1.0, (radius + feather - distance) / feather))


def stroke(x, y, x0, y0, x1, y1, radius=7, feather=4):
    dx, dy = x1 - x0, y1 - y0
    t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
    return disk(x, y, x0 + t * dx, y0 + t * dy, radius, feather)


def pigment_mask(x, y):
    if not (875 <= x <= 1085 and 300 <= y <= 465):
        return 0.0
    # The old right hand begins below-left of the new chalk dab. Its pixels
    # retain priority even at the edge of the new pigment.
    if x < 936 and y > 440:
        return 0.0
    shapes = [
        disk(x, y, 908, 337, 28), disk(x, y, 1035, 341, 30),
        disk(x, y, 1030, 432, 27), disk(x, y, 912, 428, 24),
        disk(x, y, 970, 386, 22),
        stroke(x, y, 928, 351, 953, 374),
        stroke(x, y, 988, 375, 1015, 352),
        stroke(x, y, 985, 398, 1013, 418),
        stroke(x, y, 951, 398, 931, 413),
    ]
    return max(shapes)


def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))


def encode_png(width, height, rows):
    raw = b''.join(b'\0' + row for row in rows)
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main():
    old_width, old_height, old_rows = png_rows(source_bytes())
    new_width, new_height, new_rows = thumbnail.png_rgb(OUTPUT)
    if (old_width, old_height) != (1254, 1254) or (new_width, new_height) != (1254, 1254):
        raise ValueError('wall dimensions must stay 1254 square')
    rows = []
    changed = 0
    for y, (old, new) in enumerate(zip(old_rows, new_rows)):
        result = bytearray(old)
        for x in range(875, 1086):
            alpha = pigment_mask(x, y)
            if not alpha:
                continue
            at = 3 * x
            for channel in range(3):
                result[at + channel] = round(old[at + channel] * (1 - alpha) + new[at + channel] * alpha)
            if result[at:at + 3] != old[at:at + 3]:
                changed += 1
        rows.append(bytes(result))
    OUTPUT.write_bytes(encode_png(old_width, old_height, rows))
    print(f'new pigment pixels: {changed}; output SHA-256: {hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
