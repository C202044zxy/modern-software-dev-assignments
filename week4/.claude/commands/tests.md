---
description: Run the backend test suite (fail-fast), then coverage if green
argument-hint: "[optional pytest path or -m marker, e.g. backend/tests/test_notes.py or 'not slow']"
allowed-tools: Bash(PYTHONPATH=. pytest:*), Bash(make test:*), Read
---

Run the test suite for this repo and report back. All commands run from the `week4/` directory and require `PYTHONPATH=.` (the backend uses package-relative imports).

## Steps

1. **Fail-fast run.** Run the tests, stopping at the first failure:

   ```bash
   PYTHONPATH=. pytest -q backend/tests --maxfail=1 -x $ARGUMENTS
   ```

   `$ARGUMENTS` is an optional path or `-m <marker>` selector. If empty, the whole `backend/tests` suite runs.

2. **If anything failed**, STOP. Do not run coverage. Instead:
   - Show the failing test name(s) and the key assertion/traceback line.
   - Read the relevant test and source file to diagnose the likely cause.
   - Summarize the failure and suggest 1–3 concrete next steps (which file/function to look at). Do **not** modify code unless the user asks.

3. **If green**, run coverage over the app package:

   ```bash
   PYTHONPATH=. pytest -q backend/tests --cov=backend/app --cov-report=term-missing $ARGUMENTS
   ```

   If `pytest-cov` is not installed, note that and skip coverage rather than failing.

## Output

- ✅/❌ overall status and the exact command(s) you ran.
- On failure: a short diagnosis + suggested next steps.
- On success: total coverage % and the 3 lowest-covered files (with missing-line ranges) as candidates for new tests.
