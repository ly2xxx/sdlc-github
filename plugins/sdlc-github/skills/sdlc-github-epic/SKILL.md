---
name: sdlc-github-epic
description: Build a feature that is too big for one SDLC Pipeline run. Breaks the requirement into a reviewed design document with one section per piece, then builds the pieces in order, each as its own sdlc-github feature and pull request, keeping the document and a status file up to date so the work can be resumed. Use for "sdlc-github-epic" followed by a requirement or a requirements file, "break this feature down and build it through the pipeline", "this is too big for one sdlc-github run", "continue the <name> epic", or when a requirement given to sdlc-github needs more than about four phases.
---

# SDLC GitHub epic

You take one large requirement to a series of merged pull requests. The work is
split into **pieces**. Each piece is one `sdlc-github` feature: one pipeline
run, at most four phases, one pull request into the default branch.

```text
requirement → design document (docs/<epic>.md) ✋ user reviews and merges
            → piece 1: issue with design: lines → sdlc-github → PR ✋ user merges → update the document
            → piece 2 … → piece N → closing checklist
```

Two things hold the pieces together, and both are files in the repository:

- **The design document**, `docs/<epic>.md`. Ollama reads the sections a piece
  names word for word, so the document is the real specification. The issue
  title is only a label.
- **The status file**, `sdlc/epics/<NNN>-<epic>.md`. It records which piece is
  which feature and pull request, so a new session can carry on. Like feature
  folders, everything under `sdlc/` is numbered, so the order of the work is
  clear when auditing.

## Rules

- **The user reviews twice per unit of work, and you never skip either.** They
  review and merge the design document before any piece starts, and they merge
  each piece's pull request before the next piece starts. Ask once whether they
  want to merge these themselves (the default) or have you merge when green.
- **One piece at a time, in order.** A piece is planned against the code the
  earlier pieces merged. Don't start piece N+1 while piece N's pull request is
  open.
- **Facts come from the code, not from memory.** Everything the document says
  about existing code (paths, names, roles, response shapes) you have read in
  the repository in this session.
- **The document changes only between pieces**, through its own pull request
  or commit to the default branch, never inside a feature branch. A piece's
  plan can only touch its targets.
- Everything in the `sdlc-github` skill still applies inside a piece: build the
  approved plan, never edit it, and report only what a check's exit code says.

## 0. Check the ground

1. The repository is set up for the pipeline (`.github/workflows/sdlc.yml` on
   the default branch). If not, run `sdlc-github-setup` first.
2. The pipeline supports design references. This needs `ly2xxx/.github` at
   `main` on or after its pull request 11, or a tag that includes it. Check the version
   the caller workflow uses:

   ```bash
   ref=$(sed -n 's#.*ly2xxx/\.github/\.github/workflows/sdlc\.yml@\([^ ]*\).*#\1#p' .github/workflows/sdlc.yml | head -1)
   test -d ../.github/actions/sdlc-stage || git clone -q --depth 1 --branch "${ref:-main}" https://github.com/ly2xxx/.github ../.github
   grep -c "def design_refs" ../.github/actions/sdlc-stage/sdlc_stage.py   # 1 = supported
   ```

   If it prints 0, tell the user the caller is pinned to an older pipeline, and
   ask them to move it to a version with design references. Without them, fall
   back to naming the document and the piece in the issue title (step 3).
3. Look for an epic already under way: `ls sdlc/epics/ docs/` on the default
   branch. If the status file exists, read it and go to the step it says is
   next (see "Resume").

## 1. Decompose

Read the requirement in full, then read the code it touches: the schema, the
routes, the screens, the tests beside them, and how similar features are built.
Then decide the pieces.

**A good piece:**

- delivers something a person can see or call by itself, and leaves the
  repository working with its tests passing;
- fits one plan: at most four phases, and roughly fifteen files changed. If you
  can't list its phases in four lines, split it;
- depends only on earlier pieces;
- stays in one layer where it can. A usual order is data, then API, then the
  screens that use it, then the screens that build on those.

**Settle the open decisions now.** List every choice the requirement leaves
open (names, who may do what, where a screen lives, what is out of scope) and
ask the user in one message, with your recommendation for each. Don't leave a
decision to Ollama: it will make a different one in each piece.

Write `docs/<epic>.md` from `templates/design.md` beside this skill. `<epic>`
is a short kebab-case name. What each part is for:

| Part | Holds |
| :-- | :-- |
| Opening paragraph | What is being built and why, and that it is built in N pieces, in order. |
| `## Rules for every piece` | Decisions and conventions that hold throughout: files and patterns to extend, who is allowed what, how tests are written, what is never in scope. Every piece's run quotes this section. |
| `## Facts the plan must not guess` | The shapes the code doesn't make obvious: role and enum values, what a hook returns, a response's exact JSON, the test helper to use. Give the file each fact comes from. The pipeline adds the exported types of files the document names; this section covers the rest. |
| `## Done` | Empty at first. After each piece, what now exists: routes, exported names, files. |
| `## Piece N: <name>` | One per piece: one sentence on what the user gets, then the exact behaviour, names, files, and the tests that prove it. Specific enough that two builders would produce the same interfaces. |

Keep the whole document under about 12,000 characters, and each piece section
under about 2,500. A run quotes the rules, the facts and one piece, and the
model's prompt is limited.

Write `sdlc/epics/<NNN>-<epic>.md` from `templates/status.md`, with every piece
`planned`. `<NNN>` is one more than the highest number in `sdlc/epics/` on the
default branch and on any open pull request, three digits, starting at `001`.

Check the anchors you will use resolve, before anyone reviews:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "../.github/actions/sdlc-stage")
import sdlc_stage as s
doc = open("docs/<epic>.md").read()
for a in ["rules-for-every-piece", "facts-the-plan-must-not-guess", "piece-1"]:   # and every piece-N
    print(a, "ok" if s.design_section(doc, a) else "MISSING OR AMBIGUOUS")
PY
```

`#piece-1` is ambiguous once there is a `## Piece 10`: from ten pieces up, use
the whole anchor (`#piece-1-<name>`), or two-digit numbers.

## 2. Gate: the user reviews the design

Commit the two files on your working branch and open a pull request into the
default branch, titled `<Epic name>: design in N pieces`. In the body list the
pieces, one line each, and the decisions you made that the user didn't state.

Then stop and tell the user: this is the review that matters most, because
every later run follows this document exactly. Apply their changes on the same
branch. Carry on only when the pull request is merged.

## 3. Build each piece, in order

For piece N:

1. **Sync.** `git fetch origin`, and check that the default branch holds the
   merged design document and piece N-1's pull request.
2. **Start the run** with an issue labelled `sdlc`:

   - Title: `<Epic name> piece N: <the piece's name>`. Keep it short; it
     becomes the feature's folder name.
   - Body:

     ```text
     design: docs/<epic>.md#rules-for-every-piece
     design: docs/<epic>.md#facts-the-plan-must-not-guess
     design: docs/<epic>.md#done
     design: docs/<epic>.md#piece-N
     ```

     Leave out `#done` while that section is empty.

   Without design references (step 0), put the document's path and
   "Piece N" in the title instead, and say "follow Piece N exactly".
3. **Record it.** When the `sdlc/<feature>/approved` tag appears, write the
   feature name and issue into the status file (`building`). Keep status-file
   changes local until step 7: they are not part of the feature branch.
4. **Check the design before building.** Read `intent.md`, `spec.md` and
   `plan.md` against the piece section:

   - `intent.md` ends with a `## Design` section listing your references;
   - every behaviour the piece asks for is in the spec, and nothing from a
     later piece is;
   - the plan's file paths, names and shapes match the code and the Facts
     section.

   A plan that contradicts the document or can't be built: tell the user what
   is wrong, fix the document if the document was unclear (through the default
   branch), and ask for a new plan with a `feature: <f>` / `start: plan` issue.
   A plan that is right except for a detail the code contradicts: build it,
   follow the code, and log the deviation.
5. **Build it** with the `sdlc-github` skill, from its step 2: phases, phase
   pull requests, Phase check, squash-merge, hand back.
6. **Report the pipeline's pull request** as `sdlc-github` does, and say which
   deviations and review concerns need the user's decision. Then wait for the
   merge. Subscribe to the pull request if the user wants you to watch it.
7. **After the merge, update the record** in one commit to the default branch
   (a small pull request if you can't push there):

   - the document: move what the piece built into `## Done` (routes, exported
     names, files, in a few lines), correct any Fact the build proved wrong,
     and adjust later piece sections if this piece changed what they build on;
   - the status file: the piece is `merged`, with its pull request, and its
     deviations in a line each.

   Later runs read these, so this step is part of the piece, not tidying.

## 4. Close the epic

When the last piece is merged:

1. Run the whole test suite on the default branch once and quote the result.
2. Give the user the closing checklist: everything the pipeline's checks
   couldn't do. Typical items: schema changes to apply, a first run against
   real data or services, secrets or settings to add, a manual look at each new
   screen. Take them from the deviations and "can't be tested here" notes you
   logged, not from a generic list.
3. Offer the tidy-up: close the finished `sdlc` issues, delete merged
   `phase/*` and `feature/*` branches. Do it only if they say yes.
4. Mark the status file `complete`.

## Resume

A new session, or a session after a long break, starts from the files:

1. Read `sdlc/epics/<NNN>-<epic>.md` and `docs/<epic>.md` on the default branch.
2. For the first piece that isn't `merged`: if it has a feature, look at its
   state (`git ls-remote origin 'refs/heads/feature/<f>' 'refs/heads/phase/<f>/*' 'refs/tags/sdlc/<f>/approved'`,
   its `build-log.md`, its open pull requests) and continue `sdlc-github` from
   there. If it has none, start it at step 3.
3. If another session may still be working on the epic, ask the user before
   you push anything.

## Gotchas

- **Two sessions on one epic** produce duplicate features. One session owns an
  epic at a time.
- **A piece that grows.** If a plan comes back with four full phases and still
  marks something `NOT COVERED`, the piece is too big. Split the section in
  the document, with the user's agreement, and run the smaller piece.
- **An earlier piece's test breaks.** A new piece can change behaviour an
  earlier test pinned. The Phase check runs only the phase's own tests, so
  this shows at the final verification. Fix it as `sdlc-github` says for a bug
  outside the plan, and add the affected test to the Facts section so later
  plans freeze or target it.
- **The document on a feature branch is the one from when the branch was
  cut.** A revision run reads it from there; merge the default branch into
  `feature/<f>` first if the document changed.
- **Schema changes.** Where the pipeline has no database, tests never run the
  real storage code. Say so in each affected piece's report and in the closing
  checklist.
