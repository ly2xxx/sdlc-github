#!/usr/bin/env python3
"""Read and edit a pip requirements file without changing its bytes otherwise.

    manifest.py check requirements.txt
        Prints the encoding facts a design must state: byte-order mark, line endings,
        final line break, and the pinned packages.
    manifest.py pin requirements.txt torch==2.13.0 flask==3.1.3 [--before pandas] [--remove openai ...]
        Replaces each named package's line in place (whatever its old specifier); a
        package not in the file is added before the line of --before (or at the end).
        --remove deletes a package's line. The BOM, the line endings and the final line
        break stay as they were. Fails when --remove names a package that isn't there.

Names compare the PEP 503 way (Streamlit, streamlit and stream_lit are one). Standard
library only.
"""
import argparse
import re
import sys
from pathlib import Path

BOM = b"\xef\xbb\xbf"
NAME = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalize(name):
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def line_name(line):
    """The package a requirements line names, normalized; None for comments and blanks."""
    text = line.lstrip("﻿").strip()
    if not text or text.startswith(("#", "-")):
        return None
    m = NAME.match(text)
    return normalize(m.group(1)) if m else None


def parse(raw):
    """(has_bom, newline, final_newline, lines without line breaks)."""
    has_bom = raw.startswith(BOM)
    text = raw[len(BOM):].decode("utf-8") if has_bom else raw.decode("utf-8")
    crlf, lf = text.count("\r\n"), text.count("\n")
    newline = "\r\n" if crlf and crlf == lf else "\n"
    final = text.endswith("\n")
    lines = text.split(newline)
    if final:
        lines.pop()
    return has_bom, newline, final, lines


def endings(raw):
    text = raw.decode("utf-8", errors="replace")
    crlf, lf = text.count("\r\n"), text.count("\n")
    return "none" if not lf else "CRLF" if crlf == lf else "LF" if not crlf else "mixed"


def check(path):
    raw = Path(path).read_bytes()
    has_bom, _, final, lines = parse(raw)
    pins = [l.strip() for l in lines if line_name(l)]
    unpinned = [p for p in pins if "==" not in p]
    print(f"{path}: byte-order mark {'yes' if has_bom else 'no'}; line endings {endings(raw)}; "
          f"final line break {'yes' if final else 'no'}; {len(pins)} packages, {len(unpinned)} not pinned with ==")
    for p in unpinned:
        print(f"  not pinned: {p}")
    return 0


def pin(path, specs, before=None, remove=()):
    raw = Path(path).read_bytes()
    has_bom, newline, final, lines = parse(raw)
    wanted = {}
    for spec in specs:
        m = NAME.match(spec)
        if not m or "==" not in spec:
            sys.exit(f"not a name==version pin: {spec}")
        wanted[normalize(m.group(1))] = spec.strip()
    gone = {normalize(r) for r in remove}
    present = {line_name(l) for l in lines}
    missing = gone - present
    if missing:
        sys.exit(f"--remove names packages that aren't in {path}: {', '.join(sorted(missing))}")
    out, done = [], set()
    for line in lines:
        name = line_name(line)
        if name in gone:
            continue
        if name in wanted:
            out.append(wanted[name])
            done.add(name)
        else:
            out.append(line)
    new = [wanted[n] for n in wanted if n not in done]
    if new:
        anchor = normalize(before) if before else None
        at = next((i for i, l in enumerate(out) if anchor and line_name(l) == anchor), len(out))
        if anchor and at == len(out):
            sys.exit(f"--before names a package that isn't in {path}: {before}")
        out[at:at] = new
    if out and out[0].startswith("﻿"):
        out[0] = out[0][1:]
    text = newline.join(out) + (newline if final else "")
    Path(path).write_bytes((BOM if has_bom else b"") + text.encode("utf-8"))
    print(f"{path}: {len(done)} replaced, {len(new)} added, {len(gone)} removed")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check").add_argument("path")
    p = sub.add_parser("pin")
    p.add_argument("path")
    p.add_argument("specs", nargs="*")
    p.add_argument("--before")
    p.add_argument("--remove", action="append", default=[])
    args = parser.parse_args(argv)
    if args.command == "check":
        return check(args.path)
    return pin(args.path, args.specs, args.before, args.remove)


if __name__ == "__main__":
    sys.exit(main())
