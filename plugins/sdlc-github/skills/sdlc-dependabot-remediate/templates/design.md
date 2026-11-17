# Dependabot remediation

Clear the Dependabot alerts on `<owner>/<repo>` (`<manifests>`) without breaking
<what the project does>. It is built in <N> pieces, one SDLC feature each, in order.
Each piece builds on the code the earlier ones merged: extend those files and tests,
never redesign them.

## Rules for every piece

- **Alerts**: the source of truth is the open issue labelled `dependabot` (#<n>), kept
  up to date by `.github/workflows/dependabot-monitor.yml`. A piece fixes only the
  packages it names.
- **Pins**: every pin a piece sets is written in its section; never choose another
  version. <How the manifest pins: `==`, order kept, new lines before `<last lines>`.>
  Every pin must install with the pipeline's install command on Python <version>.
- **Manifest bytes**: <byte-order mark yes/no, CRLF/LF, final line break>; keep them.
- **Code changes**: only what a section lists. Live code only: leave commented-out lines
  alone. No refactoring, no new features. Keep each screen's or command's behaviour.
- **Tests**: <framework, folder, naming, how screens are tested>. No network, API key or
  GPU: <the fakes and local fixtures>. Earlier pieces' tests pass unchanged, except the
  ones a section says to change or delete. A test that scans source files skips `.venv/`
  and its own file.
- **Install**: <the pipeline's python-version and install-command>.
- **Never in scope**: <folders and files no piece touches>, and alerts in packages a
  piece doesn't name.

## Facts the plan must not guess

Read from the code and issue #<n> on <date>. Use these exactly.

<Output of `scripts/alert_facts.py`: the open alerts per package, with targets.>

- <Dependencies imported nowhere; imports not declared (arriving through a package
  being removed).>
- <Interim pins a fresh install needs, each with the newest working version, why, and
  its advisories if any (accepted in `.trivyignore` until piece N).>
- <For each package a piece upgrades: the files that import it, the names they use, the
  call shapes the upgrade changes.>
- <Paths no test can reach (need a real key, a network service, a person).>
- <Test fixtures and sample files, with paths.>

## Done

Nothing yet.

## Piece 1: Test baseline<, and removals>

The project has a smoke-test suite<, and the alerts of packages it drops are gone>.
Prototyped on <date>: <N> tests pass on a fresh install.

- Pins: <exact list: removed, added before `<line>`, changed in place>.
- <Code changes by file.>
- Tests: <each file, with the code that passed in the prototype, or its exact assertions>.

## Piece 2: <package family>

<Packages> are on fixed versions. <Outline until prototyped: packages → targets.>

- Pins: <exact resolved versions, including packages that must move with them>.
- <Exact code changes by file; earlier tests to change or delete.>
- Tests: <new test code that passed in the prototype>. <"Build it in one phase" when
  the piece only changes pins.>
