# Licensing

This repository is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).

## Free

- **Personal use** for research, experiments and testing, personal study, private
  entertainment, hobby projects and amateur pursuits, with no commercial application in view.
- **Noncommercial organisations**: charities, educational institutions, public research
  organisations, public safety or health organisations, environmental protection organisations
  and government institutions.

## Paid

Any other use, including use at or for a business, needs a commercial license. To ask for one,
contact [ly2xxx on GitHub](https://github.com/ly2xxx).

## Contributions

A contribution has to be licensable under both the PolyForm Noncommercial terms and the
commercial license, so outside pull requests need a contributor agreement first. Ask before
opening one.

## Publishing notes (for future reference)

1. **Your own marketplace.** No review, works right away. You make a public GitHub repo with
   three files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and
   `skills/sdlc-github/SKILL.md`. People add it from **Customize > Plugins > Add > Add
   marketplace**, or with `claude plugin marketplace add ly2xxx/<repo>` in Claude Code. It needs
   to be its own repo, since you didn't want the skill anywhere in `.github`.
2. **Anthropic's directory.** That's the "Anthropic Directory" stuff in your screenshot. You
   submit at claude.ai/directory/manage, which needs a paid plan (Pro or Max is fine) and a
   public GitHub repo. Every version gets an automated check and a security scan, and a human
   reviews your first listing. After that, merging to your branch publishes new versions. The
   "by Anthropic" plugins are a separate official marketplace that doesn't take submissions.
