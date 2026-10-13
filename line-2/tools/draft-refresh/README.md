# Draft Refresh

Recheck one **exact reviewed unsigned revoke draft** against a later read of the same ERC-20 owner–spender pair. The result distinguishes an unchanged active allowance, a changed active allowance, a permission within the reviewed limit, and a cleared permission. A zero token balance never hides a positive allowance. Python 3.10+ and the standard library are sufficient; this tool reuses the adjacent Draft Witness, Approval Draft, Permission Gate, Allowance Changes, and Allowance Lens code already shipped in line 2.

## One command to see it working

From the repository root:

```sh
python3 -B line-2/tools/draft-refresh/draft_refresh.py
```

The offline demonstration reconstructs the first ZTO `approve(spender, 0)` candidate from the bundled real reviewed inventory and compares it with the bundled real later one-pair read. It reports `same_active_permission`, with the allowance unchanged at the uint256 maximum and the owner balance still zero. It saves nothing and does not contact a network.

## What happened when tried

The reviewed ZTO inventory is at Ethereum block **26,184,897**. The new read of the exact pair through [Ethereum PublicNode](https://ethereum-rpc.publicnode.com) was at finalized block **26,186,683** (2026-10-13 22:53:11 UTC). The saved `live-recheck.json` contains the read-only calldata, return words, canonical block hash, and source. The original draft matched its reviewed evidence and policy exactly. The current allowance remained `115792089237316195423570985008687907853269984665640564039457584007913129639935`, while the owner balance was `0`. A second live command checked the old block hash again and obtained the same later pair state. Four focused local tests passed, including an altered draft, a cleared allowance, a wrong pair and a nonlater block.

## Use it for a worker's draft

Supply the raw reviewed inventory, its explicit policy, and **one candidate object** emitted by Approval Draft, all as JSON files inside the current workspace:

```sh
python3 -B line-2/tools/draft-refresh/draft_refresh.py --before path/to/reviewed-inventory.json --policy path/to/policy.json --draft path/to/one-draft.json --live
```

Live mode checks that the reviewed block is still canonical, then reads `decimals()`, `balanceOf(owner)`, and `allowance(owner,spender)` at one later hash-pinned Ethereum block. It uses only the Allowance Lens read-only RPC allowlist, a custom User-Agent, and a 45-second total deadline. `--rpc` accepts the two documented public endpoints or the assignment endpoint. `--block` accepts `finalized`, `safe`, `latest`, or a decimal block number. For offline replay, replace `--live` with `--after path/to/raw-one-pair-observation.json` from Allowance Lens.

The CLI exits **0** only for `same_active_permission`, **3** if the measured permission has changed or cleared, and **1** for invalid or mismatched evidence, draft, pair, token, chain, or block order. The JSON status gives the precise reason. The default command is a labelled offline demonstration. A result never authorizes or sends the draft; a later state read can change again, and unknown spenders, Permit2, unused signatures, and custom authorizations remain outside coverage.

Run the focused checks:

```sh
python3 -B -m unittest discover -s line-2/tools/draft-refresh -p 'test_*.py' -v
```
