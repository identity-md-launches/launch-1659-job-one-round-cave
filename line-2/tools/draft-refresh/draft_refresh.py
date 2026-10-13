#!/usr/bin/env python3
"""Recheck one reviewed unsigned ZTO/IMD revoke draft against a later ERC-20 read."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'draft-witness'))
import draft_witness as witness_tool

drafts = witness_tool.drafts
gate = drafts.gate
lens = gate.lens
DEFAULT_AFTER = HERE / 'live-recheck.json'


def compare(candidate, before, policy, after):
    """Accept only an exact reviewed draft and one later exact-pair observation."""
    review = witness_tool.witness(candidate, before, policy)
    lens.require(review['matches_reviewed_draft'], 'draft does not match reviewed evidence and policy')
    old = gate.changes.flatten(before)
    fresh = lens.report(after)
    owner, spender = candidate['owner'], candidate['spender']
    lens.require(fresh['chain_id'] == old['chain_id'] and
                 fresh['token_address'] == old['token_address'],
                 'fresh read has a different chain or token')
    lens.require(fresh['discovery']['mode'] == 'explicit_pairs' and
                 fresh['discovery']['owner'] == owner and
                 fresh['discovery']['spenders'] == [spender] and
                 len(fresh['pairs']) == 1,
                 'fresh read must measure only the reviewed owner-spender pair')
    lens.require(fresh['block_number'] > old['block_number'],
                 'fresh read must be at a later block')
    row = fresh['pairs'][0]
    allowance = int(row['allowance_raw'])
    limit = int(candidate['policy_limit_raw'])
    if allowance == 0:
        state = 'permission_cleared'
    elif allowance <= limit:
        state = 'within_reviewed_limit'
    elif row['allowance_raw'] == candidate['allowance_raw']:
        state = 'same_active_permission'
    else:
        state = 'changed_active_permission'
    return {
        'schema': 'allowance-draft-refresh-v1',
        'status': state,
        'reviewed_draft_exact_match': True,
        'token': fresh['token'],
        'token_address': fresh['token_address'],
        'owner': owner,
        'spender': spender,
        'previous_block_number': old['block_number'],
        'previous_block_hash': old['block_hash'],
        'current_block_number': fresh['block_number'],
        'current_block_hash': fresh['block_hash'],
        'current_block_time_utc': fresh['block_time_utc'],
        'current_source': fresh['source'],
        'previous_allowance_raw': candidate['allowance_raw'],
        'current_allowance_raw': row['allowance_raw'],
        'reviewed_limit_raw': candidate['policy_limit_raw'],
        'previous_balance_raw': candidate['balance_raw'],
        'current_balance_raw': row['balance_raw'],
        'allowance_unchanged': row['allowance_raw'] == candidate['allowance_raw'],
        'balance_unchanged': row['balance_raw'] == candidate['balance_raw'],
        'complete_wallet_audit': False,
        'limitations': [
            'Only this exact owner-spender pair is rechecked; unknown spenders remain unknown.',
            'Offline replay trusts saved RPC responses. Live mode checks the old block hash again.',
            'A later read does not authorize, sign, simulate, submit, or guarantee a transaction.',
            'Permit2, unused signatures, custom authorizations, and other tokens are not covered.',
        ],
    }


def capture_checked(endpoint, before, token, owner, spender, block_tag):
    """Read the old header and a new canonical hash-pinned pair in one bounded worker."""
    rpc = lens.RPC(endpoint)
    old = gate.changes.flatten(before)
    lens.require(rpc.call('eth_chainId', []) == '0x1', 'expected Ethereum chain 1')
    past = lens.header(rpc.call('eth_getBlockByNumber', [hex(old['block_number']), False]))
    lens.require(lens.quantity(past['number']) == old['block_number'] and
                 past['hash'] == old['block_hash'],
                 'reviewed block is no longer canonical or unavailable')
    observed = lens.capture(rpc, token, block_tag, 1, owner, [spender])
    lens.require(lens.quantity(observed['block']['number']) > old['block_number'],
                 'new observation must follow reviewed block')
    return observed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', help='reviewed raw observation or inventory')
    parser.add_argument('--policy', help='reviewed Permission Gate policy')
    parser.add_argument('--draft', help='one unsigned draft object from Approval Draft')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--after', help='later raw one-pair Allowance Lens observation')
    mode.add_argument('--live', action='store_true', help='read this pair at a later Ethereum block')
    parser.add_argument('--rpc', choices=sorted(lens.ENDPOINTS), default=lens.PUBLIC_RPC)
    parser.add_argument('--block', default='finalized', help='finalized, safe, latest, or decimal number')
    parser.add_argument('--timeout', type=float, default=45, help='total live-read deadline in seconds')
    args = parser.parse_args(argv)
    try:
        lens.require(all((args.before, args.policy, args.draft)) or
                     not any((args.before, args.policy, args.draft)),
                     'provide --before, --policy and --draft together')
        demonstration = not any((args.before, args.policy, args.draft, args.after, args.live))
        before = gate.load(args.before or witness_tool.DEFAULT_OBSERVATION)
        policy = gate.load(args.policy or witness_tool.DEFAULT_POLICY)
        candidate = (witness_tool.load_draft(args.draft) if args.draft else
                     drafts.build(before, policy)['drafts'][0])
        # Refuse an altered draft before making any network request.
        lens.require(witness_tool.witness(candidate, before, policy)['matches_reviewed_draft'],
                     'draft does not match reviewed evidence and policy')
        if args.live:
            tag = hex(int(args.block)) if args.block.isdecimal() else args.block
            after = lens.run_bounded(capture_checked,
                (args.rpc, before, before['observations'][0]['token']
                 if before.get('schema') == gate.changes.BUNDLE_SCHEMA else before['token'],
                 candidate['owner'], candidate['spender'], tag), timeout=args.timeout)
        else:
            lens.require(args.rpc == lens.PUBLIC_RPC and args.block == 'finalized' and
                         args.timeout == 45,
                         'RPC, block and timeout options require --live')
            after = gate.load(args.after or DEFAULT_AFTER)
        result = compare(candidate, before, policy, after)
        result['demonstration'] = demonstration
        print(json.dumps(result, indent=2))
        return 0 if result['status'] == 'same_active_permission' else 3
    except (ValueError, KeyError, TypeError, OSError, OverflowError, IndexError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
