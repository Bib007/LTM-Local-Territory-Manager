"""Read-only GitHub release discovery for the installed LTM channel and platform.

No account, territory data, local paths or credentials are sent to GitHub.
An absent/unreachable release feed is deliberately silent, not an update error.
"""
import json
import platform
import re
import sys
import threading
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

REPOSITORY = 'https://github.com/Bib007/LTM-Local-Territory-Manager'
RELEASES = REPOSITORY + '/releases'
FEED = 'https://api.github.com/repos/Bib007/LTM-Local-Territory-Manager/releases?per_page=100'
VERSION_RE = re.compile(r'^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-beta\.(0|[1-9]\d*))?$')


def version_key(value):
    """Numeric version ordering, including beta.10 > beta.9 and stable > beta."""
    if not isinstance(value, str):
        return None
    match = VERSION_RE.fullmatch(value)
    if not match:
        return None
    major, minor, patch, beta = match.groups()
    return (int(major), int(minor), int(patch), float('inf') if beta is None else int(beta))


def track_for(home_assistant=False, system=None, server_mode=False):
    if home_assistant:
        return 'home-assistant'
    system = sys.platform if system is None else system
    if system == 'darwin':
        return 'macos-server' if server_mode else 'macos-app'
    if system == 'win32':
        return 'windows-server' if server_mode else 'windows-app'
    return 'other'


def asset_names(track, version, machine=''):
    """Only exact filenames of documented, independent release tracks."""
    names = []
    if track == 'macos-app':
        arch = ('AppleSilicon' if machine.lower() in ('arm64', 'aarch64') else
                'Intel' if machine.lower() in ('x86_64', 'amd64') else None)
        if arch:
            names.append('LTM-macOS-v' + version + '-' + arch + '.dmg')
    if track == 'windows-app':
        names.append('LTM-Windows-v' + version + '-Setup.exe')
    prefix = {
        'home-assistant': 'LTM-Home-Assistant',
        'macos-app': 'LTM-macOS-app', 'macos-server': 'LTM-macOS-server',
        'windows-app': 'LTM-Windows-app', 'windows-server': 'LTM-Windows-server',
        'other': 'LTM',
    }[track]
    names.append(prefix + '-v' + version + '.zip')
    return names


def select_release(releases, installed, track, machine=''):
    """Return only a newer published release of the same Stable/Beta channel."""
    current = version_key(installed)
    if current is None or not isinstance(releases, list):
        return None
    beta = '-beta.' in installed
    choices = []
    for release in releases:
        if not isinstance(release, dict) or release.get('draft') is not False:
            continue
        if release.get('prerelease') is not beta or not release.get('published_at'):
            continue
        tag = release.get('tag_name')
        if not isinstance(tag, str) or not tag.startswith('v'):
            continue
        version = tag[1:]
        key = version_key(version)
        if key is None or key <= current or ('-beta.' in version) != beta:
            continue
        # Never trust an unverified URL returned by a remote document.
        if release.get('html_url') != RELEASES + '/tag/' + quote(tag, safe=''):
            continue
        choices.append((key, version, tag, release))
    if not choices:
        return None
    _, version, tag, release = max(choices, key=lambda choice: choice[0])
    download = None
    for wanted in asset_names(track, version, machine):
        for asset in release.get('assets', []):
            if not isinstance(asset, dict) or asset.get('name') != wanted:
                continue
            expected = RELEASES + '/download/' + quote(tag, safe='') + '/' + quote(wanted, safe='')
            if (asset.get('browser_download_url') == expected and
                    asset.get('state') == 'uploaded' and
                    isinstance(asset.get('size'), int) and asset['size'] > 0):
                download = expected
                break
        if download:
            break
    return {
        'version': version, 'channel': 'beta' if beta else 'stable',
        'platform': track, 'file_available': bool(download),
        'url': download or RELEASES,
    }


def published_releases():
    # Fixed HTTPS endpoint; never include cookies, tokens or local application data.
    request = Request(FEED, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'LTM-read-only-release-check',
    })
    with urlopen(request, timeout=4) as response:
        if response.status != 200:
            raise OSError('GitHub release feed unavailable')
        raw = response.read(8000001)
    if len(raw) > 8000000:
        raise ValueError('Release feed exceeded size limit')
    return json.loads(raw)


class UpdateChecker:
    def __init__(self, version, *, home_assistant=False, system=None,
                 machine=None, server_mode=False, fetcher=published_releases,
                 clock=time.monotonic):
        self.version = version
        self.track = track_for(home_assistant, system, server_mode)
        self.machine = platform.machine() if machine is None else machine
        self.fetcher = fetcher
        self.clock = clock
        self.until = -1
        self.result = None
        self.pending = False
        self.lock = threading.Lock()

    def _refresh(self):
        try:
            result = select_release(self.fetcher(), self.version, self.track, self.machine)
            ttl = 3600
        except (OSError, ValueError, TypeError, KeyError):
            # Offline/rate-limited/invalid feed: keep the rest of LTM unaffected.
            result, ttl = None, 300
        with self.lock:
            self.result = result
            self.until = self.clock() + ttl
            self.pending = False

    def check(self):
        # profile_scope holds an accounts permission lock during this GET.
        # Never perform an external network request while that lock is held.
        with self.lock:
            if self.clock() >= self.until and not self.pending:
                self.pending = True
                threading.Thread(target=self._refresh, daemon=True).start()
            return {'checking': True} if self.pending else self.result
