---
name: sdlc-github-setup
description: Onboard a GitHub repository to the SDLC Pipeline so the sdlc-github skill can run on it. Checks what the repository already has, pushes the two caller workflows to the default branch, creates the sdlc label, turns on the optional settings where it can, and walks the user through the one step only they can do, the OLLAMA_API_KEY secret. Safe to run again; it only adds what is missing. Use for "set up sdlc-github", "onboard this repo to the SDLC pipeline", "install the sdlc workflows", "check my sdlc-github setup", or when sdlc-github finds no .github/workflows/sdlc.yml on the default branch.
---

# SDLC GitHub setup

You make one repository ready for the SDLC Pipeline (`ly2xxx/.github`), then hand over
to the `sdlc-github` skill. The goal is the fewest steps for the user: do everything
you can yourself, and ask them only for what you can't do.

A repository is ready when it has:

| # | What | Who |
| :-- | :-- | :-- |
| 1 | `.github/workflows/sdlc.yml` and `sdlc-phase.yml` on the default branch | you |
| 2 | The `sdlc` label | you |
| 3 | The `OLLAMA_API_KEY` Actions secret | **the user** |
| 4 | Optional: "Allow GitHub Actions to create and approve pull requests" | you with `gh` and admin access, else the user |
| 5 | Optional: required reviewers on the `sdlc-review` environment | you with `gh` and admin access, else the user |

Every step checks first and changes only what is missing, so running the skill again
is safe, and "check my setup" is steps 1 and 6 alone.

## Rules

- **Never handle the Ollama key.** Don't ask for it in chat, and don't write it to a
  file or a command line. If the user pastes it anyway, don't repeat it; tell them to
  delete that key on ollama.com and create a new one.
- **Push the setup commit straight to the default branch.** Run workflow and the issue
  trigger only use workflows that are on it. Don't open a pull request for it unless
  the push is refused and the user picks that (step 3).
- **Leave existing workflows as they are.** If `sdlc.yml` or `sdlc-phase.yml` is
  already there, report how it differs from the template and change it only when the
  user asks.
- Change nothing else in the repository, except the `.gitignore` line in step 2.
- Report a setting as on only when you read it back, not because a command returned.

## 1. Check

Find the repository (`git remote get-url origin`) and its default branch
(`git remote show origin`, or `get_file_contents` / `list_branches` with the GitHub MCP
tools). Then find out which tools you have, because that decides who does items 4 and 5:

```bash
gh auth status && gh api repos/<owner>/<repo> -q .permissions.admin   # "true" = you can do items 4 and 5
```

No `gh`, or not `true`: you have the GitHub MCP tools only, which can't read or change
secrets or settings.

Check each item and show the user the table above with a state for each: done, will
do, or needs you.

- **Workflows:** `git fetch origin <default>` then
  `git ls-tree -r --name-only origin/<default> .github/workflows/`.
- **Label:** `gh label list --search sdlc`, or `get_label`.
- **Secret** (`gh` only): `gh secret list` shows names, never values. An organization
  secret counts too: `gh secret list --org <owner>`. Without `gh`, mark it "can't
  check from here".
- **Pull request setting** (`gh` only):
  `gh api repos/<owner>/<repo>/actions/permissions/workflow -q .can_approve_pull_request_reviews`.
- **Environment** (`gh` only): `gh api repos/<owner>/<repo>/environments/sdlc-review`
  (404 means none).
- **Actions is on** (`gh` only): `gh api repos/<owner>/<repo>/actions/permissions -q .enabled`.
  If `false`, which is the default on a fork, the user turns it on under Settings >
  Actions > General. If `allowed_actions` there is `selected`, the organization must
  also allow `ly2xxx/.github`; tell the user, since only an owner can.

If everything required is done, say so and stop.

## 2. Prepare the workflows

Skip this and step 3 when both files are already on the default branch.

1. Get the two templates, `sdlc.yml` and `sdlc-phase.yml`. They belong to the
   `sdlc-github` skill of this plugin: read them from `../sdlc-github/templates/`,
   relative to this skill's base directory. If that directory isn't there, download
   them:

   ```bash
   base=https://raw.githubusercontent.com/ly2xxx/sdlc-github/main/plugins/sdlc-github/skills/sdlc-github/templates
   mkdir -p .github/workflows
   curl -fsSL "$base/sdlc.yml" -o .github/workflows/sdlc.yml
   curl -fsSL "$base/sdlc-phase.yml" -o .github/workflows/sdlc-phase.yml
   ```

2. Copy them to `.github/workflows/` unchanged, except for `test-command`. Set it to
   the same value in both files; it must run the whole test suite and fail when it
   finds no tests.

   | The repository's top level has | `test-command` |
   | :-- | :-- |
   | `pyproject.toml`, `requirements.txt` or `setup.py`, or nothing yet | `python -m pytest -q` (the template's value) |
   | `package.json` with a `test` script | `npm test`, or `pnpm test` / `yarn test` to match the lockfile |
   | both Python and Node.js | both, joined: `python -m pytest -q && npm test` |
   | anything else, or tests in a subdirectory | ask the user for the command |

   A `test` script that passes with no tests (`--passWithNoTests`, or npm's default
   `echo "Error: no test specified" && exit 1` placeholder) isn't a test suite yet;
   tell the user, and keep the command the first plan will make real.

3. A repository with a `package.json` must ignore `node_modules/`. If `.gitignore`
   doesn't list it, add the line.

## 3. Push to the default branch

1. Switch to the default branch at its latest commit (`git switch <default> && git pull`),
   keeping any work in progress out of the commit: stage only the two workflow files,
   and `.gitignore` if you changed it. An empty repository gets them as its first
   commit.
2. Commit as `sdlc: add the SDLC Pipeline` and `git push origin <default>`.
   Where you can't push with git, write the same files to the default branch in one
   commit with the GitHub MCP `push_files` tool.
3. Read it back: the files are in `git ls-tree origin/<default>` after a fetch.

**If the push is refused**, don't retry it and don't work around it. Say which rule
refused it, then give the user the choice:

- *Branch protection or a ruleset:* they push it themselves, allow you past the rule,
  or tell you to open a pull request for them to merge.
- *The token can't write workflow files* ("refusing to allow ... to create or update
  workflow"): the session's GitHub access lacks the workflows permission. They grant
  it, or commit the two files themselves; show the files' final content.
- *The session is limited to its own branch:* push there, and ask them to merge that
  branch into the default branch.

Setup isn't finished until the files are on the default branch. Carry on with steps 4
and 5 meanwhile.

## 4. Label and optional settings

Create the label if it's missing:

```bash
gh label create sdlc --color 5319e7 --description "Starts an SDLC Pipeline run"
```

Without `gh`, use the GitHub MCP tools; if they have no tool that creates a label,
open the first `sdlc` issue with the label and check it was applied. If it wasn't, ask
the user to create the label at `https://github.com/<owner>/<repo>/labels`.

With `gh` and admin access, offer items 4 and 5 in one question, and do what the user
accepts. Recommend item 4; item 5 is for people who want to approve each document.

```bash
# 4: let the last step open the pull request. Send the current default back unchanged.
current=$(gh api repos/<owner>/<repo>/actions/permissions/workflow -q .default_workflow_permissions)
gh api -X PUT repos/<owner>/<repo>/actions/permissions/workflow \
  -f default_workflow_permissions="$current" -F can_approve_pull_request_reviews=true

# 5: pause the run at each review job until the user approves it.
gh api -X PUT repos/<owner>/<repo>/environments/sdlc-review --input - <<EOF
{"reviewers": [{"type": "User", "id": $(gh api user -q .id)}], "prevent_self_review": false}
EOF
```

Item 4 can be refused when the organization forbids it, and item 5 on a private
repository whose plan has no required reviewers. Report the refusal and move on:
both are optional.

Without `gh`, don't ask the user to do them now. Mention them once at the end as
optional, with their links (step 6). Without item 4 the pipeline still finishes;
`sdlc-github` opens the pull request itself.

## 5. The Ollama key

This is the one step only the user can do. Skip it when step 1 found the secret.
Give them both links, complete, and then wait for them to say it's done:

1. Create a key at https://ollama.com/settings/keys (**Create API key**), and copy it.
2. Add it as a repository secret named exactly `OLLAMA_API_KEY`:
   - in a browser, at `https://github.com/<owner>/<repo>/settings/secrets/actions/new`; or
   - in their own terminal, `gh secret set OLLAMA_API_KEY --repo <owner>/<repo>`, which
     asks for the value without showing it. They run it, not you.

For several repositories under one organization, an organization secret set once
covers them all: `https://github.com/organizations/<org>/settings/secrets/actions`.

While you wait, finish anything left from steps 3 and 4.

## 6. Confirm and hand over

Run step 1's checks again and show the final table. For each line say what you read
back, or that you couldn't check it from here. Without `gh` the secret can't be
checked: say that the first run proves it, because its first job stops at once with
"needs ollama-api-key" when the secret is missing or misnamed, before anything is
built.

List what is still the user's, with links:

- the secret, if they haven't confirmed it;
- the default-branch push, if it was refused;
- optional, if not done: `https://github.com/<owner>/<repo>/settings/actions`
  (Workflow permissions) and `https://github.com/<owner>/<repo>/settings/environments`
  (`sdlc-review`, Required reviewers, leave "Prevent self-review" off).

When items 1 to 3 are done, the repository is ready. Ask for the first idea, and
build it with the `sdlc-github` skill.

## Gotchas

- **A fork.** Actions is off until the user enables it, and its secrets are its own:
  the parent repository's key doesn't carry over.
- **The secret was added but the run still says "needs ollama-api-key".** The name is
  wrong, or it was added as a variable, a Dependabot secret or an environment secret.
  It must be an Actions repository (or organization) secret.
- **An organization secret** limited to selected repositories must include this one.
- **The label exists with another colour or case.** Labels match without case; leave
  it as it is.
- **Workflows on a branch only.** A run can't start until the files are on the default
  branch, whatever the Actions tab shows.
