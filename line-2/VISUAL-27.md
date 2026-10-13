# Pepe 27 — Fresh Pair

Two broken charcoal arcs hold a red-ochre old reading and a smaller yellow-ochre fresh reading in open stone between Pepe and the inherited upper-right marks. It depicts a read-only permission recheck before an unsigned draft is shown to its owner.

| Output | Format | Dimensions | Bytes |
| --- | --- | --- | ---: |
| `artifacts/line-2/wall.png` and `artifacts/line-2/wall-v7.png` | 8-bit RGB, non-interlaced PNG | 1254 × 1254 | 3,949,349 each |
| `dist/line-2/27.jpg` | Baseline three-component JPEG | 512 × 512 | 56,004 |

The verified Pepe 26 source hash was `0ff0a6cdd0f6b5c371392f36f2ff003b82131f900e748b2fdc5824108fe62330`. The new mark is confined to **x=690, y=305, width=130, height=120**. The composite reported **7,627 changed pixels** and asserted every source pixel outside that rectangle is unchanged. A separate decoded comparison with the recovered ancestor found the same 7,627 changed pixels and zero changes outside the rectangle. Both finished PNG paths have SHA-256 `53bd236f05aa1ccd5811f243431c024c9f6377ea76a93c9f2b948564141cea14`.

Chosen review: inspect the full-resolution PNG and the 512-pixel JPEG. The rock, cracks, warm light, cave framing and every inherited mark remain. The central Pepe retains his wide mouth, heavy-lidded eyes and two five-digit hands (four fingers and one thumb each); the new motif has no hand or handprint. No letters, numbers, caption, signature, logo, watermark, border, frame, photograph, 3D render, real person, political or hateful symbol was observed. The mark uses charcoal, red ochre and yellow ochre. **Unmet visual requirements observed: none.** This is a visual review, not independent certification.

The installed built-in imagegen editor created an isolated transparent pigment motif using the inherited wall solely as a style reference. Its returned PNG bytes went to the compositor through standard input; no insert image was saved in the workspace. `finish_wall_27.py` verified the ancestor wall hash, composited only the placement rectangle and wrote the two complete wall paths. The already reviewed standard-library thumbnail encoder produced the numbered JPEG.

Prompt used:

> Use case: illustration-story. Asset type: isolated small pigment mark to add to a prehistoric cave painting. The supplied wall is a style reference only; do not reproduce the wall or its figures. Create ONLY a compact motif: two short broken charcoal arcs suggesting a repeated read, surrounding one small red-ochre dot and a slightly offset smaller yellow-ochre dot, like a fresh measurement beside an old one. Handmade primitive burnt-stick and thumb pigment, uneven, lightly worn, flat 2D, no tidy geometric symmetry. Use charcoal, muted red ochre, yellow ochre and sparse chalk white only. Fully transparent background, with ample transparent space around the motif. No rock background. No letters, numbers, caption, writing, runes, logo, border, frame, Pepe, frog, face, hand, handprint, person, recognizable modern object, photography, shadows or 3D.
