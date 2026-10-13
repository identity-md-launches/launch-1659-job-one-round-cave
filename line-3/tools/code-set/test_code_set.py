"""Real-evidence replay plus adversarial exact-set and CLI boundaries."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import code_set as tool
from code_set_demo import inputs

HERE = Path(__file__).resolve().parent


class SetTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.evidence = inputs()
        self.height = int(self.manifest['code_block']['number'], 16)
        # Observed fixture hash, NOT an independently trusted anchor.
        self.observed_hash = self.manifest['code_block']['hash']

    def evaluate(self, **changes):
        args = dict(manifest=self.manifest, evidence=self.evidence,
                    as_of_block=self.height, anchor_hash=self.observed_hash)
        args.update(changes)
        return tool.evaluate(**args)

    def test_real_set_without_independent_anchor_refuses(self):
        result = self.evaluate(anchor_hash=None)
        self.assertEqual(result['decision'], 'refuse')
        self.assertEqual(result['member_count'], 2)
        self.assertTrue(all(m['review_result']['state_inclusion_verified'] for m in result['members']))
        self.assertTrue(all(m['member_reasons'] == ['missing-caller-anchor'] for m in result['members']))

    def test_explicit_hash_equality_is_not_authentication(self):
        result = self.evaluate()
        self.assertEqual(result['decision'], 'accept-set-identity')
        self.assertFalse(result['anchor_authenticity_verified'])
        self.assertFalse(result['consensus_verified'])
        self.assertTrue(all(m['review_result']['anchor_hash_matched'] for m in result['members']))

    def test_manifest_and_evidence_order_do_not_change_result(self):
        baseline = self.evaluate()
        self.manifest['members'].reverse()
        self.evidence.reverse()
        self.assertEqual(baseline, self.evaluate())

    def test_omitted_or_extra_member_never_passes(self):
        with self.assertRaisesRegex(ValueError, 'missing manifest evidence'):
            self.evaluate(evidence=self.evidence[:1])
        self.manifest['members'] = self.manifest['members'][:1]
        with self.assertRaisesRegex(ValueError, 'unexpected evidence target'):
            self.evaluate()

    def test_duplicate_evidence_never_substitutes_for_missing_member(self):
        with self.assertRaisesRegex(ValueError, 'duplicate evidence target'):
            self.evaluate(evidence=[self.evidence[0], self.evidence[0]])

    def test_duplicate_roles_or_normalized_targets_refused(self):
        self.manifest['members'][1]['role'] = self.manifest['members'][0]['role']
        with self.assertRaisesRegex(ValueError, 'duplicate manifest'):
            self.evaluate()
        self.manifest, _ = inputs()
        self.manifest['members'][1]['target'] = '0x' + self.manifest['members'][0]['target'][2:].upper()
        with self.assertRaisesRegex(ValueError, 'duplicate manifest'):
            self.evaluate()

    def test_review_replacement_cannot_relax_age(self):
        self.evidence[0][1]['max_age_blocks'] += 100
        result = self.evaluate()
        self.assertEqual(result['decision'], 'refuse')
        self.assertIn('manifest-review-digest-mismatch', result['reasons'][0]['reasons'])

    def test_review_hash_swap_refused(self):
        self.manifest['members'][0]['review_digest'] = self.manifest['members'][1]['review_digest']
        result = self.evaluate()
        self.assertEqual(result['decision'], 'refuse')
        self.assertIn('manifest-review-digest-mismatch', result['reasons'][0]['reasons'])

    def test_swapped_bundles_refused_even_at_same_block(self):
        swapped = [(self.evidence[1][0], self.evidence[0][1]),
                   (self.evidence[0][0], self.evidence[1][1])]
        result = self.evaluate(evidence=swapped)
        self.assertEqual(result['decision'], 'refuse')
        self.assertTrue(all('manifest-target-mismatch' in r['reasons'] for r in result['reasons']))

    def test_different_manifest_block_refused(self):
        self.manifest['code_block']['number'] = hex(self.height - 1)
        result = self.evaluate()
        self.assertEqual(result['decision'], 'refuse')
        self.assertTrue(all('manifest-code-block-mismatch' in r['reasons'] for r in result['reasons']))

    def test_mixed_header_evidence_cannot_form_one_snapshot(self):
        # Synthetic header mutation over real trie fixtures; never called real chain evidence.
        bundle = self.evidence[1][0]
        proof = tool.review_tool.proof
        fields = proof.rlp_decode(proof.hex_bytes(bundle['header_rlp']))
        fields[8] = proof.integer_bytes(self.height + 1)
        fields[11] = proof.integer_bytes(proof.scalar(fields[11]) + 12)
        encoded = proof.rlp_encode(fields)
        bundle['header_rlp'] = '0x' + encoded.hex()
        bundle['observation']['block'] = {'number': hex(self.height + 1),
                                          'hash': tool.lens.digest(encoded)}
        result = self.evaluate(as_of_block=self.height + 1, anchor_hash=None)
        self.assertEqual(result['decision'], 'refuse')
        mismatches = [r for r in result['reasons'] if 'manifest-code-block-mismatch' in r['reasons']]
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]['target'], tool.lens.IMD)
        with self.assertRaises(ValueError):
            self.evaluate(as_of_block=self.height + 1)

    def test_age_bound_and_future_reference(self):
        self.assertEqual(self.evaluate(as_of_block=self.height + 8)['decision'], 'accept-set-identity')
        result = self.evaluate(as_of_block=self.height + 9)
        self.assertTrue(all('code-evidence-too-old' in r['reasons'] for r in result['reasons']))
        for height in (self.height - 1, True, -1, 1.5, 2**64):
            with self.subTest(height=height), self.assertRaises(ValueError):
                self.evaluate(as_of_block=height)

    def test_altered_proof_and_wrong_anchor_never_emit_verdict(self):
        with self.assertRaises(ValueError):
            self.evaluate(anchor_hash=tool.lens.digest(b'wrong anchor'))
        self.evidence[0][0]['proofs'][0]['accountProof'].pop()
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_manifest_schema_and_bounds(self):
        for key, value in [('schema', 'other'), ('chain_id', True), ('chain_id', 8453),
                           ('members', []), ('members', self.manifest['members'] * 9)]:
            manifest = copy.deepcopy(self.manifest)
            manifest[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.evaluate(manifest=manifest)
        for role in ('', ' leading', 'line\nfeed', 'é', 'x' * 65):
            manifest = copy.deepcopy(self.manifest)
            manifest['members'][0]['role'] = role
            with self.subTest(role=role), self.assertRaises(ValueError):
                self.evaluate(manifest=manifest)
        self.manifest['allow_missing'] = True
        with self.assertRaisesRegex(ValueError, 'extra manifest'):
            self.evaluate()

    def test_unknown_member_field_rejected(self):
        self.manifest['members'][0]['trusted'] = True
        with self.assertRaisesRegex(ValueError, 'extra manifest member'):
            self.evaluate()

    def test_json_reader_refuses_duplicates_oversize_and_workspace_escape(self):
        scratch = Path.cwd() / 'test/scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        read = tool.review_tool.ancestry.read_json
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            path = Path(directory) / 'input.json'
            path.write_text('{"schema":1,"schema":2}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON'):
                read(path)
            path.write_bytes(b' ' * 100001)
            with self.assertRaisesRegex(ValueError, 'exceeds 100000'):
                read(path)
            path.unlink()
            path.symlink_to(Path.cwd().parent / 'not-read')
            with self.assertRaisesRegex(ValueError, 'inside workspace'):
                read(path)

    def test_cli_refusal_acceptance_error_and_no_partial_json(self):
        base = [sys.executable, '-B', str(HERE / 'code_set.py'),
                '--manifest', str(HERE / 'zto-imd-manifest.json'),
                '--as-of-block', str(self.height)]
        for token in ('zto', 'imd'):
            base += ['--member', str(HERE.parent / 'code-proof' / (token + '-proof.json')),
                     str(HERE.parent / 'code-review' / (token + '-review.json'))]
        for extra, expected in [([], 3), (['--anchor-hash', self.observed_hash], 0),
                                (['--anchor-hash', tool.lens.digest(b'wrong')], 1)]:
            run = subprocess.run(base + extra, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, expected, run.stderr)
            if expected == 1:
                self.assertEqual(run.stdout, '')
            else:
                self.assertEqual(json.loads(run.stdout)['decision'],
                                 'refuse' if expected == 3 else 'accept-set-identity')


if __name__ == '__main__':
    unittest.main()
