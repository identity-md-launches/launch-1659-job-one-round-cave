#!/usr/bin/env python3
"""Offline exact-set gate for reviewed Ethereum code at one proved block."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code-review'))
import code_review as review_tool

lens = review_tool.lens
require = lens.require
keys = review_tool.keys
MAX_MEMBERS = 16


def digest(document):
    return lens.digest(json.dumps(document, sort_keys=True,
                                  separators=(',', ':')).encode('ascii'))


def normalize_manifest(document):
    keys(document, ('schema', 'chain_id', 'code_block', 'members'), 'manifest')
    require(document['schema'] == 'code-set-v1' and type(document['chain_id']) is int
            and document['chain_id'] == 1, 'wrong manifest schema or chain')
    block = review_tool.ancestry.block_identity(document['code_block'])
    members = document['members']
    require(isinstance(members, list) and 1 <= len(members) <= MAX_MEMBERS,
            'manifest must contain 1 to 16 members')
    targets, roles, normalized = set(), set(), []
    for member in members:
        keys(member, ('role', 'target', 'review_digest'), 'manifest member')
        role = member['role']
        require(isinstance(role, str) and 1 <= len(role) <= 64
                and role.isascii() and all(32 <= ord(c) <= 126 for c in role)
                and role == role.strip(), 'role must be 1 to 64 printable ASCII characters')
        target = lens.address(member['target'])
        require(target not in targets and role not in roles, 'duplicate manifest target or role')
        targets.add(target)
        roles.add(role)
        normalized.append({'role': role, 'target': target,
                           'review_digest': lens.fixed_hex(member['review_digest'], 32)})
    return {'schema': 'code-set-v1', 'chain_id': 1, 'code_block': block,
            'members': sorted(normalized, key=lambda m: m['target'])}


def evaluate(manifest, evidence, as_of_block, anchor_hash=None):
    """Evidence is a list of (raw proof bundle, exact review) pairs, never summaries."""
    manifest = normalize_manifest(manifest)
    as_of_block = review_tool.uint64(as_of_block, 'as_of_block')
    require(isinstance(evidence, list) and 1 <= len(evidence) <= MAX_MEMBERS,
            'evidence must contain 1 to 16 pairs')
    expected = {m['target']: m for m in manifest['members']}
    supplied = {}
    for pair in evidence:
        require(isinstance(pair, (tuple, list)) and len(pair) == 2, 'invalid evidence pair')
        bundle, document = pair
        checked_review = review_tool.validate_review(document)
        target = checked_review['target']
        require(target in expected, 'unexpected evidence target: ' + target)
        require(target not in supplied, 'duplicate evidence target: ' + target)
        supplied[target] = (bundle, checked_review)
    require(set(supplied) == set(expected), 'missing manifest evidence member')
    results, reasons = [], []
    for member in manifest['members']:
        bundle, document = supplied[member['target']]
        # Reconstruct raw state proofs each time; embedded success claims grant no trust.
        result = review_tool.evaluate(bundle, document, as_of_block, anchor_hash)
        member_reasons = list(result['reasons'])
        if result['target'] != member['target']:
            member_reasons.append('manifest-target-mismatch')
        if result['code_block'] != manifest['code_block']:
            member_reasons.append('manifest-code-block-mismatch')
        if result['review_digest'] != member['review_digest']:
            member_reasons.append('manifest-review-digest-mismatch')
        if member_reasons:
            reasons.append({'role': member['role'], 'target': member['target'],
                            'reasons': member_reasons})
        results.append({'role': member['role'], 'target': member['target'],
                        'member_reasons': member_reasons, 'review_result': result})
    return {'schema': 'code-set-result-v1', 'chain_id': 1,
            'decision': 'refuse' if reasons else 'accept-set-identity',
            'manifest_digest': digest(manifest), 'code_block': manifest['code_block'],
            'as_of_block': as_of_block, 'member_count': len(results),
            'reasons': reasons, 'members': results,
            'anchor_authenticity_verified': False, 'consensus_verified': False,
            'scope': 'Exact manifest member set, reviewed identities and measured slots '
                     'at one proved historical block only. Caller must independently trust '
                     'the manifest, reviews and anchor. No semantic safety, completeness of '
                     'contract dependencies, inter-contract compatibility, code at today, '
                     'consensus, or authorization to transact is established.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, help='independently selected exact member manifest')
    parser.add_argument('--member', nargs=2, action='append', required=True,
                        metavar=('BUNDLE', 'REVIEW'), help='repeat for each raw proof/review pair')
    parser.add_argument('--as-of-block', type=int, required=True)
    parser.add_argument('--anchor-hash', help='separately supplied independently trusted block hash')
    args = parser.parse_args()
    try:
        require(len(args.member) <= MAX_MEMBERS, 'too many evidence pairs')
        read = review_tool.ancestry.read_json
        result = evaluate(read(args.manifest), [(read(b), read(r)) for b, r in args.member],
                          args.as_of_block, args.anchor_hash)
        print(json.dumps(result, indent=2))
        return 0 if result['decision'] == 'accept-set-identity' else 3
    except (ValueError, KeyError, TypeError, OSError, OverflowError, AttributeError,
            IndexError, RecursionError) as error:
        print('Code Set: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
