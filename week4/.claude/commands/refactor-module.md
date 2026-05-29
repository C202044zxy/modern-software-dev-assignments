---
description: Safely rename/move a Python module, update all imports, then lint + test
argument-hint: "<old_path> <new_path>  e.g. backend/app/services/extract.py backend/app/services/parser.py"
allowed-tools: Bash(git mv:*), Bash(make lint:*), Bash(make test:*), Bash(PYTHONPATH=. pytest:*), Bash(ruff:*), Bash(grep:*), Bash(rg:*), Read, Edit
---

Rename/move a module and fix every reference to it. Arguments: `$ARGUMENTS` = `<old_path> <new_path>` (two paths, space-separated). Run from the `week4/` directory.

If `$ARGUMENTS` does not contain exactly two paths, ask the user for the old and new path and stop.

## Steps

1. **Confirm the plan.** Derive the old and new module import paths (e.g. `backend.app.services.extract` → `backend.app.services.parser`). State what you're about to rename.

2. **Find all references** before moving anything, so you know the blast radius:

   ```bash
   rg -n "services\.extract|from .*extract import|import extract" backend
   ```

   (Adjust the pattern to the actual module name.) List every file that references the old module.

3. **Move the file** preserving history:

   ```bash
   git mv <old_path> <new_path>
   ```

4. **Update imports** in every referencing file (routers, tests, `main.py`, other services) to point at the new module path. Use Edit; keep changes minimal and import-only.

5. **Verify.** Run lint then tests:

   ```bash
   make lint
   make test
   ```

   If anything fails, fix the remaining references and re-run until green.

## Output

A checklist of:
- [ ] File moved (`old → new`)
- [ ] List of every file whose imports were updated
- [ ] `make lint` result
- [ ] `make test` result

End with any manual follow-ups (e.g. docs/CLAUDE.md mentions of the old name that are descriptive, not code).

## Safety

Use `git mv` (not `rm` + create) so the move is reversible via `git restore`/`git checkout`. Do not change behavior — imports and the filename only.
