"""The mocked cases isolate glue rules; the demo case replays real evidence."""
import copy
import unittest
from unittest.mock import patch

import swap_code_context as tool


class SwapCodeContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = tool.demo_inputs()

    def test_real_saved_evidence_refuses_cross_block_handoff(self):
        result = tool.assess(*self.inputs)
        self.assertEqual(result['decision'], 'refuse')
        self.assertEqual(result['swap_review_status'], 'accepted')
        self.assertEqual(result['code_set_decision'], 'refuse')
        self.assertIn('pool-and-code-block-differ', result['reasons'])
        self.assertEqual(result['usable_bounds'], [])

    def test_aligned_accepted_upstream_results_release_bounds(self):
        snapshot, report, policy, manifest, members, _, _ = self.inputs
        swap = tool.zto_review.review(snapshot, report, policy)
        accepted = {
            'decision': 'accept-set-identity', 'code_block': copy.deepcopy(swap['block']),
            'members': [{'target': tool.zto_review.sizes.path.z.ZTO},
                        {'target': tool.zto_review.sizes.path.z.IMD}],
            'reasons': [], 'manifest_digest': 'synthetic-glue-test-only'}
        with patch.object(tool.code_set, 'evaluate', return_value=accepted):
            result = tool.assess(snapshot, report, policy, manifest, members,
                                 policy['reference_block'], 'synthetic-glue-test-only')
        self.assertEqual(result['decision'], 'coherent')
        self.assertEqual(len(result['usable_bounds']), 2)

    def test_missing_token_refuses_even_if_upstream_accepts(self):
        snapshot, report, policy, manifest, members, _, _ = self.inputs
        swap = tool.zto_review.review(snapshot, report, policy)
        accepted = {
            'decision': 'accept-set-identity', 'code_block': copy.deepcopy(swap['block']),
            'members': [{'target': tool.zto_review.sizes.path.z.ZTO}],
            'reasons': [], 'manifest_digest': 'synthetic-glue-test-only'}
        with patch.object(tool.code_set, 'evaluate', return_value=accepted):
            result = tool.assess(snapshot, report, policy, manifest, members,
                                 policy['reference_block'], 'synthetic-glue-test-only')
        self.assertEqual(result['decision'], 'refuse')
        self.assertIn('zto-or-imd-code-missing', result['reasons'])
        self.assertEqual(result['usable_bounds'], [])


if __name__ == '__main__':
    unittest.main()
