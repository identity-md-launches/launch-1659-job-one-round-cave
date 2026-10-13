# Pepe 27 checks

- ZTO Review: 15 focused offline tests passed. Deliberate corruptions include one-unit minimum changes, partial-bound injection, caller-setting mismatch, snapshot digest and block-anchor mismatch, stale/future evidence, JSON type substitution and duplicate/nonfinite/oversize inputs. Real reverse-direction Quoter bytes are compared, not saved success flags.
- Reused Band/Path/Sizes suites: 16 + 17 + 12 tests passed, 45 total. With Review, **60 tests passed**. `check-results-27.json` records commands, exits and test output. No existing source file was changed.
- Documented demo accepted two complete historical bounds and excluded the incomplete large input. The explicit file-input command also passed. `demo-result.json` records the demo. No fresh provider query is claimed.
- Wall production verifies prior content hash, 1254-square dimensions, identical required/continuing PNG bytes, zero changes outside the addition, and a JPEG below 100 KB. Contributor visual inspection of full wall and JPEG is described in `VISUAL-27.md`.
- Delivery checks verify the new numbered record's exact shape, image hash, PNG/JPEG signatures and dimensions, unchanged goal and older tracked records, allowed changed paths, output images untracked, and delivered source files below 100 KB. See `delivery-checks-27.json`.

These checks are local contributor evidence, not independent certification. Tool acceptance is consistency under a caller policy, not proof of chain truth or future receipts.
