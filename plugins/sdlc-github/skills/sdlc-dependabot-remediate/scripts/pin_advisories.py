#!/usr/bin/env python3
"""List the known advisories of exact pins, before a piece adds them.

    pin_advisories.py requirements.txt                 # every name==version line
    pin_advisories.py --pin transformers==4.46.3 --pin werkzeug==2.0.3

Asks the OSV database (https://api.osv.dev, the source GitHub and Trivy draw on) about
each PyPI pin and prints one line per pin with advisories: the IDs (CVE where one
exists) and the lowest version that fixes them all. Exits 1 when any pin has an
advisory, 0 when none do, 2 when api.osv.dev can't be reached (a session whose network
doesn't allow it: check the pins on https://osv.dev or GitHub's advisory database instead). Use it on the interim pins a piece adds, so the user decides
about them at triage instead of the pipeline's security scan blocking the piece.
Standard library only.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

OSV = "https://api.osv.dev/v1"


def pins_in(path):
    raw = Path(path).read_bytes().decode("utf-8-sig")
    out = []
    for line in raw.splitlines():
        line = line.split("#", 1)[0].split(";", 1)[0].strip()
        m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*==\s*([^\s,]+)$", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def post(path, payload):
    req = urllib.request.Request(f"{OSV}/{path}", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def get(path):
    with urllib.request.urlopen(f"{OSV}/{path}", timeout=60) as r:
        return json.load(r)


def version_key(v):
    return tuple(int(p) for p in re.findall(r"\d+", v.split("+")[0])) or (0,)


def fixed_versions(vuln, name):
    """The 'fixed' events of the vulnerability's ranges for this package."""
    out = []
    for affected in vuln.get("affected", []):
        pkg = affected.get("package", {})
        if pkg.get("ecosystem") != "PyPI" or pkg.get("name", "").lower().replace("_", "-") != name.lower().replace("_", "-"):
            continue
        for r in affected.get("ranges", []):
            out += [e["fixed"] for e in r.get("events", []) if "fixed" in e]
    return out


def label(vuln):
    cves = [a for a in vuln.get("aliases", []) if a.startswith("CVE-")]
    return cves[0] if cves else vuln["id"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("--pin", action="append", default=[], help="name==version")
    args = parser.parse_args(argv)
    pins = pins_in(args.manifest) if args.manifest else []
    for spec in args.pin:
        name, _, version = spec.partition("==")
        pins.append((name.strip(), version.strip()))
    if not pins:
        parser.error("no name==version pins given")
    try:
        return report(pins)
    except (urllib.error.URLError, OSError) as e:
        print(f"Can't reach api.osv.dev ({e}); check these pins on https://osv.dev instead.", file=sys.stderr)
        return 2


def report(pins):
    results = post("querybatch", {"queries": [{"package": {"name": n, "ecosystem": "PyPI"}, "version": v}
                                              for n, v in pins]}).get("results", [])
    found = 0
    for (name, version), result in zip(pins, results):
        ids = [v["id"] for v in result.get("vulns", [])]
        if not ids:
            continue
        found += 1
        vulns = [get(f"vulns/{i}") for i in ids]
        fixes = [f for v in vulns for f in fixed_versions(v, name) if version_key(f) > version_key(version)]
        target = max(fixes, key=version_key) if fixes else "no fix"
        print(f"{name}=={version}: {len(ids)} advisories ({', '.join(sorted({label(v) for v in vulns}))}); "
              f"fixed in {target}")
    if not found:
        print(f"No known advisories for the {len(pins)} pins.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
