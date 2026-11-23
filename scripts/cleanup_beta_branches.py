#!/usr/bin/env python3
"""One owner-authorized cleanup after the consolidated November 2026 beta.

Archive every exact branch head before atomically deleting the leased refs.
New or changed branches stop cleanup; the three permanent branches stay intact.
"""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PERMANENT = frozenset(('main', 'develop', 'beta'))
VERSION = '1.13.0-beta.3'
INTEGRATION = 'release/all-beta-prs-20261123'
ARCHIVE = 'archive/beta-20261123/'


def command(args):
    return subprocess.check_output(args, text=True).strip()


def plan(expected, current):
    if set(expected) & PERMANENT:
        raise ValueError('The cleanup manifest must never contain permanent branches')
    if set(current) - PERMANENT - set(expected) - {INTEGRATION}:
        raise ValueError('New branches appeared; review the manifest before cleanup')
    changed = [name for name, sha in expected.items()
               if name in current and current[name] != sha]
    if changed:
        raise ValueError('Branches changed since review: ' + ', '.join(changed))
    selected = {name: sha for name, sha in expected.items() if name in current}
    if INTEGRATION in current:
        selected[INTEGRATION] = current[INTEGRATION]
    return selected


def archive_and_delete(selected, run=command):
    if not selected:
        return
    # One atomic archive push must finish successfully before any deletion.
    run(['git', 'push', '--atomic', 'origin'] +
        [sha + ':refs/tags/' + ARCHIVE + name for name, sha in sorted(selected.items())])
    # Git's leases and atomic push close the read/delete race for every ref.
    run(['git', 'push', '--atomic'] +
        ['--force-with-lease=refs/heads/' + name + ':' + sha
         for name, sha in sorted(selected.items())] +
        ['origin'] + [':refs/heads/' + name for name in sorted(selected)])


def main():
    if os.environ.get('GITHUB_REF') != 'refs/heads/develop':
        raise ValueError('Cleanup is restricted to a verified develop release')
    version = command(['python3', '-c',
        "import sys;sys.path.insert(0,'scripts');import build_beta;print(build_beta.release.version())"])
    if version != VERSION:
        print('One-time branch cleanup does not apply to this release')
        return
    repo = os.environ['GITHUB_REPOSITORY']
    release = json.loads(command(['gh', 'release', 'view', 'v' + VERSION,
                                 '--repo', repo, '--json', 'targetCommitish,isPrerelease,assets']))
    revision = os.environ['GITHUB_SHA']
    if release['targetCommitish'] != revision or not release['isPrerelease']:
        raise ValueError('The immutable beta release does not match this checked commit')
    assets = {asset['name'] for asset in release['assets']}
    if not {'LTM-v' + VERSION + '.zip', 'LTM-HA-v' + VERSION + '.zip'} <= assets:
        raise ValueError('Both verified beta release packages must exist before cleanup')
    raw = command(['gh', 'api', '--paginate', 'repos/' + repo +
                   '/branches?per_page=100', '--jq', '.[] | [.name,.commit.sha] | @tsv'])
    current = dict(line.split('\t') for line in raw.splitlines())
    records = json.loads((ROOT / 'docs/maintenance/branches-20261123.json').read_text())
    selected = plan({row['name']: row['sha'] for row in records}, current)
    if INTEGRATION in selected:
        command(['git', 'merge-base', '--is-ancestor', selected[INTEGRATION], revision])
    archive_and_delete(selected)
    remaining = command(['gh', 'api', '--paginate', 'repos/' + repo +
                         '/branches?per_page=100', '--jq', '.[].name']).splitlines()
    if set(remaining) != PERMANENT:
        raise ValueError('Branch cleanup needs review: ' + ', '.join(remaining))
    print('Archived and removed %s branches; only main, develop and beta remain' % len(selected))


if __name__ == '__main__':
    main()
