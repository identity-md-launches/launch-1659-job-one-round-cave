# ZTO Review

Review a saved ZTO/IMD swap-size report before carrying its planning minimum into later work. This offline Python 3.10+ tool recomputes ZTO Sizes from a caller-pinned real Uniswap v4 liquidity snapshot, checks every report field with exact JSON types, and releases only complete positive-output bounds. No network, wallet, environment, signing, sending, payment or deployment is involved. Uses only the standard library and the committed sibling `zto-sizes`, `zto-path` and `zto-band` folders; keep them together.

One command from the repository root:

```sh
python3 -B line-1/tools/zto-review/zto_review.py --demo
```

When tried, it accepted the ancestor's real Ethereum evidence at block **26,184,260** (hash `0xcd8e7e4ba940af1feac8d6b441c37ef0230c4bcd2fd55d36376038a4b4c36650`). Of three independently tested inputs, two have usable bounds: 1 ZTO estimates 0.000015292155595473 IMD, with a 100-bps planning minimum of 0.000015139234039518 IMD; 100,000,000 ZTO estimates 1,196.130391948897309582 IMD, minimum 1,184.169088029408336486 IMD. The 1,000,000,000-ZTO input is outside recorded coverage and is never released as a usable bound. These amounts demonstrate historical coverage and are not trade recommendations. `demo-result.json` records the actual run. The bundled policy pins that historical demonstration; it is not an independent trust anchor, live quote or owner authorization.

## Review your own evidence

Prepare a ZTO Sizes report from a ZTO Path snapshot. Supply a **separate caller-selected policy**, then run:

```sh
python3 -B line-1/tools/zto-review/zto_review.py --snapshot line-1/tools/zto-path/observation.json --report line-1/tools/zto-sizes/demo-report.json --policy line-1/tools/zto-review/demo-policy.json
```

That second command still reviews bundled historical data; replace its three paths with your workspace evidence and independently reviewed policy. The tool deliberately does not extract your intended amounts, direction, tolerance, anchor or reference height from an untrusted report. Anyone who can change both evidence and policy can change the review decision. Select and protect the policy through your own trusted review process.

Policy fields must be exactly these; see `demo-policy.json` for a concrete example:

| Field | Meaning |
| --- | --- |
| `schema` | `zto-review-policy-v1` |
| `snapshot_sha256` | Lowercase SHA-256 of canonical **parsed** snapshot JSON, not of raw file bytes |
| `block_number`, `block_hash` | Expected snapshot height as a decimal JSON integer and lowercase `0x` bytes32 hash |
| `reference_block` | Caller-selected decimal reference height, checked without consulting a clock or RPC |
| `max_age_blocks` | Maximum permitted height difference, inclusive; zero means exact reference height |
| `input_token` | `ZTO` or `IMD`; output is the other assigned token |
| `amounts` | Ordered list of 1–20 positive plain decimal strings, within on-chain decimal precision; candidates are independent |
| `slippage_bps` | Explicit integer 0–9999 for minimum rounding |
| `max_spot_loss_bps` | Integer 0–9999 for the optional fee-inclusive initial-spot-loss filter, or `null` |

Canonical JSON uses `json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)` encoded as ASCII. Key order and whitespace do not affect identity; metadata, array order, integer/string types and raw ABI text do. To inspect the canonical digest of an already reviewed workspace snapshot, use this read-only command:

```sh
python3 -B -c "import sys; sys.path.insert(0,'line-1/tools/zto-review'); import zto_review as r; print(r.digest(r.read_json('line-1/tools/zto-path/observation.json')))"
```

A digest establishes exact evidence identity only. Computing it from an untrusted file does not make the file trustworthy. Snapshot hash, block number/hash and age policy all must match before recomputation. The tool validates real-pool identity, currencies, fees, hook restrictions, complete bitmap coverage and tick records through the ancestor decoder. It then recomputes the entire `zto-sizes-report-v1` with the supplied policy and compares it, including candidate order, partial diagnostics, rounded minimums, fee/spot-loss calculations, and summary counts. Unknown/missing report fields, one-unit alterations, boolean/integer substitutions and extra claimed bounds cause refusal. JSON duplicate keys, floating/nonfinite numbers and files over 100 KB cause errors. Input paths must resolve inside the current workspace.

## Results and checks

- Exit **0**, `accepted`: exact recomputation matches and at least one complete, positive minimum passed the policy. Only those candidates appear in `usable_bounds`.
- Exit **2**, `refuse`: identity/age mismatch, report mismatch, or no usable bound. `usable_bounds` is empty; reasons and up to 40 mismatch locations explain the refusal without echoing report values.
- Exit **1**: malformed policy/evidence, unsupported data, or file error; JSON error on stderr. Parser usage errors use argparse's conventional exit 2 and are not review results.

Result hashes identify snapshot, report and policy. `mode` distinguishes `historical_demo` from `caller_policy`. Matching reports that contain partial or zero-output candidates may be accepted when other candidates are usable; those partial/zero candidates remain excluded. Minimums use integer floor rounding and are planning numbers only.

**15 focused tests passed**, including real saved Quoter output in the reverse IMD direction, raw-unit minimum tampering, partial-bound injection, altered settings/source identity, exact age boundary and future snapshot refusal, no-usable-bound refusal, JSON ambiguity and offline CLI behavior. The 45 ancestor Band/Path/Sizes tests also passed. Run:

```sh
python3 -B -m unittest discover -s line-1/tools/zto-review -p 'test_*.py' -v
```

This reuses the ancestor numerical implementation, so it checks consistency and handoff integrity rather than independently proving the arithmetic. Hashes do not prove Ethereum consensus or provider authenticity; age is relative to a caller-supplied reference block, not a live freshness guarantee. No router calldata, enforced receipt, settlement/transfer behavior, gas, MEV or future liquidity is modeled. The pool and tokens are the assigned real Ethereum ZTO/IMD pair; no new coin is needed.
