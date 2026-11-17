---
name: sdlc-dependabot-remediate
description: Fix a repository's open Dependabot alerts through the SDLC Pipeline. Refreshes and reads the tracking issue the Dependabot monitor keeps, groups the vulnerable packages into pieces by upgrade risk, prototypes each piece in a scratch install, writes the design from what worked, then builds the pieces in order with sdlc-github-epic (or one sdlc-github run when the fix is small), recording which alerts each merge closed. Use for "sdlc-dependabot-remediate", "fix the Dependabot alerts on <repo>", "clear the security alerts", "upgrade the vulnerable dependencies through the pipeline", or "continue the Dependabot remediation".
---

# SDLC Dependabot remediate

You take a repository's open Dependabot alerts to merged pull requests. The alerts come
from one issue, labelled `dependabot`, that the Dependabot monitor keeps up to date; the
fixing is an `sdlc-github-epic` whose design document is written from those alerts and
from a prototype of each piece that you have made work.

```text
/refresh → read the issue → triage, fresh install, pin advisories ✋ decisions
        → prototype piece 1 → design (✋ review) → build piece 1 → merge
        → one PR: record piece 1 + prototype-backed design of piece 2 → build piece 2 → …
        → close: monitor issue closed, closing checklist
```

## Rules

- **Everything in `sdlc-github-epic` applies**: the user reviews and merges the design,
  pieces go one at a time, each through `sdlc-github`, and only a check's exit code
  says something passed.
- **The issue is the source of the alerts.** Never take versions from memory or from an
  email: the digest lists a few alerts per repository, and its "upgrade to" is often the
  lowest of several fixes. Use each package's `fix_to`.
- **A piece's design comes from a prototype that passed.** Before you write (or rewrite)
  a piece's section, make the piece work in a scratch copy (step 3). The section then
  states facts: every pin, every code change, the test code. No "if X breaks, do Y":
  Ollama plans one branch of a conditional, often the wrong one.
- **The plan never picks a version.** Every pin a piece adds or changes is in its
  section, taken from the prototype's resolved install. A version the plan invents can
  be older than what the unpinned install used, and vulnerable.
- **Never dismiss an alert, or leave a package on a vulnerable version, without the
  user's agreement.** For an alert with no fix the choices are remove, replace, or
  accept (dismiss on GitHub with a reason, or `.trivyignore` with a comment); ask.
- **Remove what isn't used** rather than upgrading it: a package the code never imports
  (`grep -rn` over the source, notebooks excluded) goes in the first piece. Declare
  explicitly anything the code imports that only arrived through it.

## Scripts

Beside this skill, in `scripts/` (standard library only; run them with `python3`):

| Script | Does |
| :-- | :-- |
| `scripts/manifest.py check <file>` | Byte-order mark, line endings, final line break, unpinned lines: say them in Facts. |
| `scripts/manifest.py pin <file> name==ver … [--before name] [--remove name]` | Edits pins in place and keeps those bytes. Use it in prototypes and builds instead of hand edits. |
| `scripts/newest_working.py --package P --check CMD [--below V]` | Newest release of P whose CMD passes in the active environment. |
| `scripts/pin_advisories.py <file> \| --pin name==ver` | Known advisories (OSV) of exact pins, with the version that fixes them all. Exit 1 = some found; 2 = `api.osv.dev` unreachable from here (check on https://osv.dev). |
| `scripts/alert_facts.py <issue-body-file> --issue N` | The issue's data as the Facts lines, with the count history. |

## 0. Check the ground

1. The repository has `.github/workflows/dependabot-monitor.yml` and the SDLC Pipeline on
   its default branch. If not, run `sdlc-dependabot-setup` first, and read its report:
   the fresh-install result, the test situation, the sandbox limits.
2. Look for a remediation already under way: `sdlc/epics/*-dependabot-remediation*.md`
   and `docs/dependabot-remediation*.md` on the default branch. If one is in progress,
   continue it as `sdlc-github-epic` says ("Resume"). A finished one is history: start a
   new epic with a dated name (`dependabot-remediation-<YYYY-MM>`).

## 1. Read fresh alerts

1. Find the open issue labelled `dependabot` whose body starts with
   `<!-- dependabot-monitor -->` (`list_issues`, then `issue_read`).
2. If its `read_at` is more than a day old, comment `/refresh` on it (`add_issue_comment`),
   wait for the `dependabot-monitor.yml` run it starts (`actions_list`), and read it again.
3. Save the body to a file and run `scripts/alert_facts.py` on it. `source: trivy` means
   the token is missing or lapsed: tell the user and carry on only if they agree (Trivy
   sees the same pins, not dismissals). `truncated` means some alerts are left out of the
   data; the package rows and `fix_to` are complete.

No issue, or a closed one: there are no open alerts, or the monitor never ran. Check the
latest monitor run, and report.

## 2. Triage

Read every manifest the issue names and the code that imports each package. Put each
package in one group:

| Group | When | Goes in |
| :-- | :-- | :-- |
| Remove | not imported anywhere, or the user chose removal for a no-fix alert | piece 1 |
| Same-major upgrade | `fix_to` has the current major version | one piece for these, early |
| Major upgrade | `fix_to` crosses a major version (or 0.x minor) | one piece per family |
| No fix | `no_fix` lists every alert of the package | a decision for the user |

A **family** is packages that must move together: they pin each other or share an API
(`langchain*`; `torch` with `sentence-transformers` and `transformers`; `react` with
`react-dom`). Order the families so each piece's tests can pass: what others depend on
goes first.

Then, before asking anything:

1. **Tests first.** If no tests import the code an upgrade touches, piece 1 adds a smoke
   suite (imports, each screen or command, the core functions). The pipeline judges by
   tests: without them an upgrade "passes" whatever it breaks.
2. **Install it fresh.** In a clean environment on the pipeline's Python (see the
   callers' `python-version` and `install-command`), install the manifest and import every
   module and screen. Old stacks often no longer start: unpinned dependencies moved on (a
   new `pyarrow` needs NumPy 2, a new `transformers` a newer torch, Werkzeug 3 broke Flask
   2.0). For each failure, `scripts/newest_working.py` finds the newest version that
   works; those **interim pins** go in piece 1. Pin every unpinned line to the version
   the install resolved, not an older one.
3. **Check the interim pins' advisories** with `scripts/pin_advisories.py`. The pipeline's
   security scan fails a piece that adds a vulnerable pin, even one that was installed
   before, unpinned. Name each such pin, its IDs and the later piece that upgrades it.
4. **List what no test can reach**: paths that need a real API key, a network service
   or a person (a button that calls OpenAI, a page that fetches YouTube). They go on the
   closing checklist from the start, and every piece that touches them says so.

**Ask once**, in one message, with your recommendation for each: the no-fix packages,
removals of packages that *are* used, the vulnerable interim pins (accept until piece N,
or reorder), and anything a user would notice. Confirm who merges each piece's pull
request, if the user hasn't said. If they accept interim pins, put the IDs in
`.trivyignore` on the default branch now, each group commented with the piece that
removes it, before piece 1 starts.

**Small fix.** When everything fits one piece (removals and same-major upgrades, tests
already there), write a one-piece document and run it with `sdlc-github` and `design:`
lines instead of a whole epic.

## 3. Prototype a piece

Do this for piece 1 before the design pull request, and for each later piece before the
pull request that records the piece before it.

1. Copy the default branch (`git archive origin/<default> | tar -x -C <scratch>`), with
   any large files the tests read, into a scratch directory, and make a fresh
   environment there the pipeline's way.
2. Apply the piece: `scripts/manifest.py pin` for the pins, then the code changes. If
   the install doesn't resolve, read the resolver's reason: it names packages that must
   move too (`langchain-openai` needs a newer `tiktoken`).
3. Run the whole suite, and write the piece's new tests and run them. Iterate until
   everything passes.
4. Note what the design must say: the resolved versions of every package the piece pins;
   each code change by file (live lines only, leave commented-out code alone); the test
   code that passed; any earlier test the piece must change or delete; facts the build
   proved (a call that no longer works, a token counter that downloads a model).
5. If the sandbox can't reach a package index the pipeline uses (the PyTorch CPU index),
   install from PyPI and say in the build log that the pipeline checks the real build.

## 4. Write the design

Write `docs/dependabot-remediation.md` from `templates/design.md` beside this skill,
following `sdlc-github-epic` step 1: the size limits, the anchor check, and the status
file `sdlc/epics/<NNN>-dependabot-remediation.md`. Facts: the lines from
`scripts/alert_facts.py`, the manifest's encoding from `scripts/manifest.py check`, the
interim pins with why, and every import site an upgrade touches.

Write piece 1's section from its prototype. Later pieces' sections can start as a short
outline (packages and their targets); each is rewritten from its own prototype before it
starts (step 5). Size phases to the piece: a piece that only changes pins says "build
it in one phase".

Then hand over to `sdlc-github-epic` at step 2 (the design pull request).

## 5. Between pieces

When a piece's pull request merges, don't wait for the monitor:

1. Prototype the next piece (step 3) on the new default branch.
2. In **one** pull request to the default branch: the record of the piece that merged
   (`sdlc-github-epic` step 7: `## Done`, deviations, status file) and the next piece's
   section rewritten from its prototype. Merge it, then start the next piece's run.
3. The monitor reruns about ten minutes after a manifest change. Record the alerts each
   piece closed (its change comment lists them) in the next record pull request, along
   with any alert of the piece's packages still open and why, and any new alert (add it
   to its family's piece if that hasn't started, or a new last piece, with the user).

Pinning makes alerts visible: after a piece that pins packages for the first time, the
count can rise. The issue's history line shows it; say why in the status file.

**If the security scan still blocks a piece** (an advisory triage missed), tell the user
which pins, IDs and later piece, and ask. If they accept: `.trivyignore` on the default
branch in a small pull request, merge the default branch into `feature/<f>`, and open a
`start: build` issue for the feature.

## 6. Close

When the last piece is merged, do `sdlc-github-epic` step 4, and add to the closing
checklist:

- the issue's state: closed by the monitor ("No open alerts"), or the alerts still open,
  each with its decision (no fix and accepted, dismissed, out of scope); quote the
  history line;
- every path from triage step 4 that no test reached, and every deviation a person must
  check (a changed call that needs a real key);
- data saved by the old versions that may not load (pickles, caches, model files);
- the token's expiry (the comment in `dependabot-monitor.yml`), since the monitor falls
  back to Trivy after it;
- `.trivyignore`: every entry the epic added should be gone; list any left, with why.

## Gotchas

- **One advisory, several fixed versions.** `fix_to` already takes the highest across
  the package's alerts; don't lower it to avoid a major bump without asking.
- **Transitive dependencies.** An alert on a package the manifest doesn't list comes from
  a lockfile or another package's pin. Upgrade the parent, or pin the child with a
  comment saying which parent needs it.
- **Keep the manifest's bytes.** A byte-order mark or CRLF line endings must survive every
  edit; `scripts/manifest.py pin` keeps them. Say them in Facts.
- **Heavy wheels.** If the install is slow or huge (CUDA torch), set `install-command` in
  both pipeline workflows (`sdlc-dependabot-setup` step 3) before piece 1.
- **Tests that scan the source** (for an old import that must be gone) must skip `.venv/`,
  which the pipeline creates inside the checkout, and their own file, whose test names
  can contain the string they look for.
- **A plan's test text can be wrong for the installed version** (an `AppTest` accessor
  that doesn't exist). Follow the code, log the deviation; that is what the prototype's
  passing test code in the design prevents.
