# SDLC GitHub

Automated software development with AI through GitHub Actions.

A Claude plugin with one skill, `sdlc-github`, that takes a feature from a one-line idea to a
reviewed pull request through the [SDLC Pipeline](https://github.com/ly2xxx/.github) on
GitHub Actions. Ollama writes the intent, spec and plan; Claude builds the approved plan one
phase at a time, each phase on its own branch and pull request; deterministic checks decide
whether each phase, and the whole feature, is done. Claude never marks its own work as passed.

## Install

This repository is its own marketplace, `ly2xxx`.

- **claude.ai, the desktop app and Cowork:** Customize > Plugins > Add > Add marketplace, enter
  `ly2xxx/sdlc-github`, then add **SDLC GitHub**. It also reaches your Claude Code sessions.
- **Claude Code:**

  ```bash
  claude plugin marketplace add ly2xxx/sdlc-github
  claude plugin install sdlc-github@ly2xxx
  ```

## Use

In a session on a repository, say what to build:

> use sdlc-github to build a version endpoint on the FastAPI app

or join a feature that is already under way: "build feature 003", "re-verify feature 003".

**A new repository** is set up first, on request ("set up sdlc-github in this repo") or when
the skill finds no pipeline. It adds the two caller workflows,
[`sdlc.yml` and `sdlc-phase.yml`](plugins/sdlc-github/skills/sdlc-github/templates), to the
default branch and creates the `sdlc` label. You add one secret, `OLLAMA_API_KEY`, under
Settings > Secrets and variables > Actions. Two settings are optional: "Allow GitHub Actions to
create and approve pull requests" lets the pipeline open its pull request itself, and required
reviewers on the `sdlc-review` environment pause the run for your approval at each review step.
The [pipeline's README](https://github.com/ly2xxx/.github#use-it) has the details.

## What it runs

The skill is instructions only: no hooks, MCP servers or bundled programs. Following them,
Claude:

- clones `ly2xxx/.github` at the version your workflows call, and runs its `sdlc_stage.py
  verify` on your machine, along with each phase's Verify commands from the approved plan and
  your test suite;
- in a new repository, commits the two caller workflows and creates the `sdlc` label;
- pushes `phase/<feature>/<n>` branches, opens and merges pull requests into
  `feature/<feature>`, and opens `sdlc` issues to start pipeline runs;
- reads workflow runs and their logs.

It sends nothing anywhere else. The pipeline itself calls Ollama Cloud from GitHub Actions with
your repository's key.

## License

[PolyForm Noncommercial 1.0.0](LICENSE): free for personal and noncommercial use. Business use
needs a commercial license; see [LICENSING.md](LICENSING.md).
