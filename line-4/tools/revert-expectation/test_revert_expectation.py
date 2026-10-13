"""Focused refusal checks; mutations of real evidence below are synthetic."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import revert_expectation as tool


class RefusalTests(unittest.TestCase):
    def setUp(self):
        self.obs = tool.returns.read_json(tool.HERE.parent / 'call-rehearsal' / 'zto-revert-observation.json')
        self.policy = tool.returns.read_json(tool.HERE / 'zto-expectation.json')

    def verdict(self):
        return tool.evaluate(self.obs, self.policy)['verdict']

    def raw(self, value):
        self.obs['outcome']['error']['data'] = value

    def test_real_zto_demo(self):
        self.assertEqual(self.verdict(), 'match')

    def test_missing_exact_bytes(self):
        self.policy['expect'] = {'kind': 'revert_bytes', 'data': '0x'}
        self.assertEqual(self.verdict(), 'inconclusive')

    def test_explicit_empty_revert(self):
        self.raw('0x')
        self.policy['expect'] = {'kind': 'revert_bytes', 'data': '0x'}
        self.assertEqual(self.verdict(), 'match')

    def test_transport_failure(self):
        self.obs['outcome']['error'] = {'code': -32000, 'message': 'historical state unavailable'}
        self.assertEqual(self.verdict(), 'inconclusive')

    def test_return_is_mismatch_even_malformed_bool(self):
        self.obs.update(returns='bool', outcome={'result': '0x'})
        self.assertEqual(self.verdict(), 'mismatch')

    def test_exact_custom_bytes(self):
        self.raw('0xAABBCCDD')
        self.policy['expect'] = {'kind': 'revert_bytes', 'data': '0xaabbccdd'}
        self.assertEqual(self.verdict(), 'match')
        self.raw('0xaabbccde')
        self.assertEqual(self.verdict(), 'mismatch')

    def test_nonstring_revert_data(self):
        self.raw({'data': '0x'})
        self.policy['expect'] = {'kind': 'revert_bytes', 'data': '0x'}
        self.assertEqual(self.verdict(), 'inconclusive')

    def test_panic_canonical(self):
        self.policy['expect'] = {'kind': 'panic_code', 'code': '0x11'}
        self.raw('0x4e487b71' + format(17, '064x'))
        self.assertEqual(self.verdict(), 'match')
        self.raw('0x4e487b71' + format(17, '064x') + '00')
        self.assertEqual(self.verdict(), 'mismatch')

    def test_error_string_unicode(self):
        self.policy['expect'] = {'kind': 'error_string', 'reason': '拒否'}
        raw = '0x08c379a0' + format(32, '064x') + format(6, '064x') + '拒否'.encode().hex() + '00' * 26
        self.raw(raw)
        self.assertEqual(self.verdict(), 'match')
        self.raw(raw[:-2] + '01')
        self.assertEqual(self.verdict(), 'mismatch')

    def test_empty_error_string(self):
        self.policy['expect'] = {'kind': 'error_string', 'reason': ''}
        self.raw('0x08c379a0' + format(32, '064x') + '00' * 32)
        self.assertEqual(self.verdict(), 'match')

    def test_context_fields(self):
        for key, changed in [('data', '0xfffffffe'), ('value', '0x1'),
                             ('to', tool.core.TOKENS['IMD']), ('from', tool.core.TOKENS['ZTO'])]:
            with self.subTest(key=key):
                p = copy.deepcopy(self.policy)
                p['call'][key] = changed
                self.assertEqual(tool.evaluate(self.obs, p)['verdict'], 'inconclusive')
        for key, changed in [('number', '0x18f88c6'), ('timestamp', '0x6ace3258'),
                             ('hash', '0x' + '12' * 32)]:
            with self.subTest(key=key):
                p = copy.deepcopy(self.policy)
                p['block'][key] = changed
                self.assertEqual(tool.evaluate(self.obs, p)['verdict'], 'inconclusive')

    def test_single_cannot_satisfy_witness(self):
        self.policy['evidence'] = 'witness'
        self.assertEqual(self.verdict(), 'inconclusive')

    def pair(self):
        second = copy.deepcopy(self.obs)
        second['source'] = tool.core.ENDPOINTS[1]
        self.policy['evidence'] = 'witness'
        return {'schema': tool.witness.SCHEMA, 'observations': [self.obs, second]}

    def test_witness_missing_bytes(self):
        self.assertEqual(tool.evaluate(self.pair(), self.policy)['verdict'], 'inconclusive')

    def test_witness_agreed_and_conflicting_reverts(self):
        self.raw('0xaabbccdd')
        self.policy['expect'] = {'kind': 'revert_bytes', 'data': '0xaabbccdd'}
        pair = self.pair()
        self.assertEqual(tool.evaluate(pair, self.policy)['verdict'], 'match')
        pair['observations'][1]['outcome']['error']['data'] = '0xaabbccde'
        self.assertEqual(tool.evaluate(pair, self.policy)['verdict'], 'inconclusive')

    def test_bad_predicates(self):
        for value in [{'kind':'reported_revert','data':'0x'}, {'kind':'panic_code','code':'0x01'},
                      {'kind':'panic_code','code':'0x'+ 'f'*65}, {'kind':'error_string','reason':9},
                      {'kind':'error_string','reason':'x'*32001}, {'kind':'revert_bytes','data':'0x1'},
                      {'kind':'anything'}]:
            with self.subTest(value=str(value)[:80]), self.assertRaises(ValueError):
                tool.predicate(value)

    def test_unknown_and_bad_schema_fields(self):
        for patch in [{'extra': 1}, {'schema': 'call-expectation-v1'}, {'chain_id': True}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                tool.evaluate(self.obs, dict(self.policy, **patch))

    def test_json_duplicate_nonfinite_and_oversize(self):
        with tempfile.TemporaryDirectory(dir=tool.HERE) as directory:
            path = Path(directory) / 'input.json'
            for data in ['{"a":1,"a":2}', '{"a":NaN}', ' ' * 95001]:
                path.write_text(data)
                with self.assertRaises(ValueError):
                    tool.returns.read_json(path)

    def test_outside_path_refused_before_open(self):
        with self.assertRaises(ValueError):
            tool.returns.read_json(Path.cwd().parent / 'outside.json')

    def test_cli_all_exits(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(tool.main(['demo']), 0)
            with tempfile.TemporaryDirectory(dir=tool.HERE) as directory:
                evidence, policy = Path(directory) / 'obs.json', Path(directory) / 'policy.json'
                policy.write_text(json.dumps(self.policy))
                for outcome, code in [({'result':'0x'}, 1),
                                      ({'error':{'code':-32000,'message':'unavailable'}}, 2)]:
                    self.obs['outcome'] = outcome
                    evidence.write_text(json.dumps(self.obs))
                    self.assertEqual(tool.main(['check', str(evidence), str(policy)]), code)
                policy.write_text('{}')
                self.assertEqual(tool.main(['check', str(evidence), str(policy)]), 2)


if __name__ == '__main__':
    unittest.main()
