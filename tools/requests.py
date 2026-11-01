#!/usr/bin/env python3
"""Move new term requests into results/current-job.md and print the job for the term translator."""
import argparse
import os
import sys
from pathlib import Path

from store import Store

ROOT = Path(__file__).resolve().parents[1]
REQUESTS = ROOT / 'results' / 'requested-terms.md'
JOB = ROOT / 'results' / 'current-job.md'


def read_lines(path):
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def next_job(finished, requests=REQUESTS, job=JOB, store=None):
    pending = read_lines(job)
    if pending and not finished:
        return 'resume', pending
    if finished:
        unfinished = [run['term'] for run in (store or Store()).open_runs()]
        if unfinished:
            raise ValueError('open runs remain: ' + ', '.join(unfinished) +
                             "; approve each, or discard it on the user's request")
    if requests.exists():
        # One rename takes the whole file: a line appended meanwhile cannot fall between read and clear.
        os.replace(requests, job)
        requests.touch()
    else:
        job.write_text('', encoding='utf-8')
    return 'new', read_lines(job)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('next', help='print the unfinished job, or start the next one from new requests')
    p.add_argument('--finished', action='store_true', help='the current job is done and may be replaced')
    args = parser.parse_args(argv)
    try:
        state, lines = next_job(args.finished)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    print(f'{state}: {len(lines)}')
    for line in lines:
        print(line)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
