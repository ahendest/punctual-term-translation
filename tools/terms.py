#!/usr/bin/env python3
"""Term translation, independent comparison and explicit human approval into the shared store."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from store import Store, encode, knowledge_module, require


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    sub.add_parser('list')
    p = sub.add_parser('ask'); p.add_argument('--term', required=True); p.add_argument('--at', required=True)
    p.add_argument('--project'); p.add_argument('--term-id'); p.add_argument('--reconsider', action='store_true')
    p = sub.add_parser('approved'); p.add_argument('--id', required=True)
    for name in ('show', 'context', 'review-packet', 'canvas', 'discard'):
        p = sub.add_parser(name); p.add_argument('--run', required=True)
        if name == 'context': p.add_argument('--nearby', action='store_true')
    p = sub.add_parser('submit'); p.add_argument('--run', required=True); p.add_argument('--input', required=True)
    p = sub.add_parser('review'); p.add_argument('--run', required=True); p.add_argument('--choice', required=True)
    p = sub.add_parser('approve'); p.add_argument('--run', required=True); p.add_argument('--digest', required=True)
    p.add_argument('--user-text-file', required=True); p.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    store = Store()
    try:
        command = args.command
        if command == 'check': result = store.knowledge().integrity()
        elif command == 'list': result = store.open_runs()
        elif command == 'ask': result = store.ask(args.term, args.at, args.project, args.term_id, args.reconsider)
        elif command == 'approved': result = store.approved(args.id)
        elif command == 'show': result = dict(store.load(args.run), status=store.status(store.load(args.run)))
        elif command == 'context': result = store.context(args.run, args.nearby)
        elif command == 'review-packet': result = store.review_packet(args.run)
        elif command == 'canvas': result = {'canvas': store.canvas_refresh(args.run)}
        elif command == 'discard': result = store.discard(args.run)
        elif command == 'submit': result = store.submit(args.run, load(args.input))
        elif command == 'review': result = store.review(args.run, args.choice)
        else:
            # Approval covers the wording the user read: the visible block must match the stored proposal.
            require(store.canvas_current(args.run) == store.canvas_block(store.load(args.run)),
                    'results.md differs from the stored proposal; change wording through a new submit, '
                    'or run canvas --run ' + args.run + ' to restore the block, then read it again before approving')
            result = store.approve(args.run, args.digest, Path(args.user_text_file).read_text(encoding='utf-8'), args.dry_run)
        print(encode({'ok': True, 'result': result}))
        return 0
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError, knowledge_module().KnowledgeError) as error:
        print(encode({'ok': False, 'error': str(error)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
