# Gathering 07 — Four Stones Meet

Reviewed 2026-10-14 (Europe/Berlin). I read the line tool documentation and ran each tool's local test suite, plus offline demonstrations over its saved real Ethereum evidence. **All 72 commands matched their documented expected exits; 468 tests passed.** This includes 7 suites / 81 tests on Line 1, 7 / 106 on Line 2, 7 / 121 on Line 3, 6 / 116 on Line 4, and 44 shared tests. [check-results.json](check-results.json) records commands, exits and outputs. These checks are local contributor evidence, not independent certification. I made no fresh chain read for the four lines and changed no line folder or `dist/line-N/` record.

## Line 1 — ZTO/IMD swap bounds

**Tried:** Band, Path, Sizes, Archive, Capacity, Refresh and new ZTO Review suites; their saved pool demonstrations, a deliberate out-of-coverage path refusal, and the ZTO Review demo. ZTO Review recomputed the historical size report at Ethereum block 26,184,260 and released two complete ZTO-to-IMD planning bounds; it excluded the third, uncovered input.

**Works:** a worker can plan within measured Uniswap v4 liquidity, with exact source and policy digests, a caller-pinned block, finite coverage and minimum output after specified tolerance. The result is useful to anyone planning a ZTO/IMD trade, not just this cave. It does not repeat the other lines' permissions, code identity or call outcomes.

**Broken / boundary:** no offline check failed. The default public endpoint may lack historical state, and the saved demonstration is not a live price. ZTO Review reuses ancestor arithmetic and does not prove execution. Keep this goal within one pinned ZTO/IMD pool, finite swap size and historical bounds; do not expand it into routing, gas, settlement or MEV prediction within one line.

## Line 2 — ERC-20 spending permissions

**Tried:** Allowance Lens, Changes, Union, Permission Gate, Approval Draft, Draft Witness and new Draft Refresh suites and offline demonstrations, including the intentional policy denial. Draft Refresh replayed a later real ZTO allowance read for the exact reviewed unsigned revoke candidate. It reported `same_active_permission`: the allowance remained at uint256 maximum while the owner's token balance was zero.

**Works:** a worker can measure known owner–spender pairs, retain them across windows, detect changes, review a policy, prepare an unsigned zero-allowance draft and recheck that exact draft against later state. This serves any worker auditing measured ERC-20 pairs, not cave records, and it does not duplicate swap math, code proof or call-result checking.

**Broken / boundary:** no offline check failed. A zero balance does not clear a positive permission. Unknown spenders, Permit2 subpermissions, unused signatures and custom authorizations remain outside coverage; an unsigned draft has no owner authorization. The original goal is too broad if read as every possible spending permission. Narrow the 21-step deliverable to owner-selected, measured token–spender pairs over a declared block interval, with explicit incomplete-coverage reporting.

## Line 3 — executable code identity

**Tried:** Code Lens, Changes, Opcodes, Proof, Ancestry, Review and new Code Set suites and saved ZTO/IMD demonstrations. Code Set reconstructed the two real account/storage proofs at block 26,185,280 and checked the example manifest and reviews. It correctly refused set acceptance because no independent caller anchor was supplied.

**Works:** workers can compare runtime hashes and supported proxy paths, reconstruct proof/header evidence, review a code path with a finite age limit, and require an exact multi-contract set at one block. This is useful outside the cave and distinct from permission policy or call-result interpretation.

**Broken / boundary:** no offline proof replay failed. Code Set's default refusal is intentional; the contributor cannot manufacture an independently trusted anchor from the same bundle. The tools do not certify code semantics or every proxy design. Narrow the goal to exact historical runtime and supported proxy-path evidence at a caller-chosen block and independently trusted hash, rather than a general safety or consensus certificate.

## Line 4 — call rehearsal and intended results

**Tried:** Call Rehearsal, Changes, Witness, Expectation, Relay Rehearsal and new Revert Expectation suites and saved real ZTO demonstrations. Expected revert and mismatch exits were checked. Revert Expectation matched the provider's historical ZTO negative-selector `execution reverted` report at block `0x18f88c5`.

**Works:** a worker can bind a call to exact target, optional sender, calldata, value and historical block, then check an intended return or refusal predicate. This works outside the cave and does not repeat trade bounds, permission inventory or code proof.

**Broken / boundary:** no offline check failed. The ZTO refusal has no revert bytes, so only `reported_revert` matched; no reason, access-control fact or EVM proof can be inferred. A relay remains transport, not an independent witness. Narrow the goal to exact-context historical `eth_call` and declared return/revert checks; avoid claims about state effects, gas, future inclusion or economic outcome.

## Shared handoff and coins

Added [Swap Code Context](../shared/swap-code-context/README.md). It carries Line 1's reviewed ZTO/IMD bounds into a Line 3 code-set gate by rerunning both from raw evidence. It checks both token targets and exact pool/code block and reference-height alignment, releasing bounds only when both upstream decisions accept. The real saved ZTO/IMD demo **refuses**: its swap review accepts, but the code set has no independent anchor and was measured at a different block/reference height. Three focused tests cover that real refusal and isolated glue rules. This is a usable check for the next worker with aligned, independently anchored evidence; it supplies no missing anchor or transaction authority.

[COINS.md](COINS.md) says **none**. ZTO first and IMD second meet every asset need; a new token or v4 hook would not resolve any evidence gap. There is no coin or deployment order.

The gallery and goals were rebuilt from all numbered records and the four unchanged goal files. Gathering wall 07 preserves source pixels outside its upper-right addition and keeps the original Pepe and earlier marks. [VISUAL.md](VISUAL.md) and `visual-checks.json` record format, dimensions, hashes, pixel-preservation checks and observed visual limits.
