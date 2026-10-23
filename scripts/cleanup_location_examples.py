#!/usr/bin/env python3
"""One-off W61 cleanup. Never print or persist the original location examples.

Dry-run is the default. Originals stay in an ephemeral work directory; only a
redacted report may be uploaded. Published version numbers and user data stay
unchanged. Apply requires the exact repository and an unchanged develop head.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

REPOSITORY = 'Bib007/LTM-Local-Territory-Manager'
REMOTE = 'https://github.com/' + REPOSITORY + '.git'
SEED = 'v1.11.1'


def command(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Provider/process errors can contain source snippets or authenticated URLs.
        raise RuntimeError('Cleanup command failed: ' + args[0])
    return result.stdout


def git(root, *args):
    return command(['git', *args], root)


class Rules:
    def __init__(self, seed):
        match = re.search(rb'placeholder="(Skriv fx ([^"\r\n]+))"', seed)
        if not match:
            raise ValueError('The seed is already clean or its field format changed. Audit before retrying.')
        self.phrase, road = match.groups()
        parts = road.split(b' ', 1)
        if len(parts) != 2 or parts[0].lower() != b'gammel':
            raise ValueError('Unexpected seed format. No changes made.')
        self.road = re.compile(rb'\b(gammel|gl\.?)\s+' + re.escape(parts[1]) + rb'\b', re.I)
        self.numbers = re.compile(rb'(<input\b[^>]*\bname="(postcode|from|to)"[^>]*?)placeholder="\d+"')

    def clean(self, raw, hashes=None):
        if b'\0' in raw:
            return raw
        try:
            raw.decode('utf-8')
        except UnicodeError:
            return raw
        # Remove obsolete translation entries before replacing their example text.
        result = re.sub(rb'^\s*"' + re.escape(self.phrase) + rb'"\s*:[^\n]*\n', b'', raw, flags=re.M)
        result = result.replace(b'placeholder="' + self.phrase + b'"', b'placeholder="Vejnavn"')
        result = result.replace(b"I18n.attribute('placeholder',\"" + self.phrase + b'\")',
                                b"I18n.attribute('placeholder',\"Vejnavn\")")
        translated = raw.lstrip().startswith((b"'use strict';", b'"use strict";')) and b'I18n.attribute(' in raw

        def number(match):
            label = {b'postcode': b'Postnummer', b'from': b'Fra', b'to': b'Til'}[match[2]]
            attribute = b"${I18n.attribute('placeholder',\"" + label + b'\")}' if translated else b'placeholder="' + label + b'"'
            return match[1] + attribute

        result = self.numbers.sub(number, result)
        # Preserve abbreviation/normalisation test coverage using invented records.
        result = self.road.sub(lambda m: m[1] + b' Fiktivvej', result)
        if hashes and re.fullmatch(rb'(?:[a-f0-9]{64}  [^\r\n]+\n)+', result):
            result = b''.join(hashes.get(line[:64], line[:64]) + line[64:]
                              for line in result.splitlines(keepends=True))
        return result

    def remains(self, raw):
        return bool(self.road.search(raw) or self.phrase in raw or self.numbers.search(raw))


def transform_payloads(payloads, rules):
    hashes = {}
    for _ in range(8):
        cleaned = {name: rules.clean(raw, hashes) for name, raw in payloads.items()}
        updated = {hashlib.sha256(raw).hexdigest().encode(): hashlib.sha256(cleaned[name]).hexdigest().encode()
                   for name, raw in payloads.items() if raw != cleaned[name]}
        if updated == hashes:
            return cleaned
        hashes = updated
    raise ValueError('Nested checksum manifests did not converge.')


def verify_manifests(payloads):
    for name, raw in payloads.items():
        if PurePosixPath(name).name != 'SHA256SUMS.txt':
            continue
        parent = str(PurePosixPath(name).parent)
        parent = '' if parent == '.' else parent + '/'
        for line in raw.decode().splitlines():
            digest, relative = line.split('  ', 1)
            candidates = [parent + relative, parent + 'distrikt/' + relative]
            target = next((p for p in candidates if p in payloads), None)
            if target is None or hashlib.sha256(payloads[target]).hexdigest() != digest:
                raise ValueError('An internal archive checksum did not verify.')


def clean_zip(source, destination, rules, version):
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        if len(infos) > 5000 or len({i.filename for i in infos}) != len(infos):
            raise ValueError('Unexpected archive structure.')
        if sum(i.file_size for i in infos) > 500_000_000:
            raise ValueError('Unexpected archive size.')
        for info in infos:
            path = PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename:
                raise ValueError('Unsafe archive member.')
        payloads = {i.filename: archive.read(i) for i in infos}
    cleaned = transform_payloads(payloads, rules)
    if any(rules.remains(raw) for raw in cleaned.values()):
        raise ValueError('Location examples remain in an archive.')
    verify_manifests(cleaned)
    servers = [raw for name, raw in cleaned.items() if name.endswith('/app/server.py')]
    if not servers or any(not re.search(rb"VERSION\s*=\s*['\"]" + re.escape(version.encode()) + rb"['\"]", raw) for raw in servers):
        raise ValueError('The original archive version was not preserved.')
    with zipfile.ZipFile(destination, 'w') as archive:
        for info in infos:
            archive.writestr(info, cleaned[info.filename])
    with zipfile.ZipFile(destination) as archive:
        if archive.namelist() != list(payloads) or any(archive.read(n) != cleaned[n] for n in cleaned):
            raise ValueError('Written archive did not verify.')
    changed = [name for name in payloads if payloads[name] != cleaned[name]]
    if not changed:
        destination.write_bytes(source.read_bytes())
    return changed


def refs(root):
    lines = git(root, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads', 'refs/tags').decode().splitlines()
    return dict(line.split(' ', 1) for line in lines)


def blobs(root):
    ids = dict.fromkeys(line.split(b' ', 1)[0] for line in git(root, 'rev-list', '--objects', '--all').splitlines())
    proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for ident in ids:
            proc.stdin.write(ident + b'\n'); proc.stdin.flush()
            header = proc.stdout.readline().split()
            if len(header) != 3:
                raise ValueError('Unexpected Git object.')
            raw = proc.stdout.read(int(header[2]))
            if proc.stdout.read(1) != b'\n':
                raise ValueError('Incomplete Git object.')
            if header[1] == b'blob':
                yield ident, raw
    finally:
        proc.stdin.close(); proc.stdout.close()
        if proc.wait() != 0:
            raise ValueError('Git object audit failed.')


def rewrite(root, rules):
    import git_filter_repo as filtering
    originals = dict(blobs(root))
    cleaned = transform_payloads(originals, rules)
    hashes = {hashlib.sha256(raw).hexdigest().encode(): hashlib.sha256(cleaned[name]).hexdigest().encode()
              for name, raw in originals.items() if raw != cleaned[name]}
    changed = sum(originals[n] != cleaned[n] for n in originals)
    previous = Path.cwd()
    try:
        os.chdir(root)
        options = filtering.FilteringOptions.parse_args(['--force', '--prune-empty', 'never', '--prune-degenerate', 'never'])
        filtering.RepoFilter(options, blob_callback=lambda blob, _metadata: setattr(blob, 'data', rules.clean(blob.data, hashes)),
                             message_callback=lambda message: rules.clean(message)).run()
    finally:
        os.chdir(previous)
    if any(rules.remains(raw) for _ident, raw in blobs(root)):
        raise ValueError('Examples remain reachable in Git history.')
    return changed


def gh_json(*args):
    return json.loads(command(['gh', 'api', *args]))


def remote_refs(root):
    raw = git(root, 'ls-remote', '--heads', '--tags', REMOTE).decode().splitlines()
    return {ref: ident for ident, ref in (line.split('\t') for line in raw) if not ref.endswith('^{}')}


def run(work, expected_head, apply=False):
    if os.environ.get('GITHUB_REPOSITORY', REPOSITORY) != REPOSITORY:
        raise ValueError('Wrong repository.')
    if work.exists():
        raise ValueError('Use a new empty work directory.')
    work.mkdir(parents=True)
    root = work / 'mirror.git'
    git(work, 'clone', '--bare', REMOTE, str(root))
    # Bare clone includes all heads; explicitly fetch every published tag.
    git(root, 'fetch', 'origin', '+refs/tags/*:refs/tags/*')
    before = refs(root)
    pull_refs = git(root, 'ls-remote', REMOTE, 'refs/pull/*/head').decode().splitlines()
    if before.get('refs/heads/develop') != expected_head:
        raise ValueError('Develop moved. Audit again before applying.')
    rules = Rules(git(root, 'show', SEED + ':distrikt/app/road-search.js'))
    releases = gh_json('repos/' + REPOSITORY + '/releases?per_page=100')
    if len(releases) >= 100:
        raise ValueError('Release pagination needs explicit review.')
    allowed = {'v1.11.0', 'v1.11.1'} | {'v1.12.0-beta.' + str(i) for i in range(1, 30)}
    if {r['tag_name'] for r in releases} != allowed:
        raise ValueError('The release inventory changed. Review scope before applying.')
    staged = []
    for release in releases:
        if release.get('immutable') or release.get('draft'):
            raise ValueError('A release cannot be updated using the reviewed procedure.')
        tag = release['tag_name']
        if 'refs/tags/' + tag not in before:
            raise ValueError('Release tag missing.')
        assets = release['assets']
        zips = [a['name'] for a in assets if a['name'].endswith('.zip')]
        if len(zips) != 1 or {a['name'] for a in assets} != {zips[0], zips[0] + '.sha256'}:
            raise ValueError('Unexpected release assets.')
        original, clean = work / tag / 'original', work / tag / 'clean'
        original.mkdir(parents=True); clean.mkdir()
        command(['gh', 'release', 'download', tag, '--repo', REPOSITORY, '--dir', str(original)])
        archive = original / zips[0]
        old_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if (original / (zips[0] + '.sha256')).read_text().split()[0] != old_digest:
            raise ValueError('Original archive checksum did not match.')
        changed = clean_zip(archive, clean / zips[0], rules, tag[1:])
        new_digest = hashlib.sha256((clean / zips[0]).read_bytes()).hexdigest()
        checksum = clean / (zips[0] + '.sha256')
        checksum.write_text(new_digest + '  ' + zips[0] + '\n')
        staged.append({'tag': tag, 'id': release['id'], 'archive': str(clean / zips[0]),
                       'checksum': str(checksum), 'changed_files': changed,
                       'original_sha256': old_digest, 'clean_sha256': new_digest})
    count = rewrite(root, rules)
    after = refs(root)
    if set(before) != set(after):
        raise ValueError('A branch or tag was lost during cleanup.')
    report = {'repository': REPOSITORY, 'status': 'staged, not published', 'changed_blobs': count,
              'refs': {name: {'before': before[name], 'after': after[name]} for name in before},
              'releases': [{k: v for k, v in row.items() if k not in ('archive', 'checksum')} for row in staged],
              'published_assets': [],
              'pull_refs': [line.split('\t')[1] for line in pull_refs],
              'remaining': 'GitHub cached commit views, PR refs and other people\'s clones need separate handling.'}
    report_path = work / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    if not apply:
        return report
    # No release changes until every package and the entire rewritten history verify.
    if remote_refs(root) != before:
        raise ValueError('A remote branch/tag moved. Nothing published.')
    for row in staged:
        if not row['changed_files']:
            continue
        command(['gh', 'release', 'upload', row['tag'], row['archive'], row['checksum'], '--repo', REPOSITORY, '--clobber'])
        download = work / row['tag'] / 'verify'
        download.mkdir()
        command(['gh', 'release', 'download', row['tag'], '--repo', REPOSITORY, '--dir', str(download)])
        for key in ('archive', 'checksum'):
            original = Path(row[key])
            if (download / original.name).read_bytes() != original.read_bytes():
                raise ValueError('Published release files did not verify. Git refs remain unchanged.')
        report['published_assets'].append(row['tag'])
        report_path.write_text(json.dumps(report, indent=2) + '\n')
    if remote_refs(root) != before:
        raise ValueError('Remote refs moved during asset cleanup. Do not overwrite them.')
    # Exact leases and an atomic update: no ref deletion and no concurrent work lost.
    push = ['push', '--atomic', REMOTE]
    push += ['--force-with-lease=' + ref + ':' + before[ref] for ref in sorted(before)]
    push += [after[ref] + ':' + ref for ref in sorted(before)]
    git(root, *push)
    if remote_refs(root) != after:
        raise ValueError('Published branch/tag refs did not verify.')
    report['status'] = 'assets and Git refs published and verified; release metadata updates pending'
    report['metadata_updated'] = []
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    for row in staged:
        commit = git(root, 'rev-parse', row['tag'] + '^{commit}').decode().strip()
        gh_json('--method', 'PATCH', 'repos/' + REPOSITORY + '/releases/' + str(row['id']),
                '-f', 'target_commitish=' + commit)
        report['metadata_updated'].append(row['tag'])
        report_path.write_text(json.dumps(report, indent=2) + '\n')
    report['status'] = 'published and verified; GitHub cache/PR purge still outstanding'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        report = run(args.work.resolve(), args.expected_head, args.apply)
        print(report['status'])
        print('Releases:', len(report['releases']), '| Refs:', len(report['refs']))
    except Exception as error:
        # Never include underlying process/provider/source text in public CI logs.
        print('Cleanup stopped:', type(error).__name__, '| Review the redacted report and current refs before retrying.')
        raise SystemExit(1) from None
