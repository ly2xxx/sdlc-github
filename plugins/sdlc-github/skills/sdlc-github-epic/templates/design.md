# <Epic name>

<Two or three sentences: who needs this and what they will be able to do.>
It is built in <N> pieces, one SDLC feature each, in order. Each piece builds on
the code the earlier ones merged: extend those files, never redesign them.

## Rules for every piece

- **<Area, e.g. The table / API / Dashboard>**: <the files and patterns to
  extend, with paths; what must not change>.
- **Who may do what**: <roles and permissions, as decided with the user>.
- **Tests**: <the framework, where tests go, what they must not need (network,
  database, secrets), and an existing test file to copy the style of>.
- **Never in scope**: <what this epic deliberately leaves out>.

## Facts the plan must not guess

Read from the code on <date>. Use these exactly.

- `<path/to/file>`: <a role or enum's exact values>.
- `<path/to/file>`: `<function or hook>` returns `<exact shape>`.
- `<METHOD /route>` responds with `<exact JSON shape>`.
- <The test helper or fixture to use, and its path>.

## Done

<Nothing yet. After each piece: what exists now, in a few lines: routes,
exported names, files.>

## Piece 1: <name>

<One sentence: what the user gets.>

- <Exact behaviour, names, parameters and files.>
- <Edge cases and who is refused.>
- <The tests that prove it, and the file they go in.>

## Piece 2: <name>

<As above.>
