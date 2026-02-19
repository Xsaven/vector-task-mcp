---
name: "task:async"
description: "Async execution of vector task via agent delegation with parallel support"
---

<command>
<meta>
<id>task:async</id>
<description>Async execution of vector task via agent delegation with parallel support</description>
</meta>
<execute>Run task execution asynchronously via agent delegation.</execute>
<provides>Async vector task execution via agent delegation. Brain orchestrates with critical thinking, agents execute. Researches when ambiguous, adapts examples. Parallel when independent.</provides>

# Iron Rules
## Status-semantics (CRITICAL)
Task status has STRICT semantics: "pending" = waiting to be worked on (includes failed/blocked tasks returned to queue). "in_progress" = currently being worked on. "completed" = implementation done, ready for validation. "tested" = tests written/passed. "validated" = passed all quality gates. "stopped" = PERMANENTLY CANCELLED — task is NOT needed, will NEVER be executed. ONLY set "stopped" when: user explicitly requests cancellation, OR task is provably unnecessary (duplicate, superseded, irrelevant). NEVER set "stopped" for: failures, blocks, validation issues, tool errors, missing dependencies. For these → set "pending" with detailed blocker in comment.
- **why**: Agents misuse "stopped" as "failed/blocked" which breaks workflow permanently. A `stopped` task is removed from pipeline — it will never be picked up again. A `pending` task with a blocker comment will be retried, either automatically or manually.
- **on_violation**: If about to set "stopped": verify it is a TRUE cancellation. If task failed or is blocked → set "pending" + comment explaining what happened. "stopped" is irreversible workflow termination.

## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN analyze what to delegate.

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
Task tags MUST use ONLY predefined values. FORBIDDEN: inventing new tags, synonyms, variations. Allowed: decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression, feature, bugfix, refactor, research, docs, test, chore, spike, hotfix, backend, frontend, database, api, auth, ui, config, infra, ci-cd, migration, strict:relaxed, strict:standard, strict:strict, strict:paranoid, cognitive:minimal, cognitive:standard, cognitive:deep, cognitive:exhaustive, batch:trivial.
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

## Mandatory-level-tags (CRITICAL)
EVERY task MUST have exactly ONE strict:* tag AND ONE cognitive:* tag. Allowed strict: strict:relaxed, strict:standard, strict:strict, strict:paranoid. Allowed cognitive: cognitive:minimal, cognitive:standard, cognitive:deep, cognitive:exhaustive. Missing level tags = assign based on task scope analysis.
- **why**: Level tags enable per-task compilation and cognitive load calibration. Without them, system defaults apply blindly regardless of task complexity.
- **on_violation**: Analyze task scope and assign: strict:{level} + cognitive:{level}. Simple rename = strict:relaxed + cognitive:minimal. Production auth = strict:strict + cognitive:deep.

## Safety-escalation-non-overridable (CRITICAL)
After loading task, check file paths in task.content/comment. If files match safety patterns → effective level MUST be >= pattern minimum, regardless of task tags or .env default. Agent tags are suggestions UPWARD only — can raise above safety floor, never lower below it.
- **why**: Safety patterns guarantee minimum protection for critical code areas. Agent cannot "cheat" by under-tagging a task touching auth/ or payments/.
- **on_violation**: Raise effective level to safety floor. Log escalation in task comment.

## Smart-delegation (CRITICAL)
Brain must understand task INTENT before delegating. Agents execute, but Brain decides WHAT to delegate and HOW to split work.

## Research-triggers (CRITICAL)
Research BEFORE delegation when ANY: 1) content <50 chars, 2) contains "example/like/similar/e.g./такий як", 3) no file paths AND no class/function names, 4) references unknown library/pattern, 5) contradicts existing code, 6) multiple valid interpretations, 7) task asks "how to" without specifics.

## Research-flow (HIGH)
Research order: 1) context7 for library docs, 2) web-research-master for patterns. -y flag: auto-select best approach for delegation. No -y: present options to user.

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
If task matches pattern that failed 2+ times (from memory/sibling analysis) → DO NOT delegate same approach. Research alternatives via web-research-master or escalate to user.
- **why**: Definition of insanity: doing same thing expecting different results.

## Never-execute-directly (CRITICAL)
Brain NEVER calls Edit/Write/Glob/Grep/Read for implementation. ALL work via Task() to agents.

## Atomic-tasks (CRITICAL)
Each agent task: 1-2 files (max 3-5 if same feature). NO broad changes.

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

## Agent-dependency-instruction (HIGH)
Include in agent prompt: "If dependencies needed: detect package manager, install (composer/npm/pip/cargo/go mod). Run audit after install."
- **why**: Agents handle their own dependency installation autonomously.

## Agent-security-instruction (CRITICAL)
Include in agent prompt: "NEVER hardcode secrets. Validate external input. Escape output. Use parameterized queries."
- **why**: Security rules must propagate to all agents.

## Agent-validation-instruction (HIGH)
Include in agent prompt: "After changes: verify syntax, run linter if configured, run related tests. Fix issues before reporting completion."
- **why**: Agents must validate their own work.

## Pre-delegation-git-check (HIGH)
Before ANY delegation: check git status for awareness. Uncommitted changes: LOG and proceed. NEVER modify git state.
- **why**: Read-only git awareness only. Modification prohibition from trait.

## Delegation-context-include (CRITICAL)
Every Task() MUST include: 1) clear task description, 2) file scope, 3) memory search hints, 4) security + validation instructions.
- **why**: Agents need full context to work autonomously.

## Agent-failure-isolation (HIGH)
Agent fails: other parallel agents continue. Failed agent work: -y = mark task `pending` with `failure` details, no -y = ask "Agent X failed. Retry/Skip/Mark `pending`?"
- **why**: Rollback via git is forbidden. Failed agent files stay as-is. Next execution attempt will handle them.

## Critical-agent-failure (HIGH)
Critical agent (blocker for others) fails: -y = abort remaining + mark all `pending` with `failure` details, no -y = ask "Critical task failed. Abort all/Retry/Manual intervention?"
- **why**: Never rollback via git. Mark `pending` and let next attempt handle recovery.

## Partial-success-handling (MEDIUM)
N of M agents succeeded: -y = complete with warning listing failed parts, no -y = ask "N/M succeeded. Complete partial/Rollback all/Retry failed?"

## Agent-retry-limit (HIGH)
Agent timeout or `failure`: max 2 retries with same agent. Still fails: try alternative agent if applicable. After all retries: mark subtask failed.

## Agent-timeout (MEDIUM)
Agent execution timeout: 300s for implementation, 120s for research, 60s for validation. Timeout exceeded: cancel, retry or skip.

## Session-recovery-detection (HIGH)
Task status=`in_progress`: check task.comment for delegation state. Has agent_tasks with `pending`/running: crashed session. No state OR >1h old: stale session.

## Session-recovery-action (HIGH)
Crashed session: -y = check agent results, continue remaining, no -y = ask "Crashed session. Check agent results/Restart all?" Stale: reset to `pending`.

## Subtasks-first-batch-only (HIGH)
Parent task with subtasks: assess FIRST BATCH (first group of adjacent parallel=true OR single next sequential by order). Verify isolation for parallel groups. Delegate ONLY first batch — remaining children require separate execution cycles per one-task-per-cycle. After batch completes → STOP and report remaining.
- **why**: Inline-executing ALL children bloats context unpredictably. First-batch-only gives orchestrator control between batches.
- **on_violation**: STOP after first batch. Return RESULT with batch progress and NEXT with remaining subtask info.

## Subtasks-agent-assignment (MEDIUM)
Each subtask in first batch gets dedicated agent delegation. Track: {subtask_id, agent, status, files_touched}.

## Breaking-change-detection (HIGH)
Include in agent prompt for refactoring tasks: "Flag breaking changes (API signature, removed exports, changed types). Report in completion summary."

## Breaking-change-action (HIGH)
Agent reports breaking change: -y = accept with deprecation notice, update callers via another agent. No -y = ask "Breaking change reported. Proceed/Modify/Abort?"

## Failure-memory (MEDIUM)
On delegation `failure`: store to memory with category "debugging". Content: task summary, agent used, `failure` reason, partial results. Helps future orchestration.

## Aggregate-results (HIGH)
After all agents complete: aggregate results. Verify: no conflicts between agent changes, all expected files modified, no orphaned changes.

## Conflict-resolution (HIGH)
Agents modified same file (conflict): -y = merge if possible, prefer later change. No -y = ask "Conflict in {file}. Show diff/Prefer agent A/Prefer agent B?"


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
GOAL(Select tags per task. Combine dimensions for precision.)
WORKFLOW (pipeline stage): decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression
TYPE (work kind): feature, bugfix, refactor, research, docs, test, chore, spike, hotfix
DOMAIN (area): backend, frontend, database, api, auth, ui, config, infra, ci-cd, migration
STRICT LEVEL: strict:relaxed, strict:standard, strict:strict, strict:paranoid
COGNITIVE LEVEL: cognitive:minimal, cognitive:standard, cognitive:deep, cognitive:exhaustive
BATCH: batch:trivial
Formula: 1 TYPE + 1 DOMAIN + 0-2 WORKFLOW + 1 STRICT + 1 COGNITIVE. Example: ["feature", "api", "strict:standard", "cognitive:standard"] or ["bugfix", "auth", "validation-fix", "strict:strict", "cognitive:deep"].

# Memory tag selection
GOAL(Select 1-3 tags per memory. Combine dimensions.)
CONTENT (kind): pattern, solution, `failure`, decision, insight, workaround, deprecated
SCOPE (breadth): project-wide, module-specific, temporary, reusable
Formula: 1 CONTENT + 0-1 SCOPE. Example: ["solution", "reusable"] or ["failure", "module-specific"]. Max 3 tags.

# Safety escalation patterns
GOAL(Automatic level escalation based on file patterns and context)
File patterns → strict minimum: auth/, guards/, policies/, permissions/ → strict. payments/, billing/, stripe/, subscription/ → strict. .env, credentials, secrets, config/auth → paranoid. migrations/, schema → strict. composer.json, package.json, *.lock → standard. CI/, .github/, Dockerfile, docker-compose → strict. routes/, middleware/ → standard.
Context patterns → level minimum: priority=critical → strict+deep. tag hotfix or production → strict+standard. touches >10 files → standard+standard. tag breaking-change → strict+deep. Keywords security/encryption/auth/permission → strict. Keywords migration/schema/database/drop → strict.

# Cognitive level
GOAL(Cognitive level: standard — calibrate analysis depth accordingly)
Memory probes per phase: 2-3 targeted
Failure history: recent only
Research (context7/web): on error/ambiguity
Agent scaling: auto (2-3)
Comment parsing: basic parse

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
- `2`: IF(not found) → ABORT "Task not found"
- `3`: IF(status=`completed`) →
  IF($HAS_AUTO_APPROVE) →
  ABORT "Already `completed`. Use different task ID."
→ END-IF
  ask "Re-execute `completed` task?"
→ END-IF
- `4`: IF(status=`in_progress`) →
  Parse task.comment for delegation_state JSON
  IF(has agent_tasks with `pending`/running AND timestamp <1h) →
  STORE-AS($IS_CRASHED_SESSION = true)
  IF($HAS_AUTO_APPROVE) →
  Check agent results, continue remaining delegations
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Crashed session. Check results/Restart all?"
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
  Sort `pending` subtasks by order field. Identify FIRST BATCH: first group of adjacent parallel=true (verify isolation) OR single next sequential (parallel=false)
  STORE-AS($FIRST_BATCH = first parallel group or single next sequential subtask)
  STORE-AS($REMAINING_SUBTASKS = `pending` subtasks NOT in first batch)
  IF($HAS_AUTO_APPROVE) →
  Delegate ONLY $FIRST_BATCH to agents (parallel if group, single if sequential)
  After $FIRST_BATCH completes → STOP.
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "Batch `completed`: {FIRST_BATCH ids}. Remaining: {REMAINING_SUBTASKS ids}.", append_comment: true}')
  RESULT: PARTIAL — batch `completed`. NEXT: /task:async {$VECTOR_TASK_ID} [-y] (remaining children)
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Has N subtasks. Execute first batch ({FIRST_BATCH})?"
→ END-IF
→ END-IF
- `15`: STORE-AS($IS_SIMPLE = task.content >=50 chars AND has specific file/class/function AND no "example/like/similar" AND single clear interpretation)
- `16`: IF(STORE-GET($IS_SIMPLE)) → SKIP to step 4 (Context gathering)
- `17`: STORE-AS($NEEDS_RESEARCH = ANY: content <50 chars, contains "example/like/similar/e.g./такий як/як у", no paths AND no class names, unknown lib/pattern, contradicts code, ambiguous, "how to" without specifics)
- `18`: IF(STORE-GET($NEEDS_RESEARCH)) →
  3.1: mcp__context7__resolve-library-id('{libraryName: "{detected_lib}"}') → IF library mentioned
  3.2: mcp__context7__query-docs('{query: "{task question}"}') → get docs
  3.3: IF context7 insufficient → [DELEGATE] @agent-web-research-master: 'Research: {task.title}. Find: implementation patterns, best practices.'
  STORE-AS($RESEARCH_OPTIONS = [{option, source, pros, cons}])
→ END-IF
- `19`: IF(STORE-GET($RESEARCH_OPTIONS) AND $HAS_AUTO_APPROVE) →
  Auto-select BEST approach for delegation
→ END-IF
- `20`: IF(STORE-GET($RESEARCH_OPTIONS) AND NOT $HAS_AUTO_APPROVE) →
  Present: "Found N approaches: 1)... 2)... Which? (or your variant)"
→ END-IF
- `21`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') STORE-AS($MEMORY)
- `22`: mcp__vector-memory__search_memories('{query: "{task.title} {problem keywords} failed error not working broken", limit: 5}') STORE-AS($KNOWN_FAILURES) ← CRITICAL: what already FAILED (search by `failure` keywords, not category)
- `23`: mcp__vector-task__task_list('{query: task.title, limit: 3}') STORE-AS($RELATED)
- `24`: IF(STORE-GET($TASK).parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') STORE-AS($SIBLING_TASKS)
  FOREACH(sibling in STORE-GET($SIBLING_TASKS)) →
  mcp__vector-memory__search_memories('{query: "{sibling.title}", limit: 3}') → ALL memories for this sibling (failures, solutions, insights)
  mcp__vector-memory__search_memories('{query: "{sibling.title} failed error not working", limit: 3}') → specifically `failure`-related memories
  Append results to STORE-AS($SIBLING_MEMORIES)
→ END-FOREACH
  Extract from siblings comments + STORE-GET($SIBLING_MEMORIES): what was tried, what failed, what worked
  STORE-AS($FAILURE_PATTERNS = solutions that were tried and failed (from sibling comments + sibling memories))
→ END-IF
- `25`: IF(STORE-GET($KNOWN_FAILURES) OR STORE-GET($FAILURE_PATTERNS) not empty) →
  STORE-AS($BLOCKED_APPROACHES = STORE-GET($KNOWN_FAILURES) + STORE-GET($FAILURE_PATTERNS))
  If planned delegation uses blocked approach → STOP, research alternative or escalate
  Pass BLOCKED_APPROACHES to ALL agents in their prompts
→ END-IF
- `26`: Bash('brain docs {keywords}') STORE-AS($DOCS_INDEX)
- `27`: IF(STORE-GET($DOCS_INDEX) found) →
  [DELEGATE] @agent-explore: 'Read docs: {doc.paths}. Return full content.' → STORE-AS($DOCS_CONTENT)
  DOCS_CONTENT = COMPLETE specification. Pass to ALL agents. Documentation > task.content.
→ END-IF
- `28`: [DELEGATE] @agent-explore: 'Find SIMILAR/ANALOGOUS implementations in codebase for: {task.title}. Search: analogous class names, method patterns, trait usage, helper utilities, base classes. Return: {similar_files, approach, conventions, reusable_code}. Exclude: .brain/' → STORE-AS($EXISTING_PATTERNS)
- `29`: IF(STORE-GET($EXISTING_PATTERNS) found) →
  Include in ALL agent prompts: "Similar code exists at {files}. FOLLOW same approach/conventions. REUSE helpers/base classes."
→ END-IF
- `30`: Bash('git status --porcelain 2>/dev/null || echo "NO_GIT"') STORE-AS($GIT_STATUS)
- `31`: IF(STORE-GET($GIT_STATUS) has uncommitted changes) →
  LOG: uncommitted changes detected. Proceeding — NEVER stash or checkout.
→ END-IF
- `32`: Analyze task INTENT → break into atomic agent subtasks
- `33`: mcp__sequential-thinking__sequentialthinking({
                thought: "Planning delegation: 1) What is the INTENT? 2) Which agents? 3) Parallel or sequential? 4) File scope per agent? 5) What instructions for security/validation?",
                thoughtNumber: 1,
                totalThoughts: 2,
                nextThoughtNeeded: true
            })
- `34`: STORE-AS($PLAN = [{agent, subtask, files, parallel: bool, order, is_critical: bool}])
- `35`: Each agent prompt MUST include: task description, file scope, memory hints, security rules, validation requirements
- `36`: IF($HAS_AUTO_APPROVE) →
  execute immediately
→ ELSE →
  show plan, wait "yes"
→ END-IF
- `37`: IF(STORE-GET($TASK).parallel === true) →
  STORE-AS($MY_FILE_SCOPE = {all unique files from $PLAN agent subtasks})
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "PARALLEL SCOPE: [$MY_FILE_SCOPE]", append_comment: true}')
→ END-IF
- `38`: IF(STORE-GET($TASK).parallel === true) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') → re-fetch siblings with fresh comments
  STORE-AS($ACTIVE_SIBLINGS = filter: parallel=true AND id != $TASK.id AND status=`in_progress` → {id, title, comment})
  Extract "PARALLEL SCOPE: [...]" from each ACTIVE_SIBLINGS comment → STORE-AS($SIBLING_SCOPES = {updated sibling_id → [files]})
  Cross-reference STORE-GET($MY_FILE_SCOPE) vs STORE-GET($SIBLING_SCOPES) (`active` only) → STORE-AS($SHARED_FILES = {overlapping files — FORBIDDEN})
  IF(STORE-GET($SHARED_FILES) not empty) →
  WARN: "SHARED FILES with `active` siblings: {SHARED_FILES}. DO NOT edit. Record as SCOPE EXTENSION NEEDED. Pass to ALL agents."
→ END-IF
  IF(STORE-GET($SHARED_FILES) empty) →
  No conflicts with `active` siblings. Proceed with delegation.
→ END-IF
→ END-IF
- `39`: STORE-AS($DELEGATION_STATE = {agent_tasks: [], started_at: timestamp})
- `40`: 6.1 PARALLEL: Independent tasks → multiple [DELEGATE] @agent-{agent}: '{subtask + security + validation instructions}' in ONE message
- `41`: 6.2 SEQUENTIAL: Dependent tasks → one by one, wait for result before next
- `42`: Track each delegation: {agent, status, result, files_touched, errors}
- `43`: IF(agent fails) →
  Retry up to 2 times with same agent
  IF(still fails AND alternative agent exists) →
  Try alternative agent
→ END-IF
  IF(max retries AND is_critical) →
  IF($HAS_AUTO_APPROVE) →
  Abort remaining delegations
  DO NOT rollback — other agents have uncommitted work. Leave files as-is.
  mcp__vector-task__task_update('{status: "pending", comment: "Critical agent failed: {error}. Files left as-is (no rollback — parallel safety).", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "FAILURE: Task #{id}, agent: {name}, error: {msg}", category: "debugging"}')
  ABORT "Critical agent failed, no rollback"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Critical task failed. Abort all/Retry/Manual?"
→ END-IF
→ END-IF
  IF(max retries AND NOT is_critical) →
  Mark subtask as failed, continue others
  Update delegation_state in task.comment
→ END-IF
→ END-IF
- `44`: Update task.comment with delegation_state for recovery
- `45`: Collect all agent results
- `46`: Check for conflicts: multiple agents modified same file
- `47`: IF(conflict detected) →
  IF($HAS_AUTO_APPROVE) →
  Merge if possible, prefer later change, WARN
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Conflict in {file}. Show diff/Prefer A/Prefer B?"
→ END-IF
→ END-IF
- `48`: Verify: all expected files modified, no orphaned changes
- `49`: STORE-AS($AGENT_RESULTS = {succeeded: N, failed: M, files: [...], conflicts: [...]})
- `50`: IF(some agents failed) →
  IF($HAS_AUTO_APPROVE AND >80% succeeded) →
  mcp__vector-task__task_update('{status: "completed", comment: "Partial `success`: {succeeded}/{total}. Failed: {list}", append_comment: true}')
→ END-IF
  IF($HAS_AUTO_APPROVE AND <=80% succeeded) →
  mcp__vector-task__task_update('{status: "pending", comment: "Too many failures: {failed}/{total}", append_comment: true}')
  ABORT "Too many agent failures"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "N/M succeeded. Complete partial/Rollback all/Retry failed?"
→ END-IF
→ END-IF
- `51`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "Done. Agents: {list}. Files: {files}.", append_comment: true}')
- `52`: mcp__vector-memory__store_memory('{content: "Task #{id}: delegation strategy, agents used: {list}, learnings: {summary}", category: "code-solution"}')
- `53`: IF(TRIVIAL execution (doc-only/comment-only/formatting-only changes AND ≤1 file AND no code logic changes)) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Trivial change — validation skipped (doc/comment/formatting only).", append_comment: true}')
  NEXT: skip validation → proceed to next sibling or parent validation per next-step-lifecycle-flow.
→ END-IF
- `54`: IF(NOT trivial (code logic changes OR multiple files)) →
  NEXT: /task:validate {$VECTOR_TASK_ID} [-y] (or /task:validate-sync). ALWAYS validate after execution — NEVER suggest /task:sync or /task:async for next task before this task is `validated`.
→ END-IF

# Agents
explore = code exploration, file analysis, implementation
web-research-master = external research, best practices
documentation-master = docs research, API documentation
commit-master = git operations, commits
script-master = Laravel scripts, commands
prompt-master = Brain component generation

# Tdd mode
- `1`: IF(task.comment contains "TDD MODE" AND status=`tested`) →
  Execute implementation via agents based on task.content
→ END-IF
- `2`: Delegate implementation to agent with TDD context: "Tests exist at {path}. Implement to make tests pass."
- `3`: After implementation → [DELEGATE] @agent-explore: 'Run tests. Detect framework (jest, pytest, phpunit, pest, cargo test, go test). Report pass/fail.'
- `4`: IF(all tests pass) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "TDD: All tests PASSED", append_comment: true}')
  mcp__vector-memory__store_memory('{content: "TDD `success`: {feature}, delegation strategy: {summary}", category: "code-solution"}')
→ END-IF
- `5`: IF(tests fail) →
  Analyze `failure` from agent report
  Delegate fix to same agent with `failure` context (max 5 iterations)
  IF(still failing after 5 iterations) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "TDD stuck: {failing_tests}. Need guidance.", append_comment: true}')
  IF($HAS_AUTO_APPROVE) →
  ABORT "TDD: Cannot pass tests after 5 iterations"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Cannot pass tests via agents. Show failures for manual review?"
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
  Proceed with best-effort delegation based on existing patterns
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  Ask user for clarification with specific questions
→ END-IF
→ END-IF
- `5`: IF(multiple research options, user chose "other") →
  Ask for details, incorporate into delegation plan
→ END-IF
- `6`: IF(agent timeout) →
  Cancel agent, retry up to 2 times
  IF(still timeout) →
  IF($HAS_AUTO_APPROVE) → Skip with warning, continue other agents
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Agent {name} timed out. Retry/Skip/Abort?"
→ END-IF
→ END-IF
→ END-IF
- `7`: IF(agent returns invalid result) →
  Validate: has expected output, files touched, no errors
  IF(invalid) → Retry with clearer instructions (max 2)
  IF(still invalid) →
  IF($HAS_AUTO_APPROVE) → Mark subtask failed, continue others
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Agent returned invalid result. Show/Retry/Skip?"
→ END-IF
→ END-IF
→ END-IF
- `8`: IF(conflict between agent results) →
  Analyze: same file modified differently
  IF($HAS_AUTO_APPROVE) →
  Attempt merge, prefer later change if conflict
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Conflict in {file}. Show diff/Merge/Prefer A/Prefer B?"
→ END-IF
→ END-IF
- `9`: IF(agent reports breaking change) →
  IF($HAS_AUTO_APPROVE) →
  Accept change
  Delegate update-callers task to another agent
  Add deprecation notice in code comment
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Agent reports breaking change: {details}. Proceed/Modify/Abort?"
→ END-IF
→ END-IF
- `10`: IF(user rejects plan) →
  Accept modifications, rebuild delegation plan, re-present
→ END-IF

# Agent instruction template
Every Task() delegation MUST include these sections:
1. TASK: Clear description of what to do
2. FILES: Specific file scope (1-2 files, max 3-5 for feature)
3. DOCUMENTATION: "If docs exist: {$DOCS_CONTENT}. Documentation = COMPLETE spec. task.content may be summary. Follow DOCS."
4. BLOCKED APPROACHES: "KNOWN FAILURES (DO NOT USE): {$BLOCKED_APPROACHES}. If your solution matches - find alternative."
5. MEMORY: "Search memory for: {terms}. Check debugging category for failures. Store learnings after."
6. SECURITY: "No hardcoded secrets. Validate input. Escape output. Parameterized queries."
7. VALIDATION: "Verify syntax. Run linter if configured. Run ONLY related tests (scoped, never full suite). Fix before completion."
8. GIT: "FORBIDDEN: git checkout, git restore, git stash, git reset, git clean. These destroy parallel agents work and memory/ databases. Rollback = Read original content + Write back. Git is READ-ONLY (status, diff, log)."
9. DEPS: "If dependencies needed: detect package manager, install, run audit."
10. PATTERNS: "BEFORE coding: search codebase for similar implementations. Grep analogous class names, method patterns. Found → follow same approach, reuse helpers. NEVER reinvent existing patterns."
11. IMPACT: "BEFORE editing: Grep who imports/uses/extends target file. Dependents found → ensure changes are compatible. Changing public API → update all callers."
12. LOGIC: "After coding: verify logic for each function. What happens with null? empty? boundary (0, -1, MAX)? error path? off-by-one?"
13. PERFORMANCE: "Avoid: nested loops over data (O(n²)), query/I/O inside loops (N+1), loading full datasets, missing pagination. Batch operations."
14. HALLUCINATION: "Verify EVERY method/class/function call exists with correct signature. Read source to confirm. NEVER assume API from naming convention."
15. CLEANUP: "After edits: remove unused imports, dead code, orphaned helpers, commented-out blocks."
16. TEST COVERAGE: "After implementation: check if changed code has tests. NO tests → WRITE them. Insufficient coverage → ADD tests. Target: >=80% coverage, critical paths 100%, meaningful assertions, edge cases (null, empty, boundary). Detect test framework from project, follow existing test patterns/structure. Run written tests to verify passing. NEVER skip — validator will reject without tests."
17. COMMENT CONTEXT: "Task comment contains accumulated inter-session context: {$COMMENT_CONTEXT}. Use memory IDs to fetch prior findings. Use file_paths as starting points. Respect decisions already made. Avoid repeating failures. DO NOT ignore comment history."
18. PARALLEL CONTEXT: "IF $ACTIVE_SIBLINGS not empty: Other agents MAY be executing sibling tasks concurrently. Your file scope: {MY_FILE_SCOPE}. Sibling scopes (from their task comments): {SIBLING_SCOPES}. SHARED/FORBIDDEN files: {SHARED_FILES}. Modify ONLY files in YOUR scope. Out-of-scope file needed → DO NOT edit, record in task comment as SCOPE EXTENSION NEEDED. Shared files (config, .env, migrations, routes) → NEVER edit in parallel context. Sibling without scope in comment = still planning, NOT a red flag."
19. DOCUMENTATION: "After implementation: IF task adds NEW feature/module/API → run brain docs \\"{keywords}\\" to check existing docs. NOT found → CREATE .docs/{feature}.md with YAML front matter (name, description, type, date, version) + markdown body (purpose, usage, key concepts, API/interface). Documentation = description for humans, text-first, minimize code. IF task CHANGES existing behavior and docs exist → UPDATE relevant docs. Bugfix/refactor without behavior change OR trivial → SKIP docs."

</command>