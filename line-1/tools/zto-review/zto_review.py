#!/usr/bin/env python3
"""Recompute a saved ZTO Sizes report under an explicit caller review policy."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'zto-sizes'))
import zto_sizes as sizes

HERE = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT = sizes.DEFAULT_SNAPSHOT
DEFAULT_REPORT = HERE.parent / 'zto-sizes' / 'demo-report.json'
POLICY_KEYS = {'schema', 'snapshot_sha256', 'block_number', 'block_hash',
               'reference_block', 'max_age_blocks', 'input_token', 'amounts',
               'slippage_bps', 'max_spot_loss_bps'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def unsupported_number(value):
    raise ValueError('JSON floats and nonfinite numbers are unsupported: ' + value)


def read_json(filename):
    # Reuse the ancestor workspace boundary, but use an unambiguous JSON parser.
    with sizes.path.z.workspace_file(filename).open('rb') as handle:
        data = handle.read(100001)
    sizes.path.z.require(len(data) <= 100000, 'JSON exceeds 100 KB')
    return json.loads(data, object_pairs_hook=pairs, parse_float=unsupported_number,
                      parse_constant=unsupported_number)


def differences(actual, expected, prefix='$'):
    """Bounded, type-sensitive diagnostics; do not echo untrusted report values."""
    if type(actual) is not type(expected):
        return [prefix + ': type mismatch']
    if isinstance(expected, dict):
        result = []
        if set(actual) != set(expected):
            result.append(prefix + ': keys mismatch')
        for key in sorted(set(actual) & set(expected)):
            result.extend(differences(actual[key], expected[key], prefix + '.' + key))
            if len(result) >= 40:
                break
        return result[:40]
    if isinstance(expected, list):
        if len(actual) != len(expected):
            return [prefix + ': length mismatch']
        result = []
        for index, (a, e) in enumerate(zip(actual, expected)):
            result.extend(differences(a, e, prefix + '[' + str(index) + ']'))
            if len(result) >= 40:
                break
        return result[:40]
    return [] if actual == expected else [prefix + ': value mismatch']


def review(observation, report, policy):
    require = sizes.path.z.require
    require(type(policy) is dict and set(policy) == POLICY_KEYS,
            'policy must contain exactly the documented fields')
    require(policy['schema'] == 'zto-review-policy-v1', 'wrong policy schema')
    require(isinstance(policy['snapshot_sha256'], str) and
            re.fullmatch('[0-9a-f]{64}', policy['snapshot_sha256']) is not None,
            'snapshot_sha256 must be a lowercase canonical JSON SHA-256')
    require(isinstance(policy['block_hash'], str) and
            re.fullmatch('0x[0-9a-f]{64}', policy['block_hash']) is not None,
            'block_hash must be a lowercase bytes32')
    for key in ('block_number', 'reference_block', 'max_age_blocks'):
        require(type(policy[key]) is int and 0 <= policy[key] < 1 << 64,
                key + ' must be a nonnegative uint64 integer')
    sizes.bps(policy['slippage_bps'], 'slippage bps')
    if policy['max_spot_loss_bps'] is not None:
        sizes.bps(policy['max_spot_loss_bps'], 'maximum spot loss bps')
    require(policy['input_token'] in ('ZTO', 'IMD'), 'input must be ZTO or IMD')
    require(type(policy['amounts']) is list and 1 <= len(policy['amounts']) <= 20
            and all(type(a) is str and len(a) <= 100 for a in policy['amounts']),
            'amounts must be 1..20 short decimal strings')
    # Validate pool evidence even when its identity fails the caller anchor.
    state, _, _ = sizes.path.decode(observation)
    din = state['decimals'][1 if policy['input_token'] == 'ZTO' else 0]
    for amount in policy['amounts']:
        raw = sizes.path.z.parse_amount(amount, din)
        require(raw < 1 << 127, 'input must fit positive int128 pool delta')
    block = observation['base']['block']
    number = int(block['number'], 16)
    age = policy['reference_block'] - number
    reasons = []
    if digest(observation) != policy['snapshot_sha256']:
        reasons.append('snapshot_digest_mismatch')
    if number != policy['block_number'] or block['hash'] != policy['block_hash']:
        reasons.append('block_anchor_mismatch')
    if age < 0:
        reasons.append('snapshot_after_reference')
    elif age > policy['max_age_blocks']:
        reasons.append('snapshot_too_old_for_policy')
    output = {'schema': 'zto-review-result-v1', 'status': 'refuse',
              'chain_id': 1, 'pool_id': sizes.path.z.POOL,
              'snapshot_sha256': digest(observation), 'policy_sha256': digest(policy),
              'report_sha256': digest(report), 'block': block,
              'reference_block': policy['reference_block'], 'age_blocks': age,
              'reasons': reasons, 'differences': [], 'usable_bounds': [],
              'limitations': [
                  'Caller policy is a trust input; the bundled demo policy is historical demonstration only.',
                  'Digest pins supplied evidence, not Ethereum consensus or provider authenticity.',
                  'Age is relative to the supplied reference block, not a live freshness check.',
                  'Reuses ZTO Sizes/Path arithmetic; this is not an independent numerical implementation.',
                  'Planning bounds do not enforce receipts or simulate settlement, transfers, gas or MEV.']}
    if reasons:
        return output
    expected = sizes.compare_sizes(observation, policy['amounts'], policy['input_token'],
                                   policy['slippage_bps'], policy['max_spot_loss_bps'])
    output['differences'] = differences(report, expected)
    if output['differences']:
        reasons.append('report_recomputation_mismatch')
        return output
    for row in expected['candidates']:
        if row['status'] == 'candidate':
            output['usable_bounds'].append({
                'input_token': expected['input_token'], 'output_token': expected['output_token'],
                'requested_input_raw': row['requested_input_raw'],
                'estimated_output_raw': row['estimate']['output_raw'],
                'minimum_output_raw': row['minimum_output_raw']})
    if not output['usable_bounds']:
        reasons.append('no_usable_bound')
    else:
        output['status'] = 'accepted'
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true', help='offline historical real-pool review')
    mode.add_argument('--policy', help='caller-supplied workspace review policy JSON')
    parser.add_argument('--snapshot', help='workspace ZTO Path snapshot JSON')
    parser.add_argument('--report', help='workspace ZTO Sizes report JSON')
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if args.snapshot or args.report:
                raise ValueError('--demo cannot be combined with custom files')
            policy_file, snapshot_file, report_file = HERE / 'demo-policy.json', DEFAULT_SNAPSHOT, DEFAULT_REPORT
        else:
            if not args.snapshot or not args.report:
                raise ValueError('--policy requires --snapshot and --report')
            policy_file, snapshot_file, report_file = args.policy, args.snapshot, args.report
        result = review(read_json(snapshot_file), read_json(report_file), read_json(policy_file))
        result['mode'] = 'historical_demo' if args.demo else 'caller_policy'
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['status'] == 'accepted' else 2
    except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError,
            RecursionError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
