"""Keep the generated addition only, preserving all other ancestor pixels.

Artifact-production helper; not a Code Set dependency. Run once, before wall.png
is replaced: generated wall-v7.png and the verified record-26 wall.png are inputs.
No preview or intermediate images are saved.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('thumbnail', ROOT / 'shared/wall-thumbnail/thumbnail.py')
thumbnail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thumbnail)
ancestor_path = ROOT / 'artifacts/line-3/wall.png'
generated_path = ROOT / 'artifacts/line-3/wall-v7.png'
ancestor_bytes = ancestor_path.read_bytes()
generated_bytes = generated_path.read_bytes()
assert hashlib.sha256(ancestor_bytes).hexdigest() == 'ea9248dd84c6c542aee27976baaffc145aabfacf2281c286f4c444e74ec46a31'
width, height, ancestor = thumbnail.png_rgb(ancestor_path)
gw, gh, generated = thumbnail.png_rgb(generated_path)
assert (width, height) == (gw, gh) == (1254, 1254)
# Previously bare upper-right stone. Includes only the new portrait and enclosure.
box = (830, 80, 1155, 244)
x0, y0, x1, y1 = box
rows = [bytearray(row) for row in ancestor]
for y in range(y0, y1):
    for x in range(x0, x1):
        alpha = min(1, min(x-x0, x1-1-x, y-y0, y1-1-y) / 6)
        for c in range(3):
            rows[y][3*x+c] = round(ancestor[y][3*x+c]*(1-alpha) + generated[y][3*x+c]*alpha)
inside = outside = 0
for y in range(height):
    for x in range(width):
        if rows[y][3*x:3*x+3] != ancestor[y][3*x:3*x+3]:
            if x0 <= x < x1 and y0 <= y < y1:
                inside += 1
            else:
                outside += 1
assert inside > 0 and outside == 0


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))


png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(b''.join(b'\0'+row for row in rows), 9))
png += chunk(b'IEND', b'')
generated_path.write_bytes(png)
ancestor_path.write_bytes(png)
report = {'ancestor_sha256': hashlib.sha256(ancestor_bytes).hexdigest(),
          'generated_before_assembly_sha256': hashlib.sha256(generated_bytes).hexdigest(),
          'wall_sha256': hashlib.sha256(png).hexdigest(), 'format': 'PNG',
          'dimensions': [width, height], 'mode': 'RGB', 'wall_bytes': len(png),
          'addition_box_xyxy': list(box), 'changed_pixels_inside_box': inside,
          'changed_pixels_outside_box': outside, 'manual_review_pending': True}
(ROOT / 'line-3/visual-checks-27.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
