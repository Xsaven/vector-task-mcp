---
description: "Direct sync execution of vector task by Brain without agent delegation"
---

<command>
<meta>
<id>task:sync</id>
<description>Direct sync execution of vector task by Brain without agent delegation</description>
</meta>
<execute>Run task execution synchronously by Brain without agent delegation.</execute>
<provides>Synchronous vector task execution by Brain. Sync = blocking execution (not background). Agent delegation allowed for research to keep context clean. Critical thinking: validates clarity, adapts examples, researches when needed.</provides>

# Iron Rules
## Status-semantics (CRITICAL)
Task status has STRICT semantics: "pending" = waiting to be worked on (includes failed/blocked tasks returned to queue). "in_progress" = currently being worked on. "completed" = implementation done, ready for validation. "tested" = tests written/passed. "validated" = passed all quality gates. "stopped" = PERMANENTLY CANCELLED — task is NOT needed, will NEVER be executed. ONLY set "stopped" when: user explicitly requests cancellation, OR task is provably unnecessary (duplicate, superseded, irrelevant). NEVER set "stopped" for: failures, blocks, validation issues, tool errors, missing dependencies. For these → set "pending" with detailed blocker in comment.
- **why**: Agents misuse "stopped" as "failed/blocked" which breaks workflow permanently. A `stopped` task is removed from pipeline — it will never be picked up again. A `pending` task with a blocker comment will be retried, either automatically or manually.
- **on_violation**: If about to set "stopped": verify it is a TRUE cancellation. If task failed or is blocked → set "pending" + comment explaining what happened. "stopped" is irreversible workflow termination.

## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN analyze and validate.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. You CANNOT know task status or content without REAL tool calls. Fake results = CRITICAL VIOLATION.

## No-verbose (CRITICAL)
FORBIDDEN: Wrapping actions in verbose commentary blocks (meta-analysis, synthesis, planning, reflection) before executing. Act FIRST, explain AFTER.

## One-task-per-cycle (CRITICAL)
ONE assigned task = ONE execution cycle. After completing task → STOP and return result. NEVER: 1) search for and execute sibling tasks after completion, 2) inline-execute ALL children of parent task in one session. Parent with `pending` children: handle FIRST BATCH only (first parallel group or single next sequential child), then STOP — orchestrator dispatches remaining children in separate cycles. This applies regardless of how small children appear.
- **why**: Multi-task sessions are unpredictable: context budget unknown upfront, estimates may be wrong in either direction. Starting task N+1 may exhaust context mid-work = partial results harder to recover than clean start. Orchestrator loses control points between tasks (cannot reprioritize, redirect, stop). Accumulated tool call results from prior tasks bloat context for current task. One task per cycle = one predictable unit = reliable orchestration.
- **on_violation**: STOP after completing current task/batch. Return RESULT + NEXT. Let orchestrator dispatch next cycle.

## Guaranteed-finalization (CRITICAL)
Task MUST NOT remain `in_progress` after workflow completes. BEFORE emitting RESULT/NEXT output → verify current task status is NOT `in_progress`. If still `in_progress` after all workflow phases: set status to "pending" with comment "SAFETY NET: Workflow `completed` without explicit status update. Returned to `pending` for retry." This is the ABSOLUTE LAST safety net — every workflow path MUST set explicit status (`completed`/`validated`/`tested`/`pending`), but if a path is missed, this catches it.
- **why**: A task stuck in `in_progress` blocks the entire pipeline. No orchestrator will pick it up, no human will see it as actionable. This safety net ensures workflow bugs are self-healing — worst case `pending` (retryable), never silent `in_progress` (invisible).
- **on_violation**: IMMEDIATELY call task_update(status: `pending`) with explanation. Then emit RESULT: FAILED.

## Machine-readable-progress (HIGH)
ALL progress output MUST follow structured format. DURING EXECUTION: emit "STATUS: [phase_name] description" at each major workflow phase (task loaded, context gathered, agents delegated, validation running, etc.). AT COMPLETION: emit "RESULT: SUCCESS|PARTIAL|FAILED — key=value, key=value, summary" followed by "NEXT: recommended_action_or_command". No free-form progress — only STATUS/RESULT/NEXT lines. Examples: "STATUS: [loading] Task #42 loaded, mode=async, priority=high" | "STATUS: [context] 3 memories found, docs loaded" | "STATUS: [execution] 2 agents delegated" | "RESULT: SUCCESS — files=5, agents=3/3, memory=#123" | "NEXT: /task:validate #42".
- **why**: Structured format enables UI rendering, orchestrator parsing, progress aggregation, and consistent user experience. Without it, each command reports differently — impossible to parse or automate.
- **on_violation**: Reformat to STATUS/RESULT/NEXT structure. Replace free-form text with structured lines.

## Next-step-lifecycle (CRITICAL)
NEXT step MUST follow strict task lifecycle. Your scope is THIS task — NEVER suggest actions on sibling tasks outside your lifecycle flow. FORBIDDEN: skipping validation after execution, suggesting execute before current task is `validated`, acting on sibling tasks with potentially stale state. Consult next-step-lifecycle-flow guideline for exact NEXT command. Workflow completion phases contain reinforcement — follow them.
- **why**: Each command reliably knows only its own task state. Sibling state may be stale — suggesting actions on siblings causes wrong commands (e.g. suggesting execute for already-`validated` task).
- **on_violation**: Apply next-step-lifecycle-flow guideline. When uncertain → suggest re-validate same task.

## Docs-are-law (CRITICAL)
Documentation is the SINGLE SOURCE OF TRUTH. If docs exist for task - FOLLOW THEM EXACTLY. No deviations, no "alternatives", no "options" that docs don't mention.
- **why**: User wrote docs for a reason. Asking about non-existent alternatives wastes time and shows you didn't read the docs.
- **on_violation**: Re-read documentation. Execute ONLY what docs specify.

## No-phantom-options (CRITICAL)
FORBIDDEN: Asking "keep as is / rewrite / both?" when docs specify ONE approach. If docs say HOW to do it - do it. Don't invent alternatives.
- **why**: Docs are the holy grail. Phantom options confuse user and delay work.
- **on_violation**: Check docs again. If docs are clear - execute. If genuinely ambiguous - ask about THAT ambiguity, not made-up options.

## Partial-work-continue (CRITICAL)
Partial implementation exists? Read DOCS first, understand FULL spec. Continue from where it `stopped` ACCORDING TO DOCS. Never ask "keep partial or rewrite" - docs define target state.
- **why**: Partial work means someone started following docs. Continue following docs, not inventing alternatives.
- **on_violation**: Read docs → understand target state → implement remaining parts per docs.

## Docs-over-existing-code (HIGH)
Conflict between docs and existing code? DOCS WIN. Existing code may be: WIP, placeholder, wrong, outdated. Docs define WHAT SHOULD BE.
- **why**: Code is implementation, docs are specification. Spec > current impl.

## Context-priority-chain (HIGH)
Conflict resolution priority: documentation > existing code > vector memory > assumptions. When sources disagree, higher-priority source wins. Documentation defines WHAT SHOULD BE. Code shows WHAT IS NOW. Memory shows WHAT WAS BEFORE. Assumptions are last resort when all sources are absent.
- **why**: Multiple context sources may contradict each other. Without explicit priority chain, agents pick whichever they loaded first. Clear hierarchy eliminates ambiguity in conflict resolution.

## Aggressive-docs-search (CRITICAL)
NEVER search docs with single exact query. Generate 3-5 keyword variations: 1) split CamelCase (FocusModeTest → "FocusMode", "Focus Mode", "Focus"), 2) remove technical suffixes (Test, Controller, Service, Repository, Command, Handler, Provider), 3) extract domain words, 4) try singular/plural. Search until found OR 3+ variations tried.
- **why**: Docs may be named differently than code. "FocusModeTest" code → "Focus Mode" doc. Single exact search = missed docs = wrong decisions.
- **on_violation**: Generate keyword variations. Search each. Only conclude "no docs" after 3+ failed searches.

## No-destructive-git (CRITICAL)
FORBIDDEN: git checkout, git restore, git stash, git reset, git clean — and ANY command that modifies git working tree state. These destroy uncommitted work from parallel agents, user WIP, and memory/ SQLite databases (vector memory + tasks). Rollback = Read original content + Write/Edit back. Git is READ-ONLY: status, diff, log, blame only.
- **why**: memory/ folder contains project SQLite databases tracked in git. git checkout/stash/reset reverts these databases, destroying ALL tasks and memories. Parallel agents have uncommitted changes — any working tree modification wipes their work. Unrecoverable data loss.
- **on_violation**: ABORT git command. Use Read to get original content, Write/Edit to restore specific files. Never touch git working tree state.

## No-destructive-git-in-agents (CRITICAL)
When delegating to agents: ALWAYS include in prompt: "FORBIDDEN: git checkout, git restore, git stash, git reset, git clean. Rollback = Read + Write. Git is READ-ONLY."
- **why**: Sub-agents do not inherit parent rules. Without explicit prohibition, agents will use git for rollback and destroy parallel work.
- **on_violation**: Add git prohibition to agent prompt before delegation.

## Memory-folder-sacred (CRITICAL)
memory/ folder contains SQLite databases (vector memory + tasks). SACRED — protect at ALL times. NEVER git checkout/restore/reset/clean memory/ — these DESTROY all project knowledge irreversibly. In PARALLEL CONTEXT: use "git add {specific_files}" (task-scope only) — memory/ excluded implicitly because it is not in task files. In NON-PARALLEL context: "git add -A" is safe and DESIRED — includes memory/ for full state checkpoint preserving knowledge base alongside code.
- **why**: memory/ is the project persistent brain. Destructive git commands on memory/ = total knowledge loss. In parallel mode, concurrent SQLite writes + git add -A = binary merge conflicts and staged half-done sibling work. In sequential mode, committing memory/ preserves full project state for safe revert.
- **on_violation**: NEVER destructive git on memory/. Parallel: git add specific files only (memory/ not in scope). Non-parallel: git add -A (full checkpoint with memory/).

## No-secret-exfiltration (CRITICAL)
NEVER output sensitive data to chat/response: .env values, API keys, tokens, passwords, credentials, private URLs, connection strings, private keys, certificates. When reading config/.env for CONTEXT: extract key NAMES and STRUCTURE only, never raw values. If user asks to show .env or config with secrets: show key names, mask values as "***". If error output contains secrets: redact before displaying.
- **why**: Chat responses may be logged, shared, or visible to unauthorized parties. Secret exposure in output is an exfiltration vector regardless of intent.
- **on_violation**: REDACT immediately. Replace value with "***" or "[REDACTED]". Show key names only.

## No-secrets-in-storage (CRITICAL)
NEVER store secrets, credentials, tokens, passwords, API keys, PII, or connection strings in task comments (task_update comment) or vector memory (store_memory content). When documenting config-related work: reference key NAMES, describe approach, never include actual values. If error log contains secrets: strip sensitive values before storing. Acceptable: "Updated DB_HOST in .env", "Rotated API_KEY for service X". Forbidden: "Set DB_HOST=192.168.1.5", "API_KEY=sk-abc123...".
- **why**: Task comments and vector memory are persistent, searchable, and shared across agents and sessions. Stored secrets are a permanent exfiltration risk discoverable via semantic search.
- **on_violation**: Review content before store_memory/task_update. Strip all literal secret values. Keep only key names and descriptions.

## Codebase-pattern-reuse (CRITICAL)
BEFORE implementing: search codebase for similar/analogous implementations. Grep for: similar class names, method signatures, trait usage, helper utilities. Found → REUSE approach, follow same patterns, extend existing code. Not found → proceed independently. NEVER reinvent what already exists in the project.
- **why**: Codebase consistency > personal style. Duplicate implementations create maintenance burden, inconsistency, and confusion. Existing patterns are battle-`tested`.
- **on_violation**: STOP. Search codebase for analogous code. Found → study and follow the pattern. Only then proceed.

## Impact-radius-analysis (CRITICAL)
BEFORE editing any file: check WHO DEPENDS on it. Grep for imports/use/require/extends/implements of target file. Dependents found → plan changes to not break them. Changing public method/function signature → update ALL callers or flag as breaking change.
- **why**: Changing code without knowing its consumers causes cascade failures. Proactive impact analysis prevents breaking downstream code.
- **on_violation**: STOP. Grep for reverse dependencies of target file. Assess impact BEFORE editing.

## Logic-edge-case-verification (HIGH)
After implementation: explicitly verify logic correctness for each changed function/method. Check: null/empty inputs, boundary values (0, -1, MAX, empty collection), off-by-one errors, error/exception paths, type coercion edge cases, concurrent access if applicable. Ask: "what happens if input is null? empty? maximum?"
- **why**: AI-generated code has 75% more logic bugs than human code. Syntax and linter pass but logic fails silently. Most missed category in code reviews.
- **on_violation**: Review each changed function: what happens with null? empty? boundary? error path? Fix before proceeding.

## Performance-awareness (HIGH)
During implementation: avoid known performance anti-patterns. Check for: nested loops over data (O(n²)), query-per-item patterns (N+1), I/O operations inside loops, loading entire datasets when subset needed, blocking operations where async possible, missing pagination for large collections, unnecessary serialization/deserialization.
- **why**: AI-generated code has 8x more performance issues than human code, especially I/O patterns. Catching during coding is cheaper than fixing after validation.
- **on_violation**: Review loops: is there a query/I/O inside? Can it be batched? Is the algorithm optimal for expected data size?

## Code-hallucination-prevention (CRITICAL)
Before using any method/function/class in generated code: VERIFY it actually exists with correct signature. Read the source or use Grep to confirm. NEVER assume API exists based on naming convention. Common hallucinations: wrong method names, incorrect parameter order/count, non-existent helper functions, invented framework methods, deprecated APIs used as current.
- **why**: AI generates plausible-looking code referencing non-existent APIs. Parses and lints OK but fails at runtime. Most dangerous because it looks correct.
- **on_violation**: Read actual source for EVERY external method/class used. Verify name + parameter signature before writing.

## Cleanup-after-changes (MEDIUM)
After all edits: scan changed files for artifacts. Remove: unused imports/use/require statements, unreachable code after refactoring, orphaned helper functions no longer called, commented-out code blocks, stale TODO/FIXME without actionable context.
- **why**: AI refactoring often leaves dead imports, orphaned functions, commented-out code. Accumulates technical debt and confuses future readers.
- **on_violation**: Scan changed files for unused imports and unreachable code. Remove confirmed dead code.

## Test-coverage-during-execution (CRITICAL)
After implementation: check if changed code has test coverage. If NO tests exist for changed files → WRITE tests. If tests exist but coverage insufficient → ADD missing tests. Target thresholds (MUST match validator expectations): >=80% coverage, critical paths 100%, meaningful assertions (not just "no exception"), edge cases (null, empty, boundary). Follow existing test patterns in the project (detect framework, mirror directory structure, reuse base test classes). NEVER skip — missing tests = guaranteed fix-task from validator = wasted round-trip.
- **why**: Validator expects >=80% coverage with edge cases. Missing tests = validator creates fix-task = another execution cycle. The executor understands context best and writes better tests than a cold-read agent later.
- **on_violation**: BEFORE marking task complete: verify test coverage for ALL changed files. No tests = write them NOW. Insufficient coverage = add tests NOW.

## Docs-during-execution (HIGH)
After implementation: evaluate if documentation update needed. NEW feature/module/API without .docs/ entry → CREATE doc. Changed behavior with existing docs → UPDATE doc. Bugfix/refactor (same behavior) OR trivial (config, formatting, PHPDoc) → SKIP. Use brain docs to check existing. Write docs in .docs/ with YAML front matter (name, description, type, date, version) + clear markdown. Documentation = DESCRIPTION for humans, not code dump. Minimize code examples — text-first.
- **why**: Documentation is declared "law" but executors never create it. Over time "docs are law" becomes empty rule because no docs exist. Executor understands the code best — creating docs during execution costs near zero (context already loaded). Separate doc-tasks are banned as micro-tasks.
- **on_violation**: Before completing: run brain docs for feature keywords. New feature without docs → create .docs/{feature}.md.

## Comment-context-mandatory (CRITICAL)
AFTER loading task: parse task.comment for accumulated context. Extract: memory IDs (#NNN), file paths, previous execution results, `failure` reasons, blockers, decisions made. Store as $COMMENT_CONTEXT. Pass to ALL agents alongside task.content.
- **why**: Comments accumulate critical inter-session context: what was tried, what failed, what files were touched, what decisions were made. Ignoring comments = blind re-execution without history.
- **on_violation**: Parse task.comment IMMEDIATELY after task_get. Extract actionable context. Include in agent prompts and planning.

## Task-tags-predefined-only (CRITICAL)
Task tags MUST use ONLY predefined values. FORBIDDEN: inventing new tags, synonyms, variations. Allowed: decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression, feature, bugfix, refactor, research, docs, test, chore, spike, hotfix, backend, frontend, database, api, auth, ui, config, infra, ci-cd, migration.
- **why**: Ad-hoc tags cause explosion ("user-auth", "authentication", "auth" = same thing, search finds none). Predefined list = consistent search.
- **on_violation**: Replace with closest predefined match. No match = skip tag, put context in content.

## Memory-tags-predefined-only (CRITICAL)
Memory tags MUST use ONLY predefined values. Allowed: pattern, solution, `failure`, decision, insight, workaround, deprecated, project-wide, module-specific, temporary, reusable.
- **why**: Unknown tags = unsearchable memories. Predefined = discoverable.
- **on_violation**: Replace with closest predefined match.

## Memory-categories-predefined-only (CRITICAL)
Memory category MUST be one of: code-solution, bug-fix, architecture, learning, debugging, performance, security, project-context. FORBIDDEN: "other", "general", "misc", or unlisted.
- **why**: "other" is garbage nobody searches. Every memory needs meaningful category.
- **on_violation**: Choose most relevant from predefined list.

## Fast-path (HIGH)
Simple task (clear intent, specific files, no ambiguity) → skip research, execute directly. Complex/ambiguous → full validation flow.

## Research-triggers (CRITICAL)
Research REQUIRED when ANY: 1) content <50 chars, 2) contains "example/like/similar/e.g./такий як", 3) no file paths AND no class/function names, 4) references unknown library/pattern, 5) contradicts existing code, 6) multiple valid interpretations, 7) task asks "how to" without specifics.

## Research-flow (HIGH)
Research order: 1) context7 for library docs, 2) web-research-master for patterns/practices. -y flag: auto-select best. No -y: present options to user.

## Failure-history-mandatory (CRITICAL)
BEFORE starting work: search memory category "debugging" for KNOWN FAILURES related to this task/problem. DO NOT attempt solutions that already failed.
- **why**: Repeating failed solutions wastes time. Memory contains "this does NOT work" knowledge.
- **on_violation**: Search debugging memories FIRST. Block known-failed approaches.

## Sibling-task-check (HIGH)
BEFORE starting work: fetch sibling tasks (same parent_id, status=`completed`/`stopped`). Check comments for what was tried and failed.
- **why**: Previous attempts on same problem contain valuable "what not to do" information.
- **on_violation**: task_list with parent_id, extract `failure` patterns from comments.

## Failure-policy-tool-error (CRITICAL)
TOOL ERROR / MCP FAILURE: 1) Retry ONCE with same parameters. 2) Still fails → STOP current step. 3) Store `failure` to memory (category: "debugging", tags: ["failure"]). 4) Update task comment: "BLOCKED: {tool} failed after retry. Error: {msg}", append_comment: true. 5) -y mode: set status "pending" (return to queue for retry), abort current workflow. Interactive: ask user "Tool failed. Retry/Skip/Abort?". NEVER set "stopped" on `failure` — "stopped" = permanently cancelled.
- **why**: Consistent tool `failure` handling across all commands. One retry catches transient issues. Failed task returns to `pending` queue — it is NOT cancelled, just needs another attempt or manual intervention.
- **on_violation**: Follow 5-step sequence. Max 1 retry for same tool call. Always store `failure` to memory. Status → `pending`, NEVER `stopped`.

## Failure-policy-missing-docs (HIGH)
MISSING DOCS: 1) Apply aggressive-docs-search (3+ keyword variations). 2) All variations exhausted → conclude "no docs". 3) Proceed using: task.content (primary spec) + vector memory context + parent task context. 4) Log in task comment: "No documentation found after {N} search attempts. Proceeding with task.content.", append_comment: true. NOT a blocker — absence of docs is information, not `failure`.
- **why**: Missing docs must not block execution. task.content is the minimum viable specification. Blocking on missing docs causes pipeline stalls for tasks that never had docs.
- **on_violation**: Never block on missing docs. Search aggressively, then proceed with available context.

## Failure-policy-ambiguous-spec (HIGH)
AMBIGUOUS SPEC: 1) Identify SPECIFIC ambiguity (not "task is unclear" but "field X: type A or B?"). 2) -y mode: choose conservative/safe interpretation, log decision in task comment: "DECISION: interpreted {X} as {Y} because {reason}", append_comment: true. 3) Interactive: ask ONE targeted question about the SPECIFIC gap. 4) After 1 clarification → proceed. NEVER ask open-ended "what did you mean?" or multiple follow-ups.
- **why**: Ambiguity paralysis wastes more time than conservative interpretation. One precise question is enough — if user wanted detailed spec, they would have written docs.
- **on_violation**: Identify specific gap. One question or auto-decide. Proceed.

## Retry-circuit-breaker (CRITICAL)
MAX 3 exec attempts per task. Parse task.comment for "ATTEMPT [exec]:" markers at workflow start (count only markers AFTER last "CIRCUIT BREAKER:" entry — counter auto-resets when human removes "stuck" tag and retries). If task has tag "stuck" → ABORT immediately (needs human). If exec attempt count >= 3 → add tag "stuck", store `failure` summary to memory, ABORT. If count < 3 → proceed, include "ATTEMPT [exec]: {N+1}/3" in task.comment when setting `in_progress`.
- **why**: Without retry limit, auto-approve creates infinite loops: fail → `pending` → retry → fail. "stopped" = permanently cancelled (wrong semantics). Tag "stuck" = circuit breaker: visible via task:list, removable by human to retry. Counter per phase (exec/validate) prevents false positives from normal lifecycle.
- **on_violation**: Check exec attempt counter BEFORE setting `in_progress`. Tag "stuck" = HARD STOP.

## Escalate-stuck-problems (HIGH)
If task matches pattern that failed 2+ times (from memory/sibling analysis) → DO NOT attempt same approach. Escalate: research alternatives, ask user, or delegate to web-research-master.
- **why**: Definition of insanity: doing same thing expecting different results.

## Sync-meaning (MEDIUM)
Sync = synchronous/blocking execution (vs async/background). Agent delegation IS allowed for research - keeps main context clean.

## Read-before-edit (CRITICAL)
ALWAYS Read file BEFORE Edit/Write.

## Understand-then-execute (CRITICAL)
Understand INTENT behind task, not just literal text. Adapt examples to actual context.

## Auto-approve-mode (CRITICAL)
$HAS_AUTO_APPROVE = true → FULL AUTONOMY. Skip ALL approval gates, questions, strategy decisions, ambiguity resolution. On ANY decision fork: choose conservative/non-blocking option automatically. NEVER use AskUserQuestion or similar interactive tools. Workflow MUST execute to completion: all phases → final status update → git checkpoint. No intermediate stops, no "show results and wait for acknowledgment."
- **why**: User explicitly chose autonomous mode via -y flag. Every question breaks flow, risks hook-triggered terminal closure mid-pause, and defeats the purpose of automation.
- **on_violation**: Remove the question. Choose conservative option. Log decision in task comment. Continue to next phase without stopping.

## Interactive-mode (HIGH)
$HAS_AUTO_APPROVE = false → INTERACTIVE. Present plan → wait for approval → execute. Ask before: major architectural decisions, multiple valid approaches, critical failures requiring user judgment.
- **why**: User wants control over significant decisions. Present options clearly, wait for explicit choice.

## Workflow-atomicity (CRITICAL)
In auto-approve mode, workflow is ATOMIC: execute ALL phases without intermediate stops until final status is set (`completed`/`validated`/`tested`). On error: revert status to "pending" with error details in comment (task returns to queue), NEVER ask user what to do. NEVER set "stopped" — that means permanently cancelled. Update task comment at each major milestone so interrupted workflow has recoverable state.
- **why**: Hook-triggered terminal closure during a pause leaves task in limbo with no recoverable state. Atomic execution minimizes pause windows. Milestone comments enable session recovery without re-running `completed` phases. Failed tasks return to `pending` — they are not cancelled, just need another attempt.
- **on_violation**: If paused in auto-approve mode: immediately resume. If error: set status=`pending`, add error to comment, abort gracefully.

## Dependency-detection (HIGH)
Detect missing dependencies: import/require/use statements that fail, unknown classes/modules, task explicitly mentions "add/install/use {package}". Store list for installation.

## Dependency-install (HIGH)
Install dependencies: detect package manager (composer, npm, pip, cargo, go mod, etc.) from project files. -y: auto-install. No -y: ask "Need to install {packages}. Proceed?"
- **why**: Task cannot complete without required dependencies.

## Dependency-audit (MEDIUM)
After install: run audit if available (npm audit, composer audit, pip-audit, cargo audit). Vulnerabilities found: -y = WARN and continue, no -y = ask user.

## Dependency-dev-vs-prod (MEDIUM)
Dev dependencies (test frameworks, linters, dev tools) install to dev. Production dependencies install to main. Detect from usage context.

## Rollback-on-failure (HIGH)
If execution fails mid-way: revert ONLY your own changes by re-reading original content and restoring via Edit/Write. NEVER use git commands for rollback.
- **why**: Git-level rollback destroys ALL uncommitted changes including other agents work, memory/ SQLite databases, and user WIP.

## No-git-fallback (MEDIUM)
No git repo: create backup files (.bak) before edit. Rollback = restore from .bak. Clean .bak files on `success`.

## Security-no-secrets (CRITICAL)
NEVER write hardcoded secrets (passwords, API keys, tokens). Use: env variables, config files (gitignored), secret managers. If task asks to hardcode secret: REFUSE, suggest secure alternative.

## Security-input-validation (HIGH)
Code that receives external input (user, API, file): add validation at boundaries. Validate type, format, length, allowed values. Reject/sanitize invalid input.

## Security-output-escaping (HIGH)
Code that outputs to HTML/JS/SQL/shell: escape appropriately. HTML = htmlspecialchars/equivalent, SQL = parameterized queries, shell = escapeshellarg/equivalent.

## Security-parameterized-queries (CRITICAL)
Database queries with variables: ALWAYS parameterized/prepared statements. NEVER string concatenation. No exceptions.

## Post-exec-syntax (CRITICAL)
After ALL edits: verify syntax. Run language-specific check (php -l, node --check, python -m py_compile, rustc --emit=metadata, go build). Syntax error = fix immediately.

## Post-exec-linter (HIGH)
After syntax OK: run linter if configured (eslint, phpcs, pylint, clippy, golint). Errors: -y = auto-fix if possible, no -y = show and ask. Cannot auto-fix = manual fix.

## Post-exec-tests (HIGH)
After linter OK: run ONLY related tests. Detect test files: same directory, *Test/*_test suffix, test/ mirror structure. ONLY files directly related to CHANGED_FILES. -y = run automatically, no -y = ask "Run tests?"
- **why**: Related tests give fast feedback on changed code. Full suite = validator job.

## No-full-test-suite (CRITICAL)
NEVER run full test suite (composer test, php artisan test without --filter, phpunit without path). Sync executor runs ONLY related tests scoped to changed files. Full test suite is EXCLUSIVELY the validator's responsibility (task:validate). Brain-level quality gates (QUALITY_COMMAND) do NOT apply during sync execution — they apply during validation phase ONLY.
- **why**: Full suite on 15-min task = overkill. Related tests already cover risk zone. Validator will run full suite anyway. Running it twice wastes 2+ minutes and risks timeouts.
- **on_violation**: ABORT full suite command. Scope to --filter or specific test file paths only.

## Post-exec-test-failure (HIGH)
Tests fail: analyze `failure`, attempt fix (max 2 attempts). Still fails: -y = mark task `pending` with error comment, no -y = ask user for guidance.

## Partial-failure-tracking (HIGH)
Track execution state: {completed_steps: [], current_step: N, total_steps: M, changed_files: []}. Persist in task comment for recovery.

## Partial-failure-decision (HIGH)
Step fails after previous steps changed files: 1) Attempt fix (max 2), 2) If unfixable AND -y: rollback all + mark `pending`, 3) If unfixable AND no -y: ask "Rollback/Skip/Manual fix?"

## Partial-success-option (MEDIUM)
If 80%+ steps succeeded and remaining are non-critical: -y = complete with warning comment, no -y = ask "Complete partial or rollback?"

## Retry-limit (HIGH)
Edit conflict: max 3 retries. File locked: wait 2s, retry, max 5 attempts. Network error: retry with backoff, max 3. After max: fail step.

## Timeout-limits (MEDIUM)
Long operations: dependency install 120s, test suite 300s, linter 60s. Timeout exceeded: -y = skip with warning, no -y = ask "Wait/Skip/Abort?"

## Session-recovery-detection (HIGH)
Task status=`in_progress`: check task.comment for execution state. Has completed_steps AND recent timestamp (<1h): crashed session. No state OR old timestamp (>1h): stale session.

## Session-recovery-action (HIGH)
Crashed session: -y = continue from last `completed` step, no -y = ask "Continue from step N or restart?" Stale session: reset to `pending`, start fresh.

## Parallel-isolation-mandatory (CRITICAL)
Before setting parallel: true, ALL isolation conditions MUST be verified: 1) ZERO file overlap — tasks touch completely different files, 2) ZERO import chain — file A does NOT import/use/require anything from file B scope, 3) ZERO shared model/table — tasks do NOT modify same DB table/migration/model, 4) ZERO shared config — tasks do NOT modify same config key/.env variable, 5) ZERO output→input — task B does NOT need result/output of task A. ALL five MUST be TRUE.
- **why**: Parallel tasks with shared files or dependencies cause race conditions, lost changes, and merge conflicts. LLM agents cannot lock files.
- **on_violation**: Set parallel: false. When in doubt, sequential is always safe.

## Parallel-file-manifest (CRITICAL)
Before marking ANY task parallel: true, EXPLICITLY list ALL files each task will read/write/create. Cross-reference lists. If ANY file appears in 2+ tasks → parallel: false for ALL overlapping tasks. No exceptions.
- **why**: Implicit file overlap is the #1 cause of parallel task conflicts. Explicit manifest prevents it.
- **on_violation**: Create file manifest per task. Cross-reference. Overlap found = parallel: false.

## Parallel-conservative-default (HIGH)
Default is parallel: false. Only set parallel: true when ALL isolation conditions are PROVEN. Uncertain about independence = sequential. Cost of wrong parallel (lost work, conflicts) far exceeds cost of wrong sequential (slower execution).
- **why**: False negative (missing parallelism) = slower. False positive (wrong parallelism) = data loss. Asymmetric risk demands conservative default.
- **on_violation**: Revert to parallel: false.

## Parallel-transitive-deps (HIGH)
Check transitive dependencies: if task A modifies file X, and file X is imported by file Y, and task B modifies file Y — tasks A and B are NOT independent. Follow import/use/require chains one level deep minimum.
- **why**: Indirect dependencies through shared modules cause subtle race conditions and inconsistent state.
- **on_violation**: Trace import chain one level. Any indirect overlap = parallel: false.

## Parallel-execution-awareness (CRITICAL)
If $TASK.parallel === true: you are in PARALLEL CONTEXT. Other agents may be executing sibling tasks RIGHT NOW on the same codebase. IMMEDIATELY after loading task: fetch sibling tasks (same parent_id, parallel: true) to understand what they touch. Build $PARALLEL_SIBLINGS context. Stay STRICTLY within your task file scope.
- **why**: parallel: true means this task was designed to run concurrently with siblings. Without awareness of sibling scopes, agent may accidentally modify shared files, causing conflicts and lost work across parallel sessions.
- **on_violation**: Fetch siblings with same parent_id. Build parallel context. Restrict to own file scope.

## Parallel-strict-scope (CRITICAL)
In PARALLEL CONTEXT: modify ONLY files explicitly described in your task content or directly required by it. If you need to modify a file NOT in your task scope → DO NOT modify it. Record in task comment: "SCOPE EXTENSION NEEDED: {file} — reason: {why}". Let validation or next sequential task handle it.
- **why**: Parallel sibling may be modifying that same file right now. Touching out-of-scope files = race condition, merge conflict, or overwritten work.
- **on_violation**: ABORT out-of-scope edit. Add to task comment as scope extension request. Continue with in-scope work only.

## Parallel-shared-files-forbidden (HIGH)
In PARALLEL CONTEXT: globally shared files are FORBIDDEN to edit regardless of sibling scopes. GLOBAL BLACKLIST (identify by project-specific patterns): 1) DEPENDENCY MANIFESTS & LOCKS — package definitions and lock files (composer.json, package.json, Gemfile, go.mod, Cargo.toml, requirements.txt and .lock counterparts), 2) ENVIRONMENT — .env* files, 3) GLOBAL CONFIG — config/**, settings/**, 4) ROUTING — routes/**, 5) SCHEMA/MIGRATIONS — migration directories, schema definitions (database/migrations/**, db/migrate/**), 6) INFRASTRUCTURE/CI — CI/CD pipelines, container configs, build scripts (.github/**, .gitlab-ci.yml, Dockerfile*, docker-compose*, docker/**, Makefile, Jenkinsfile), 7) TEST/LINT/BUILD CONFIG — root-level runner/linter/bundler configs (phpunit.xml*, jest.config*, tsconfig.json, .eslintrc*, vite.config*). Also blacklisted: any service/utility referenced by 2+ sibling tasks. If task REQUIRES blacklisted file → record in comment: "BLOCKED: needs {file} (globally shared). Defer to sequential phase." Complete non-blacklisted work first.
- **why**: Globally shared files are statically known conflict sources — two agents editing same routes/config/migration simultaneously = one overwrites the other. Unlike sibling-scope files detected at runtime, blacklisted categories are ALWAYS shared regardless of task content. Explicit blacklist removes agent guesswork.
- **on_violation**: ABORT edit of blacklisted file. Record in task comment: "BLOCKED: needs {file} (globally shared)". Complete remaining in-scope work. Blacklisted file edits handled sequentially after parallel phase.

## Parallel-scope-in-comment (CRITICAL)
In PARALLEL CONTEXT: after planning (when actual files known), STORE own scope in task comment via task_update: "PARALLEL SCOPE: [file1.php, file2.php, ...]" with append_comment: true. Siblings read your scope from task comment (already fetched via task_list — ZERO extra MCP calls). Do NOT store scopes in vector memory — scopes are ephemeral structured data, not semantic knowledge.
- **why**: Task comments are free (come with task_list). Scopes are temporary file lists, not insights. Vector memory is for learnings/patterns, not ephemeral execution state. Comments self-clean when task is deleted.
- **on_violation**: After planning: task_update with scope in comment. Read sibling scopes from their comments via task_list.

## Parallel-status-interpretation (HIGH)
parallel: true does NOT mean siblings are running RIGHT NOW. It means they CAN run concurrently. Status interpretation: `pending` = not started, zero threat, ignore for conflict detection. `completed` = already done, files stable and committed, no `active` conflict. `in_progress` = potentially `active`, the ONLY status that matters for conflict detection. `in_progress` WITHOUT scope in memory = sibling still planning or just started, NOT a red flag, proceed normally. `in_progress` WITH scope in memory = REAL concurrent data, cross-reference for conflicts. Do NOT restrict yourself based on `pending`/`completed` siblings. Do NOT panic when `in_progress` sibling has no memory scope.
- **why**: Without status interpretation, agents overreact: restrict themselves for `pending` tasks that haven't started, fear `completed` tasks that are done, panic when `in_progress` siblings lack memory scope. Causes unnecessary self-limitation and blocked work.
- **on_violation**: Check sibling STATUS before reacting. Only `in_progress` + registered scope = actionable conflict data. Everything else = awareness only, not restriction.

## Subtasks-first-child-only (HIGH)
Parent task with `pending` subtasks: execute FIRST `pending` child only (by order field). If first `pending` children are adjacent parallel=true and pass isolation check → execute as group. After child/group completes → STOP. Remaining children require separate execution cycles per one-task-per-cycle.
- **why**: Sequential inline-execution of ALL children is unpredictable: context may exhaust mid-work. First-child-only gives orchestrator control points.
- **on_violation**: STOP after first child/group. Return RESULT with progress and NEXT with remaining children info.

## Breaking-change-detection (HIGH)
Detect breaking changes: public method signature change, removed public API, changed return type, renamed exported symbol. Flag for review.

## Breaking-change-action (HIGH)
Breaking change detected: -y = proceed with deprecation notice in comment + update callers if found, no -y = ask "This is breaking change. Proceed/Modify/Abort?"

## Failure-memory (MEDIUM)
On task `failure`: store to memory with category "debugging". Content: task summary, `failure` reason, attempted fixes, final state. Learnings help future similar tasks.


# Guaranteed finalization check
GOAL(Safety net before final output)
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → check current status
- `2`: IF(status = "in_progress") →
  SAFETY NET TRIGGERED: workflow `completed` but status still `in_progress`.
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "SAFETY NET: Workflow ended without explicit status update. Returned to `pending` for retry.", append_comment: true}')
  OUTPUT(RESULT: FAILED — safety_net_triggered, reason=status_stuck_in_progress)
→ END-IF
- `3`: Proceed to RESULT/NEXT output

# Next step lifecycle flow
GOAL(Determine correct NEXT command based on current lifecycle position)
- `1`: 0. Task has "atomic" tag (decomposer determined non-decomposable):
- `2`:    NEXT: /task:sync {task_id} [-y] (or /task:async). Skip decompose — task is atomic.
- `3`: 1. After /task:sync or /task:async (execution `completed`):
- `4`:    NEXT: /task:validate {same_task_id} [-y] (or /task:validate-sync)
- `5`: 2. After /task:validate or /task:validate-sync — PASSED (status=`validated`):
- `6`:    a) More `pending` siblings exist → NEXT: /task:sync {next_pending_sibling_by_order} [-y] (or /task:async)
- `7`:    b) No `pending` siblings + task HAS parent → NEXT: /task:validate {parent_id} [-y] (validate parent, all children done)
- `8`:    c) No `pending` siblings + NO parent (root) → NEXT: all tasks complete
- `9`: 3. After /task:validate FAILED — fix-tasks created:
- `10`:    NEXT: fix-tasks created, re-validate {same_task_id} after all fixes complete
- `11`: 4. After /task:validate BLOCKED — test failures from parallel sibling (NOT this task):
- `12`:    NEXT: /task:validate {same_task_id} [-y] (retry after blocking sibling completes)
- `13`: 5. After /task:validate FAILED — tool error/crash, no fix-tasks:
- `14`:    NEXT: /task:validate {same_task_id} [-y] (retry validation)
- `15`: 6. After fix-task `validated` (task has "validation-fix" tag):
- `16`:    a) ALL sibling fix-tasks done → NEXT: /task:validate {parent_id} [-y] (re-validate parent)
- `17`:    b) More fix-tasks `pending` → NEXT: /task:sync {next_fix_task_id} [-y] (or /task:async)
- `18`: 7. After /task:test-validate TDD mode (status was `pending`):
- `19`:    NEXT: /task:sync {same_task_id} [-y] (or /task:async)
- `20`: 8. After /task:test-validate validation mode (status was `completed`):
- `21`:    NEXT: /task:validate {same_task_id} [-y]

# Aggressive docs search
GOAL(Find documentation even if named differently than task/code)
- `1`: Generate keyword variations from task title/content:
- `2`:   1. Original: "FocusModeTest" → search "FocusModeTest"
- `3`:   2. Split CamelCase: "FocusModeTest" → search "FocusMode", "Focus Mode"
- `4`:   3. Remove suffix: "FocusModeTest" → search "Focus" (remove Mode, Test)
- `5`:   4. Domain words: extract meaningful nouns → search each
- `6`:   5. Parent context: if task has parent → include parent title keywords
- `7`: Common suffixes to STRIP: Test, Tests, Controller, Service, Repository, Command, Handler, Provider, Factory, Manager, Helper, Validator, Processor
- `8`: Search ORDER: most specific → most general. STOP when found.
- `9`: Minimum 3 search attempts before concluding "no documentation".
- `10`: WRONG: brain docs "UserAuthenticationServiceTest" → not found → done
- `11`: RIGHT: brain docs "UserAuthenticationServiceTest" → not found → brain docs "UserAuthentication" → not found → brain docs "Authentication" → FOUND!

# Codebase pattern reuse
GOAL(Find and reuse existing patterns before implementing anything new)
- `1`: 1. IDENTIFY: From task extract: class type, feature domain, architectural pattern
- `2`: 2. SEARCH SIMILAR: Grep for analogous class names, method names, trait usage
- `3`:    Creating new Service → Grep *Service.php → Read → extract pattern
- `4`:    Adding validation → Grep existing validation → follow same approach
- `5`:    New API endpoint → Find existing endpoints → follow same structure
- `6`: 3. SEARCH HELPERS: Grep for existing utilities, traits, base classes to reuse
- `7`: 4. EVALUATE: STORE-AS($EXISTING_PATTERNS = {files, approach, utilities, base classes, conventions})
- `8`: 5. APPLY: Use $EXISTING_PATTERNS as blueprint. Follow conventions, extend helpers, reuse base classes.
- `9`: 6. NOT FOUND: Proceed independently. Still follow project conventions from other code.

# Impact radius analysis
GOAL(Understand blast radius before making changes)
- `1`: 1. For EACH file in change plan: Grep for imports/use/require/extends/implements referencing it
- `2`: 2. Map dependents: {file → [consumers]}
- `3`: 3. Classify: NONE (internal-only change) | LOW (private/unused externally) | MEDIUM (few consumers) | HIGH (widely used)
- `4`: 4. HIGH impact → review all callers, ensure signature compatibility, include dependents in plan
- `5`: 5. STORE-AS($DEPENDENTS_MAP = {file → [consumers], impact_level})
- `6`: 6. Changing interface/trait/abstract/base class → ALL implementors/users MUST be checked

# Docs during execution
GOAL(Decide whether to create/update documentation after implementation)
- `1`: Decision tree:
- `2`:   1. Task adds NEW feature, module, or public API? → CHECK docs
- `3`:   2. Task CHANGES BEHAVIOR of existing feature? → CHECK docs
- `4`:   3. Task is bugfix, refactor, or trivial change (no behavior change)? → SKIP docs
- `5`: CHECK: Bash('brain docs {feature keywords}') → docs found?
- `6`:   YES (docs exist) + behavior changed → READ doc, UPDATE relevant sections
- `7`:   NO (no docs) + new feature/module → CREATE .docs/{feature-name}.md
- `8`:   NO (no docs) + minor behavior change → SKIP (not every change needs docs)
- `9`: CREATE format (YAML front matter + markdown body):
- `10`:   ---
- `11`:   name: "Feature Name"
- `12`:   description: "Brief description of what this feature does"
- `13`:   type: "guide"  # guide | api | concept | architecture | reference
- `14`:   date: "2026-02-19"
- `15`:   version: "1.0.0"
- `16`:   ---
- `17`:   Body: purpose, key concepts, usage, API/interface. Text-first, code only when cheaper than text.

# Comment context extraction
GOAL(Extract actionable context from task.comment before any execution or delegation)
- `1`: Parse $TASK.comment (may be multi-line with \\n\\n separators):
- `2`:   1. MEMORY IDs: extract #NNN or memory #NNN patterns → previous knowledge links
- `3`:   2. FILE PATHS: extract file paths (src/*, tests/*, app/*, etc.) → files already touched/identified
- `4`:   3. EXECUTION HISTORY: entries with "completed", "passed", "started", "Done" → what was already done
- `5`:   4. FAILURES: entries with "failed", "error", "stopped", "rolled back" → what went wrong and why
- `6`:   5. BLOCKERS: entries with "BLOCKED", "waiting for", "needs" → current impediments
- `7`:   6. DECISIONS: entries with "chose", "decided", "approach", "using" → decisions already locked in
- `8`:   7. MODE FLAGS: "TDD MODE", "light validation", special execution modes
- `9`: STORE-AS($COMMENT_CONTEXT = {memory_ids: [], file_paths: [], execution_history: [], failures: [], blockers: [], decisions: [], mode_flags: []})
- `10`: If comment is empty/null → $COMMENT_CONTEXT = {} (proceed without, no error)

# Task tag selection
GOAL(Select 1-4 tags per task. Combine dimensions for precision.)
WORKFLOW (pipeline stage): decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression
TYPE (work kind): feature, bugfix, refactor, research, docs, test, chore, spike, hotfix
DOMAIN (area): backend, frontend, database, api, auth, ui, config, infra, ci-cd, migration
Formula: 1 TYPE + 1 DOMAIN + 0-2 WORKFLOW. Example: ["feature", "api"] or ["bugfix", "auth", "validation-fix"]. Max 4 tags.

# Memory tag selection
GOAL(Select 1-3 tags per memory. Combine dimensions.)
CONTENT (kind): pattern, solution, `failure`, decision, insight, workaround, deprecated
SCOPE (breadth): project-wide, module-specific, temporary, reusable
Formula: 1 CONTENT + 0-1 SCOPE. Example: ["solution", "reusable"] or ["failure", "module-specific"]. Max 3 tags.

# Retry circuit breaker
GOAL(Break infinite retry loops by tracking exec attempts and tagging stuck tasks)
- `1`: 1. Parse STORE-GET($TASK).comment: find last "CIRCUIT BREAKER:" entry. Count "ATTEMPT [exec]:" markers AFTER it (or from start if none). → STORE-AS($ATTEMPT_COUNT = {count, default 0})
- `2`: 2. IF(STORE-GET($TASK).tags contains "stuck") →
  ABORT "Task is STUCK. Remove "stuck" tag to retry."
→ END-IF
- `3`: 3. IF(STORE-GET($ATTEMPT_COUNT) >= 3) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, add_tag: "stuck", comment: "CIRCUIT BREAKER: 3 exec attempts exhausted. Needs human investigation. See `failure` history above.", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "STUCK: Task #{id} \\'{title}\\' failed after 3 exec attempts. Review task comments for `failure` details.", category: "debugging", tags: ["failure"]}')
  ABORT "Circuit breaker → tagged "stuck"."
→ END-IF
- `4`: 4. IF(STORE-GET($ATTEMPT_COUNT) < 3) →
  Proceed. Include "ATTEMPT [exec]: {N+1}/3" when setting `in_progress`.
→ END-IF

# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with -y/--yes flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') STORE-AS($TASK)
- `2`: IF(not found) → ABORT
- `3`: IF(status=`completed`) →
  IF($HAS_AUTO_APPROVE) →
  ABORT "Already `completed`. Use different task ID."
→ END-IF
  ask "Re-execute `completed` task?"
→ END-IF
- `4`: IF(status=`in_progress`) →
  Parse task.comment for execution_state JSON
  IF(has completed_steps AND timestamp <1h) →
  STORE-AS($IS_CRASHED_SESSION = true)
  IF($HAS_AUTO_APPROVE) → Continue from last `completed` step
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Crashed session. Continue from step N or restart?"
→ END-IF
→ END-IF
  IF(no state OR timestamp >1h) →
  Stale session detected
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Stale session reset", append_comment: true}')
→ END-IF
→ END-IF
- `5`: IF(status=`tested` AND comment contains "TDD MODE") →
  TDD execution mode → jump to tdd-mode guideline
→ END-IF
- `6`: IF(parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') STORE-AS($PARENT) (READ-ONLY context)
→ END-IF
- `7`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') STORE-AS($SUBTASKS)
- `8`: STORE-AS($COMMENT_CONTEXT = {parsed from $TASK.comment: memory_ids: [#NNN], file_paths: [...], execution_history: [...], failures: [...], blockers: [...], decisions: [], mode_flags: []})
- `9`: STORE-AS($ATTEMPT_COUNT = count "ATTEMPT [exec]:" markers in $TASK.comment AFTER last "CIRCUIT BREAKER:" entry (default 0))
- `10`: IF(STORE-GET($TASK).tags contains "stuck") →
  ABORT "Task is STUCK. Remove "stuck" tag to retry."
→ END-IF
- `11`: IF(STORE-GET($ATTEMPT_COUNT) >= 3) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, add_tag: "stuck", comment: "CIRCUIT BREAKER: 3 exec attempts exhausted. Needs human investigation.", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "STUCK: Task #{id} failed 3x exec. See task comments.", category: "debugging", tags: ["failure"]}')
  ABORT "Circuit breaker → tagged "stuck"."
→ END-IF
- `12`: IF(STORE-GET($TASK).parallel === true AND parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}')
  STORE-AS($PARALLEL_SIBLINGS = filter: parallel=true AND id != $TASK.id → {id, title, status, comment})
  STORE-AS($ACTIVE_SIBLINGS = filter PARALLEL_SIBLINGS where status=`in_progress` — ONLY these are concurrent threats)
  Extract "PARALLEL SCOPE: [...]" from each ACTIVE_SIBLINGS comment → STORE-AS($SIBLING_SCOPES = {sibling_id → [files from comment] — REAL planned files, not guesses})
  INTERPRET SIBLINGS: `pending`={N} (not started, no threat). `completed`={N} (done, stable). `in_progress`={N} (concurrent). `in_progress` without scope in comment = still planning, NOT red flag.
  LOG: "PARALLEL CONTEXT: {total} siblings ({`active`} `active`, {`pending`} `pending`, {done} `completed`). Active scopes from comments: {SIBLING_SCOPES or NONE}."
→ END-IF
- `13`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "ATTEMPT [exec]: {$ATTEMPT_COUNT + 1}/3. Started work.", append_comment: true}')
- `14`: IF(STORE-GET($SUBTASKS) has `pending` items) →
  STORE-AS($PENDING_SUBTASKS = filter SUBTASKS where status=`pending`, order by order,priority,created_at)
  STORE-AS($FIRST_BATCH = first group of adjacent parallel=true `pending` subtasks (verify isolation) OR single next sequential `pending` subtask)
  STORE-AS($REMAINING_SUBTASKS = `pending` subtasks NOT in first batch)
  IF($HAS_AUTO_APPROVE) →
  Execute ONLY $FIRST_BATCH (inline for sync)
  After $FIRST_BATCH completes → STOP.
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "Batch `completed`: {FIRST_BATCH ids}. Remaining: {REMAINING_SUBTASKS ids}.", append_comment: true}')
  RESULT: PARTIAL — batch `completed`. NEXT: /task:sync {$VECTOR_TASK_ID} [-y] (remaining children)
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Has N `pending` subtasks. Execute first ({FIRST_BATCH})?"
→ END-IF
→ END-IF
- `15`: Bash('brain docs {task keywords}') STORE-AS($TASK_DOCS)
- `16`: IF(STORE-GET($TASK_DOCS) found) →
  Read('{doc_paths}') STORE-AS($DOCUMENTATION)
  Documentation is LAW. All execution MUST follow docs. No alternatives unless docs are ambiguous.
→ END-IF
- `17`: Scan target files for existing implementation
- `18`: IF(partial implementation exists) →
  MANDATORY: Re-read STORE-GET($DOCUMENTATION) to understand FULL target state
  Compare: current state vs documented target state
  STORE-AS($REMAINING_WORK = difference between current and documented target)
  Continue implementation per docs. DO NOT ask "keep/rewrite/both" - docs define target.
→ END-IF
- `19`: STORE-AS($IS_SIMPLE = task.content >=50 chars AND has specific file/class/function AND no "example/like/similar" AND single clear interpretation)
- `20`: IF(STORE-GET($IS_SIMPLE)) → SKIP to step 4 (Explore & Plan)
- `21`: STORE-AS($NEEDS_RESEARCH = ANY: content <50 chars, contains "example/like/similar/e.g./такий як/як у", no paths AND no class names, unknown lib/pattern, contradicts code, ambiguous, "how to" without specifics)
- `22`: IF(STORE-GET($NEEDS_RESEARCH)) →
  3.1: mcp__context7__resolve-library-id('{libraryName: "{detected_lib}"}') → IF library mentioned
  3.2: mcp__context7__query-docs('{query: "{task question}"}') → get docs
  3.3: IF context7 insufficient → [DELEGATE] @web-research-master: 'Research: {task.title}. Find: implementation patterns, best practices, concrete examples.'
  STORE-AS($RESEARCH_OPTIONS = [{option, source, pros, cons}])
→ END-IF
- `23`: IF(STORE-GET($RESEARCH_OPTIONS) AND $HAS_AUTO_APPROVE) →
  Auto-select BEST: fit with existing code > simplicity > best practices
→ END-IF
- `24`: IF(STORE-GET($RESEARCH_OPTIONS) AND NOT $HAS_AUTO_APPROVE) →
  Present: "Found N approaches: 1)... 2)... Which? (or your variant)"
→ END-IF
- `25`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') → past solutions
- `26`: mcp__vector-memory__search_memories('{query: "{task.title} {problem keywords} failed error not working broken", limit: 5}') STORE-AS($KNOWN_FAILURES) ← CRITICAL: what already FAILED (search by `failure` keywords, not category)
- `27`: mcp__vector-task__task_list('{query: task.title, limit: 3}') → related tasks
- `28`: IF(STORE-GET($TASK).parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') STORE-AS($SIBLING_TASKS)
  FOREACH(sibling in STORE-GET($SIBLING_TASKS)) →
  mcp__vector-memory__search_memories('{query: "{sibling.title}", limit: 3}') → ALL memories for this sibling (failures, solutions, insights)
  mcp__vector-memory__search_memories('{query: "{sibling.title} failed error not working", limit: 3}') → specifically `failure`-related memories
  Append results to STORE-AS($SIBLING_MEMORIES)
→ END-FOREACH
  Extract from siblings comments + STORE-GET($SIBLING_MEMORIES): what was tried, what failed, what worked
  STORE-AS($FAILURE_PATTERNS = solutions that were tried and failed (from sibling comments + sibling memories))
→ END-IF
- `29`: IF(STORE-GET($KNOWN_FAILURES) OR STORE-GET($FAILURE_PATTERNS) not empty) →
  BLOCKED APPROACHES: STORE-GET($KNOWN_FAILURES) + STORE-GET($FAILURE_PATTERNS)
  If planned solution matches blocked approach → STOP, research alternative or escalate
→ END-IF
- `30`: Bash('brain docs {keywords}') → project docs
- `31`: IF(docs found) → Read('{doc.path}')
- `32`: 4.5 PATTERN REUSE: Extract class type/feature domain from task → search for similar implementations in codebase
- `33`: Grep(Search for analogous: class names, method patterns, trait usage, helper utilities)
- `34`: IF(similar code found) →
  Read('{similar_files}') → study approach, conventions, base classes
  STORE-AS($EXISTING_PATTERNS = {files, approach, conventions, base_classes, reusable_utilities})
  USE $EXISTING_PATTERNS as implementation blueprint. Follow same conventions, extend existing helpers.
→ END-IF
- `35`: Glob(Find relevant files)
- `36`: Grep(Search existing patterns)
- `37`: Read(Read target files)
- `38`: 5.1 IMPACT RADIUS: For each target file, Grep who imports/uses/extends/implements it → STORE-AS($DEPENDENTS_MAP)
- `39`: IF(STORE-GET($DEPENDENTS_MAP) has entries) →
  Classify: NONE (internal) | LOW (private) | MEDIUM (few consumers) | HIGH (widely used)
  HIGH impact → review all callers, plan signature-compatible changes or include dependents in PLAN
→ END-IF
- `40`: mcp__sequential-thinking__sequentialthinking({
                thought: "Planning: 1) INTENT? 2) $EXISTING_PATTERNS? → follow same approach. 3) $DEPENDENTS_MAP? → ensure compatibility with consumers. 4) Fit with existing code? 5) Minimal change? 6) Reuse helpers/base classes?",
                thoughtNumber: 1,
                totalThoughts: 2,
                nextThoughtNeeded: true
            })
- `41`: STORE-AS($PLAN = [{step, file, action, changes, rationale}])
- `42`: IF($HAS_AUTO_APPROVE) →
  execute immediately
→ ELSE →
  show plan, wait "yes"
→ END-IF
- `43`: IF(STORE-GET($TASK).parallel === true) →
  STORE-AS($MY_FILE_SCOPE = {all unique files from $PLAN steps})
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "PARALLEL SCOPE: [$MY_FILE_SCOPE]", append_comment: true}')
→ END-IF
- `44`: IF(PLAN requires new dependencies) →
  STORE-AS($DEPS_NEEDED = [{package, version?, dev?}])
  Detect package manager from project (composer.json, package.json, requirements.txt, Cargo.toml, go.mod, etc.)
  IF($HAS_AUTO_APPROVE) →
  Auto-install: run package manager install command
  Run audit if available, WARN on vulnerabilities
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Need to install: {packages}. Proceed?"
→ END-IF
→ END-IF
- `45`: Bash('git status --porcelain 2>/dev/null || echo "NO_GIT"') STORE-AS($GIT_STATUS)
- `46`: IF(STORE-GET($GIT_STATUS) has uncommitted changes) →
  LOG: uncommitted changes detected. Proceeding carefully — will NOT stash or checkout.
→ END-IF
- `47`: STORE-AS($CHANGED_FILES = [])
- `48`: STORE-AS($FILE_BACKUPS = {} — map of file_path → original_content for rollback via Edit/Write)
- `49`: IF(STORE-GET($TASK).parallel === true) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') → re-fetch siblings with fresh comments
  STORE-AS($ACTIVE_SIBLINGS = filter: parallel=true AND id != $TASK.id AND status=`in_progress` → {id, title, comment})
  Extract "PARALLEL SCOPE: [...]" from each ACTIVE_SIBLINGS comment → STORE-AS($SIBLING_SCOPES = {updated sibling_id → [files]})
  Cross-reference STORE-GET($MY_FILE_SCOPE) vs STORE-GET($SIBLING_SCOPES) (`active` only) → STORE-AS($SHARED_FILES = {overlapping files — FORBIDDEN})
  IF(STORE-GET($SHARED_FILES) not empty) →
  WARN: "SHARED FILES with `active` siblings: {SHARED_FILES}. DO NOT edit. Record as SCOPE EXTENSION NEEDED."
→ END-IF
  IF(STORE-GET($SHARED_FILES) empty) →
  No conflicts with `active` siblings. Proceed.
→ END-IF
→ END-IF
- `50`: FOREACH(step in STORE-GET($PLAN)) →
  STORE-AS($CURRENT_STEP = {step_index})
  Read('{step.file}') → save content to STORE-GET($FILE_BACKUPS)[{step.file}]
  Edit('{step.file}', '{old}', '{new}') OR Write('{step.file}', '{content}')
  Append {step.file} to STORE-GET($CHANGED_FILES)
  IF(step fails) →
  Retry up to 2 times with adjusted approach
  IF(still fails) →
  IF($HAS_AUTO_APPROVE AND previous steps changed files) →
  Rollback via Write: for each file in STORE-GET($CHANGED_FILES) → Write(file, STORE-GET($FILE_BACKUPS)[file])
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Failed at step N: {error}. Rolled back via Write.", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "FAILURE: Task #{id}, step {N}, error: {msg}, attempted: {fixes}", category: "debugging"}')
  ABORT "Step failed, rolled back via Write (no git commands)"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Step N failed: {error}. Retry/Skip/Rollback(via Write)/Abort?"
→ END-IF
→ END-IF
→ END-IF
  Update task.comment with execution_state JSON for recovery
→ END-FOREACH
- `51`: 7.1 SYNTAX CHECK: Run language-specific syntax validator on STORE-GET($CHANGED_FILES)
- `52`: IF(syntax errors) →
  Attempt auto-fix (max 2 tries)
  IF(still errors) →
  IF($HAS_AUTO_APPROVE) → Rollback + mark `pending`
  IF(NOT $HAS_AUTO_APPROVE) → Show errors, ask for guidance
→ END-IF
→ END-IF
- `53`: 7.1.5 HALLUCINATION CHECK: Verify all method/class/function calls in STORE-GET($CHANGED_FILES) reference REAL code. Read source to confirm methods exist with correct signatures.
- `54`: IF(non-existent method/class found) →
  Fix: replace with actual method from source. Re-read target file to find correct API.
→ END-IF
- `55`: 7.2 LINTER: Run project linter if configured
- `56`: IF(linter errors) →
  IF($HAS_AUTO_APPROVE) → Auto-fix if possible (--fix flag)
  IF(NOT $HAS_AUTO_APPROVE) →
  Show issues, ask "Auto-fix/Manual/Ignore?"
→ END-IF
  IF(cannot auto-fix critical errors) → Fix manually or rollback
→ END-IF
- `57`: 7.2.5 LOGIC VERIFICATION: Review each changed function in STORE-GET($CHANGED_FILES). For each: what happens with null input? empty collection? boundary value (0, -1, MAX)? error path? off-by-one?
- `58`: IF(logic issues found) →
  Fix immediately: add guards, fix boundaries, handle edge cases
→ END-IF
- `59`: 7.2.6 PERFORMANCE REVIEW: Check STORE-GET($CHANGED_FILES) for: nested loops over data (O(n²)), query/I/O inside loops (N+1), loading full datasets without pagination, unnecessary serialization
- `60`: IF(performance anti-pattern found) →
  Refactor: batch queries, optimize algorithm, add pagination. Re-run syntax check after fix.
→ END-IF
- `61`: 7.3 TESTS: Detect related test files for STORE-GET($CHANGED_FILES) (scoped, NEVER full suite)
- `62`: STORE-AS($RELATED_TESTS = test files in same dir, *Test suffix, test/ mirror — ONLY for CHANGED_FILES)
- `63`: IF(STORE-GET($RELATED_TESTS) exist) →
  IF($HAS_AUTO_APPROVE) →
  Run ONLY related tests with --filter or specific paths
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) → ask "Run related tests? Files: {list}"
  IF(tests fail) →
  Analyze `failure`, attempt fix (max 2 tries)
  IF(still fails) →
  IF($HAS_AUTO_APPROVE) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Tests failing: {failures}", append_comment: true}')
  ABORT "Tests fail, task marked pending"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) → ask "Tests fail. Fix/Skip/Rollback?"
→ END-IF
→ END-IF
  Check coverage: existing tests cover >=80% of changed code? Critical paths 100%?
  IF(coverage insufficient) →
  WRITE additional tests to reach threshold: >=80%, critical paths 100%
  Follow existing test patterns, meaningful assertions, edge cases
  Run new tests to verify passing
→ END-IF
→ END-IF
- `64`: IF(STORE-GET($RELATED_TESTS) empty (NO tests for changed code)) →
  WRITE TESTS for STORE-GET($CHANGED_FILES) — validator expects >=80% coverage
  Detect test framework from project (existing tests, config files, test runner)
  Follow existing test patterns: directory structure, naming conventions, base test classes
  Write tests with: meaningful assertions, edge cases (null, empty, boundary, error paths)
  Target: >=80% coverage, critical paths 100%
  Run written tests to verify passing
  IF(written tests fail) →
  Fix test or implementation (max 2 tries)
  IF(still fails) →
  IF($HAS_AUTO_APPROVE) →
  Mark in comment: "Tests written but failing: {details}". Continue.
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Written tests fail. Fix/Skip tests/Rollback?"
→ END-IF
→ END-IF
→ END-IF
  Append test files to STORE-GET($CHANGED_FILES)
→ END-IF
- `65`: 7.4 CLEANUP: Scan STORE-GET($CHANGED_FILES) for: unused imports/use/require, dead code from refactoring, orphaned helpers no longer called, commented-out blocks
- `66`: IF(cleanup needed) →
  Remove dead code, re-run syntax check on cleaned files
→ END-IF
- `67`: IF(task adds NEW feature/module/API (not bugfix/refactor/trivial)) →
  Bash('brain docs {feature keywords}') → check if docs exist
  IF(no docs found for this feature) →
  CREATE .docs/{feature-name}.md with YAML front matter (name, description, type, date, version) + markdown (purpose, usage, key concepts, API/interface)
  Append doc file to STORE-GET($CHANGED_FILES)
→ END-IF
  IF(docs exist AND behavior changed) →
  UPDATE relevant .docs/ files to reflect behavior changes
  Append updated doc files to STORE-GET($CHANGED_FILES)
→ END-IF
→ END-IF
- `68`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "Done. Files: {changed_files}. Tests: {pass/skip/none}.", append_comment: true}')
- `69`: mcp__vector-memory__store_memory('{content: "Task #{id}: {approach}, files: {list}, patterns used, learnings", category: "code-solution"}')
- `70`: IF(TRIVIAL execution (doc-only/comment-only/formatting-only changes AND ≤1 file AND no code logic changes)) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Trivial change — validation skipped (doc/comment/formatting only).", append_comment: true}')
  NEXT: skip validation → proceed to next sibling or parent validation per next-step-lifecycle-flow.
→ END-IF
- `71`: IF(NOT trivial (code logic changes OR multiple files)) →
  NEXT: /task:validate {$VECTOR_TASK_ID} [-y] (or /task:validate-sync). ALWAYS validate after execution — NEVER suggest /task:sync or /task:async for next task before this task is `validated`.
→ END-IF

# Tdd mode
- `1`: IF(task.comment contains "TDD MODE" AND status=`tested`) →
  Execute implementation based on task.content
→ END-IF
- `2`: Implement feature following existing code patterns
- `3`: Run tests: detect test framework from project (jest, pytest, phpunit, pest, cargo test, go test, etc.)
- `4`: IF(all tests pass) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "TDD: All tests PASSED", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "TDD `success`: {feature}, implementation approach: {summary}", category: "code-solution"}')
→ END-IF
- `5`: IF(tests fail) →
  Analyze `failure`: assertion error vs exception vs timeout
  Implement fix based on test expectation
  Re-run tests (max 5 iterations)
  IF(still failing after 5 iterations) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "TDD stuck: {failing_tests}. Need guidance.", append_comment: true}')
  IF($HAS_AUTO_APPROVE) →
  ABORT "TDD: Cannot pass tests after 5 iterations"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Cannot pass tests. Show failures for manual review?"
→ END-IF
→ END-IF
→ END-IF

# Error handling
- `1`: IF(task not found) → ABORT "suggest task_list or task_create"
- `2`: IF(task already `completed` AND -y) → ABORT "Already completed"
- `3`: IF(task already `completed` AND no -y) →
  ask "Re-execute `completed` task?"
→ END-IF
- `4`: IF(research triggers matched but context7 empty AND web-research empty) →
  IF($HAS_AUTO_APPROVE) →
  Proceed with best-effort based on existing codebase patterns
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  Ask user for clarification with specific questions
→ END-IF
→ END-IF
- `5`: IF(multiple research options, user chose "other") →
  Ask for details, incorporate into plan
→ END-IF
- `6`: IF(file not found for edit) →
  IF($HAS_AUTO_APPROVE AND file should exist) →
  ABORT "Expected file not found: {path}"
→ END-IF
  IF($HAS_AUTO_APPROVE AND new file needed) → Create file with Write
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "File not found. Create/Specify path/Abort?"
→ END-IF
→ END-IF
- `7`: IF(edit conflict (old_string not found)) →
  Re-read file to get current content
  Adjust old_string to match current state
  Retry edit (max 3 attempts)
  IF(3 failures) →
  IF($HAS_AUTO_APPROVE) → Use Write to replace entire file if safe
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Cannot edit. Show diff for manual resolution?"
→ END-IF
→ END-IF
→ END-IF
- `8`: IF(user rejects plan) →
  Accept modifications, rebuild plan, re-present
→ END-IF
- `9`: IF(partial implementation AND tempted to ask "keep/rewrite/both") →
  STOP. This is FORBIDDEN question.
  Read documentation again
  Documentation defines target state
  Implement REMAINING parts per docs
  NEVER ask about non-existent alternatives
→ END-IF
- `10`: IF(dependency install fails) →
  Check: network, permissions, version conflicts
  IF($HAS_AUTO_APPROVE) →
  mcp__vector-task__task_update('{status: "pending", comment: "Dependency install failed: {error}"}') + abort
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Install failed: {error}. Retry/Skip dependency/Abort?"
→ END-IF
→ END-IF
- `11`: IF(syntax check fails after edit) →
  Parse error message, identify line/column
  Attempt fix (missing semicolon, bracket, import, etc.)
  Re-check (max 2 attempts)
  IF(still fails) → Rollback file, report syntax error
→ END-IF
- `12`: IF(linter finds critical issues) →
  IF(auto-fixable) → Run linter --fix
  IF(not auto-fixable) →
  IF($HAS_AUTO_APPROVE) → Add TODO comment, proceed with warning
  IF(NOT $HAS_AUTO_APPROVE) → Show issues, ask for action
→ END-IF
→ END-IF
- `13`: IF(timeout on long operation) →
  IF($HAS_AUTO_APPROVE) → Skip with warning, continue
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Operation timed out. Wait longer/Skip/Abort?"
→ END-IF
→ END-IF

</command>