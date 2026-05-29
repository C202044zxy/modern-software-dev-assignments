# Week 4 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## YOUR RESPONSES
### Automation #1 — Cooperating SubAgents: TestAgent + CodeAgent (TDD workflow)
a. Design inspiration (e.g. cite the best-practices and/or sub-agents docs)
> This automation is the **SubAgents** option from the assignment (Part C, Example 1: *TestAgent + CodeAgent*). It is inspired by the Claude Code **SubAgents overview** (https://docs.anthropic.com/en/docs/claude-code/sub-agents), which recommends role-specialized agents with their own system prompts, tools, and context, and the **Claude Code best practices** guide (https://www.anthropic.com/engineering/claude-code-best-practices), specifically its advice to write tests first, confirm they fail, then implement until they pass, and to give each agent a focused, tool-scoped role. The two agents also encode this repo's own documented workflow from `CLAUDE.md`: *"When asked to add an endpoint, first write a failing test, then implement, then run pre-commit."*

b. Design of each automation, including goals, inputs/outputs, steps
> **Goal:** turn any feature/bugfix request into a verified change via a clean test-driven hand-off, with a hard separation of concerns so neither agent can shortcut the other.
>
> Two agents are defined as Markdown files with YAML frontmatter (`name`, `description` with usage examples, `tools`, `model`, `color`):
> - **TestAgent** — `.claude/agents/test-author.md`. Tools: `Read, Write, Edit, Bash, Grep, Glob`. **Restricted to `backend/tests/` only.**
>   - *Input:* a described behavior change (e.g. a `docs/TASKS.md` item).
>   - *Steps:* restate the behavior as a testable spec → read `backend/tests/conftest.py` + the nearest existing test to match conventions → write the smallest failing tests using the `client` fixture (incl. edge cases like 404s) → run them and confirm they fail **for the right reason** (a behavior gap, not an import/collection error) → emit a hand-off.
>   - *Output:* failing test files + a hand-off report (test names, expected routes/status codes/response shapes, the exact pytest command, the "red" baseline output, and non-binding implementation hints).
> - **CodeAgent** — `.claude/agents/code-implementer.md`. Tools: `Read, Write, Edit, Bash, Grep, Glob`. **Owns `backend/app/`; must not edit tests.**
>   - *Input:* the TestAgent hand-off + the red test files.
>   - *Steps:* reproduce the red baseline (`make test`) → read the relevant router/schema/model/service → make the minimal change following the repo's documented schema→model/seed→router workflow (and the route-ordering / `model_validate` / 404-handling gotchas from `CLAUDE.md`) → run `make format`, `make lint`, then full `make test` until green.
>   - *Output:* the implementation + a report (checklist of changed files, final `make test` / `make lint` summary lines, any escalations). If a test seems wrong it escalates back rather than editing it.

c. How to run it (exact commands), expected outputs, and rollback/safety notes
> Both are invoked from within Claude Code (no shell command). Either let Claude auto-delegate based on the `description` fields, or invoke explicitly, e.g.:
> - "Use the **test-author** agent to write failing tests for TASKS.md item #5 (Notes CRUD: `PUT`/`DELETE /notes/{id}`)."
> - then: "Use the **code-implementer** agent to make those tests pass."
>
> *Expected output:* TestAgent leaves the suite **red** with a hand-off; CodeAgent leaves it **green + lint-clean** (`make test` → all passed, `make lint` → `All checks passed!`).
>
> *Rollback / safety:* changes are confined to the working tree — revert with `git checkout -- backend/` (or `git restore .`) / `git clean -fd` for new files; nothing is committed automatically. Safety is enforced structurally: TestAgent can only touch `backend/tests/`, CodeAgent never edits tests, both rely on the isolated per-test temp SQLite DB from `conftest.py` (production `data/app.db` is never touched), and every change is gated by `make lint` + `make test`.

d. Before vs. after (i.e. manual workflow vs. automated workflow)
> **Before (manual):** read the task, hand-write tests while guessing the fixture/route conventions, hand-write the endpoint in the same pass (easy to write the test *to* the code rather than the code *to* the test), then manually run pytest/ruff and iterate — with no enforced red→green discipline and a real risk of tweaking a test just to make it pass.
> **After (automated):** one request kicks off a disciplined pipeline — TestAgent specs the behavior as genuinely-failing tests with a documented red baseline, then CodeAgent implements the minimum to go green and self-verifies with lint + tests. The role split makes "writing the test to fit the code" structurally impossible and produces a written audit trail (red baseline → files changed → green summary) for free.

e. How you used the automation to enhance the starter application
> I ran the pair on **`docs/TASKS.md` item #5 (Notes CRUD enhancements)**. TestAgent added 6 failing tests to `backend/tests/test_notes.py` covering `PUT /notes/{id}` (200 + updated `NoteRead`, persistence, 404 on missing id) and `DELETE /notes/{id}` (204, removal verified via a follow-up GET 404, 404 on missing id), and confirmed they failed for the right reasons (405 for the missing routes, a no-op PUT, a non-deleting DELETE). CodeAgent then added `PUT /{note_id}` and `DELETE /{note_id}` handlers to `backend/app/routers/notes.py` (404 via `db.get`, update/delete, `NoteRead.model_validate`, `status_code=204`), honoring the documented route-ordering gotcha. Result: the notes resource gained full CRUD, with the suite going from **3 → 9 passing tests** and `make lint` clean.


### Automation #2
a. Design inspiration (e.g. cite the best-practices and/or sub-agents docs)
> TODO

b. Design of each automation, including goals, inputs/outputs, steps
> TODO

c. How to run it (exact commands), expected outputs, and rollback/safety notes
> TODO

d. Before vs. after (i.e. manual workflow vs. automated workflow)
> TODO

e. How you used the automation to enhance the starter application
> TODO


### *(Optional) Automation #3*
*If you choose to build additional automations, feel free to detail them here!*

a. Design inspiration (e.g. cite the best-practices and/or sub-agents docs)
> TODO

b. Design of each automation, including goals, inputs/outputs, steps
> TODO

c. How to run it (exact commands), expected outputs, and rollback/safety notes
> TODO

d. Before vs. after (i.e. manual workflow vs. automated workflow)
> TODO

e. How you used the automation to enhance the starter application
> TODO
