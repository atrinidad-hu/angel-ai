# Sentry morning digest — instructions for Claude

Morning Sentry triage for a Humand mobile engineer: digest + root-cause analysis + spec + TDD fix for every NEW issue. Write every user-facing output in Spanish.

The scheduled task reads this file on every run; edits apply from the next run.

## Context
- Sentry org "humand" (region https://us.sentry.io), project "humand-app" only. Uses the Sentry connector in Claude.
- Paths (inside the task, with the remote-devices `device_bash` tool):
  - `ANGEL_AI` = `$HOME/mnt/angel-ai` (this repo)
  - `HUMAND_MOBILE` = `$HOME/mnt/humand-mobile` (the codebase)
- Read `$HUMAND_MOBILE/CLAUDE.md` first and follow its conventions (notably: never write unit tests for components that return JSX; test pure functions/utils, hooks, services, schemas, sagas, stores; extract logic into a utils/ helper or hook if needed). Existing specs live in `specs/<topic>/spec.md` — mirror their structure (Problem / Repro, Root cause, Fix, Tests, Risks).
- Tests run with: `NODE_OPTIONS=--no-experimental-webstorage node node_modules/.bin/jest <path> --ci --watchAll=false` (yarn is not on PATH in that shell). device_bash calls time out at ~180s, so run single test files, not the whole suite.
- The shell has no git credentials for GitHub (no fetch/push). Use the local `origin/develop` as the base and record its last commit date in each spec.
- NEVER touch the main checkout of humand-mobile: do not switch branches, stash, commit, or edit files in the main working tree (it may have uncommitted work). All code changes go in git worktrees. Deleting files is not permitted; don't try.

## Lookback window
Mondays: last 72 hours. Tuesday–Friday: last 24 hours.

## Step 1 — Digest (read-only in Sentry)
1. NEW issues: unresolved, first seen within the window.
2. SPIKING issues: unresolved, first seen before the window, with ~3x+ their recent daily average of events/users inside the window, or regressions (resolved issues that reappeared).
3. For each: title/error type, culprit, level, events and users in the window, first/last seen, release/environment, link.
4. URGENT = fatal/crash, many users affected, regression, sharp spike in the latest release, or core flows (login/auth, feed, chat, payroll, notifications).
Never resolve, assign, ignore or comment on Sentry issues.

## Step 2 — Deep analysis, NEW issues only (spiking issues stay digest-only)
Process in priority order (urgent first, then by users affected), up to 5 issues per run; list the rest as "pendientes de análisis". For each new issue:
a. Pull the issue details and latest event (stack trace, breadcrumbs, tags, release, device/OS) from Sentry.
b. Locate the code in the repo and determine the root cause. State a confidence level (alta/media/baja) and the evidence. If the cause is outside this repo (backend, third-party SDK, native crash with no JS frames, OS-specific), say so and skip the code steps.
c. Create an isolated worktree: `git -C $HUMAND_MOBILE worktree add .claude/worktrees/sentry-<SHORT_ID> -b sentry/<SHORT_ID>-<short-slug> origin/develop`, then symlink node_modules from the main repo into it (`ln -s ../../../node_modules`). If the branch/worktree already exists from a previous run, reuse it and don't redo finished work.
d. TDD inside the worktree:
   - Write a test that reproduces the bug. Run it and confirm it FAILS for the right reason (capture the failure output).
   - Implement the minimal fix. Run the test again and confirm it PASSES. Also run the existing test files next to the changed code to check nothing broke.
   - If a meaningful unit test is not possible (UI-only, native, needs a device), don't fake one: explain why and propose how to verify it (Maestro E2E, manual QA steps).
   - Commit locally on the worktree branch (message: `fix(<module>): <summary> [Sentry <SHORT_ID>]`). Do not push or open a PR.
e. Write `specs/sentry-<SHORT_ID>/spec.md` in the worktree (commit it too) with: Sentry link and metrics; Problem + repro; Root cause with file:line references and confidence; Fix applied and alternatives considered; Tests (what they cover + red/green evidence: the command and the relevant failing and passing output); Risks/side effects; and a clearly marked section "⚠️ Requiere validación humana" listing everything a person must confirm (low-confidence hypotheses, product/UX decisions, native/device verification, backend involvement, untested paths). If nothing needs validation, say so explicitly.

## Step 3 — Final report (Spanish)
Write it to `$ANGEL_AI/sentry-digest/reports/<today YYYY-MM-DD>.md` (overwrite if it exists; the folder is git-ignored — never commit it) AND return it as the final answer of the run:
- One-line summary (e.g. "2 urgentes, 5 nuevos, 3 con pico, 4 analizados").
- 🚨 Urgente, with a one-line reason each.
- Nuevos: per issue — link, users/events, root cause (1–2 lines + confidence), status (fix + tests verde / solo spec / fuera de este repo), branch and worktree path, spec path, and whether it requires human validation.
- Con pico: before vs. after numbers, with links.
- Pendientes de análisis, if any.
- A reminder that the branches are local only and must be reviewed, pushed and PR'd by a human.
If nothing notable happened, say so in one line (and still write the file).
