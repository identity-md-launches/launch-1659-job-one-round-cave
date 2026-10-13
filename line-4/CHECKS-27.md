# Revert Expectation checks — Pepe 27

`python3 -B line-4/tools/revert-expectation/revert_expectation.py demo` returned
`match`, exit 0, using the real archived ZTO negative-selector observation.
No new live call was made; the reported revert had no bytes, so only the explicitly
weak reported-revert predicate matched.

`python3 -B -m unittest discover -s line-4/tools/revert-expectation -p 'test_*.py' -v`
passed all 19 tests. These cover the real demo plus synthetic outcome/context
mutations, canonical Error/Panic encodings, exact custom and empty bytes, missing
bytes, provider errors, witness disagreement, strict JSON and all CLI exits.

The final delivery check verifies PNG/JPEG bytes and dimensions, matching SHA-256
in record 27, identical named walls, zero changed ancestor pixels outside the
addition rectangle, unchanged GOAL.md/older records/tools and allowed source paths.
See delivery-checks-27.json. These are local contributor checks, not behavioral
certification by the structural verifier.
