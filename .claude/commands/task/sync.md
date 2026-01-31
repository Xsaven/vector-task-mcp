---
name: "task:sync"
description: "Direct sync execution of vector task by Brain without agent delegation"
---

<command>
<meta>
<id>task:sync</id>
<description>Direct sync execution of vector task by Brain without agent delegation</description>
</meta>
<execute>Run task execution synchronously by Brain without agent delegation.</execute>
<provides>Direct sync execution of vector task by Brain. No agent delegation. Uses Read/Edit/Write/Glob/Grep directly. Includes docs gathering via brain docs, web research, TDD mode support.</provides>

# Iron Rules
## Tool-call-first (CRITICAL)
YOUR VERY FIRST RESPONSE MUST BE A TOOL CALL. No text before tools. No analysis. No thinking out loud. CALL mcp__vector-task__task_get IMMEDIATELY.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. You CANNOT know task status or content without REAL tool calls. Fake results = CRITICAL VIOLATION.

## No-verbose (CRITICAL)
FORBIDDEN: <meta>, <synthesis>, <plan>, <analysis> tags. No long explanations before action.

## Show-progress (HIGH)
ALWAYS show brief step status and results. User must see what is happening and can interrupt/correct at any moment.

## No-interpretation (CRITICAL)
NEVER interpret task content. Task ID given = execute it. JUST DO IT.

## Auto-approve (HIGH)
-y flag = auto-approve. Skip "Proceed?" questions, but STILL show progress. User sees everything, just no approval prompts.

## No-delegation (CRITICAL)
Brain executes ALL steps directly. NO Task() delegation. Use ONLY: Read, Edit, Write, Glob, Grep, Bash.

## Read-before-edit (CRITICAL)
ALWAYS Read file BEFORE Edit/Write.

## Atomic-only (CRITICAL)
Execute ONLY task.content requirements. NO improvisation.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}')
- `2`: IF(not found) → ABORT
- `3`: IF(status=`completed`) → ask "Re-execute?"
- `4`: IF(status=`in_progress`) →
  SESSION RECOVERY: check if crashed session
→ ELSE →
  continue OR ABORT "another session active"
→ END-IF
- `5`: IF(status=`tested` AND comment contains "TDD MODE") →
  TDD execution mode (tests exist, implement feature)
→ END-IF
- `6`: IF(parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') for broader context
→ END-IF
- `7`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') → load subtasks if any
- `8`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') → past implementations, patterns
- `9`: mcp__vector-task__task_list('{query: task.title, limit: 5}') → related tasks
- `10`: Bash('brain docs {keywords from task}') → get documentation index (returns: Path, Name, Description)
- `11`: IF(docs found) → Read('{doc.path}') for each relevant doc
- `12`: IF(web research needed) →
  WebSearch(Research best practices for task)
→ END-IF
- `13`: mcp__vector-memory__store_memory('{content: "Context for task: {summary}", category: "tool-usage"}')
- `14`: Glob(Find relevant files based on task)
- `15`: Grep(Search code patterns)
- `16`: Read(Read identified files)
- `17`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Planning execution steps. Analyzing: file dependencies, edit order, atomic changes, rollback points, risk assessment.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 3,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `18`: STORE-AS($PLAN = [{step, file, action: read|edit|write, changes}])
- `19`: IF($HAS_AUTO_APPROVE) →
  skip to execution immediately
→ ELSE →
  show brief plan, wait "yes"
→ END-IF
- `20`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Execution started", append_comment: true}')
- `21`: FOREACH(step in STORE-GET($PLAN)) →
  Read('{step.file}')
  Edit('{step.file}', '{old}', '{new}')
  OR Write('{step.file}', '{content}')
→ END-FOREACH
- `22`: IF(step fails) → Retry/Skip/Abort
- `23`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "Files: {list}", append_comment: true}')
- `24`: mcp__vector-memory__store_memory('{content: "Task #{id}: {approach}, files: {list}, learnings: {insights}", category: "code-solution"}')

# Tdd mode
- `1`: IF(task.comment contains "TDD MODE" AND status=`tested`) →
  Execute implementation based on task.content
→ END-IF
- `2`: Bash(Run related tests) → [php artisan test --filter="{pattern}" OR vendor/bin/pest --filter="{pattern}"] → END-Bash
- `3`: IF(all tests pass) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "TDD: Tests PASSED", append_comment: true}')
→ END-IF
- `4`: IF(tests fail) → continue implementation, do NOT mark `completed`

# Error handling
- `1`: IF(task not found) → ABORT "suggest task_list"
- `2`: IF(task already `completed`) → ask "Re-execute?"
- `3`: IF(file not found) → offer: Create / Specify correct path / Abort
- `4`: IF(edit conflict (old_string not found)) →
  Re-read file, adjust edit, retry
→ END-IF
- `5`: IF(user rejects plan) →
  accept modifications, rebuild plan, re-present
→ END-IF

</command>