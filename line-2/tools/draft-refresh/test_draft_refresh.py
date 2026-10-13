import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import draft_refresh as refresh


class DraftRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = refresh.gate.load(refresh.witness_tool.DEFAULT_OBSERVATION)
        cls.policy = refresh.gate.load(refresh.witness_tool.DEFAULT_POLICY)
        cls.candidate = refresh.drafts.build(cls.before, cls.policy)['drafts'][0]
        cls.after = refresh.gate.load(refresh.DEFAULT_AFTER)

    def test_real_recheck_keeps_zero_balance_permission_visible(self):
        result = refresh.compare(self.candidate, self.before, self.policy, self.after)
        self.assertEqual(result['status'], 'same_active_permission')
        self.assertEqual(result['current_balance_raw'], '0')
        self.assertEqual(result['current_allowance_raw'], self.candidate['allowance_raw'])
        self.assertFalse(result['complete_wallet_audit'])

    def test_cleared_permission_is_distinguished(self):
        after = copy.deepcopy(self.after)
        after['raw']['allowances'][0]['result'] = '0x' + '0' * 64
        result = refresh.compare(self.candidate, self.before, self.policy, after)
        self.assertEqual(result['status'], 'permission_cleared')
        self.assertFalse(result['allowance_unchanged'])

    def test_changed_pair_or_old_block_is_refused(self):
        after = copy.deepcopy(self.after)
        after['query']['owner'] = '0xbadb536e95f450a4978445d7a0e363a42ec37eb4'
        with self.assertRaises(ValueError):
            refresh.compare(self.candidate, self.before, self.policy, after)
        after = copy.deepcopy(self.after)
        after['block'] = copy.deepcopy(self.before['observations'][0]['block'])
        after['query']['from_block'] = after['query']['to_block'] = refresh.lens.quantity(after['block']['number'])
        with self.assertRaises(ValueError):
            refresh.compare(self.candidate, self.before, self.policy, after)

    def test_changed_draft_is_refused(self):
        candidate = copy.deepcopy(self.candidate)
        candidate['transaction']['data'] = candidate['transaction']['data'][:-1] + '1'
        with self.assertRaises(ValueError):
            refresh.compare(candidate, self.before, self.policy, self.after)


if __name__ == '__main__':
    unittest.main()
