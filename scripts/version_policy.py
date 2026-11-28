#!/usr/bin/env python3
"""Guard Beta and independent Stable releases against divergent/reused versions.

The GitHub release jobs call 'verify' after fetching tags and origin/main.
Pure decision functions are intentionally testable without network/user data.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
FORMAT=re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-beta\.([1-9]\d*))?$")
LEGACY_STABLE=(1,12,35)  # One-time bridge: old Beta used 1.12.19-beta.N.
# Owner-approved report hotfix. Other versions keep the published Beta requirement.
REPORT_HOTFIX=(1,14,4)
REPORT_HOTFIX_BASE=(1,14,3)


@dataclass(frozen=True)
class Version:
    major:int
    minor:int
    patch:int
    beta:Optional[int]=None

    @property
    def base(self):
        return self.major,self.minor,self.patch

    def __str__(self):
        value=".".join(map(str,self.base))
        return value+(f"-beta.{self.beta}" if self.beta is not None else "")


def parse(value):
    match=FORMAT.fullmatch(value)
    if not match:
        raise ValueError("Version must be X.Y.Z or X.Y.Z-beta.N with N >= 1: "+value)
    parts=[int(p) if p is not None else None for p in match.groups()]
    return Version(*parts)


def next_bases(stable):
    major,minor,patch=stable.base
    return {(major,minor,patch+1),(major,minor+1,0),(major+1,0,0)}


def next_version(stable,change):
    major,minor,patch=stable.base
    changes={"fix":(major,minor,patch+1),"feature":(major,minor+1,0),"breaking":(major+1,0,0)}
    if change not in changes:raise ValueError("Choose fix, feature or breaking.")
    return Version(*changes[change],beta=1)


def tagged_versions(tags):
    result={}
    for tag in tags:
        if tag.startswith("v") and FORMAT.fullmatch(tag[1:]):
            result[tag]=parse(tag[1:])
    return result


def validate(channel,current,stable_baseline,tags,tag_shas,head,main_synced=True,source_matches=True):
    """Fail closed on stale, reused, skipped, or wrongly based release numbers."""
    current=parse(str(current)) if not isinstance(current,Version) else current
    stable_baseline=parse(str(stable_baseline)) if not isinstance(stable_baseline,Version) else stable_baseline
    if channel=="beta" and current.beta is None:raise ValueError("Beta must use X.Y.Z-beta.N.")
    if channel=="stable" and current.beta is not None:raise ValueError("Stable must use X.Y.Z without -beta.")
    known=tagged_versions(tags)
    current_tag="v"+str(current)
    if current_tag in known and tag_shas.get(current_tag)!=head:
        raise ValueError("Version already tagged for different code: "+current_tag)
    published_stable=[v for v in known.values() if v.beta is None]
    previous=max(published_stable,key=lambda v:v.base,default=None)
    if channel=="beta":
        if current.beta is None:raise ValueError("Beta must use X.Y.Z-beta.N.")
        if stable_baseline.beta is not None:raise ValueError("origin/main must have a Stable version.")
        if current.base not in next_bases(stable_baseline):
            raise ValueError("Beta must target the next fix, feature or breaking version after origin/main: "+str(stable_baseline))
        if not main_synced:
            raise ValueError("Beta is missing the latest main/Stable changes: merge main into develop first.")
        other=[v for v in known.values() if v.beta is not None and v.base>current.base]
        if other:raise ValueError("An already published Beta uses a newer version base.")
        same=[v.beta for v in known.values() if v.beta is not None and v.base==current.base]
        if current_tag not in known and current.beta!=(max(same,default=0)+1):
            raise ValueError("Next Beta must increment beta.N by exactly one, starting at beta.1.")
    elif channel=="stable":
        if current.beta is not None:raise ValueError("Stable must use X.Y.Z without -beta.")
        if current!=stable_baseline:
            raise ValueError("Stable release must run from the exact origin/main version.")
        if current_tag not in known:
            if previous and current.base not in next_bases(previous):
                raise ValueError("Stable must increment patch, minor or major from the last published Stable.")
        if current.base!=LEGACY_STABLE:
            matches=[v for v in known.values() if v.beta is not None and v.base==current.base]
            if not matches:
                predecessor=max((v.base for v in published_stable if v.base<current.base),default=None)
                if current.base!=REPORT_HOTFIX or predecessor!=REPORT_HOTFIX_BASE:
                    raise ValueError("Stable needs a published Beta with exactly the same X.Y.Z base.")
            elif not source_matches:
                raise ValueError("Stable app differs from the latest Beta source; publish a new Beta first.")
    else:
        raise ValueError("Channel must be beta or stable.")
    return current


def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,stderr=subprocess.PIPE).decode().strip()


def git_version(ref):
    text=git("show",ref+":distrikt/config.yaml")
    match=re.search(r'^version:\s*["\']([^"\']+)["\']',text,re.M)
    if not match:raise ValueError("Cannot read version from "+ref)
    return parse(match.group(1))


def tag_commit(tag):
    return git("rev-parse","--verify","refs/tags/"+tag+"^{commit}")


def stable_source_matches_beta(beta_tag):
    """Compare actual source, not version/docs; only the server VERSION differs."""
    folders=("distrikt/app","distrikt/templates","distrikt/translations")
    def names(ref):
        return set(git("ls-tree","-r","--name-only",ref,"--",*folders).splitlines())
    if names(beta_tag)!=names("HEAD"):return False
    for name in sorted(names("HEAD")):
        old=subprocess.check_output(["git","show",beta_tag+":"+name],cwd=ROOT)
        new=subprocess.check_output(["git","show","HEAD:"+name],cwd=ROOT)
        if name=="distrikt/app/server.py":
            old=re.sub(rb"(?m)^VERSION='[^']+'$",b"VERSION='<release>'",old)
            new=re.sub(rb"(?m)^VERSION='[^']+'$",b"VERSION='<release>'",new)
        if old!=new:return False
    return True


def verify(channel):
    import build_release
    version=parse(build_release.version())
    baseline=git_version("refs/remotes/origin/main")
    tags=git("tag","--list","v*").splitlines()
    relevant=tagged_versions(tags)
    current_tag="v"+str(version)
    sha=git("rev-parse","HEAD")
    shas={current_tag:tag_commit(current_tag)} if current_tag in relevant else {}
    synced=True
    if channel=="beta":
        synced=subprocess.run(["git","merge-base","--is-ancestor","refs/remotes/origin/main","HEAD"],
                              cwd=ROOT,check=False).returncode==0
    matches=[(tag,v) for tag,v in relevant.items() if v.beta is not None and v.base==version.base]
    newest=max(matches,key=lambda entry:entry[1].beta)[0] if matches else None
    parity=stable_source_matches_beta(newest) if channel=="stable" and newest and version.base!=LEGACY_STABLE else True
    validate(channel,version,baseline,tags,shas,sha,main_synced=synced,source_matches=parity)
    print(f"Version policy OK: {channel} {version}; main {baseline}; git {sha[:10]}")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    check=sub.add_parser("verify",help="Validate against fetched Git tags and origin/main before publication")
    check.add_argument("--channel",choices=("beta","stable"),required=True)
    next_cmd=sub.add_parser("next",help="Print next Beta number from a Stable version")
    next_cmd.add_argument("--stable",required=True)
    next_cmd.add_argument("--change",choices=("fix","feature","breaking"),required=True)
    args=parser.parse_args()
    if args.command=="next":
        stable=parse(args.stable)
        if stable.beta is not None:parser.error("--stable requires an X.Y.Z Stable version")
        print(next_version(stable,args.change))
    else:
        try:verify(args.channel)
        except (ValueError,subprocess.CalledProcessError) as exc:
            print("Version policy failed:",exc,file=sys.stderr)
            sys.exit(1)


if __name__=="__main__":main()
