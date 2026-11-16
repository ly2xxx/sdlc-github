---
name: sdlc-dependabot-remediate
description: Fix a repository's open Dependabot alerts through the SDLC Pipeline. Refreshes and reads the tracking issue the Dependabot monitor keeps, groups the vulnerable packages into pieces by upgrade risk, writes a design document from the alerts and the code, then builds the pieces in order with sdlc-github-epic (or one sdlc-github run when the fix is small), checking after each merge which alerts closed. Use for "sdlc-dependabot-remediate", "fix the Dependabot alerts on <repo>", "clear the security alerts", "upgrade the vulnerable dependencies through the pipeline", or "continue the Dependabot remediation".
---

# SDLC Dependabot remediate

You take a repository's open Dependabot alerts to merged pull requests. The alerts come
from one issue, labelled `dependabot`, that the Dependabot monitor keeps up to date; the
fixing is an `sdlc-github-epic` whose design document is written from those alerts.

```text
/refresh → read the issue's JSON → triage (remove / upgrade / no fix) ✋ decisions
        → docs/dependabot-remediation.md → sdlc-github-epic (design ✋, pieces, merges)
        → after each merge: the monitor reruns → record the alerts that closed
        → issue closes itself, or a closing list of what is left
```

## Rules

- **Everything in `sdlc-github-epic` applies**: the user reviews and merges the design,
  pieces go one at a time, each through `sdlc-github`, and only a check's exit code
  says something passed.
- **The issue is the source of the alerts.** Never take versions from memory or from an
  email: the email digest lists at most a few alerts per repository, and its "upgrade to"
  is often the lowest of several fixes. Use each package's `fix_to`.
- **Never dismiss an alert, or leave a package on a vulnerable version, without the
  user's agreement.** For an alert with no fix, the choices are remove the package,
  replace it, or accept it (dismiss it on GitHub with a reason, or add the ID to
  `.trivyignore` with a comment); ask.
- **Remove what isn't used** rather than upgrading it: a package the code never imports
  (check with `grep -rn` over the source, the notebooks excluded) goes in the first piece.
  Declare explicitly anything the code imports that only arrived through it.

## 0. Check the ground

1. The repository has `.github/workflows/dependabot-monitor.yml` and the SDLC Pipeline on
   its default branch. If not, run `sdlc-dependabot-setup` first.
2. Look for a remediation already under way: `sdlc/epics/*-dependabot-remediation*.md`
   and `docs/dependabot-remediation*.md` on the default branch. If one is in progress,
   continue it as `sdlc-github-epic` says ("Resume"). A finished one is history: start
   a new epic, with a dated name (`dependabot-remediation-<YYYY-MM>`).

## 1. Read fresh alerts

1. Find the open issue labelled `dependabot` whose body starts with
   `<!-- dependabot-monitor -->` (`list_issues`, then `issue_read`).
2. If its `read_at` is more than a day old, comment `/refresh` on it (`add_issue_comment`),
   wait for the `dependabot-monitor.yml` run it starts to finish (`actions_list`), and
   read the issue again.
3. Parse the JSON block under "Data for tools". Check `source`: `trivy` means the token
   is missing or lapsed; tell the user, and carry on only if they agree (Trivy sees the
   same vulnerable pins, but not dismissals). `truncated: true` means some alerts are
   left out of the data; the package rows and `fix_to` are still complete.

No issue, or a closed one: there are no open alerts, or the monitor never ran. Check the
latest monitor run, and report.

## 2. Triage

Read every manifest the issue names and the code that imports each package. Then put
each package in one group:

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

**Tests first.** If the repository has no tests that import the code an upgrade touches,
piece 1 adds a smoke suite (imports, each screen or command, the core functions) before
anything is upgraded. The pipeline judges by tests: without them an upgrade "passes"
whatever it breaks.

**Install it fresh before you design.** Old stacks often no longer install into a working
app: their unpinned dependencies have moved on (a new `pyarrow` needs NumPy 2; a new
`transformers` needs a newer torch; `huggingface-hub` dropped an API an old package
imports; Werkzeug 3 broke Flask 2.0). In a clean environment on the pipeline's Python,
install the manifest as the pipeline does and import every module and screen. For each
failure, find the newest version of the moved package that works, and put those pins in
piece 1 and in Facts. Check each pin's CVEs too (the pipeline's security scan sees them,
step 4 of "After each piece").

**Ask once**, in one message, with your recommendation for each: the no-fix packages,
removals of packages that *are* used, and anything that changes behaviour a user would
notice. Then also confirm who merges each piece's pull request, if the user hasn't said.

**Small fix.** When everything fits one piece (at most four phases: typically removals
and same-major upgrades, with tests already there), write a one-piece document and run
it with `sdlc-github` and `design:` lines instead of a whole epic.

## 3. Write the design

Write `docs/dependabot-remediation.md` from `templates/design.md` beside this skill,
following `sdlc-github-epic` step 1: the size limits, the anchor check, and the status
file `sdlc/epics/<NNN>-dependabot-remediation.md`. In **Facts**, give the issue number and
its `read_at`, and one line per package: current version, `fix_to`, worst severity,
number of alerts; plus every import site an upgrade may break, read from the code.

Then hand over to `sdlc-github-epic` at step 2 (the design pull request).

## 4. After each piece

When a piece's pull request merges, the monitor's push trigger reruns about ten minutes
later. Then, as part of `sdlc-github-epic` step 7:

1. Read the issue again (comment `/refresh` if it hasn't moved). The issue's change
   comment lists the alerts that closed.
2. In the status file, record them on the piece's line, and any alert of the piece's
   packages still open, with why (often a second advisory with a higher fix: then the
   next piece, or a fix-up piece, takes it).
3. Update the document's Facts with the new alert list, so later pieces plan from it.

New alerts can appear mid-epic. Add them to the piece of their family if it hasn't
started, or to a new last piece, with the user's agreement.

**The security scan blocks a piece that adds a vulnerable pin.** The pipeline's step 5
fails only on findings the branch adds, and a newly explicit pin of a vulnerable version
counts, even if that version was installed before through another package. Don't work
around it: tell the user which pins, which IDs and which later piece upgrades them, and
ask. If they accept, add the IDs to `.trivyignore` on the default branch in a small pull
request, each group commented with the piece that removes it; add "delete these entries"
to those pieces in the design; merge the default branch into `feature/<f>`; and open a
`start: build` issue for the feature.

## 5. Close

When the last piece is merged, do `sdlc-github-epic` step 4, and add to the closing
checklist:

- the issue's state: closed by the monitor ("No open alerts"), or the alerts still open,
  each with its decision (no fix and accepted, dismissed, out of scope);
- the token's expiry, if the user gave one, since the monitor falls back to Trivy after it;
- `.trivyignore`: every entry the epic added should be gone; list any left, with why.

## Gotchas

- **One advisory, several fixed versions.** `fix_to` already takes the highest across
  the package's alerts; don't lower it to avoid a major bump without asking.
- **Transitive dependencies.** An alert on a package the manifest doesn't list comes
  from a lockfile or another package's pin. Upgrade the parent, or pin the child
  explicitly with a comment saying which parent needs it.
- **Keep the manifest's bytes.** A byte-order mark or CRLF line endings must survive
  every edit, or the diff shows every line changed. Say so in Facts.
- **Heavy wheels.** A remediation run installs the project on every check. If the
  install is slow or huge (CUDA torch), set `install-command` in both pipeline
  workflows (see `sdlc-dependabot-setup` step 3) before piece 1.
- **The pipeline's security scan** fails a branch only on findings it adds, so an
  upgrade that clears some alerts and introduces none passes it; a piece that adds a
  new vulnerable package fails at step 5, by design.
