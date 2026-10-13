#!/usr/bin/env python3
"""Check an explicit expected refusal against historical Ethereum call evidence."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'call-expectation'))
import call_expectation as returns

core, changes, witness = returns.core, returns.changes, returns.witness
HERE = Path(__file__).resolve().parent
SCHEMA = 'revert-expectation-v1'
LIMITS = ('Checks unauthenticated historical provider claims, not EVM execution proofs. '
          'A reported revert may be misclassified by an RPC. A match proves no access control, '
          'state effects, safety, canonicality, provider independence or future refusal. '
          'reported_revert requires no bytes and makes no claim about the reason. Nothing sent.')


def predicate(value):
    core.require(isinstance(value, dict), 'expect must be an object')
    kind = value.get('kind')
    if kind == 'reported_revert':
        core.require(set(value) == {'kind'}, 'reported_revert accepts only kind')
        return {'kind': kind}, None
    if kind == 'revert_bytes':
        core.require(set(value) == {'kind', 'data'}, 'revert_bytes requires data')
        raw = core.data(value['data'])
        return {'kind': kind, 'data': raw}, raw
    if kind == 'error_string':
        core.require(set(value) == {'kind', 'reason'} and isinstance(value['reason'], str),
                     'error_string requires a UTF-8 reason')
        body = value['reason'].encode('utf-8')
        core.require(len(body) <= 32000, 'reason exceeds byte limit')
        raw = ('0x08c379a0' + format(32, '064x') + format(len(body), '064x') +
               body.hex() + '00' * ((-len(body)) % 32))
        return {'kind': kind, 'reason': value['reason']}, raw
    if kind == 'panic_code':
        core.require(set(value) == {'kind', 'code'}, 'panic_code requires code')
        number = core.quantity(value['code'])
        return {'kind': kind, 'code': hex(number)}, '0x4e487b71' + format(number, '064x')
    raise ValueError('unsupported revert expectation kind')


def policy(value):
    core.require(isinstance(value, dict) and set(value) == returns.POLICY_KEYS,
                 'expectation must have exactly the documented fields')
    core.require(value['schema'] == SCHEMA, 'unsupported expectation schema')
    expected, raw = predicate(value['expect'])
    # Reuse the existing exact-call/block/mode validator, without changing it.
    temporary = dict(value, schema=returns.SCHEMA, expect={'kind': 'return_bytes', 'data': '0x'})
    normalized = returns.policy(temporary)
    normalized.update(schema=SCHEMA, expect=expected)
    return normalized, raw


def evaluate(evidence, expectation):
    wanted, expected_bytes = policy(expectation)
    if isinstance(evidence, dict) and evidence.get('schema') == witness.SCHEMA:
        core.require(set(evidence) == {'schema', 'observations'}, 'invalid witness fields')
        pair = witness.witness(evidence['observations'])
        observations, mode, agreement = evidence['observations'], 'witness', pair['verdict']
    else:
        changes.validate(evidence)
        observations, mode, agreement = [evidence], 'single', 'not_requested'
    results = [changes.validate(obs)['result'] for obs in observations]
    report = {'schema': SCHEMA, 'verdict': 'inconclusive', 'reason': '',
              'expected': wanted, 'evidence': mode, 'agreement': agreement,
              'results': results, 'limits': LIMITS}

    def finish(verdict, reason):
        report.update(verdict=verdict, reason=reason)
        return report

    if mode != wanted['evidence']:
        return finish('inconclusive', 'evidence mode differs from expectation')
    for obs in observations:
        if core.transaction(obs['call']) != wanted['call']:
            return finish('inconclusive', 'evidence is for a different call')
        if core.header(obs['block']) != wanted['block']:
            return finish('inconclusive', 'evidence is for a different block')
    if agreement in ('disagree', 'inconclusive'):
        return finish('inconclusive', 'witnesses disagree or lack comparable execution evidence')
    result = results[0]
    # Any valid result field establishes a provider-reported return, even if its
    # bytes do not fit the saved ABI interpretation. Such a call did not revert.
    if 'result' in observations[0]['outcome']:
        return finish('mismatch', 'provider returned rather than reverted')
    if result['status'] != 'reverted':
        return finish('inconclusive', 'RPC failure is not evidence of a revert')
    if expected_bytes is None:
        return finish('match', 'provider reported a revert; no reason or bytes required')
    execution = changes.execution_evidence(observations[0], result)
    if execution is None or execution[1] is None:
        return finish('inconclusive', 'expected revert bytes are missing or malformed')
    match = execution[1] == expected_bytes
    return finish('match' if match else 'mismatch',
                  'exact revert bytes satisfy expectation' if match else 'revert bytes differ')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='offline real ZTO negative-selector refusal')
    check = sub.add_parser('check', help='check EVIDENCE EXPECTATION offline')
    check.add_argument('evidence')
    check.add_argument('expectation')
    args = parser.parse_args(argv)
    try:
        expected = returns.read_json(HERE / 'zto-expectation.json' if args.command == 'demo'
                                     else args.expectation)
        policy(expected)
        evidence = returns.read_json(HERE.parent / 'call-rehearsal' / 'zto-revert-observation.json'
                                     if args.command == 'demo' else args.evidence)
        result = evaluate(evidence, expected)
        print(json.dumps(result, indent=2, allow_nan=False))
        return returns.exit_code(result)
    except (ValueError, KeyError, TypeError, OSError, RecursionError, core.RPCError) as exc:
        print(json.dumps({'schema': SCHEMA, 'verdict': 'inconclusive', 'error': str(exc)}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
