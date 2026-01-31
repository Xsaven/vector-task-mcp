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
<provides>Async execution of vector task via agent delegation. Brain orchestrates, agents execute. Includes docs gathering, web research, TDD mode. Parallel when independent.</provides>

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

## Never-execute-directly (CRITICAL)
Brain NEVER calls Edit/Write/Glob/Grep/Read for implementation. ALL work via Task() to agents.

## Atomic-tasks (CRITICAL)
Each agent task: 1-2 files (max 3-5 if same feature). NO broad changes.

## Parallel-when-safe (HIGH)
Parallel: independent tasks, different files, no data flow. Multiple Task() in ONE message.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → STORE-AS($TASK = task.content IS your work order)
- `2`: IF(not found) → ABORT "Task not found"
- `3`: IF(status=`completed`) → ask "Re-execute?"
- `4`: IF(status=`in_progress`) →
  SESSION RECOVERY: check if crashed session → continue
→ ELSE →
  ABORT "another session active"
→ END-IF
- `5`: IF(status=`tested` AND comment contains "TDD MODE") →
  TDD execution mode (tests exist, implement feature)
→ END-IF
- `6`: IF(parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') for broader context
→ END-IF
- `7`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') → STORE-AS($SUBTASKS)
- `8`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') → STORE-AS($MEMORY = past implementations, patterns)
- `9`: mcp__vector-task__task_list('{query: task.title, limit: 5}') → STORE-AS($RELATED = related tasks)
- `10`: Bash('brain docs {keywords from task}') → STORE-AS($DOCS = documentation index)
- `11`: IF(docs found) →
  delegate: [DELEGATE] @agent-explore: 'Read and analyze documentation files: {doc.paths}'
→ END-IF
- `12`: IF(web research needed) →
  delegate: [DELEGATE] @agent-web-research-master: 'Research best practices for: {task.title}'
→ END-IF
- `13`: mcp__vector-memory__store_memory('{content: "Context for task: {summary}", category: "tool-usage"}')
- `14`: Analyze task.content → break into atomic agent subtasks
- `15`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Planning agent delegation. Analyzing: task boundaries, parallelization opportunities, agent selection, subtask dependencies, file scope per agent.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 3,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `16`: STORE-AS($PLAN = [{agent, subtask, files, parallel: true/false, order}])
- `17`: IF($HAS_AUTO_APPROVE) →
  skip to execution immediately
→ ELSE →
  show brief plan, wait "yes"
→ END-IF
- `18`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Execution started", append_comment: true}')
- `19`: Delegate to agents based on STORE-GET($PLAN):
- `20`: Independent subtasks → multiple [DELEGATE] @agent-{agent}: '{subtask}' in ONE message (parallel)
- `21`: Dependent subtasks → sequential delegation
- `22`: Available agents: Bash('brain list:masters')
- `23`: Collect agent results
- `24`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "Files: {list}", append_comment: true}')
- `25`: mcp__vector-memory__store_memory('{content: "Task #{id}: {approach}, files: {list}, learnings: {insights}", category: "code-solution"}')

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
- `2`: After implementation → [DELEGATE] @agent-explore: 'Run tests: php artisan test --filter="{pattern}"'
- `3`: IF(all tests pass) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "TDD: Tests PASSED", append_comment: true}')
→ END-IF
- `4`: IF(tests fail) →
  continue implementation via agents, do NOT mark `completed`
→ END-IF

# Error handling
- `1`: IF(task not found) → ABORT "suggest task_list"
- `2`: IF(task already `completed`) → ask "Re-execute?"
- `3`: IF(agent fails) →
  retry with different agent
→ ELSE →
  escalate to user
→ END-IF
- `4`: IF(user rejects plan) →
  accept modifications, rebuild plan, re-present
→ END-IF

# Agent memory
ALL agent delegations MUST include memory instruction:
"Search memory for: {relevant_terms}. Store learnings after completion."
Memory = agent communication channel across sessions

</command>