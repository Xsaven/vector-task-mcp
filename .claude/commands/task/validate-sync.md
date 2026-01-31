---
name: "task:validate-sync"
description: "Direct sync validation of vector task without agent delegation"
---

<command>
<meta>
<id>task:validate-sync</id>
<description>Direct sync validation of vector task without agent delegation</description>
</meta>
<execute>Validate completed vector task synchronously without agent delegation.</execute>
<provides>Direct synchronous vector task validation without agent delegation. Accepts task ID reference (formats: "15", "#15", "task 15"), validates completed tasks against task.content requirements (TASK SCOPE ONLY), code quality, tests, and completeness. Creates follow-up tasks for functional issues. Cosmetic issues fixed inline. Idempotent. Best for: validation requiring direct execution without parallel agents.</provides>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING input: Your FIRST output MUST be "=== TASK:VALIDATE-SYNC ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain docs), code generation, file analysis.
- **why**: Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.
- **on_violation**: STOP IMMEDIATELY. Delete any tool calls. Output "=== TASK:VALIDATE-SYNC ACTIVATED ===" and restart from Phase 0.

## Validation-only-no-execution (CRITICAL)
VALIDATION command validates EXISTING work. NEVER implement, fix, or create functional code directly. Only validate and CREATE TASKS for functional issues found.
- **why**: Validation is read-only audit. Execution belongs to task:async or task:sync.
- **on_violation**: Abort any implementation. Create task instead of fixing directly.

## No-delegation (CRITICAL)
SYNC validation executes directly. NO Task() delegation to agents. Use ONLY direct tools: Read, Edit, Write, Glob, Grep, Bash.
- **why**: Sync mode is for direct execution without agent overhead.
- **on_violation**: Remove Task() calls. Execute directly.

## Vector-task-id-required (CRITICAL)
$TASK_ID MUST be a valid vector task ID reference. Valid formats: "15", "#15", "task 15", "task:15", "task-15". If not a valid task ID, abort and suggest /do:validate for text-based tasks.
- **why**: This command is exclusively for vector task execution. Text descriptions belong to /do:validate.
- **on_violation**: STOP. Report: "Invalid task ID. Use /do:validate for text-based tasks or provide valid task ID."

## Validatable-status-required (CRITICAL)
ONLY tasks with status "completed", "tested", or "validated" can be `validated`. Pending/`in_progress`/`stopped` tasks MUST first be `completed` via task:async or task:sync.
- **why**: Validation audits finished work. Incomplete work cannot be `validated`.
- **on_violation**: Report: "Task #{id} has status {status}. Complete via /task:async or /task:sync first."

## Auto-approval-flag (CRITICAL)
If $HAS_AUTO_APPROVE is true, auto-approve all approval gates. Skip approval checkpoints and proceed directly.
- **why**: Flag -y enables automated execution without user interaction.
- **on_violation**: Check $HAS_AUTO_APPROVE before showing approval checkpoint.

## Idempotent-validation (HIGH)
Validation is IDEMPOTENT. Running multiple times produces same result (no duplicate tasks, no repeated fixes).
- **why**: Allows safe re-runs without side effects.
- **on_violation**: Check existing tasks before creating. Skip duplicates.

## Session-recovery-via-history (HIGH)
If task status is "in_progress", check status_history. If last entry has "to: null" - previous session crashed mid-execution. Can RESUME execution WITHOUT changing status (already `in_progress`). Treat vector memory findings from crashed session with caution - previous context is lost. Execution stage is unknown - may need to verify what was `completed`.
- **why**: Prevents blocking on crashed sessions. Allows recovery while maintaining awareness that previous work may be incomplete.
- **on_violation**: Check status_history before blocking. If to:null found, proceed with recovery mode.

## No-direct-fixes-functional (CRITICAL)
VALIDATION command NEVER fixes FUNCTIONAL issues directly. Code logic, architecture, functionality issues MUST become tasks.
- **why**: Traceability and audit trail. Code changes must be tracked via task system.
- **on_violation**: Create task for the functional issue instead of fixing directly.

## Parent-id-mandatory (CRITICAL)
When working with task $VECTOR_TASK_ID, ALL new tasks created MUST have parent_id = $VECTOR_TASK_ID. IRON LAW: Fix-tasks are ALWAYS children of the `validated` task, NEVER orphans, NEVER grandchildren. $TASK_PARENT_ID = $VECTOR_TASK_ID always.
- **why**: Task hierarchy integrity. Orphan tasks break traceability. Grandchildren break workflow.
- **on_violation**: ABORT task_create if parent_id != $VECTOR_TASK_ID. Verify TASK_PARENT_ID = VECTOR_TASK_ID before ANY task_create.

## Cosmetic-auto-fix (CRITICAL)
COSMETIC issues (whitespace, indentation, extra spaces, trailing spaces, documentation typos, formatting inconsistencies, empty lines) MUST be auto-fixed INLINE when discovered during validation. When you find a cosmetic issue, fix it IMMEDIATELY with Edit tool, increment cosmetic_fixes counter, then continue validation. NO separate phase. NO restart. NO tasks.
- **why**: Inline fix eliminates separate cosmetic phase. Faster validation, no restarts, no extra phases.
- **on_violation**: Fix cosmetic issues inline during validation. Report total cosmetic_fixes_applied at end.

## Task-scope-only (CRITICAL)
Validate ONLY what task.content describes. Do NOT check unrelated code/files. Do NOT expand scope. Task says "add X" = check X exists and works. Task says "fix Y" = check Y is fixed. NOTHING MORE.
- **why**: Scope creep wastes time and creates false positives.
- **on_violation**: Remove out-of-scope findings. Focus ONLY on task.content requirements.

## Task-complete (CRITICAL)
ALL task requirements MUST be done. Parse task.content for requirements list. Each requirement = verified. Missing requirement = fix-task.
- **why**: Partial completion is not completion.
- **on_violation**: Create fix-task for missing requirements.

## No-garbage (CRITICAL)
Detect garbage: unused imports, dead code, debug statements, commented-out code, orphan files, test artifacts. Garbage in task scope = fix-task.
- **why**: Clean code is part of completion.
- **on_violation**: Create fix-task for garbage removal.

## Vector-memory-mandatory (HIGH)
ALL agents MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.
- **why**: Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps
- **on_violation**: Include explicit vector memory instructions in agent Task() delegation.

## Phase-sequence-strict (CRITICAL)
Phases MUST execute in STRICT sequential order: Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6. NO phase may start until previous phase is FULLY COMPLETED. Each phase MUST output its header "=== PHASE N: NAME ===" before any actions.
- **why**: Sequential execution ensures data dependencies are satisfied. Each phase depends on variables stored by previous phases.
- **on_violation**: STOP. Return to last `completed` phase. Execute current phase fully before proceeding.

## No-phase-skip (CRITICAL)
FORBIDDEN: Skipping phases. ALL phases 0-6 MUST execute even if a phase has no issues to report. Empty results are valid; skipped phases are VIOLATION.
- **why**: Phase skipping breaks data flow. Later phases expect variables from earlier phases.
- **on_violation**: ABORT. Return to first skipped phase. Execute ALL phases in sequence.

## Phase-completion-marker (HIGH)
Each phase MUST end with its output block before next phase begins. Phase N output MUST appear before "=== PHASE N+1 ===" header.
- **why**: Output markers confirm phase completion. Missing output = incomplete phase.
- **on_violation**: Complete current phase output before starting next phase.

## Output-status-conditional (CRITICAL)
Output status depends on validation outcome: 1) PASSED + no tasks created → "validated", 2) Tasks created for fixes → "pending". Status "validated" means work is COMPLETE and verified.
- **why**: If fix tasks were created, work is NOT done - task returns to `pending` queue. Only when validation passes completely (no critical issues, no missing requirements, no tasks created) can status be "validated".
- **on_violation**: Check CREATED_TASKS.count: if > 0 → set "pending", if === 0 AND passed → set "validated". NEVER set "validated" when fix tasks exist.

## Fix-task-parent-is-validated-task (HIGH)
ALL fix tasks created during validation MUST have parent_id = $VECTOR_TASK_ID. This maintains hierarchy: `validated` task → fix subtasks.
- **why**: Ensures fix tasks are linked to their source validation task for tracking and completion.
- **on_violation**: Set parent_id: $VECTOR_TASK_ID when creating fix tasks.

## Task-size-5-8h (HIGH)
Each created task MUST have estimate between 5-8 hours. Never create tasks < 5h (consolidate) or > 8h (split).
- **why**: Optimal task size for focused work sessions. Too small = context switching overhead. Too large = hard to track progress.
- **on_violation**: Merge small issues into consolidated task OR split large task into 5-8h batches.

## Task-comprehensive-context (CRITICAL)
Each task MUST include: all file:line references, memory IDs, related task IDs, documentation paths, detailed issue descriptions with suggestions, evidence from validation.
- **why**: Enables full context restoration without re-exploration. Saves agent time on task pickup.
- **on_violation**: Add missing context references before creating task.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Phase0 task loading
GOAL(Load vector task using $VECTOR_TASK_ID (already parsed from input), verify validatable status)
- `1`: OUTPUT(=== TASK:VALIDATE-SYNC ACTIVATED ===  === PHASE 0: VECTOR TASK LOADING === Loading task #{$VECTOR_TASK_ID}...)
- `2`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}')
- `3`: STORE-AS($VECTOR_TASK = {task object with title, content, status, parent_id, priority, tags})
- `4`: IF($VECTOR_TASK not found) →
  REPORT(Vector task #$VECTOR_TASK_ID not found)
  Suggest: Check task ID with mcp__vector-task__task_list
  ABORT command
→ END-IF
- `5`: IF($VECTOR_TASK.status NOT IN ["completed", "tested", "validated", "in_progress"]) →
  OUTPUT(=== VALIDATION BLOCKED === Task #$VECTOR_TASK_ID has status: {$VECTOR_TASK.status} Only tasks with status `completed`/`tested`/`validated` can be `validated`. Run /task:async or /task:sync $VECTOR_TASK_ID to complete first.)
  ABORT validation
→ END-IF
- `6`: IF($VECTOR_TASK.status === "in_progress") →
  NOTE(Check status_history for session crash indicator)
  STORE-AS($LAST_HISTORY_ENTRY = {last element of $VECTOR_TASK.status_history array})
  IF($LAST_HISTORY_ENTRY.to === null) →
  STORE-AS($IS_SESSION_RECOVERY = true)
  OUTPUT(⚠️ SESSION RECOVERY DETECTED Task #{$VECTOR_TASK_ID} was `in_progress` but session crashed (status_history.to = null) Continuing validation without status change. NOTE: Previous session vector memory findings should be treated with caution.)
→ END-IF
  IF($LAST_HISTORY_ENTRY.to !== null) →
  OUTPUT(=== VALIDATION BLOCKED === Task #{$VECTOR_TASK_ID} is currently `in_progress` by another session. Wait for completion or use /task:async to take over.)
  ABORT validation
→ END-IF
→ END-IF
- `7`: NOTE(CRITICAL: Set TASK_PARENT_ID to the CURRENTLY `validated` task ID IMMEDIATELY after loading. This ensures fix tasks become children of the task being `validated`, NOT grandchildren.)
- `8`: STORE-AS($TASK_PARENT_ID = {$VECTOR_TASK_ID})
- `9`: NOTE(TASK_PARENT_ID = $VECTOR_TASK_ID (the task we are validating NOW). Any fix tasks created will be children of THIS task, regardless of whether this task itself has a parent.)
- `10`: IF($VECTOR_TASK.parent_id !== null) →
  NOTE(Fetching parent task FOR CONTEXT DISPLAY ONLY. This DOES NOT change TASK_PARENT_ID.)
  mcp__vector-task__task_get('{task_id: $VECTOR_TASK.parent_id}')
  STORE-AS($PARENT_TASK_CONTEXT = {parent task for display context only - NOT for parent_id assignment})
→ END-IF
- `11`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID, limit: 50}')
- `12`: STORE-AS($SUBTASKS = {list of subtasks})
- `13`: STORE-AS($TASK_DESCRIPTION = {$VECTOR_TASK.title + $VECTOR_TASK.content})
- `14`: OUTPUT( === PHASE 0: VECTOR TASK LOADED === Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Status: {$VECTOR_TASK.status} | Priority: {$VECTOR_TASK.priority} Parent context: {$PARENT_TASK_CONTEXT.title or "none"} Subtasks: {$SUBTASKS.count} Fix tasks parent_id will be: $TASK_PARENT_ID (THIS task))

# Phase1 context preview
GOAL(Present validation scope for approval (sync mode, no agents))
- `1`: OUTPUT( === PHASE 1: VALIDATION PREVIEW ===)
- `2`: Bash(brain docs {keywords from $TASK_DESCRIPTION}) → [Get documentation INDEX preview] → END-Bash
- `3`: STORE-AS($DOCS_PREVIEW = Documentation files available)
- `4`: OUTPUT(Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Documentation files: {$DOCS_PREVIEW.count} Validation mode: SYNC (direct tools, no agents))
- `5`: IF($HAS_AUTO_APPROVE === false) →
  OUTPUT( ⚠️  APPROVAL REQUIRED ✅ approved/yes - start validation | ❌ no/modifications)
  WAIT for user approval
  VERIFY-SUCCESS(User approved)
  IF(rejected) → Accept modifications → Re-present → WAIT
→ END-IF
- `6`: IF($HAS_AUTO_APPROVE === true) →
  OUTPUT(✅ Auto-approved via -y flag)
→ END-IF
- `7`: After approval (manual or auto) - set task `in_progress` (validation IS execution)
- `8`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Sync validation started after approval", append_comment: true}')
- `9`: OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} started (sync validation phase))

# Phase2 context gathering
GOAL(Gather deep context via vector memory searches (no agents))
- `1`: OUTPUT( === PHASE 2: DEEP CONTEXT GATHERING ===)
- `2`: IF($IS_SESSION_RECOVERY === true) →
  NOTE(CAUTION: Session recovery. Memory findings from crashed session should be verified against current codebase.)
→ END-IF
- `3`: mcp__vector-memory__search_memories('{query: "validation context {$TASK_DESCRIPTION}", limit: 5, category: "code-solution,architecture,bug-fix"}')
- `4`: STORE-AS($MEMORY_CONTEXT = {memory findings for validation})
- `5`: mcp__vector-task__task_list('{query: "$TASK_DESCRIPTION", limit: 10}')
- `6`: STORE-AS($RELATED_TASKS = Related vector tasks)
- `7`: OUTPUT(Context gathered: - Memory insights: {$MEMORY_CONTEXT.count} - Related tasks: {$RELATED_TASKS.count})

# Phase3 direct validation
GOAL(Validate task.content requirements using direct tools. TASK SCOPE ONLY. FIX COSMETIC ISSUES INLINE.)
- `1`: OUTPUT( === PHASE 3: DIRECT VALIDATION (TASK SCOPE) ===)
- `2`: STORE-AS($COSMETIC_FIXES_APPLIED = 0)
- `3`: NOTE(TASK SCOPE RULE: Parse $TASK_DESCRIPTION (task.content) for requirements. Validate ONLY those requirements. Do NOT expand scope to unrelated code.)
- `4`: NOTE(COSMETIC FIX RULE: Whitespace, indentation, trailing spaces, typos, formatting - FIX IMMEDIATELY with Edit tool. Increment $COSMETIC_FIXES_APPLIED. Continue. NO tasks for cosmetic.)
- `5`: 3.1 TASK COMPLETION: Parse task.content → list ALL requirements → verify EACH is done
- `6`: Glob(Discover files mentioned/created by task)
- `7`: Read(Read task-related files to confirm implementation)
- `8`: Detect garbage in task scope: unused imports, dead code, debug statements, commented-out code
- `9`: 3.2 CODE QUALITY: Check ONLY task-related code
- `10`: Grep(Search for implementation patterns and potential issues)
- `11`: Verify: logic correct, no security issues, architecture ok for task scope
- `12`: 3.3 QUALITY GATES: Run quality commands
- `13`: Bash({QUALITY_COMMAND from groupVars}) → [Run quality gate commands] → END-Bash
- `14`: Quality gate FAIL = create fix-task
- `15`: 3.4 TESTING: Verify tests for task scope ONLY
- `16`: Check: tests exist for new code, tests pass, edge cases covered
- `17`: Missing tests = fix-task. Failing tests = fix-task.
- `18`: During validation: cosmetic issue found → Edit → fix → $COSMETIC_FIXES_APPLIED++ → continue
- `19`: STORE-AS($VALIDATION_FINDINGS = {task requirements mapping, code issues, test issues, garbage found, quality gate results, cosmetic_fixes_applied: $COSMETIC_FIXES_APPLIED})
- `20`: OUTPUT(Direct validation `completed`. Files reviewed: {count} Cosmetic fixes applied inline: {$COSMETIC_FIXES_APPLIED} Findings captured for aggregation.)

# Phase4 results aggregation
GOAL(Aggregate all validation results and categorize FUNCTIONAL issues only (cosmetic already fixed inline))
- `1`: OUTPUT( === PHASE 4: RESULTS AGGREGATION ===)
- `2`: Merge results from direct validation findings
- `3`: STORE-AS($ALL_ISSUES = {merged FUNCTIONAL issues from validation findings})
- `4`: STORE-AS($TOTAL_COSMETIC_FIXES = {$COSMETIC_FIXES_APPLIED from Phase 3})
- `5`: Categorize FUNCTIONAL issues (require tasks):
- `6`: STORE-AS($CRITICAL_ISSUES = {issues with severity: critical - code logic, security, architecture})
- `7`: STORE-AS($MAJOR_ISSUES = {issues with severity: major - functionality, tests, dependencies})
- `8`: STORE-AS($MINOR_ISSUES = {issues with severity: minor - code style affecting logic, naming conventions})
- `9`: STORE-AS($MISSING_REQUIREMENTS = {task.content requirements not implemented})
- `10`: NOTE(Cosmetic issues were already fixed inline during Phase 3. No separate cosmetic tracking needed.)
- `11`: STORE-AS($FUNCTIONAL_ISSUES_COUNT = {$CRITICAL_ISSUES.count + $MAJOR_ISSUES.count + $MINOR_ISSUES.count + $MISSING_REQUIREMENTS.count})
- `12`: OUTPUT(Validation results: - Critical issues: {$CRITICAL_ISSUES.count} - Major issues: {$MAJOR_ISSUES.count} - Minor issues: {$MINOR_ISSUES.count} - Missing requirements: {$MISSING_REQUIREMENTS.count} - Cosmetic fixes (inline): {$TOTAL_COSMETIC_FIXES}  Functional issues total: {$FUNCTIONAL_ISSUES_COUNT})

# Phase5 task creation
GOAL(Create consolidated tasks (5-8h each) for FUNCTIONAL issues with comprehensive context (cosmetic already fixed inline))
- `1`: OUTPUT( === PHASE 5: TASK CREATION (CONSOLIDATED) ===)
- `2`: NOTE(CRITICAL VERIFICATION: Confirm TASK_PARENT_ID before creating any tasks)
- `3`: VERIFY-SUCCESS($TASK_PARENT_ID === $VECTOR_TASK_ID TASK_PARENT_ID is the ID of the task we are validating (NOT its parent))
- `4`: OUTPUT(Fix tasks will have parent_id: $TASK_PARENT_ID (Task #{$VECTOR_TASK_ID}))
- `5`: Check existing tasks to avoid duplicates
- `6`: mcp__vector-task__task_list('{query: "fix issues $TASK_DESCRIPTION", limit: 20}')
- `7`: STORE-AS($EXISTING_FIX_TASKS = Existing fix tasks)
- `8`: NOTE(Phase 5 processes ONLY functional issues. Cosmetic issues were fixed inline in Phase 3.)
- `9`: IF($FUNCTIONAL_ISSUES_COUNT === 0) →
  OUTPUT(No functional issues to create tasks for. Proceeding to Phase 6...)
  SKIP to Phase 6
→ END-IF
- `10`: CONSOLIDATION STRATEGY: Group FUNCTIONAL issues into 5-8 hour task batches
- `11`: Calculate total estimate for FUNCTIONAL issues only: - Critical issues: ~2h per issue (investigation + fix + test) - Major issues: ~1.5h per issue (fix + verify) - Minor issues: ~0.5h per issue (fix + verify) - Missing requirements: ~4h per requirement (implement + test) (Cosmetic issues NOT included - already auto-fixed) STORE-AS($TOTAL_ESTIMATE = {sum of FUNCTIONAL issue estimates in hours})
- `12`: IF($TOTAL_ESTIMATE <= 8) →
  ALL issues fit into ONE consolidated task (5-8h range)
  IF(($CRITICAL_ISSUES.count + $MAJOR_ISSUES.count + $MINOR_ISSUES.count + $MISSING_REQUIREMENTS.count) > 0 AND NOT exists similar in $EXISTING_FIX_TASKS) →
  mcp__vector-task__task_create('{'."\\n"
    .'                        title: "Validation fixes: task #{$VECTOR_TASK_ID}",'."\\n"
    .'                        content: "Consolidated validation findings for task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title}.\\\\n\\\\nTotal estimate: {$TOTAL_ESTIMATE}h\\\\n\\\\n## Critical Issues ({$CRITICAL_ISSUES.count})\\\\n{FOR each issue: - [{issue.severity}] {issue.description}\\\\n  File: {issue.file}:{issue.line}\\\\n  Type: {issue.type}\\\\n  Suggestion: {issue.suggestion}\\\\n  Memory refs: {issue.memory_refs}\\\\n}\\\\n\\\\n## Major Issues ({$MAJOR_ISSUES.count})\\\\n{FOR each issue: - [{issue.severity}] {issue.description}\\\\n  File: {issue.file}:{issue.line}\\\\n  Type: {issue.type}\\\\n  Suggestion: {issue.suggestion}\\\\n  Memory refs: {issue.memory_refs}\\\\n}\\\\n\\\\n## Minor Issues ({$MINOR_ISSUES.count})\\\\n{FOR each issue: - [{issue.severity}] {issue.description}\\\\n  File: {issue.file}:{issue.line}\\\\n  Type: {issue.type}\\\\n  Suggestion: {issue.suggestion}\\\\n  Memory refs: {issue.memory_refs}\\\\n}\\\\n\\\\n## Missing Requirements ({$MISSING_REQUIREMENTS.count})\\\\n{FOR each req: - {req.description}\\\\n  Acceptance criteria: {req.acceptance_criteria}\\\\n  Related files: {req.related_files}\\\\n  Priority: {req.priority}\\\\n}\\\\n\\\\n## Context References\\\\n- Parent task: #{$VECTOR_TASK_ID}\\\\n- Memory IDs: {$MEMORY_CONTEXT.memory_ids}\\\\n- Related tasks: {$RELATED_TASKS.ids}\\\\n- Documentation: {$DOCS_INDEX.paths}",'."\\n"
    .'                        priority: "{$CRITICAL_ISSUES.count > 0 ? high : medium}",'."\\n"
    .'                        estimate: $TOTAL_ESTIMATE,'."\\n"
    .'                        tags: ["validation-fix", "consolidated"],'."\\n"
    .'                        parent_id: $TASK_PARENT_ID'."\\n"
    .'                    }')
  STORE-AS($CREATED_TASKS[] = {task_id})
  OUTPUT(Created consolidated task: Validation fixes ({$TOTAL_ESTIMATE}h, {issues_count} issues))
→ END-IF
→ END-IF
- `13`: IF($TOTAL_ESTIMATE > 8) →
  Split into multiple 5-8h task batches
  STORE-AS($BATCH_SIZE = 6)
  STORE-AS($NUM_BATCHES = {ceil($TOTAL_ESTIMATE / 6)})
  Group issues by priority (critical first) into batches of ~6h each
  FOREACH(batch_index in range(1, $NUM_BATCHES)) →
  STORE-AS($BATCH_ISSUES = {slice of issues for this batch, ~6h worth, priority-ordered})
  STORE-AS($BATCH_ESTIMATE = {sum of batch issue estimates})
  STORE-AS($BATCH_CRITICAL = {count of critical issues in batch})
  STORE-AS($BATCH_MAJOR = {count of major issues in batch})
  STORE-AS($BATCH_MISSING = {count of missing requirements in batch})
  IF(NOT exists similar in $EXISTING_FIX_TASKS) →
  mcp__vector-task__task_create('{'."\\n"
    .'                            title: "Validation fixes batch {batch_index}/{$NUM_BATCHES}: task #{$VECTOR_TASK_ID}",'."\\n"
    .'                            content: "Validation batch {batch_index} of {$NUM_BATCHES} for task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title}.\\\\n\\\\nBatch estimate: {$BATCH_ESTIMATE}h\\\\nBatch composition: {$BATCH_CRITICAL} critical, {$BATCH_MAJOR} major, {$BATCH_MISSING} missing reqs\\\\n\\\\n## Issues in this batch\\\\n{FOR each issue in $BATCH_ISSUES:\\\\n### [{issue.severity}] {issue.title}\\\\n- File: {issue.file}:{issue.line}\\\\n- Type: {issue.type}\\\\n- Description: {issue.description}\\\\n- Suggestion: {issue.suggestion}\\\\n- Evidence: {issue.evidence}\\\\n- Memory refs: {issue.memory_refs}\\\\n}\\\\n\\\\n## Full Context References\\\\n- Parent task: #{$VECTOR_TASK_ID}\\\\n- Memory IDs: {$MEMORY_CONTEXT.memory_ids}\\\\n- Related tasks: {$RELATED_TASKS.ids}\\\\n- Documentation: {$DOCS_INDEX.paths}\\\\n- Total batches: {$NUM_BATCHES} ({$TOTAL_ESTIMATE}h total)",'."\\n"
    .'                            priority: "{$BATCH_CRITICAL > 0 ? high : medium}",'."\\n"
    .'                            estimate: $BATCH_ESTIMATE,'."\\n"
    .'                            tags: ["validation-fix", "batch-{batch_index}"],'."\\n"
    .'                            parent_id: $TASK_PARENT_ID'."\\n"
    .'                        }')
  STORE-AS($CREATED_TASKS[] = {task_id})
  OUTPUT(Created batch {batch_index}/{$NUM_BATCHES}: {$BATCH_ESTIMATE}h ({$BATCH_ISSUES.count} issues))
→ END-IF
→ END-FOREACH
→ END-IF
- `14`: OUTPUT(Tasks created: {$CREATED_TASKS.count} (total estimate: {$TOTAL_ESTIMATE}h))

# Phase6 completion
GOAL(Complete validation, update task status, store summary to memory)
- `1`: OUTPUT( === PHASE 6: VALIDATION COMPLETE ===)
- `2`: STORE-AS($VALIDATION_SUMMARY = {all_issues_count, tasks_created_count, pass_rate})
- `3`: STORE-AS($VALIDATION_STATUS = IF($CRITICAL_ISSUES.count === 0 AND $MISSING_REQUIREMENTS.count === 0) →
  PASSED
→ ELSE →
  NEEDS_WORK
→ END-IF)
- `4`: mcp__vector-memory__store_memory('{content: "Validation of task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title}\\\\n\\\\nStatus: {$VALIDATION_STATUS}\\\\nCritical: {$CRITICAL_ISSUES.count}\\\\nMajor: {$MAJOR_ISSUES.count}\\\\nMinor: {$MINOR_ISSUES.count}\\\\nTasks created: {$CREATED_TASKS.count}\\\\n\\\\nFindings:\\\\n{summary of key findings}", category: "code-solution", tags: ["validation", "audit", "task:validate-sync"]}')
- `5`: IF($VALIDATION_STATUS === "PASSED" AND $CREATED_TASKS.count === 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Sync validation PASSED. All requirements implemented, no issues found.", append_comment: true}')
  OUTPUT(✅ Task #{$VECTOR_TASK_ID} marked as VALIDATED)
→ END-IF
- `6`: IF($CREATED_TASKS.count > 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Sync validation found issues. Created {$CREATED_TASKS.count} fix tasks: Critical: {$CRITICAL_ISSUES.count}, Major: {$MAJOR_ISSUES.count}, Minor: {$MINOR_ISSUES.count}, Missing: {$MISSING_REQUIREMENTS.count}. Returning to `pending` - fix tasks must be `completed` before re-validation.", append_comment: true}')
  OUTPUT(⏳ Task #{$VECTOR_TASK_ID} returned to PENDING ({$CREATED_TASKS.count} fix tasks required before re-validation))
→ END-IF
- `7`: OUTPUT( === VALIDATION REPORT === Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Status: {$VALIDATION_STATUS}  | Metric | Count | |--------|-------| | Critical issues | {$CRITICAL_ISSUES.count} | | Major issues | {$MAJOR_ISSUES.count} | | Minor issues | {$MINOR_ISSUES.count} | | Missing requirements | {$MISSING_REQUIREMENTS.count} | | Cosmetic fixes (inline) | {$TOTAL_COSMETIC_FIXES} | | Tasks created | {$CREATED_TASKS.count} |  {IF $TOTAL_COSMETIC_FIXES > 0: "✅ Cosmetic issues fixed inline during validation"} {IF $CREATED_TASKS.count > 0: "Follow-up tasks: {$CREATED_TASKS}"}  Validation stored to vector memory.)

# Error handling
Graceful error handling for validation process
- `1`: IF(vector task not found) →
  Report: "Vector task #{id} not found"
  Suggest: Check task ID with mcp__vector-task__task_list
  Abort validation
→ END-IF
- `2`: IF(vector task not in validatable status) →
  Report: "Vector task #{id} status is {status}, not `completed`/`tested`/validated"
  Suggest: Run /task:async or /task:sync #{id} first
  Abort validation
→ END-IF
- `3`: IF(invalid task ID format) →
  Report: "Invalid task ID format. Expected: 15, #15, task 15, task:15"
  Suggest: "Use /do:validate for text-based validation"
  Abort command
→ END-IF
- `4`: IF(validation fails) →
  Log: "Validation failed: {error}"
  Report partial validation in summary
→ END-IF
- `5`: IF(task creation fails) →
  Log: "Failed to create task: {error}"
  Store issue details to vector memory for manual review
  Continue with remaining tasks
→ END-IF

# Constraints
Validation constraints and limits (sync)
- `1`: Max 20 tasks created per validation run
- `2`: Validation timeout: 10 minutes total
- `3`: VERIFY-SUCCESS(vector_task_loaded = true validatable_status_verified = true task_scope_validated = true quality_gates_executed = true results_stored_to_memory = true no_direct_fixes = true)

# Example simple validation
SCENARIO(Sync validate completed vector task)
- `input`: "task 15" or "#15" where task #15 is "Implement user login"
- `load`: task_get(15) → title, content, status: `completed`
- `flow`: Task Loading → Preview → Context → Validation (task scope) → Aggregate → Create Tasks → Complete
- `result`: Validation PASSED → status: `validated` OR NEEDS_WORK → N fix tasks created

# Example with fixes
SCENARIO(Sync validation finds issues)
- `input`: "#28" where task #28 has status: `completed`
- `validation`: Found: 2 critical, 3 major, 1 missing requirement
- `tasks`: Created 1 consolidated fix task (6h estimate)
- `result`: Task #28 status → `pending`, 1 fix task created as child

# Example rerun
SCENARIO(Re-run sync validation (idempotent))
- `input`: "task 15" (already `validated` before)
- `behavior`: Skips existing tasks, only creates NEW issues found
- `result`: Same/updated validation report, no duplicate tasks

# Validate vs validate sync
When to use /task:validate vs /task:validate-sync
- `USE /task:validate`: Async validation with parallel agents for large/complex tasks.
- `USE /task:validate-sync`: Direct sync validation without agents. Best for smaller or isolated tasks.

# Response format
=== headers | single approval | progress markers | tables for results | Created tasks listed | 📋 task ID references

</command>