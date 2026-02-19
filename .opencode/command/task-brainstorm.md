---
description: "Collaborative brainstorming session anchored to a vector task. Loads task context, prompts for topic, facilitates ideation with research delegation and optional task creation."
---

<command>
<meta>
<id>task:brainstorm</id>
<description>Collaborative brainstorming session anchored to a vector task. Loads task context, prompts for topic, facilitates ideation with research delegation and optional task creation.</description>
</meta>
<execute>Facilitates structured brainstorming for vector tasks. Loads task by ID, asks user for discussion topic, then provides collaborative ideation with agent delegation for research (web, code, docs) and ability to create subtasks from brainstorm outcomes.</execute>
<provides>Collaborative brainstorming anchored to vector task. Loads task, asks user for topic, facilitates ideation with research delegation, optional task modification/subtask creation.</provides>

# Iron Rules
## Status-semantics (CRITICAL)
Task status has STRICT semantics: "pending" = waiting to be worked on (includes failed/blocked tasks returned to queue). "in_progress" = currently being worked on. "completed" = implementation done, ready for validation. "tested" = tests written/passed. "validated" = passed all quality gates. "stopped" = PERMANENTLY CANCELLED — task is NOT needed, will NEVER be executed. ONLY set "stopped" when: user explicitly requests cancellation, OR task is provably unnecessary (duplicate, superseded, irrelevant). NEVER set "stopped" for: failures, blocks, validation issues, tool errors, missing dependencies. For these → set "pending" with detailed blocker in comment.
- **why**: Agents misuse "stopped" as "failed/blocked" which breaks workflow permanently. A `stopped` task is removed from pipeline — it will never be picked up again. A `pending` task with a blocker comment will be retried, either automatically or manually.
- **on_violation**: If about to set "stopped": verify it is a TRUE cancellation. If task failed or is blocked → set "pending" + comment explaining what happened. "stopped" is irreversible workflow termination.

## Task-get-first (CRITICAL)
FIRST action = mcp__vector-task__task_get. Load task context before anything.

## Topic-prompt-mandatory (CRITICAL)
MUST ask user for brainstorm topic after loading task. NEVER assume or invent topic.

## Collaborative-mode (HIGH)
Brainstorm is DIALOGUE. Present ideas → ask feedback → iterate. NOT monologue. User can invite specialist agents.

## Iterative-ideation (CRITICAL)
After initial ideas, keep proposing until user says "that's all" / "proceed". NEVER skip this loop.

## Research-on-demand (HIGH)
Delegate research ONLY when needed. Unknown tech → context7. Codebase analysis → explore agent. Simple topics → no delegation.

## Codebase-pattern-reuse (CRITICAL)
BEFORE implementing: search codebase for similar/analogous implementations. Grep for: similar class names, method signatures, trait usage, helper utilities. Found → REUSE approach, follow same patterns, extend existing code. Not found → proceed independently. NEVER reinvent what already exists in the project.
- **why**: Codebase consistency > personal style. Duplicate implementations create maintenance burden, inconsistency, and confusion. Existing patterns are battle-`tested`.
- **on_violation**: STOP. Search codebase for analogous code. Found → study and follow the pattern. Only then proceed.

## Comment-context-mandatory (CRITICAL)
AFTER loading task: parse task.comment for accumulated context. Extract: memory IDs (#NNN), file paths, previous execution results, `failure` reasons, blockers, decisions made. Store as $COMMENT_CONTEXT. Pass to ALL agents alongside task.content.
- **why**: Comments accumulate critical inter-session context: what was tried, what failed, what files were touched, what decisions were made. Ignoring comments = blind re-execution without history.
- **on_violation**: Parse task.comment IMMEDIATELY after task_get. Extract actionable context. Include in agent prompts and planning.

## Docs-provide-context (HIGH)
If documentation exists for topic → READ IT FIRST. Docs contain: constraints, decisions, rejected alternatives. Ideas must NOT contradict documented architecture/decisions.
- **why**: Brainstorming without doc context = reinventing wheel or proposing already-rejected ideas.
- **on_violation**: Search and read docs before generating ideas. Note constraints from docs.

## Modification-user-approved (HIGH)
Modify task or create subtasks ONLY when user explicitly requests. Options: update content, rewrite, append, create subtasks.

## Parent-id-mandatory (CRITICAL)
ALL new tasks/subtasks created MUST have parent_id = $VECTOR_TASK_ID. No orphan tasks. No exceptions.
- **why**: Task hierarchy integrity. Orphan tasks break traceability and workflow.
- **on_violation**: ABORT task_create if parent_id missing or != $VECTOR_TASK_ID.

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

# Parallel isolation checklist
GOAL(Systematic verification of task independence before setting parallel: true)
- `1`: For EACH pair of tasks being considered for parallel execution:
- `2`:   1. FILE MANIFEST: List ALL files each task will read/write/create
- `3`:   2. FILE OVERLAP: Cross-reference manifests → shared file = parallel: false for BOTH
- `4`:   3. IMPORT CHAIN: Check if any file in task A imports/uses files from task B scope (and vice versa)
- `5`:   4. SHARED MODEL: Check if tasks modify same DB table, model, or migration
- `6`:   5. SHARED CONFIG: Check if tasks modify same config key, .env variable, or shared state
- `7`:   6. OUTPUT→INPUT: Check if task B needs any result/artifact/output from task A
- `8`:   7. TRANSITIVE: Follow imports one level deep — indirect overlap = NOT independent
- `9`:   8. GLOBAL BLACKLIST: If ANY task modifies globally shared files (dependency manifests/locks, .env*, config/**, routes/**, migration directories, CI/CD configs, test/lint/build configs) → that task MUST be parallel: false. Globally shared files are NEVER safe for parallel modification.
- `10`:   RESULT: ALL checks pass → parallel: true | ANY check fails → parallel: false
- `11`:   DEFAULT: When analysis is uncertain or incomplete → parallel: false (safe default)

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
GOAL(Brainstorm: load task → ask topic → gather context → ideate → iterate → actions)
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → STORE-AS($TASK)
- `2`: IF(not found) →
  ABORT "Task not found. Use /do:brainstorm for topic-only."
→ END-IF
- `3`: IF(TASK.parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') → STORE-AS($PARENT)
→ END-IF
- `4`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') → STORE-AS($SUBTASKS)
- `5`: STORE-AS($COMMENT_CONTEXT = {parsed from $TASK.comment: memory_ids: [#NNN], file_paths: [...], execution_history: [...], failures: [...], blockers: [...], decisions: [], mode_flags: []})
- `6`: Show: Task #{id}, title, status, content, parent, subtasks count, $COMMENT_CONTEXT summary
- `7`: Ask: "What aspect would you like to brainstorm?"
- `8`: WAIT for user topic → STORE-AS($TOPIC)
- `9`: Bash('brain docs {TOPIC} {TASK.title}') → STORE-AS($DOCS_INDEX)
- `10`: IF(STORE-GET($DOCS_INDEX) found) →
  Read('{doc_paths}') → STORE-AS($DOCUMENTATION)
  DOCUMENTATION provides: constraints, existing decisions, rejected alternatives. Ideas MUST respect documented architecture.
→ END-IF
- `11`: mcp__vector-memory__search_memories('{query: "{TASK.title} {TOPIC}", limit: 5}') → STORE-AS($MEMORY)
- `12`: IF(unknown library/tech in TOPIC) →
  mcp__context7__query-docs('{query: "{library}"}') → understand first
→ END-IF
- `13`: IF(needs codebase analysis) →
  [DELEGATE] @explore: 'Analyze codebase for {TOPIC}. Find: relevant files, patterns, implementations.' → STORE-AS($CODE_CONTEXT)
→ END-IF
- `14`: IF(needs external research) →
  [DELEGATE] @web-research-master: 'Research {TOPIC}: best practices, patterns, pitfalls.' → STORE-AS($WEB_RESEARCH)
→ END-IF
- `15`: Present structured ideas:
- `16`: ## Constraints from Docs - IF DOCUMENTATION exists, list: architecture decisions, rejected alternatives, hard limits ## Approaches - 2-4 potential approaches (MUST NOT contradict docs) ## Pros/Cons - for each approach ## Recommendation - top choice with rationale ## Open Questions - needs user input
- `17`: STORE-AS($IDEATION_DONE = false)
- `18`: Ask: "Your thoughts? More ideas? Say 'proceed' when done."
- `19`: FOREACH(WHILE NOT IDEATION_DONE) →
  IF(user says proceed/done) → STORE-AS($IDEATION_DONE = true)
  IF(user shares ideas) → Build on them, propose 2-3 more, ask again
  IF(user wants deep dive) → Expand specific idea, then ask again
→ END-FOREACH
- `20`: Show options: 1) Invite specialist, 2) Update task, 3) Create subtasks, 4) Research more, 5) End session
- `21`: WAIT for user choice
- `22`: IF(user wants specialist) →
  Bash('brain list:masters') → show available
  WAIT for selection
  [DELEGATE] @{selected}: 'Specialist perspective on {TOPIC} for task {TASK.title}. Current approaches: {summary}. Provide: alternatives, issues, recommendations.'
  Present specialist input, continue brainstorm
→ END-IF
- `23`: IF(user wants task update) →
  Show current vs proposed changes
  Options: apply, rewrite, append, cancel
  IF(confirmed) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, content: "{new}", comment: "Brainstorm: {TOPIC}", append_comment: true}')
→ END-IF
→ END-IF
- `24`: IF(user wants subtasks) →
  List actionable items from brainstorm
  Apply parallel-isolation-checklist for each subtask pair: list files, cross-reference, verify ALL 5 isolation conditions. Default: parallel: false.
  Ask: "Create these subtasks? (yes/no/modify)"
  IF(confirmed) →
  mcp__vector-task__task_create_bulk('{tasks: [{title, content, parent_id: $VECTOR_TASK_ID, priority, estimate, order, parallel, file_manifest: [files]}]}')
→ END-IF
→ END-IF
- `25`: mcp__vector-memory__store_memory('{content: "Brainstorm #{TASK.id}: {TOPIC}. Insights: {summary}. Modified: {yes/no}. Subtasks: {count}.", category: "architecture", tags: ["insight"]}')
- `26`: IF(task modified OR subtasks created) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "Brainstorm `completed`: {TOPIC}", append_comment: true}')
→ END-IF
- `27`: Report: task, topic, modifications, subtasks created

# Error handling
- `1`: IF(task not found) → ABORT "Use /do:brainstorm for topic-only"
- `2`: IF(empty topic) → Re-prompt: "Please specify aspect to brainstorm"
- `3`: IF(research agent fails) →
  Continue with available context, note limitation
→ END-IF
- `4`: IF(task creation fails) →
  Report which failed, suggest manual creation
→ END-IF

</command>