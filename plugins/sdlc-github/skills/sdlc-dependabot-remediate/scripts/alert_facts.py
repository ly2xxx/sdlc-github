#!/usr/bin/env python3
"""Turn the Dependabot monitor's issue into the lines a design's Facts section needs.

    alert_facts.py issue-body.md [--issue 4]

Reads the issue body (save it from `issue_read`), parses the JSON block under "Data
for tools", and prints, wrapped for the design document:

    - Open alerts (issue #4, read 2026-11-16 21:02 UTC), 94 in 8 packages (current →
      upgrade to): torch 2.1.0 → 2.13.0 (12, critical); ...; pandasai 0.2.15 (4,
      critical; no fix for CVE-...).
    - History: 94 → 120 → 35 open alerts.

Exits 1 when the body has no readable data block. Standard library only.
"""
import argparse
import json
import re
import sys
import textwrap
from pathlib import Path


def data_of(body):
    m = re.search(r"```json\n(.*?)\n```", body, flags=re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def package_line(p):
    current = f" {p['current']}" if p.get("current") else ""
    target = f" → {p['fix_to']}" if p.get("fix_to") else ""
    count = len(p.get("alerts", []))
    extra = f"; no fix for {', '.join(p['no_fix'])}" if p.get("no_fix") else ""
    return f"{p['package']}{current}{target} ({count}, {p['severity']}{extra})"


def facts(data, issue=None):
    where = f"issue #{issue}, " if issue else ""
    packages = data.get("packages", [])
    head = f"Open alerts ({where}read {data.get('read_at', '?')}), {data.get('open', 0)} in {len(packages)} packages"
    if not packages:
        lines = [f"{head}: none."]
    else:
        lines = [f"{head} (current → upgrade to): " + "; ".join(package_line(p) for p in packages) + "."]
    if data.get("truncated"):
        lines.append("The report was cut down to fit the issue: some alerts are missing from the data; "
                     "the package rows and upgrade targets are complete.")
    if data.get("source") == "trivy":
        lines.append("Source: Trivy, not the Dependabot API (no working DEPENDABOT_ALERTS_TOKEN): "
                     "dismissed alerts still show.")
    history = data.get("history") or []
    if len(history) > 1:
        lines.append("History: " + " → ".join(str(h["open"]) for h in history) + " open alerts.")
    return "\n".join(textwrap.fill(l, width=88, initial_indent="- ", subsequent_indent="  ") for l in lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("body", help="file holding the issue body")
    parser.add_argument("--issue", help="the issue number, for the reference")
    args = parser.parse_args(argv)
    data = data_of(Path(args.body).read_text(encoding="utf-8"))
    if data is None:
        print("No readable data block (```json under 'Data for tools') in the issue body.", file=sys.stderr)
        return 1
    print(facts(data, args.issue))
    return 0


if __name__ == "__main__":
    sys.exit(main())
