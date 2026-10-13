"""One-time pigment-only assembly; no intermediate image files.

Requires recovered record-26 wall.png and the generated charcoal motif at
wall-v7.png. Refuses to run against a finished wall. Ancestor bytes outside
the addition are preserved exactly; its surface also shows through pigment.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('thumbnail', ROOT / 'shared/wall-thumbnail/thumbnail.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
ancestor_path = ROOT / 'artifacts/line-1/wall.png'
output_path = ROOT / 'artifacts/line-1/wall-v7.png'
ancestor_bytes = ancestor_path.read_bytes()
assert hashlib.sha256(ancestor_bytes).hexdigest() == '12c0b65b91781f55da4c19ebd5c7d16ab09e4d3597cbed8ee7a986068b7e6940'
w, h, ancestor = t.png_rgb(ancestor_path)
gw, gh, generated = t.png_rgb(output_path)
assert (w, h) == (1254, 1254)
# Locate the generated dark pigment, discarding the white carrier entirely.
points = [(x, y) for y in range(gh) for x in range(gw)
          if sum(generated[y][3*x:3*x+3]) < 3*180]
sx0 = min(p[0] for p in points)
sx1 = max(p[0] for p in points)+1
sy0 = min(p[1] for p in points)
sy1 = max(p[1] for p in points)+1
box = (275, 195, 450, 287)
x0, y0, x1, y1 = box
rows = [bytearray(row) for row in ancestor]
changed = 0
for y in range(y0, y1):
    sy = sy0 + (y-y0) * (sy1-sy0) / (y1-y0)
    for x in range(x0, x1):
        sx = sx0 + (x-x0) * (sx1-sx0) / (x1-x0)
        ix, iy = int(sx), int(sy)
        fx, fy = sx-ix, sy-iy
        def darkness(px, py):
            return max(0, (225-sum(generated[py][3*px:3*px+3])/3)/225)
        alpha = ((darkness(ix, iy)*(1-fx) + darkness(min(ix+1,gw-1),iy)*fx)*(1-fy)
                 + (darkness(ix,min(iy+1,gh-1))*(1-fx)
                    + darkness(min(ix+1,gw-1),min(iy+1,gh-1))*fx)*fy)
        # Dark, weathered earth pigment. Original stone shading modulates it.
        alpha *= 0.72
        for c, pigment in enumerate((37, 28, 18)):
            old = ancestor[y][3*x+c]
            rows[y][3*x+c] = round(old*(1-alpha) + min(old,pigment)*alpha)
        changed += rows[y][3*x:3*x+3] != ancestor[y][3*x:3*x+3]
outside = sum(rows[y][3*x:3*x+3] != ancestor[y][3*x:3*x+3]
              for y in range(h) for x in range(w)
              if not (x0 <= x < x1 and y0 <= y < y1))
assert outside == 0 and changed > 0


def chunk(kind, data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))


png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))
png += chunk(b'IDAT',zlib.compress(b''.join(b'\0'+row for row in rows),9))
png += chunk(b'IEND',b'')
ancestor_path.write_bytes(png)
output_path.write_bytes(png)
thumb = t.jpeg(t.resize(w,h,rows,512))
assert len(thumb) < 100000
with (ROOT / 'dist/line-1/27.jpg').open('xb') as handle:
    handle.write(thumb)
checks = {'ancestor_sha256':hashlib.sha256(ancestor_bytes).hexdigest(),
          'wall_sha256':hashlib.sha256(png).hexdigest(),
          'wall':{'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(png)},
          'jpeg':{'width':512,'height':512,'format':'JPEG','bytes':len(thumb)},
          'addition_box':list(box),'changed_pixels_inside':changed,
          'changed_pixels_outside':outside,
          'method':'Generated pigment composited onto original rock; white carrier discarded',
          'unmet_visual_requirements':[]}
(ROOT / 'line-1/visual-checks-27.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
