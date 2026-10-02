---
name: sdlc-github
description: Take a feature from a one-line idea to a reviewed pull request through the SDLC Pipeline on GitHub Actions. Join a run someone started with Run workflow, or start one with an sdlc issue; let Ollama write intent, spec and plan; build the frozen plan phase by phase (one phase branch and pull request each, Phase check, merge); hand back so the same run verifies, reviews and opens the pull request; then report it. Use for "sdlc-github" followed by an idea, "build this idea through the pipeline", "build feature 003", or to continue, re-plan or re-verify an existing sdlc feature.
---

# SDLC GitHub

You drive one feature through the SDLC Pipeline (`ly2xxx/.github`, called by this
repo's `.github/workflows/sdlc.yml`). Ollama designs it, you build it, and
deterministic checks judge it. You never judge your own work as passed: only a
check's exit code does.

```text
one run, one line
resolve → 1 intent ✋ → 2 spec ✋ → 3 plan ✋ → 4 ⏸ hand off and wait (≤180 min)
        → 5 verify → 5 Ollama review → 6 open the PR (feature/<f> → default branch)
you, during step 4: phase/<f>/<n> → PR into feature/<f> → SDLC Phase Check → squash-merge
```

## What you can and can't do

- You **can** push branches, open, comment on and merge PRs, open issues, and
  read runs, jobs and logs (GitHub MCP tools, or `gh`).
- Where you **can't** start workflow runs or push tags (in Claude Code on the
  web, dispatch returns 403 and tag pushes are refused), start runs with issues,
  and watch them with `git ls-remote` (in a background loop) and the MCP
  `actions_*` tools.
- The pipeline doesn't need you. Anyone can run it by hand with Run workflow.
  This skill does the Claude Code parts: starting a run on request, building,
  and seeing it through.
- The repo needs these: `sdlc.yml` (an `issues: [labeled]` trigger and an `sdlc`
  label, if you start the runs) and `sdlc-phase.yml` on `pull_request` into
  `feature/**`. It also needs an `OLLAMA_API_KEY` secret, and "Allow GitHub
  Actions to create and approve pull requests" turned on. If one is missing,
  say which, and stop.

## 1. Join or start the run

**The user already started it** (with Run workflow or an issue), or names a
feature: once `git ls-remote origin refs/tags/sdlc/<f>/approved` shows the tag,
go to step 2. If the tag isn't there yet, wait for it as described below. If
the run was started with start `build`, go to step 5.

**Otherwise, start it yourself:** open an issue labelled `sdlc`. The title is
the only thing Ollama sees.

| Intent | Title | Body lines |
| :-- | :-- | :-- |
| New feature | the idea, one line | — |
| Revise a feature's intent | the change | `feature: <f>` |
| New plan, same intent and spec | the feature's idea | `feature: <f>` and `start: plan` |
| Verify and open the PR again | anything | `feature: <f>` and `start: build` |

Before opening it, note the existing tags: `git ls-remote origin 'refs/tags/sdlc/*/approved'`.
Then wait in the background, for up to 15 minutes, for a new or moved
`sdlc/<f>/approved` tag. That tag means the design is frozen and step 4 is
waiting for you. If no tag appears, find the run (`actions_list`, workflow
`sdlc.yml`), read the failed job's log, and report it. A `start: build` issue
creates no tag, so go to step 5.

## 2. Read the contract

1. Run `git fetch origin --tags`, then `git switch -c feature/<f> origin/feature/<f>`.
2. Read `sdlc/features/<f>/intent.md`, `spec.md` and `plan.md`. For each phase,
   note `<!-- targets -->`, `<!-- frozen -->`, the Definition of done and the Verify block.
3. **Never edit these three files.** Verify compares them with the tag and fails on
   any change. If the plan can't be built as written, stop and tell the user why.
   With their OK, ask for a new plan (the `start: plan` issue above).

## 3. Set up once

```bash
uv venv .venv && . .venv/bin/activate && uv pip install -r requirements.txt pytest
# the pipeline at the version this repo's workflows call (main, v1, ...)
ref=$(sed -n 's#.*ly2xxx/\.github/\.github/workflows/sdlc\.yml@\([^ ]*\).*#\1#p' .github/workflows/sdlc.yml | head -1)
test -d ../.github/actions/sdlc-stage || git clone -q --depth 1 --branch "${ref:-main}" https://github.com/ly2xxx/.github ../.github
CHECK="python ../.github/actions/sdlc-stage/sdlc_stage.py verify --test-command 'python -m pytest -q'"
```

Use `pyproject.toml` (`uv pip install -e . pytest`) when the repo has one.

## 4. Build each phase, in order

1. `git fetch origin && git switch -c phase/<f>/<n> origin/feature/<f>`.
   It can't be `feature/<f>/...`: git refuses a branch under an existing branch.
2. Change only the phase's targets, and write the tests its Definition of done
   names. When the plan gives exact file content, use it exactly.
3. Check your uncommitted work: `eval "$CHECK --feature <f> --phase <n>"`. This runs
   the Verify blocks of phases 1..n from the approved plan and the whole suite,
   and checks scope, frozen files and the contract. Iterate within the phase's
   attempt budget. Never weaken a test, skip one, or touch a frozen file to get
   to green.
4. Append to `sdlc/features/<f>/build-log.md`. This is the one file outside the
   targets you may write, and the pipeline reads it.
   - `## Phase <n>: <title>`, the status and the files changed.
   - What you built, in two sentences.
   - The exact commands and their results.
   - Deviations from the plan, and why each one stands. Write "none" if there are none.
5. Commit `sdlc(<f>): phase <n>`, push, and open a PR into `feature/<f>` titled
   `<f>: phase <n> - <title>`.
6. Wait for **SDLC Phase Check** on it (about 30s; see `actions_list`,
   workflow `sdlc-phase.yml`). If it's red, read the job log, fix on the same
   branch, and push. If it's green, squash-merge the PR and start the next phase.

In teaching or demo mode (the user asks for it, or `builder=human`), stop after
each phase PR and let the person review it and merge it.

## 5. Hand back and finish

- Merging the last phase PR is the hand-back. Once `build-log.md` has a
  `## Phase <id>:` section for every phase, step 4 notices within about 30s, and
  the same run goes on to verify, review and open the PR.
- Watch the run until it completes (`actions_get` → `get_workflow_run`), then find
  the PR: `list_pull_requests`, with head `feature/<f>`.
- **Verify failed:** read its log, fix the problem on `phase/<f>/<n>-fix` through a
  PR as in step 4, then open a `start: build` issue.
- **Step 4 timed out** (it says so in its summary): open a `start: build` issue.
- **Step 6 couldn't open the PR** (the setting is off): its log prints the
  title and body between `----- pull request` markers. Open the PR yourself with
  exactly that title and body.
- **Report:** the PR link, the verify result, Ollama's verdict and its concerns,
  and any deviations or fixes made outside the plan. Don't merge the PR into
  the default branch unless the user asks you to.

## Rules

- The approved plan is the contract. Build it, and never rewrite it. Only the
  pipeline changes it: an issue, then Ollama, then a new tag.
- Change only the current phase's targets, plus `build-log.md`. Leave frozen
  files alone.
- **A bug that is outside the plan.** A Verify block may fail because of
  something already broken on the default branch, outside the targets. Prove it
  by reproducing it on the default branch. Fix it in a separate PR against the
  default branch, and merge that PR only if the user allows changes there;
  otherwise ask. Then merge the default branch into `feature/<f>`, and log it
  in `build-log.md`.
- Merge the default branch into `feature/<f>` whenever the default branch's
  workflows or test setup change. A `pull_request` run uses the workflow files from the
  merge commit.
- Never report something as passing unless a check's exit code says so. Quote
  the check's result, not your own impression.

## Gotchas

- **A Verify block hangs.** Output piped through `grep` is buffered, so you won't
  see which command hung. Run each command alone under `timeout 120`.
- **Test-order bugs.** A test can pass alone and hang when collected after
  another module. Import side effects are the usual cause, such as locust's
  gevent monkey-patching. Try the reverse order to tell.
- **Numbering.** A new feature's number is one more than the highest in
  `sdlc/features/` or on any `feature/*` branch. Read the real name from the tag.
- **Stale local tags.** Run `git fetch --tags` before reading from
  `sdlc/<f>/approved`. The tag moves when the plan is redone.
