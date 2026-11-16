---
name: sdlc-dependabot-setup
description: Set a GitHub repository up so its Dependabot alerts are tracked in one issue and can be fixed through the SDLC Pipeline. Makes sure the pipeline is installed (running sdlc-github-setup when it isn't), adds the Dependabot monitor workflow, sets the pipeline's install command when the project needs one, and walks the user through the DEPENDABOT_ALERTS_TOKEN secret, then runs the monitor once and reads back its issue. Safe to run again; it only adds what is missing. Use for "sdlc-dependabot-setup", "monitor my Dependabot alerts", "set up Dependabot remediation", "track the security alerts on <repo>", or when sdlc-dependabot-remediate finds no monitor workflow.
---

# SDLC Dependabot setup

You make one repository ready for `sdlc-dependabot-remediate`. The goal, as with
`sdlc-github-setup`: do everything you can yourself, and ask the user only for what you
can't do.

A repository is ready when it has:

| # | What | Who |
| :-- | :-- | :-- |
| 1 | The SDLC Pipeline: `sdlc.yml`, `sdlc-phase.yml`, the `sdlc` label, `OLLAMA_API_KEY` | `sdlc-github-setup` |
| 2 | `.github/workflows/dependabot-monitor.yml` on the default branch | you |
| 3 | The `DEPENDABOT_ALERTS_TOKEN` Actions secret | **the user** |
| 4 | Dependabot alerts turned on (Settings > Advanced Security) | the user, if off |
| 5 | An open issue labelled `dependabot` from the monitor | the first run |

## Rules

- **Never handle a token.** Don't ask for the alerts token or the Ollama key in chat,
  and don't write either to a file or command line. If the user pastes one, don't
  repeat it; tell them to revoke it and create a new one.
- **Say what the monitor reports before you install it**, as `sdlc-github-setup` does
  for the pipeline: every monitor run sends this repository's name (`owner/repo`,
  nothing else) to the pipeline author's usage endpoint; it is a condition of use and
  can't be turned off. Link https://github.com/ly2xxx/.github/blob/main/LICENSING.md#usage-tracking.
  One sentence covers both when you install the pipeline in the same session. If they
  don't agree, stop.
- **Workflow files go to the default branch**: `issue_comment`, `schedule` and Run
  workflow only use workflows that are there. Same rules for a refused push as
  `sdlc-github-setup` step 3.
- Change nothing else, except the install command in step 3.
- Report a setting or a secret as there only when you read it back.

## 1. Check

1. **The pipeline.** `git fetch origin <default>` and
   `git ls-tree -r --name-only origin/<default> .github/workflows/`. Without `sdlc.yml`,
   run `sdlc-github-setup` now and come back when it reports items 1 to 3 done (it may
   finish the push in the same commit as step 2 below; see step 4).
2. **The monitor.** `dependabot-monitor.yml` in the same listing.
3. **The secret.** With `gh`: `gh secret list` shows `DEPENDABOT_ALERTS_TOKEN`. Without
   `gh`, mark it "can't check from here"; the first run's issue says which source it used.
4. **Alerts on.** The user's Dependabot email, or the `https://github.com/<owner>/<repo>/security/dependabot`
   page, proves it. With `gh`: `gh api repos/<owner>/<repo>/vulnerability-alerts` (204 = on).
5. **The issue.** An open issue labelled `dependabot` whose body starts with
   `<!-- dependabot-monitor -->` (`list_issues` with the label).

Show the table with a state for each line. If all are done, say so and hand over (step 6).

## 2. Prepare the monitor workflow

Copy `templates/dependabot-monitor.yml` beside this skill to
`.github/workflows/dependabot-monitor.yml`. If the template isn't there, download it from
`https://raw.githubusercontent.com/ly2xxx/sdlc-github/main/plugins/sdlc-github/skills/sdlc-dependabot-setup/templates/dependabot-monitor.yml`.
Change only:

- `branches: [main]` to the default branch;
- the `paths:` list, to the repository's manifests (keep it short; add `**/go.sum`,
  `**/Gemfile.lock` and so on only when they exist).

## 3. Python version and install command

Remediation runs install the project the pipeline's way, on Python 3.12 unless told
otherwise, into a `.venv` made by `uv` (it has no `pip`: use `uv pip`). Vulnerable
projects are usually old ones, so check both, and set them in **both** `sdlc.yml` and
`sdlc-phase.yml`, under `with:` next to `test-command`:

- **`python-version`**: when the pins don't install on 3.12. Check with
  `uv pip compile --python-version 3.12 requirements.txt -o /dev/null`; on a
  "requires CPython" failure, use the version in `.python-version`, `.devcontainer`
  or `pyproject.toml`'s `requires-python` that resolves.
- **`install-command`**, when the default install won't do. One case is known:

| The manifests have | `install-command` |
| :-- | :-- |
| `torch` in `requirements.txt` | `uv pip install --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt` (CPU-only torch; the default pulls gigabytes of CUDA libraries) |

Give each setting a one-line comment saying why. When nothing calls for them, leave the
workflows alone.

## 4. Push to the default branch

Stage only the files from steps 2 and 3 (and `sdlc-github-setup`'s, when it ran in this
session and hadn't pushed yet), commit as `sdlc: add the Dependabot monitor`, and push
to the default branch, or write them in one commit with the GitHub MCP `push_files` tool.

If the push is refused, give the user the same choices as `sdlc-github-setup`. When the
session may push only to its own branch, open a pull request from that branch into the
default branch and, if the user has said you may merge, merge it once its checks pass;
otherwise ask them to merge it. A token without the workflows permission can't write
`.github/workflows/` at all: then show the files' final content and ask the user to
commit them.

## 5. The token

Skip this when step 1 found the secret. Give the user these steps, then wait:

1. Create a fine-grained personal access token at https://github.com/settings/personal-access-tokens/new:
   resource owner the repository's owner, **Only select repositories** with this one,
   repository permission **Dependabot alerts: Read-only**. Set an expiry they will
   remember; the monitor falls back to Trivy, and the issue says so, when it lapses.
2. Save it as the Actions secret `DEPENDABOT_ALERTS_TOKEN` at
   `https://github.com/<owner>/<repo>/settings/secrets/actions/new`, or in their own
   terminal with `gh secret set DEPENDABOT_ALERTS_TOKEN --repo <owner>/<repo>`.

It must be an Actions secret: a Dependabot secret of the same name isn't passed to
workflows.

## 6. First run and hand-over

Start the monitor once: Run workflow (`gh workflow run dependabot-monitor.yml`, or the
`actions_run_trigger` tool). Where you can't start runs, push the setup commit (the
push trigger runs it after its 10-minute wait) or, once an issue exists, comment
`/refresh` on it.

Watch the run (`actions_list` with workflow `dependabot-monitor.yml`), then read the
issue back and report:

- the source line: **Dependabot alerts API**, or Trivy with the reason, which means the
  token is missing or can't read alerts (go back to step 5);
- the number of open alerts and packages, and the five worst rows of the table;
- what is still the user's, with links.

Then offer to fix the alerts with `sdlc-dependabot-remediate`.

## Gotchas

- **The monitor reads only the default branch.** Dependabot alerts belong to it; a
  feature branch's dependencies show in the pipeline's own security scan instead.
- **A push run waits 10 minutes on purpose**, for Dependabot's rescan. A run that starts
  sooner reads alerts the push already fixed.
- **`/refresh` from someone without write access** is ignored by the job's `if`.
- **Organization repositories** may need an owner to approve the fine-grained token.
