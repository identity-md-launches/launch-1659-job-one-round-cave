"""Real evidence review, deliberate tampering, and refusal boundaries; offline."""
import contextlib
import copy
import io
import json
import unittest
from unittest.mock import Mock, patch

import zto_review as r


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs = r.read_json(r.DEFAULT_SNAPSHOT)
        cls.saved = r.read_json(r.DEFAULT_REPORT)
        cls.policy = r.read_json(r.HERE / 'demo-policy.json')

    def check(self, obs=None, report=None, policy=None):
        return r.review(self.obs if obs is None else obs,
                        self.saved if report is None else report,
                        self.policy if policy is None else policy)

    def test_real_report_accepts_only_complete_candidates(self):
        result = self.check()
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(len(result['usable_bounds']), 2)
        self.assertEqual(result['usable_bounds'][1]['minimum_output_raw'],
                         '1184169088029408336486')
        self.assertNotIn(str(10**27), [b['requested_input_raw'] for b in result['usable_bounds']])

    def test_changed_minimum_even_one_raw_unit_refused(self):
        report = copy.deepcopy(self.saved)
        report['candidates'][0]['minimum_output_raw'] = str(
            int(report['candidates'][0]['minimum_output_raw']) + 1)
        result = self.check(report=report)
        self.assertEqual(result['reasons'], ['report_recomputation_mismatch'])
        self.assertEqual(result['usable_bounds'], [])
        self.assertTrue(any('minimum_output_raw' in d for d in result['differences']))

    def test_partial_bound_injection_refused(self):
        report = copy.deepcopy(self.saved)
        report['candidates'][2]['status'] = 'candidate'
        report['candidates'][2]['minimum_output_raw'] = '1'
        self.assertEqual(self.check(report=report)['status'], 'refuse')

    def test_settings_not_taken_from_report(self):
        for key, value in [('slippage_bps', 200), ('input_token', 'IMD'),
                           ('amounts', ['1']), ('max_spot_loss_bps', 125)]:
            p = copy.deepcopy(self.policy)
            p[key] = value
            self.assertEqual(self.check(policy=p)['status'], 'refuse', key)

    def test_digest_binds_even_non_arithmetic_metadata(self):
        obs = copy.deepcopy(self.obs)
        obs['base']['source'] = 'https://eth.drpc.org'
        result = self.check(obs=obs)
        self.assertIn('snapshot_digest_mismatch', result['reasons'])
        self.assertEqual(result['usable_bounds'], [])

    def test_number_and_hash_anchors_checked(self):
        for key, value in [('block_number', self.policy['block_number'] + 1),
                           ('block_hash', '0x' + 'ab' * 32)]:
            p = copy.deepcopy(self.policy)
            p[key] = value
            self.assertIn('block_anchor_mismatch', self.check(policy=p)['reasons'])

    def test_age_exact_boundary_and_future_refusal(self):
        p = copy.deepcopy(self.policy)
        p['max_age_blocks'] = 10
        p['reference_block'] += 10
        self.assertEqual(self.check(policy=p)['status'], 'accepted')
        p['reference_block'] += 1
        self.assertIn('snapshot_too_old_for_policy', self.check(policy=p)['reasons'])
        p['reference_block'] = p['block_number'] - 1
        self.assertIn('snapshot_after_reference', self.check(policy=p)['reasons'])

    def test_matching_report_with_no_usable_bounds_refused(self):
        for amount in ('1000000000', '0.000000000000000001'):
            p = copy.deepcopy(self.policy)
            p['amounts'] = [amount]
            report = r.sizes.compare_sizes(self.obs, p['amounts'], 'ZTO', 100)
            result = self.check(report=report, policy=p)
            self.assertEqual(result['differences'], [])
            self.assertEqual(result['reasons'], ['no_usable_bound'])

    def test_reverse_direction_uses_real_quoter_output(self):
        p = copy.deepcopy(self.policy)
        p.update(input_token='IMD', amounts=['1000'])
        report = r.sizes.compare_sizes(self.obs, p['amounts'], 'IMD', 100)
        evidence = r.read_json(r.DEFAULT_SNAPSHOT.parent / 'quoter-check.json')
        case = next(c for c in evidence['results']
                    if c['input_token'] == 'IMD' and c['amount'] == '1000')
        observed_raw = r.sizes.path.z.words(case['raw_result'], 2)[0]
        result = self.check(report=report, policy=p)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['usable_bounds'][0]['estimated_output_raw'], str(observed_raw))

    def test_json_types_are_exact(self):
        report = copy.deepcopy(self.saved)
        report['chain_id'] = True
        self.assertEqual(self.check(report=report)['status'], 'refuse')
        report = copy.deepcopy(self.saved)
        report['candidates'][0]['estimate']['output_raw'] = int(
            report['candidates'][0]['estimate']['output_raw'])
        self.assertEqual(self.check(report=report)['status'], 'refuse')

    def test_invalid_policy_refused_before_review(self):
        for key, value in [('max_age_blocks', True), ('reference_block', -1),
                           ('slippage_bps', True), ('slippage_bps', 10000),
                           ('snapshot_sha256', 'bad'), ('block_hash', 'bad'),
                           ('amounts', []), ('amounts', ['0']), ('amounts', ['1e6'])]:
            p = copy.deepcopy(self.policy)
            p[key] = value
            with self.assertRaises(ValueError, msg=key):
                self.check(policy=p)
        p = copy.deepcopy(self.policy)
        p['unknown'] = 'field'
        with self.assertRaises(ValueError):
            self.check(policy=p)

    def test_wrong_pool_evidence_rejected(self):
        obs = copy.deepcopy(self.obs)
        obs['base']['initialize']['topics'][1] = '0x' + '11' * 32
        with self.assertRaises(ValueError):
            self.check(obs=obs)

    def test_ambiguous_json_and_oversize_refused(self):
        for payload in (b'{"x":1,"x":2}', b'{"x":{"y":1,"y":2}}',
                        b'{"x":NaN}', b'{"x":1.0}', b' ' * 100001):
            fake = Mock()
            fake.open.return_value = io.BytesIO(payload)
            with patch.object(r.sizes.path.z, 'workspace_file', return_value=fake):
                with self.assertRaises(ValueError):
                    r.read_json('unused.json')

    def test_key_order_and_whitespace_do_not_change_digest(self):
        self.assertEqual(r.digest(self.policy), r.digest(dict(reversed(list(self.policy.items())))))
        self.assertNotEqual(r.digest({'x': 1}), r.digest({'x': True}))

    def test_cli_is_offline_and_reports_invalid_arguments(self):
        with patch.object(r.sizes.path.z, 'RPC', side_effect=AssertionError('network forbidden')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(r.main(['--demo']), 0)
            self.assertEqual(json.loads(out.getvalue())['status'], 'accepted')
            for argv in (['--demo', '--report', 'x'], ['--policy', 'x']):
                with contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(r.main(argv), 1)
                self.assertIn('error', json.loads(err.getvalue()))
        with patch.object(r, 'review', return_value={'status': 'refuse'}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(['--demo']), 2)


if __name__ == '__main__':
    unittest.main()
