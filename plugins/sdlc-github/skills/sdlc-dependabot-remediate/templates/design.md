# Dependabot remediation

Clear the Dependabot alerts on `<owner>/<repo>` (`<manifests>`) without breaking
<what the project does>. It is built in <N> pieces, one SDLC feature each, in order.
Each piece builds on the code the earlier ones merged: extend those files and tests,
never redesign them.

## Rules for every piece

- **Alerts**: the source of truth is the open tracking issue labelled `dependabot`,
  kept up to date by the Dependabot monitor workflow. A piece fixes only the packages
  it names. Upgrade each to at least the **highest** `fix_to` version the issue lists
  for that package, never the lowest.
- **Pins**: <how the manifest pins versions, e.g. `==` in requirements.txt; keep the
  file's order; new lines at the end with a comment naming the piece>.
- **Code changes**: only what an upgrade forces (renamed imports, removed APIs). No
  refactoring, no new features, no UI changes. Keep each screen's or command's behaviour.
- **Tests**: <framework, folder, naming, how screens are tested>. Tests never use the
  network, an API key or a GPU: <the fakes and local fixtures to use>.
- **Install**: <the pipeline's install-command, when the setup set one>.
- **Never in scope**: <folders and files no piece touches>, and alerts in packages a
  piece doesn't name.

## Facts the plan must not guess

Read from the code and the tracking issue on <date>. Use these exactly.

- Open alerts (issue #<n>, read <date>): <package> <current> (fix <fix_to>; <worst>,
  <count> alerts); … ; <package> (no fix: <ids>).
- <Dependencies imported nowhere, and those imported but not declared (arriving
  through a package being removed).>
- <For each package a piece upgrades: the files that import it, the names they use,
  and the exact call shapes the upgrade may change.>
- <Pins a fresh install needs (packages that moved on since the manifest was written),
  each with the newest version that works and why.>
- <The manifest's encoding: byte-order mark, line endings.>
- <Test fixtures and sample files to use, with paths.>

## Done

Nothing yet.

## Piece 1: Test baseline<, and removals>

The project has a smoke-test suite<, and the alerts of packages it drops are gone>.

- <Removals, with the packages to declare explicitly in their place.>
- <Pins for unpinned dependencies whose next release breaks the code.>
- <One test file per area: imports, each screen or command, the core functions.>

## Piece 2: <package family>

<Packages> are on fixed versions.

- Upgrade <packages> to the highest fixed versions in the tracking issue.
- <Exact code changes the upgrade forces, by file.>
- Earlier pieces' tests pass unchanged. <New tests that prove this family still works.>
