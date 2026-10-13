#!/usr/bin/env python3
"""Replay real ZTO then IMD, without manufacturing an independent trust anchor."""
import json
from pathlib import Path
import code_set as tool


def inputs():
    here = Path(__file__).resolve().parent
    read = tool.review_tool.ancestry.read_json
    return read(here / 'zto-imd-manifest.json'), [
        (read(here.parent / 'code-proof' / (token + '-proof.json')),
         read(here.parent / 'code-review' / (token + '-review.json')))
        for token in ('zto', 'imd')]


def main():
    manifest, evidence = inputs()
    height = int(manifest['code_block']['number'], 16)
    result = tool.evaluate(manifest, evidence, height + 8)
    assert result['decision'] == 'refuse' and result['member_count'] == 2
    assert all(m['member_reasons'] == ['missing-caller-anchor'] for m in result['members'])
    assert all(m['review_result']['identity_matches'] for m in result['members'])
    print(json.dumps({'demonstration_passed': True,
                     'example_manifest_and_reviews_are_not_endorsements': True,
                     'independent_anchor_available': False, 'result': result}, indent=2))


if __name__ == '__main__':
    main()
