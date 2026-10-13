#!/usr/bin/env python3
"""Join a reviewed ZTO/IMD swap bound to proved token-code identities."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'line-1/tools/zto-review'))
sys.path.insert(0, str(ROOT / 'line-3/tools/code-set'))
import zto_review
import code_set

SCHEMA = 'swap-code-context-v1'


def reject_number(value):
    raise ValueError('floats and nonfinite numbers are unsupported: ' + value)


def load(filename):
    path = Path(filename).resolve()
    if not path.is_relative_to(Path.cwd().resolve()):
        raise ValueError('input must be inside the workspace')
    with path.open('rb') as handle:
        raw = handle.read(100001)
    if len(raw) > 100000:
        raise ValueError('input exceeds 100000 bytes')
    return json.loads(raw, object_pairs_hook=zto_review.pairs,
                      parse_float=reject_number, parse_constant=reject_number)


def block_id(value):
    return (int(value['number'], 16), value['hash'].lower())


def assess(snapshot, report, swap_policy, manifest, members, as_of_block, anchor_hash=None):
    """Revalidate raw evidence through both line tools; never trust saved verdicts."""
    swap = zto_review.review(snapshot, report, swap_policy)
    codes = code_set.evaluate(manifest, members, as_of_block, anchor_hash)
    code_targets = {member['target'] for member in codes['members']}
    token_targets = {zto_review.sizes.path.z.ZTO, zto_review.sizes.path.z.IMD}
    same_block = block_id(swap['block']) == block_id(codes['code_block'])
    same_reference = as_of_block == swap_policy['reference_block']
    both_tokens = token_targets <= code_targets
    reasons = []
    if swap['status'] != 'accepted': reasons.append('swap-review-refused')
    if codes['decision'] != 'accept-set-identity': reasons.append('code-set-refused')
    if not same_block: reasons.append('pool-and-code-block-differ')
    if not same_reference: reasons.append('reference-heights-differ')
    if not both_tokens: reasons.append('zto-or-imd-code-missing')
    result = {
        'schema': SCHEMA, 'decision': 'refuse' if reasons else 'coherent',
        'reasons': reasons, 'chain_id': 1,
        'pool_id': swap['pool_id'], 'pool_block': swap['block'],
        'code_block': codes['code_block'], 'reference_block': swap_policy['reference_block'],
        'code_as_of_block': as_of_block, 'same_block': same_block,
        'same_reference_height': same_reference, 'both_token_codes_present': both_tokens,
        'swap_review_status': swap['status'], 'swap_review_reasons': swap['reasons'],
        'usable_bounds': swap['usable_bounds'] if not reasons else [],
        'code_set_decision': codes['decision'], 'code_set_reasons': codes['reasons'],
        'snapshot_sha256': swap['snapshot_sha256'], 'swap_policy_sha256': swap['policy_sha256'],
        'manifest_digest': codes['manifest_digest'],
        'anchor_authenticity_verified': False, 'consensus_verified': False,
        'limits': ('Caller must independently select and trust the swap policy, code reviews, '
                   'manifest, reference height and code-block anchor. Matching historical '
                   'evidence is no execution, token-behavior, settlement, provider-authenticity '
                   'or future-liquidity guarantee. No wallet, key or transaction is used.')}
    return result


def demo_inputs():
    s = ROOT / 'line-1/tools'
    c = ROOT / 'line-3/tools'
    manifest = load(c / 'code-set/zto-imd-manifest.json')
    members = [(load(c / 'code-proof' / (token + '-proof.json')),
                load(c / 'code-review' / (token + '-review.json')))
               for token in ('zto', 'imd')]
    return (load(s / 'zto-path/observation.json'),
            load(s / 'zto-sizes/demo-report.json'),
            load(s / 'zto-review/demo-policy.json'), manifest, members, 26185288, None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='replay real saved evidence, expected to refuse')
    parser.add_argument('--snapshot')
    parser.add_argument('--report')
    parser.add_argument('--policy')
    parser.add_argument('--manifest')
    parser.add_argument('--member', nargs=2, action='append', metavar=('PROOF', 'REVIEW'))
    parser.add_argument('--as-of-block', type=int)
    parser.add_argument('--anchor-hash', help='independently trusted block hash supplied by caller')
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if any((args.snapshot, args.report, args.policy, args.manifest, args.member,
                    args.as_of_block is not None, args.anchor_hash)):
                raise ValueError('--demo takes no other inputs')
            inputs = demo_inputs()
        else:
            if not all((args.snapshot, args.report, args.policy, args.manifest,
                        args.member, args.as_of_block is not None)):
                raise ValueError('supply snapshot, report, policy, manifest, members and as-of-block')
            inputs = (load(args.snapshot), load(args.report), load(args.policy),
                      load(args.manifest), [(load(a), load(b)) for a, b in args.member],
                      args.as_of_block, args.anchor_hash)
        result = assess(*inputs)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['decision'] == 'coherent' else 2
    except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError,
            RecursionError, IndexError) as error:
        print(json.dumps({'schema': SCHEMA, 'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
