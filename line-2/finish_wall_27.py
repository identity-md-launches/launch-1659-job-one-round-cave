#!/usr/bin/env python3
"""Add one generated transparent pigment mark to the verified Pepe 26 wall.

Reads base64 PNG lines from stdin up to a line containing only END. The insert is
never saved in the workspace. Writes only the complete wall and its named copy.
"""
import base64
import hashlib
import json
from pathlib import Path
import sys

import finish_wall_26 as imageops

ROOT = Path(__file__).resolve().parents[1]
WALL = ROOT / 'artifacts' / 'line-2' / 'wall.png'
VERSIONED = ROOT / 'artifacts' / 'line-2' / 'wall-v7.png'
SOURCE_SHA256 = '0ff0a6cdd0f6b5c371392f36f2ff003b82131f900e748b2fdc5824108fe62330'
PLACEMENT = (690, 305, 130, 120)


def main():
    source = WALL.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('expected the verified Pepe 26 wall')
    width, height, channels, base = imageops.decode(source)
    if (width, height, channels) != (1254, 1254, 3):
        raise ValueError('unexpected wall dimensions')
    pieces = []
    for line in sys.stdin.buffer:
        if line.strip() == b'END':
            break
        pieces.append(line.strip())
    else:
        raise ValueError('missing END marker')
    pigment = base64.b64decode(b''.join(pieces), validate=True)
    imageops.PLACE_X, imageops.PLACE_Y, imageops.PLACE_W, imageops.PLACE_H = PLACEMENT
    result, bounds = imageops.composite(base, imageops.decode(pigment))
    x, y, w, h = PLACEMENT
    for n, (old, new) in enumerate(zip(base, result)):
        if n < y or n >= y + h:
            assert old == new
        else:
            assert old[:x*3] == new[:x*3]
            assert old[(x+w)*3:] == new[(x+w)*3:]
    output = imageops.encode(width, height, result)
    VERSIONED.write_bytes(output)
    WALL.write_bytes(output)
    changed = sum(1 for old, new in zip(base, result)
                  for offset in range(0, len(old), 3)
                  if old[offset:offset+3] != new[offset:offset+3])
    print(json.dumps({'source_sha256': SOURCE_SHA256,
                      'output_sha256': hashlib.sha256(output).hexdigest(),
                      'dimensions': [width, height], 'insert_bounds': bounds,
                      'placement': PLACEMENT, 'changed_pixels': changed,
                      'outside_placement_unchanged': True, 'output_bytes': len(output)}))


if __name__ == '__main__':
    main()
