# Code Set

Code Set checks two or more contract code identities together at one proved block. A worker can name the contracts required for a job, pin each exact reviewed identity, and refuse the whole set if a member is missing, substituted, stale, or from another block. It uses Python's standard library and the committed sibling Code Review, Code Ancestry, Code Proof and Code Lens tools. No installation or network is required.

Run from the repository root:

```sh
python3 -B line-3/tools/code-set/code_set_demo.py
```

What happened: the demonstration reconstructed the saved real Ethereum ZTO and IMD account/storage proofs at block **26185280** (`0x18f8e40`), matched both example reviews and their manifest digests, and returned `demonstration_passed: true`. Its set decision is deliberately **refuse**, with `missing-caller-anchor` for both members. No independent anchor was supplied or invented. The demonstration exits 0 because this refusal is the expected outcome; it is not an acceptance or safety endorsement. These are historical observations, not new live measurements. The saved output is `demo-result.json`.

For a caller-selected manifest and raw evidence, the CLI is:

```sh
python3 -B line-3/tools/code-set/code_set.py \
  --manifest line-3/tools/code-set/zto-imd-manifest.json \
  --member line-3/tools/code-proof/zto-proof.json line-3/tools/code-review/zto-review.json \
  --member line-3/tools/code-proof/imd-proof.json line-3/tools/code-review/imd-review.json \
  --as-of-block 26185288
```

This command exits **3** with a JSON refusal. A person who independently trusts the exact block hash can supply it separately with `--anchor-hash`; the tool never takes trust from a manifest or bundle. CLI exit 0 means `accept-set-identity`, 3 means a completed refusal, and 1 means invalid input or failed proof reconstruction, with no partial result on stdout. Argument-usage errors use argparse's exit 2.

The manifest has exactly `schema`, `chain_id`, `code_block`, and `members`, as shown in `zto-imd-manifest.json`. Each of its 1–16 members has a unique printable `role`, unique nonzero `target`, and `review_digest`. The digest is Ethereum Keccak-256 of the Code Review **normalized review**, serialized as ASCII JSON with sorted keys and compact separators. It commits to the complete path, measured slots and age limit. Programmatic callers can compute it with `code_set.digest(code_set.review_tool.validate_review(review))` after selecting their review; the shipped manifest is example data, not a review approval. The output also commits to the normalized manifest (members sorted by target). Evidence order does not affect the result.

Every invocation reconstructs every raw state proof; a saved success summary cannot substitute for a bundle. Evidence must exactly cover the target set, each actual target must match its review and manifest member, and every proved block number **and hash** must match the manifest block. Replacing a review with a more permissive age limit changes its digest and refuses the set. Every member still inherits Code Review's exact identity, age and unproven beacon routing checks. This version anchors the original code block directly; it does not accept later ancestry checkpoints.

The worker must independently trust the manifest, its reviews, the reference height and the separately supplied anchor. A copied observed hash exercises equality only. Acceptance does not certify contract semantics, dependency completeness, proxy routing behavior, inter-contract compatibility, consensus/finality, unchanged code between blocks, current code, or authorization to transact. The tool makes no network requests, reads only explicit workspace JSON inputs (each at most 100,000 bytes), rejects duplicate keys and resolved paths outside the workspace, and does not sign or send anything.

Validation:

```sh
python3 -B -m unittest discover -s line-3/tools/code-set -p 'test_*.py' -v
```

All **17 tests passed** locally. They cover real proof replay, exact-set omissions/duplicates, swapped targets, review replacement, age boundaries, mixed-block evidence, corrupt proofs, wrong anchors, JSON/path limits and CLI exits. Synthetic header mutations are explicitly test data; no fabricated header is presented as a real chain observation.
