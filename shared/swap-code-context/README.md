# Swap Code Context

This standard-library gate brings Line 1's **ZTO Review** and Line 3's **Code Set** together before a worker carries a ZTO/IMD planning bound forward. It revalidates the raw pool snapshot, size report, caller policy, token code proofs, code reviews and exact code manifest. It releases usable bounds only when both line tools accept, the pool and code evidence have the same block number and hash, both use the same caller-selected reference height, and the code set contains both real ZTO and IMD addresses. A saved success summary is never accepted as input.

From the repository root, run the real saved-evidence demonstration:

```sh
python3 -B shared/swap-code-context/swap_code_context.py --demo
```

It exits **2** with `refuse`, as it should: the historical ZTO/IMD pool snapshot passes ZTO Review, but the Code Set sample has no independent caller anchor, was measured at a different block, and uses a different reference height. The result contains **no** released planning bounds. This was tried locally; `demo-result.json` records the result. The source Line 1 and Line 3 observations were not changed. The demonstration cannot certify a trade or a code identity.

For your own evidence, supply paths under the workspace and an independently selected anchor:

```sh
python3 -B shared/swap-code-context/swap_code_context.py \
  --snapshot path/to/pool-snapshot.json --report path/to/size-report.json \
  --policy path/to/swap-policy.json --manifest path/to/code-manifest.json \
  --member path/to/zto-proof.json path/to/zto-review.json \
  --member path/to/imd-proof.json path/to/imd-review.json \
  --as-of-block YOUR_REVIEWED_REFERENCE_HEIGHT \
  --anchor-hash YOUR_INDEPENDENTLY_TRUSTED_BLOCK_HASH
```

The reference height must equal the swap policy's `reference_block`. The anchor must be a separately trusted hash for the Code Set proof block; the tool never copies one from its own evidence. Omitting it gives a diagnostic refusal. Exit **0** means the historical evidence is coherent under the caller's inputs; exit **2** is a completed refusal; exit **1** is malformed evidence or input. All JSON files are bounded to 100 KB, duplicate keys/floats/nonfinite numbers are refused, and paths must resolve inside the current workspace.

The handoff helps another line use a swap bound without silently overlooking a token code change or mixing historical blocks. It does not prove on-chain consensus, provider authenticity, code semantics, quote execution, token transfers, gas, current liquidity, or the safety of a transaction. It reads no wallet, key or environment variable and signs or sends nothing. It needs the committed `line-1/tools/zto-review/` and `line-3/tools/code-set/` dependency trees (including their sibling tools); there is no package download.

Three focused checks passed: real-evidence cross-block refusal and two explicitly mocked glue cases. Run:

```sh
python3 -B -m unittest discover -s shared/swap-code-context -p 'test_*.py' -v
```
