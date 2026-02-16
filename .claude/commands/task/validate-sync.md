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
<provides>Sync validation of completed vector task. Direct tools (no agents). Validates task.content requirements, code quality, tests. Cosmetic fixed inline. Functional issues → fix-tasks. Idempotent.</provides>

# Iron Rules
## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN validate.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. Fake results = CRITICAL VIOLATION.

## No-delegation (CRITICAL)
SYNC validation = direct tools only. NO Task() delegation. Use: Read, Edit, Glob, Grep, Bash.

## Validation-only (CRITICAL)
VALIDATION reads and audits. NEVER implement or fix functional code. Functional issues → create fix-task.

## Auto-approve (HIGH)
-y flag = auto-approve. Skip "Proceed?" but show progress.

## Parent-id-mandatory (CRITICAL)
ALL fix-tasks MUST have parent_id = $VECTOR_TASK_ID. No orphans.
- **on_violation**: ABORT task_create if parent_id wrong.

## Task-scope-only (CRITICAL)
Validate ONLY task.content requirements. Do NOT expand scope.

## Task-complete (CRITICAL)
ALL requirements MUST be done. Missing = fix-task.

## No-garbage (CRITICAL)
Detect garbage in task scope: unused imports, dead code, debug statements. Garbage = fix-task.

## Cosmetic-inline (CRITICAL)
Cosmetic issues (whitespace, typos, formatting) = fix IMMEDIATELY with Edit. Increment counter. NO task.

## Functional-to-task (CRITICAL)
Functional issues = fix-task. Functional: logic bugs, security, architecture violations, missing tests.

## Fix-task-blocks-validated (CRITICAL)
Fix-task created → status MUST be "pending". "validated" = ZERO fix-tasks.

## Idempotent (HIGH)
Re-run produces same result. Check existing tasks before creating. Skip duplicates.

## Test-coverage (HIGH)
New code MUST have test coverage >=80%. No coverage = fix-task.

## Slow-test-detection (HIGH)
Slow tests = fix-task. Unit >500ms, integration >2s, any >5s = CRITICAL.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
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
- `7`: STORE-AS($TASK_PARENT_ID = $VECTOR_TASK_ID)
- `8`: Show: Task #{id}, title, status, subtasks count
- `9`: IF($HAS_AUTO_APPROVE) →
  Auto-approved
→ ELSE →
  Ask: "Validate? (yes/no)"
→ END-IF
- `10`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Sync validation started"}')
- `11`: mcp__vector-memory__search_memories('{query: "{TASK.title}", limit: 5, category: "code-solution"}') → STORE-AS($MEMORY)
- `12`: mcp__vector-task__task_list('{query: "{TASK.title}", limit: 5}') → STORE-AS($RELATED)
- `13`: IF(unknown library/pattern) →
  mcp__context7__query-docs('{query: "{library}"}') → understand before validating
→ END-IF
- `14`: STORE-AS($COSMETIC_FIXES = 0)
- `15`: 4.1 COMPLETION: Parse task.content → list requirements → verify each done
- `16`: Glob(Find task-related files)
- `17`: Read(Read files, confirm implementation)
- `18`: Detect garbage: unused imports, dead code, debug statements
- `19`: 4.2 CODE QUALITY: Task scope only
- `20`: Grep(Search patterns, potential issues)
- `21`: Check: logic, security, architecture. Unknown lib → context7.
- `22`: 4.3 QUALITY GATES
- `23`: Bash({QUALITY_COMMAND}) → [Run quality gates] → END-Bash
- `24`: Gate FAIL = fix-task
- `25`: 4.4 TESTING: Task scope only
- `26`: Check: tests exist (>=80%), pass, edge cases. Slow tests = issue.
- `27`: During validation: cosmetic found → Edit → fix → COSMETIC_FIXES++ → continue
- `28`: STORE-AS($ISSUES = {critical, major, minor, missing_requirements})
- `29`: STORE-AS($FUNCTIONAL_COUNT = critical + major + minor + missing)
- `30`: IF(FUNCTIONAL_COUNT = 0) → Skip to completion
- `31`: mcp__vector-task__task_list('{query: "fix {TASK.title}", limit: 10}') → check duplicates
- `32`: STORE-AS($TOTAL_ESTIMATE = critical*2h + major*1.5h + minor*0.5h + missing*4h)
- `33`: IF(TOTAL_ESTIMATE <= 8 AND no duplicate) →
  mcp__vector-task__task_create('{title: "Validation fixes: #{TASK.id}", content: "{issues}", parent_id: $TASK_PARENT_ID, priority: "{critical>0 ? high : medium}", estimate: {TOTAL_ESTIMATE}, tags: ["validation-fix"]}')
  STORE-AS($CREATED_TASKS[] = {id})
→ END-IF
- `34`: IF(TOTAL_ESTIMATE > 8) →
  Split into 5-8h batches, create multiple tasks
→ END-IF
- `35`: IF(CREATED_TASKS.count = 0 AND FUNCTIONAL_COUNT = 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Sync validation PASSED"}')
→ END-IF
- `36`: IF(CREATED_TASKS.count > 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Validation found issues. Fix-tasks: {count}"}')
→ END-IF
- `37`: mcp__vector-memory__store_memory('{content: "Validated #{TASK.id}: {status}. Issues: {counts}. Fix-tasks: {count}.", category: "code-solution"}')
- `38`: Report: task, status, issues counts, cosmetic fixes, fix-tasks created

# Error handling
- `1`: IF(task not found) → ABORT "Check task ID"
- `2`: IF(task not validatable status) →
  ABORT "Complete via /task:sync first"
→ END-IF
- `3`: IF(validation fails) → Report partial, store to memory
- `4`: IF(task creation fails) → Store to memory for manual review

</command>