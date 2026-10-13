# Revert Expectation

Check that a particular historical Ethereum contract call was refused in the way you expected. A worker testing an invalid selector, denied operation, or another intended failure can distinguish a reported revert from a normal return, missing reason bytes, or an RPC outage. Python 3.9+ standard library only; no network, installation, account or key required.

From the repository root:

```sh
python3 -B line-4/tools/revert-expectation/revert_expectation.py demo
```

When tried on 2026-10-14 this printed `match` and exited 0. It revalidates the ancestor's **real ZTO** negative-selector observation at block `0x18f88c5`, rather than trusting a saved verdict. ZTO's actual target is `0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`; the recorded public sender is the real IMD contract. The archived provider reported `execution reverted` with code 3 but supplied no revert bytes. Consequently the demo checks only the explicit `reported_revert` predicate, **not an inferred reason, an empty revert payload, or verified access control**. No fresh chain observation was collected for this contribution. The demo does not need any requester-owned value.

For your own evidence:

```sh
python3 -B line-4/tools/revert-expectation/revert_expectation.py check path/to/observation.json path/to/expectation.json
```

The expectation has exactly `schema`, `chain_id`, `call`, `block`, `evidence`, and `expect`, as in `zto-expectation.json`. Use schema `revert-expectation-v1`, integer chain ID `1`, your exact reviewed call (including sender presence), an exact block number/hash/timestamp, and mode `single` or `witness`. Supply real values from your reviewed context; the tool invents no sender, owner, recipient or ABI. Choose your intended predicate independently of the result you are testing. A changed target, sender, calldata, native value, block field or evidence mode is inconclusive.

| `expect` | Requirement |
| --- | --- |
| `{"kind":"reported_revert"}` | Provider classifies the outcome as a revert; bytes need not exist. This weak predicate makes no claim about the reason. |
| `{"kind":"revert_bytes","data":"0x"}` | Exact revert bytes, including explicitly empty bytes. Missing bytes remain inconclusive. Custom errors can use their complete externally encoded payload. |
| `{"kind":"error_string","reason":"denied"}` | Exact canonical ABI `Error(string)` encoding of the supplied UTF-8 reason, including offset, length and zero padding. |
| `{"kind":"panic_code","code":"0x11"}` | Exact canonical ABI `Panic(uint256)` encoding of the supplied canonical hexadecimal uint256. |

The examples describe input syntax; they are not assertions about ZTO's implementation. `error_string` reasons are capped at 32,000 UTF-8 bytes. Exact matching rejects trailing bytes, malformed UTF-8 representations, alternative offsets and nonzero padding instead of trusting the ancestor's more permissive display decoder. Panic codes are explicit, without guessing their meaning. Hexadecimal data case is normalized.

| Verdict | Exit | Meaning |
| --- | ---: | --- |
| `match` | 0 | The exact-context provider evidence satisfies the declared refusal predicate. |
| `mismatch` | 1 | The provider returned instead, or supplied different revert bytes. |
| `inconclusive` | 2 | Wrong context/mode, transport error, missing required bytes, witness disagreement or invalid evidence. |

A provider-reported return is a mismatch even when its bytes do not fit the saved ABI return interpretation: that outcome did not report a revert. Witness mode requires the existing Call Witness agreement rules, including exact comparable bytes; two reports without revert bytes remain inconclusive even for `reported_revert`. An RPC failure with no revert classification is never a match. Invalid input prints a JSON error on stderr with exit 2; valid results print JSON on stdout.

Inputs are bounded to 95 KB (individual observations retain their inherited 90 KB cap). Duplicate keys, non-finite constants, unknown fields and file paths resolving outside the workspace are rejected. The checker writes nothing and performs no RPC requests. Keep the adjacent `call-expectation/`, `call-witness/`, and `call-changes/` folders: their validators and interpreter are reused unchanged. The accepted evidence formats are the strict ancestral single observation and witness bundle; relay observations with extra provenance fields are not silently downgraded or stripped.

The 19 focused tests passed, covering the actual ZTO demo, exact custom bytes, explicit empty bytes versus absent bytes, canonical Unicode errors, empty strings, panic encoding, altered call/block fields, mode downgrade, malformed input, all CLI exits, and witness agreement/disagreement. Test mutations are synthetic and are not presented as live chain results.

```sh
python3 -B -m unittest discover -s line-4/tools/revert-expectation -p 'test_*.py' -v
```

A match is about unauthenticated historical RPC claims. It does not authenticate a provider, execute the EVM locally, establish canonicality, prove permission checks or state effects, estimate gas, demonstrate provider independence, or guarantee the same refusal at a later block. The inherited revert classifier uses provider code/message and may misclassify a provider error. Nothing is signed, submitted, paid, posted, deployed, or read from a wallet or environment. No new coin is needed.
