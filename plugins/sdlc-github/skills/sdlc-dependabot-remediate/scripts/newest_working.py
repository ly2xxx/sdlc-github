#!/usr/bin/env python3
"""Find the newest release of a package that still works with the rest of a stack.

    newest_working.py --package pyarrow --check "python -c 'import streamlit'" [--below 26] [--tries 8]

Tries the package's releases newest first (final releases only, yanked ones skipped):
installs each into the active environment with --install (default
`uv pip install -q {spec}`) and runs --check, a shell command, with the candidate in
$CANDIDATE. Prints the first version whose check exits 0 and exits 0; exits 1 when
none of the tried versions work. --below skips versions at or above a ceiling (for a
release line known to break). Release lists come from PyPI's JSON API, or --versions
for a fixed list. The last version tried stays installed: reinstall the manifest after.

Old stacks stop installing into a working app when unpinned dependencies move on
(a new pyarrow needs NumPy 2, a new transformers a newer torch); this finds each pin
piece 1 needs. Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

PRE = re.compile(r"(a|b|rc|alpha|beta|pre|preview|dev|c)\d*", re.IGNORECASE)


def version_key(version):
    parts = re.findall(r"\d+", version.split("+")[0])
    return tuple(int(p) for p in parts) or (0,)


def is_final(version):
    return not PRE.search(version.split("+")[0].lower().replace("post", ""))


def pypi_versions(package):
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url, timeout=30) as r:
        releases = json.load(r).get("releases", {})
    return [v for v, files in releases.items() if files and not all(f.get("yanked") for f in files)]


def candidates(versions, below=None):
    out = [v for v in versions if is_final(v)]
    if below:
        out = [v for v in out if version_key(v) < version_key(below)]
    return sorted(set(out), key=version_key, reverse=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--package", required=True)
    parser.add_argument("--check", required=True, help="shell command; exit 0 = works")
    parser.add_argument("--below", help="only versions lower than this")
    parser.add_argument("--tries", type=int, default=8)
    parser.add_argument("--install", default="uv pip install -q {spec}")
    parser.add_argument("--versions", help="comma-separated versions instead of PyPI's")
    args = parser.parse_args(argv)
    versions = args.versions.split(",") if args.versions else pypi_versions(args.package)
    for version in candidates(versions, args.below)[: args.tries]:
        spec = f"{args.package}=={version}"
        env = {**os.environ, "CANDIDATE": version}
        if subprocess.run(args.install.format(spec=spec), shell=True, env=env,
                          capture_output=True, text=True).returncode != 0:
            print(f"{spec}: doesn't install", file=sys.stderr)
            continue
        if subprocess.run(args.check, shell=True, env=env, capture_output=True, text=True).returncode == 0:
            print(version)
            return 0
        print(f"{spec}: check fails", file=sys.stderr)
    print(f"No working version of {args.package} in the {args.tries} newest tried.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
