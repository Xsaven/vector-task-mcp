---
description: "Direct sync validation of vector task without agent delegation"
---

<command>
<meta>
<id>task:validate-sync</id>
<description>Direct sync validation of vector task without agent delegation</description>
</meta>
<execute>Validate completed vector task synchronously without agent delegation.</execute>
<provides>Sync validation of completed vector task. Direct tools (no agents). Validates task.content requirements, code quality, tests. Cosmetic fixed inline. Functional issues → fix-tasks. Idempotent.</provides>

# Iron Rules
## Status-semantics (CRITICAL)
Task status has STRICT semantics: "pending" = waiting to be worked on (includes failed/blocked tasks returned to queue). "in_progress" = currently being worked on. "completed" = implementation done, ready for validation. "tested" = tests written/passed. "validated" = passed all quality gates. "stopped" = PERMANENTLY CANCELLED — task is NOT needed, will NEVER be executed. ONLY set "stopped" when: user explicitly requests cancellation, OR task is provably unnecessary (duplicate, superseded, irrelevant). NEVER set "stopped" for: failures, blocks, validation issues, tool errors, missing dependencies. For these → set "pending" with detailed blocker in comment.
- **why**: Agents misuse "stopped" as "failed/blocked" which breaks workflow permanently. A `stopped` task is removed from pipeline — it will never be picked up again. A `pending` task with a blocker comment will be retried, either automatically or manually.
- **on_violation**: If about to set "stopped": verify it is a TRUE cancellation. If task failed or is blocked → set "pending" + comment explaining what happened. "stopped" is irreversible workflow termination.

## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN validate.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. Fake results = CRITICAL VIOLATION.

## No-delegation (CRITICAL)
SYNC validation = direct tools only. NO Task() delegation. Use: Read, Edit, Glob, Grep, Bash.

## Validation-only (CRITICAL)
VALIDATION reads and audits. NEVER implement or fix functional code. Functional issues → create fix-task.

## One-task-per-cycle (CRITICAL)
ONE assigned task = ONE execution cycle. After completing task → STOP and return result. NEVER: 1) search for and execute sibling tasks after completion, 2) inline-execute ALL children of parent task in one session. Parent with `pending` children: handle FIRST BATCH only (first parallel group or single next sequential child), then STOP — orchestrator dispatches remaining children in separate cycles. This applies regardless of how small children appear.
- **why**: Multi-task sessions are unpredictable: context budget unknown upfront, estimates may be wrong in either direction. Starting task N+1 may exhaust context mid-work = partial results harder to recover than clean start. Orchestrator loses control points between tasks (cannot reprioritize, redirect, stop). Accumulated tool call results from prior tasks bloat context for current task. One task per cycle = one predictable unit = reliable orchestration.
- **on_violation**: STOP after completing current task/batch. Return RESULT + NEXT. Let orchestrator dispatch next cycle.

## Guaranteed-finalization (CRITICAL)
Task MUST NOT remain `in_progress` after workflow completes. BEFORE emitting RESULT/NEXT output → verify current task status is NOT `in_progress`. If still `in_progress` after all workflow phases: set status to "pending" with comment "SAFETY NET: Workflow `completed` without explicit status update. Returned to `pending` for retry." This is the ABSOLUTE LAST safety net — every workflow path MUST set explicit status (`completed`/`validated`/`tested`/`pending`), but if a path is missed, this catches it.
- **why**: A task stuck in `in_progress` blocks the entire pipeline. No orchestrator will pick it up, no human will see it as actionable. This safety net ensures workflow bugs are self-healing — worst case `pending` (retryable), never silent `in_progress` (invisible).
- **on_violation**: IMMEDIATELY call task_update(status: `pending`) with explanation. Then emit RESULT: FAILED.

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

## Failure-history-mandatory (CRITICAL)
BEFORE starting work: search memory category "debugging" for KNOWN FAILURES related to this task/problem. DO NOT attempt solutions that already failed.
- **why**: Repeating failed solutions wastes time. Memory contains "this does NOT work" knowledge.
- **on_violation**: Search debugging memories FIRST. Block known-failed approaches.

## Sibling-task-check (HIGH)
BEFORE starting work: fetch sibling tasks (same parent_id, status=`completed`/`stopped`). Check comments for what was tried and failed.
- **why**: Previous attempts on same problem contain valuable "what not to do" information.
- **on_violation**: task_list with parent_id, extract `failure` patterns from comments.

## Stuck-pattern-detection (HIGH)
Before creating fix-tasks: analyze FAILURE_PATTERNS + SIBLING_MEMORIES + KNOWN_FAILURES for circular patterns. STUCK PATTERN = same problem zone (file path + issue category) failed 2+ times across validation cycles or sibling task attempts. Indicators: same file in multiple sibling failures, same error category repeated, same fix approach suggested and failed. When stuck pattern detected → ESCALATION REQUIRED before creating fix-task.
- **why**: Without pattern detection, validator creates the same fix-task with the same approach that already failed. Agent executes, fails, validator creates again → infinite loop. Circuit breaker catches after 3 wasted cycles. Early detection + research saves 2 cycles.
- **on_violation**: Analyze `failure` history BEFORE task_create. Stuck pattern found → research escalation. Never create fix-task with known-failed approach.

## Stuck-research-escalation (HIGH)
When stuck pattern detected: 1) Collect all failed approaches for the stuck zone from memory + sibling comments. 2) Research alternative solutions — async validator: launch research agent; sync validator: inline context7 + web search. 3) Inject findings into fix-task content: "STUCK ZONE: {file}:{issue}. Failed approaches: {list}. Research: {alternatives}. Recommended: {best_untried}." 4) Auto-approve mode: auto-select highest-confidence untried approach. 5) NO alternative found → ESCALATE to human via task comment, do NOT create doomed fix-task.
- **why**: Research costs ~30s but prevents 2+ wasted cycles (each = agent execution + validation = minutes + tokens). Research once > fail three times.
- **on_violation**: Stuck pattern without research = BLOCK fix-task creation. Research first, create with alternative.

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
MAX 3 validate attempts per task. Parse task.comment for "ATTEMPT [validate]:" markers at workflow start (count only markers AFTER last "CIRCUIT BREAKER:" entry — counter auto-resets when human removes "stuck" tag and retries). If task has tag "stuck" → ABORT immediately (needs human). If validate attempt count >= 3 → add tag "stuck", store `failure` summary to memory, ABORT. If count < 3 → proceed, include "ATTEMPT [validate]: {N+1}/3" in task.comment when setting `in_progress`.
- **why**: Without retry limit, auto-approve creates infinite loops: fail → `pending` → retry → fail. "stopped" = permanently cancelled (wrong semantics). Tag "stuck" = circuit breaker: visible via task:list, removable by human to retry. Counter per phase (exec/validate) prevents false positives from normal lifecycle.
- **on_violation**: Check validate attempt counter BEFORE setting `in_progress`. Tag "stuck" = HARD STOP.

## Collateral-failure-detection (HIGH)
After test execution: separate failing tests into SCOPE (tests for files/modules in task.content or changed by this task) and COLLATERAL (tests for code clearly unrelated to task). Ambiguous = treat as SCOPE (conservative). If COLLATERAL failures exist AND task has ZERO in-scope failures → create max 2 GLOBAL remediation tasks with tag "regression" and NO parent_id (EXEMPT from parent-id-mandatory — intentional to prevent cascade re-validations). Current task PASSES quality gates. If task has in-scope failures → fail normally, mention collateral in report but do NOT create remediation tasks (fix own issues first). NOTE: practically triggers only on ROOT task validation (full test suite). Subtasks run scoped tests → no collateral possible.
- **why**: Ignoring unrelated test failures = hidden regressions accumulate silently. Blocking current task on others' failures = wrong task punished. Global tasks (no parent) enter normal queue without parent-status propagation → zero cascade re-validations. Max 2 per validation prevents spam. If task turns out unnecessary (already fixed), agent executes it, tests pass, done in one cycle — cheaper than missed regression.
- **on_violation**: Classify test failures by scope. In-scope = current task problem. Out-of-scope = collateral → global task. Never block validation on collateral failures.

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

## Code-hallucination-prevention (CRITICAL)
Before using any method/function/class in generated code: VERIFY it actually exists with correct signature. Read the source or use Grep to confirm. NEVER assume API exists based on naming convention. Common hallucinations: wrong method names, incorrect parameter order/count, non-existent helper functions, invented framework methods, deprecated APIs used as current.
- **why**: AI generates plausible-looking code referencing non-existent APIs. Parses and lints OK but fails at runtime. Most dangerous because it looks correct.
- **on_violation**: Read actual source for EVERY external method/class used. Verify name + parameter signature before writing.

## Cleanup-after-changes (MEDIUM)
After all edits: scan changed files for artifacts. Remove: unused imports/use/require statements, unreachable code after refactoring, orphaned helper functions no longer called, commented-out code blocks, stale TODO/FIXME without actionable context.
- **why**: AI refactoring often leaves dead imports, orphaned functions, commented-out code. Accumulates technical debt and confuses future readers.
- **on_violation**: Scan changed files for unused imports and unreachable code. Remove confirmed dead code.

## Test-scoping (CRITICAL)
Test execution MUST be scoped based on task hierarchy level. SUBTASK (has parent_id): run ONLY tests related to changed files — a) test files that directly test changed classes/modules, b) test files that import/use/depend on changed classes (reverse dependency in test directory). ROOT TASK (no parent_id): run the FULL test suite via quality gate command. NEVER run full test suite for subtasks — it wastes more time than the task itself.
- **why**: Full test suite for a 1-hour subtask can take longer than the task execution itself. Scoped tests catch 95%+ of regressions at 10% of the cost. Full suite runs at root aggregation level and manually before push.
- **on_violation**: Check task.parent_id. Has parent → scoped tests only. No parent → full suite allowed.

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

## Parent-id-mandatory (CRITICAL)
ALL new tasks/subtasks created MUST have parent_id = $VECTOR_TASK_ID. No orphan tasks. No exceptions.
- **why**: Task hierarchy integrity. Orphan tasks break traceability and workflow.
- **on_violation**: ABORT task_create if parent_id missing or != $VECTOR_TASK_ID.

## Docs-are-complete-spec (CRITICAL)
Documentation (.docs/) = COMPLETE specification. task.content may be brief summary. ALWAYS read and validate against DOCUMENTATION if exists. Missing from docs = not a requirement. In docs but not done = MISSING.
- **why**: task.content is often summary. Full spec lives in documentation. Validating only task.content misses requirements.
- **on_violation**: Check DOCS_PATHS. If docs exist → read them → extract full requirements → validate against docs.

## Task-scope-only (CRITICAL)
Validate ONLY what task.content + documentation describes. Do NOT expand scope. Task says "add X" = check X exists and works. Task says "fix Y" = check Y is fixed. NOTHING MORE.

## Task-complete (CRITICAL)
ALL task requirements MUST be done. Parse task.content → list requirements → verify each. Missing = fix-task.

## No-garbage (CRITICAL)
Garbage code in task scope = fix-task. Detect: unused imports, dead code, debug statements, commented-out blocks.

## Cosmetic-inline (CRITICAL)
Cosmetic issues = fix IMMEDIATELY inline. NO task created. Cosmetic: whitespace, typos, formatting, comments, docblocks, naming (non-breaking), import sorting.

## Functional-to-task (CRITICAL)
Functional issues = fix-task. Functional: logic bugs, security vulnerabilities, architecture violations, missing tests, broken functionality.

## Test-coverage (HIGH)
No test coverage = fix-task. Critical paths = 100%, other >= 80%.

## Slow-test-detection (HIGH)
Slow tests = fix-task. Unit >500ms, integration >2s, any >5s = CRITICAL.

## No-repeat-failures (CRITICAL)
BEFORE creating fix-task: check if proposed solution matches known `failure`. If memory says "X does NOT work for Y" — DO NOT create task suggesting X. Research alternative or escalate.
- **why**: Creating fix-task with known-failed solution = guaranteed `failure` + wasted effort.
- **on_violation**: Search memory for proposed fix. Match found in debugging = BLOCK task creation, suggest alternative.

## Fix-task-blocks-validated (CRITICAL)
Fix-task created → status MUST be "pending", NEVER "validated". "validated" = ZERO fix-tasks. NO EXCEPTIONS.
- **why**: MCP auto-propagation: when child task starts (status→`in_progress`), parent auto-reverts to `pending`. Setting "validated" with `pending` children is POINTLESS - system will reset it.
- **on_violation**: ABORT validation. Set status="pending" BEFORE task_create. Never set "validated" if ANY fix-task exists.

## Revalidation-mandatory (CRITICAL)
ALL fix-subtasks `completed`/`validated` → MANDATORY full re-validation from scratch. No fast-path, no aggregation-only. Fixes may introduce new issues, original validation may have missed gaps.
- **why**: Fix-tasks modify code that was already `validated`. Previous validation results are STALE. Only a full re-run catches regressions and new issues introduced by fixes.
- **on_violation**: Detect fix-subtasks via "validation-fix" tag. If ALL done → proceed to full validation, NEVER skip to "validated".

## Aggregation-only-path (HIGH)
Intermediate parent (has parent_id) with ALL decomposition subtasks `validated` and NO fix-subtasks → aggregation fast-path. Cross-reference parent requirements vs subtask results. If all covered → "validated" without full re-run. If gaps → scope validation to uncovered requirements only. Root tasks ALWAYS get full validation (cross-subtask integration).
- **why**: Decomposition subtasks already `validated` their scope. Re-running full validation duplicates work. Root tasks need cross-subtask integration check that subtask validators never performed.
- **on_violation**: Check: has parent_id? No fix-subtasks? All subtasks `validated`? → aggregation. Root task → ALWAYS full validation.

## Idempotent (HIGH)
Re-run produces same result. Check existing tasks before creating. Skip duplicates.

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

## Validator-parallel-cosmetic-defer (HIGH)
In PARALLEL CONTEXT: before making inline cosmetic fix, check if file is in ACTIVE sibling's scope (from $SIBLING_SCOPES). File in `active` sibling scope → DO NOT fix, record in task comment: "DEFERRED COSMETIC: {file}:{line} — {issue}. Reason: file in `active` sibling #{id} scope." File NOT in any `active` scope → safe to fix inline. This applies to ALL inline fixes: whitespace, formatting, typos, import sorting, comment cleanup.
- **why**: Validator cosmetic fixes (Edit) on files being actively modified by a parallel executor = race condition. Even a whitespace fix overwrites the executor's in-memory file content, creating silent data loss or merge conflicts.
- **on_violation**: Check $SIBLING_SCOPES before Edit. Active sibling owns file → defer cosmetic fix to task comment. Fix will be picked up by next validation pass after sibling completes.

## Scoped-git-checkpoint (CRITICAL)
Git checkpoint commits scope depends on context: 1) PARALLEL CONTEXT: "git add {task_file1} {task_file2}" — commit ONLY task-scope files. memory/ excluded implicitly (not in task files). Prevents staging other agents' uncommitted work and SQLite binary conflicts. 2) NON-PARALLEL context: "git add -A" — full state checkpoint, INCLUDES memory/ for complete project state preservation. 3) If commit fails (pre-commit hook) → LOG and continue, work is still valid.
- **why**: In parallel context, multiple agents write to memory/ SQLite and codebase concurrently. "git add -A" stages everything: other agents' half-done work + binary SQLite mid-write = corrupted checkpoint. In non-parallel, "git add -A" is safe and DESIRED — memory/ commit preserves knowledge base alongside code for full revert capability.
- **on_violation**: Parallel: "git add {specific_files}" (task scope only). Non-parallel: "git add -A" (full checkpoint with memory/).


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

# Retry circuit breaker
GOAL(Break infinite retry loops by tracking validate attempts and tagging stuck tasks)
- `1`: 1. Parse STORE-GET($TASK).comment: find last "CIRCUIT BREAKER:" entry. Count "ATTEMPT [validate]:" markers AFTER it (or from start if none). → STORE-AS($ATTEMPT_COUNT = {count, default 0})
- `2`: 2. IF(STORE-GET($TASK).tags contains "stuck") →
  ABORT "Task is STUCK. Remove "stuck" tag to retry."
→ END-IF
- `3`: 3. IF(STORE-GET($ATTEMPT_COUNT) >= 3) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, add_tag: "stuck", comment: "CIRCUIT BREAKER: 3 validate attempts exhausted. Needs human investigation. See `failure` history above.", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "STUCK: Task #{id} \\'{title}\\' failed after 3 validate attempts. Review task comments for `failure` details.", category: "debugging", tags: ["failure"]}')
  ABORT "Circuit breaker → tagged "stuck"."
→ END-IF
- `4`: 4. IF(STORE-GET($ATTEMPT_COUNT) < 3) →
  Proceed. Include "ATTEMPT [validate]: {N+1}/3" when setting `in_progress`.
→ END-IF

# Collateral failure detection
GOAL(Detect unrelated test failures and create global remediation tasks without blocking current validation)
- `1`: 1. After test execution: classify each failing test
- `2`:    SCOPE: test file directly tests classes/modules changed by or mentioned in $TASK
- `3`:    COLLATERAL: test file tests code clearly unrelated (different module, domain, component)
- `4`:    AMBIGUOUS: cannot determine origin → treat as SCOPE (conservative, safe)
- `5`: 2. IF(STORE-GET($COLLATERAL_FAILURES) not empty AND STORE-GET($ISSUES) = 0 (no in-scope failures)) →
  Group collateral failures by module/area (max 2 groups)
  FOREACH(group in collateral_groups (max 2)) →
  mcp__vector-task__task_create('{title: "Fix regression: {module/area}", content: "Test `failure`(s) detected during validation of task #{$TASK.id} (\\'{$TASK.title}\\').\\\\n\\\\nThese failures are OUTSIDE that task\\'s scope — collateral/regression.\\\\n\\\\nFailing tests:\\\\n- {test_names_with_errors}\\\\n\\\\nError summary:\\\\n{error_details}\\\\n\\\\nDiscovered by: validator during task #{$TASK.id} validation.\\\\nNOT caused by task #{$TASK.id}.", priority: "high", estimate: 2, tags: ["regression", "bugfix"]}') ← NO parent_id (global task, exempt from parent-id-mandatory)
→ END-FOREACH
  Current task: PASSES quality gates (collateral failures are NOT blockers)
→ END-IF
- `6`: 3. IF(STORE-GET($COLLATERAL_FAILURES) not empty AND STORE-GET($ISSUES) > 0) →
  Current task FAILS normally (in-scope issues take priority)
  Mention collateral failures in validation report for awareness
  Do NOT create remediation tasks — fix own issues first, collateral caught on re-validation
→ END-IF
- `7`: 4. IF(no COLLATERAL failures) →
  Normal validation flow — no additional action
→ END-IF

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

# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with -y/--yes flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
GOAL(Sync validate: load → approve → context → validate → aggregate → create tasks → complete)
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → STORE-AS($TASK)
- `2`: IF(not found) → ABORT "Task not found"
- `3`: IF(status NOT IN [`completed`, `tested`, `validated`, `in_progress`]) →
  ABORT "Complete via /task:sync first"
→ END-IF
- `4`: IF(status=`in_progress`) →
  SESSION RECOVERY: check if crashed
→ ELSE →
  ABORT "another session active"
→ END-IF
- `5`: IF(TASK.parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') → context only
→ END-IF
- `6`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') → STORE-AS($SUBTASKS)
- `7`: STORE-AS($COMMENT_CONTEXT = {parsed from $TASK.comment: memory_ids: [#NNN], file_paths: [...], execution_history: [...], failures: [...], blockers: [...], decisions: [], mode_flags: []})
- `8`: STORE-AS($ATTEMPT_COUNT = count "ATTEMPT [validate]:" markers in $TASK.comment AFTER last "CIRCUIT BREAKER:" entry (default 0))
- `9`: IF(STORE-GET($TASK).tags contains "stuck") →
  ABORT "Task is STUCK. Remove "stuck" tag to retry."
→ END-IF
- `10`: IF(STORE-GET($ATTEMPT_COUNT) >= 3) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, add_tag: "stuck", comment: "CIRCUIT BREAKER: 3 validate attempts exhausted. Needs human investigation.", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "STUCK: Task #{id} failed 3x validation. See task comments.", category: "debugging", tags: ["failure"]}')
  ABORT "Circuit breaker → tagged "stuck"."
→ END-IF
- `11`: IF(STORE-GET($TASK).parallel === true AND parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}')
  STORE-AS($PARALLEL_SIBLINGS = filter: parallel=true AND id != $TASK.id → {id, title, status, comment})
  STORE-AS($ACTIVE_SIBLINGS = filter PARALLEL_SIBLINGS where status=`in_progress`)
  Extract "PARALLEL SCOPE: [...]" from each ACTIVE_SIBLINGS comment → STORE-AS($SIBLING_SCOPES = {sibling_id → [files]})
  LOG: "PARALLEL CONTEXT (sync validator): {total} siblings ({`active`} `active`). Active scopes: {SIBLING_SCOPES or NONE}. Cosmetic fixes on `active` sibling files will be DEFERRED."
→ END-IF
- `12`: STORE-AS($TASK_PARENT_ID = $VECTOR_TASK_ID)
- `13`: STORE-AS($HAS_FIX_SUBTASKS = STORE-GET($SUBTASKS) contains ANY subtask with tag "validation-fix")
- `14`: IF(STORE-GET($SUBTASKS) not empty AND ALL subtasks status = "validated" AND STORE-GET($HAS_FIX_SUBTASKS)) →
  FIX-TASKS COMPLETED: Previous validation created fix-tasks, all now done.
  MANDATORY FULL RE-VALIDATION: fixes may have introduced new issues, original validation may have missed gaps.
  Proceed to FULL VALIDATION below — validate ENTIRE task scope from scratch.
→ END-IF
- `15`: IF(STORE-GET($SUBTASKS) not empty AND ALL subtasks status = "validated" AND NOT STORE-GET($HAS_FIX_SUBTASKS) AND STORE-GET($TASK).parent_id (NOT root)) →
  AGGREGATION-ONLY MODE: Intermediate parent, all decomposition subtasks `validated`.
  Read subtask comments → extract validation results (test counts, issues found, fixes applied)
  Parse parent task.content → list ALL parent requirements
  Cross-reference: does each parent requirement map to at least one `validated` subtask?
  IF(all parent requirements covered by subtask results) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Aggregation validation: all {N} subtasks `validated`. Requirements covered: {list}.", append_comment: true}')
  OUTPUT(task, subtask results summary, all requirements covered, status=`validated`)
  SKIP(full validation — decomposition subtasks already did the work)
→ END-IF
  IF(gaps found: some parent requirements NOT covered by any subtask) →
  STORE-AS($UNCOVERED_REQUIREMENTS = [requirements not mapped to any subtask])
  Proceed to FULL VALIDATION below, but scope to UNCOVERED_REQUIREMENTS only
→ END-IF
→ END-IF
- `16`: IF(STORE-GET($SUBTASKS) not empty AND ALL subtasks status = "validated" AND NOT STORE-GET($HAS_FIX_SUBTASKS) AND NOT STORE-GET($TASK).parent_id (ROOT task)) →
  ROOT TASK — FINAL CHECKPOINT: All subtasks `validated` individually, but this is the LAST safety net.
  Subtask validators checked isolated scopes. Cross-subtask INTEGRATION was NEVER verified.
  MANDATORY: Proceed to FULL VALIDATION — validate ENTIRE task scope from scratch.
  Focus: integration between subtasks, full test suite, all quality gates, cross-file dependencies.
→ END-IF
- `17`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "ATTEMPT [validate]: {$ATTEMPT_COUNT + 1}/3. Started validation.", append_comment: true}')
- `18`: Show: Task #{id}, title, status, subtasks count
- `19`: IF($HAS_AUTO_APPROVE) →
  Auto-approved
→ ELSE →
  Ask: "Validate? (yes/no)"
→ END-IF
- `20`: mcp__vector-memory__search_memories('{query: "{TASK.title}", limit: 5, category: "code-solution"}') → STORE-AS($MEMORY)
- `21`: mcp__vector-memory__search_memories('{query: "{TASK.title} failed error not working broken", limit: 5}') STORE-AS($KNOWN_FAILURES) ← what already FAILED
- `22`: mcp__vector-task__task_list('{query: "{TASK.title}", limit: 5}') → STORE-AS($RELATED)
- `23`: IF(STORE-GET($TASK).parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') → STORE-AS($SIBLING_TASKS)
  Extract from sibling comments: what was tried, what failed
  STORE-AS($FAILURE_PATTERNS = known failed approaches from siblings + debugging memories)
→ END-IF
- `24`: Bash('brain docs {keywords from task}') → STORE-AS($DOCS_INDEX)
- `25`: IF(STORE-GET($DOCS_INDEX) found) →
  Read('{doc_paths}') → STORE-AS($DOCUMENTATION) (COMPLETE spec)
→ END-IF
- `26`: IF(unknown library/pattern) →
  mcp__context7__query-docs('{query: "{library}"}') → understand before validating
→ END-IF
- `27`: Grep(Search for similar implementations: analogous class names, method patterns, trait usage)
- `28`: STORE-AS($EXISTING_PATTERNS = {similar implementations found in codebase})
- `29`: STORE-AS($COSMETIC_FIXES = 0)
- `30`: 4.1 COMPLETION: Extract requirements from DOCUMENTATION (primary) + task.content (secondary) → list ALL requirements → verify each done
- `31`: Glob(Find task-related files)
- `32`: Read(Read files, confirm implementation)
- `33`: Detect garbage: unused imports, dead code, debug statements, commented-out blocks
- `34`: 4.2 CODE QUALITY: Task scope only
- `35`: Grep(Search patterns, potential issues)
- `36`: Check: logic, security, architecture. Unknown lib → context7.
- `37`: 4.2.1 PATTERN CONSISTENCY: Compare implementation against $EXISTING_PATTERNS. Code should follow established project conventions.
- `38`: 4.2.2 HALLUCINATION CHECK: Verify ALL method/class/function calls reference REAL code. Read source to confirm methods exist with correct signatures.
- `39`: 4.2.3 IMPACT RADIUS: For each changed file, Grep who imports/uses/extends it. Verify consumers NOT broken.
- `40`: 4.2.4 LOGIC EDGE CASES: For each changed function, verify: null/empty handling, boundary values, off-by-one, error paths.
- `41`: 4.3 QUALITY GATES (non-test)
- `42`: Bash({non-test QUALITY_COMMAND gates}) → [Run static analysis, linting quality gates (EXCLUDE test gate)] → END-Bash
- `43`: Gate FAIL = fix-task
- `44`: 4.4 TESTING (scoped by hierarchy)
- `45`: IF(TASK.parent_id (subtask)) →
  Find test files: grep tests/ for changed class names, check mirror directory structure
  Grep(Search test directory for imports/uses of changed classes → consumer tests)
  Run ONLY found test files by EXPLICIT file path or --filter (e.g., phpunit tests/Unit/FooTest.php, php artisan test --filter=Foo)
  FORBIDDEN: running any test command without explicit file path or --filter
→ END-IF
- `46`: IF(NOT TASK.parent_id (root task)) →
  Bash({project test command}) → [Detect and run full test suite from project config] → END-Bash
→ END-IF
- `47`: Check: tests exist (>=80%), pass, edge cases. Slow tests = issue.
- `48`: 4.5 CLEANUP: Scan for unused imports, dead code, orphaned helpers, debug statements
- `49`: 4.6 DOCS COVERAGE: IF task adds NEW feature/module/API → Bash('brain docs {feature keywords}') → check if .docs/ entry exists. No docs for new feature = minor cosmetic issue. Create basic .docs/{feature}.md inline (YAML front matter + brief description). Bugfix/refactor = SKIP.
- `50`: During validation: cosmetic found → check SIBLING_SCOPES (if parallel) → file in `active` sibling scope? → DEFER to comment. File safe? → Edit → fix → COSMETIC_FIXES++ → continue
- `51`: IF(STORE-GET($KNOWN_FAILURES) not empty) →
  Before creating fix-task: verify proposed fix is NOT in known failures. Match → research alternative.
→ END-IF
- `52`: STORE-AS($ISSUES = {critical, major, minor, missing_requirements — IN-SCOPE only})
- `53`: STORE-AS($COLLATERAL_FAILURES = {test failures classified as OUTSIDE task scope — different module/domain/component})
- `54`: STORE-AS($FUNCTIONAL_COUNT = critical + major + minor + missing (in-scope only))
- `55`: IF(STORE-GET($COLLATERAL_FAILURES) not empty AND FUNCTIONAL_COUNT = 0) →
  COLLATERAL FAILURES: tests failing outside task scope.
  Group by area (max 2 groups)
  FOREACH(group (max 2)) →
  mcp__vector-task__task_create('{title: "Fix regression: {area}", content: "Test `failure`(s) outside task #{$TASK.id} scope.\\\\n\\\\nFailing: {test_names}\\\\nError: {summary}\\\\n\\\\nDiscovered during sync validation of #{$TASK.id}, NOT caused by it.", priority: "high", estimate: 2, tags: ["regression", "bugfix"]}') ← NO parent_id (global, exempt from parent-id-mandatory)
→ END-FOREACH
  Current task NOT affected by collateral failures.
→ END-IF
- `56`: IF(STORE-GET($COLLATERAL_FAILURES) not empty AND FUNCTIONAL_COUNT > 0) →
  Collateral failures noted but NOT creating tasks — fix own issues first.
→ END-IF
- `57`: IF(FUNCTIONAL_COUNT > 0) →
  For EACH issue in ISSUES: count appearances of same {file_path + issue_category} in STORE-GET($FAILURE_PATTERNS) + STORE-GET($KNOWN_FAILURES). If count >= 2 → mark as STUCK.
  STORE-AS($STUCK_ISSUES = {issues with circular `failure` pattern, count >= 2})
  IF(STORE-GET($STUCK_ISSUES) not empty) →
  STUCK PATTERN DETECTED: {count} issue(s) in circular `failure` zones.
  STORE-AS($STUCK_FAILED_APPROACHES = For each STUCK issue: collect ALL previously tried approaches from FAILURE_PATTERNS + sibling comments + debugging memories)
  For EACH stuck issue:
    1. mcp__context7__query-docs('{query: "{library/framework} {problem pattern} recommended approach"}') → official docs
    2. WebSearch({problem} {framework} best practice alternative solution) → community solutions
    3. mcp__vector-memory__search_memories('{query: "{problem} solution workaround alternative", limit: 5, category: "code-solution"}') → solutions from other contexts
    4. Cross-reference research against STUCK_FAILED_APPROACHES — eliminate already-tried
    5. Rank remaining alternatives by confidence
  STORE-AS($RESEARCH_RESULT = {research findings per stuck issue})
  Enrich each stuck issue for fix-task content:
    → "STUCK ZONE ({times_failed}x failed): {file}:{issue}"
    → "Failed: {approaches}. Research: {alternatives}. Recommended: {best_untried}."
  IF(any stuck issue has NO viable alternative) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "STUCK ESCALATION: {N} issue(s) without alternative after research. Needs human decision.", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "STUCK: Task #{TASK.id} — issues without alternative: {list}. Needs new strategy.", category: "debugging", tags: ["failure"]}')
  Remove escalated issues from ISSUES (do NOT create doomed fix-tasks)
  STORE-AS($FUNCTIONAL_COUNT = recalculate after removing escalated issues)
→ END-IF
→ END-IF
→ END-IF
- `58`: IF(FUNCTIONAL_COUNT = 0) → Skip to completion
- `59`: mcp__vector-task__task_list('{query: "fix {TASK.title}", limit: 10}') → check duplicates
- `60`: STORE-AS($TOTAL_ESTIMATE = critical*2h + major*1.5h + minor*0.5h + missing*4h)
- `61`: IF(TOTAL_ESTIMATE <= 8 AND no duplicate) →
  mcp__vector-task__task_create('{title: "Validation fixes: #{TASK.id}", content: "{issues}", parent_id: $TASK_PARENT_ID, priority: "{critical>0 ? high : medium}", estimate: {TOTAL_ESTIMATE}, parallel: false, tags: ["validation-fix"]}') ← parallel: false by default. Apply parallel-isolation-checklist against siblings before setting true.
  STORE-AS($CREATED_TASKS[] = {id})
→ END-IF
- `62`: IF(TOTAL_ESTIMATE > 8) →
  Split into 5-8h batches, create multiple tasks
→ END-IF
- `63`: IF(CREATED_TASKS.count = 0 AND FUNCTIONAL_COUNT = 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Sync validation PASSED", append_comment: true}')
  IF(STORE-GET($TASK).parallel === true AND ACTIVE_SIBLINGS exist) →
  Bash('git add {$TASK_FILES}') → PARALLEL: stage ONLY task-scope files (excludes memory/ and sibling work)
→ ELSE →
  Bash('git add -A') → NON-PARALLEL: full state checkpoint INCLUDING memory/ for complete revert capability
→ END-IF
  Bash('git commit -m "Task #$VECTOR_TASK_ID: $TASK_TITLE [`validated`]"')
  IF(commit fails (pre-commit hook)) →
  LOG: commit skipped, work is still `validated`. Continue.
→ END-IF
→ END-IF
- `64`: IF(CREATED_TASKS.count > 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Validation found issues. Fix-tasks: {count}", append_comment: true}')
→ END-IF
- `65`: IF(FUNCTIONAL_COUNT > 0) →
  mcp__vector-memory__store_memory('{content: "Validation #{TASK.id}: {issue_patterns}. Root causes and fix approaches for future reference.", category: "debugging", tags: ["failure"]}') ← ONLY issue patterns, not operational status
→ END-IF
- `66`: Report: task, status, issues counts, cosmetic fixes, fix-tasks created
- `67`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → verify status is NOT `in_progress`
- `68`: IF(task.status = "in_progress") →
  SAFETY NET TRIGGERED: workflow `completed` but status still `in_progress`.
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "SAFETY NET: Sync validation workflow ended without explicit status update. Returned to `pending`.", append_comment: true}')
→ END-IF
- `69`: NEXT STEP — determine from lifecycle position:
- `70`: IF(status = "validated") →
  IF(`pending` siblings exist (by order field)) →
  NEXT: /task:sync {next_pending_sibling_by_order} [-y] (or /task:async)
→ END-IF
  IF(no `pending` siblings AND task has parent_id) →
  NEXT: /task:validate {parent_id} [-y] (all children done, validate parent)
→ END-IF
  IF(no `pending` siblings AND no parent_id (root)) →
  NEXT: all tasks complete
→ END-IF
→ END-IF
- `71`: IF(status = "pending" (fix-tasks created)) →
  NEXT: fix-tasks created, re-validate {$VECTOR_TASK_ID} after all fixes complete
→ END-IF
- `72`: IF(status = "pending" (blocked by parallel sibling)) →
  NEXT: /task:validate-sync {$VECTOR_TASK_ID} [-y] — retry after blocking sibling completes
→ END-IF
- `73`: IF(status = "pending" (error/crash)) →
  NEXT: /task:validate-sync {$VECTOR_TASK_ID} [-y] — retry validation
→ END-IF

# Error handling
- `1`: IF(task not found) → ABORT "Check task ID"
- `2`: IF(task not validatable status) →
  ABORT "Complete via /task:sync first"
→ END-IF
- `3`: IF(validation fails) → Report partial, store to memory
- `4`: IF(task creation fails) → Store to memory for manual review

</command>