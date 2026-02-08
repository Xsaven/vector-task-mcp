---
name: "task:decompose"
description: "Decompose large task into subtasks (each <=5-8h)"
---

<command>
<meta>
<id>task:decompose</id>
<description>Decompose large task into subtasks (each <=5-8h)</description>
</meta>
<execute>Split large vector task into 5-8h subtasks with logical execution order.</execute>
<provides>Task decomposition into subtasks. 2 parallel agents research (code + memory), plans logical execution order, creates subtasks. NEVER executes - only creates.</provides>

# Iron Rules
## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN analyze how to decompose.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. Fake results = CRITICAL VIOLATION.

## No-verbose (CRITICAL)
FORBIDDEN: <meta>, <synthesis>, <plan>, <analysis> tags. Brief status only.

## Show-progress (HIGH)
Show brief step status. User must see what is happening.

## Understand-to-decompose (CRITICAL)
MUST understand task INTENT to decompose properly. Analyze: what are logical boundaries? what depends on what? Unknown library/pattern → context7 first.

## Auto-approve (HIGH)
-y flag = auto-approve. Skip "Proceed?" but show progress.

## Create-only (CRITICAL)
This command ONLY creates subtasks. NEVER execute any subtask after creation.
- **why**: Decomposition and execution are separate concerns. User decides what to execute next.
- **on_violation**: STOP immediately after subtask creation. Return control to user.

## Parent-id-required (CRITICAL)
ALL created subtasks MUST have parent_id = $TASK_ID. IRON LAW: When working with task X, EVERY new task created MUST be a child of X. No orphan tasks. No exceptions. Verify parent_id = $TASK_ID in EVERY task_create/task_create_bulk call before execution.
- **why**: Hierarchy integrity. Orphan tasks break traceability, workflow, and task relationships. Task X work = Task X children only.
- **on_violation**: ABORT if parent_id missing or != $TASK_ID. Double-check EVERY task_create call.

## Mandatory-user-approval (CRITICAL)
EVERY operation MUST have explicit user approval BEFORE execution. Present plan → WAIT for approval → Execute. NO auto-execution. EXCEPTION: If $HAS_Y_FLAG is true, auto-approve.
- **why**: User maintains control. No surprises. Flag -y enables automated execution.
- **on_violation**: STOP. Wait for explicit user approval (unless $HAS_Y_FLAG is true).

## Order-mandatory (CRITICAL)
EVERY subtask MUST have explicit order field set. Sequential: 1, 2, 3. Parallel-safe: same order.
- **why**: Order defines execution priority. Missing order = ambiguous sequence = blocked user.
- **on_violation**: Set order parameter in EVERY task_create call. Never omit.

## Sequence-analysis (CRITICAL)
When creating 2+ subtasks: STOP and THINK about optimal sequence. Consider: dependencies, data flow, setup requirements, parallel opportunities.
- **why**: Wrong sequence wastes time. User executes in order - if task 3 needs output from task 5, user is blocked.
- **on_violation**: Use SequentialThinking to analyze dependencies. Reorder before creation.

## Logical-order (HIGH)
Subtasks MUST be in logical execution order. Dependencies first, dependents after.
- **why**: Prevents blocked work. User can execute subtasks sequentially without dependency issues.
- **on_violation**: Reorder subtasks. Use SequentialThinking for complex dependencies.

## Exclude-brain-directory (HIGH)
NEVER analyze .brain/ when decomposing code tasks.
- **why**: Brain system internals are not project code.
- **on_violation**: Skip .brain/ in all exploration.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_Y_FLAG = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
GOAL(Decompose task into subtasks: load → research → plan → approve → create)
- `1`: mcp__vector-task__task_get('{task_id: $TASK_ID}') → STORE-AS($TASK)
- `2`: IF(not found) → ABORT "Task not found"
- `3`: mcp__vector-task__task_list('{parent_id: $TASK_ID, limit: 50}') → STORE-AS($EXISTING_SUBTASKS)
- `4`: IF(EXISTING_SUBTASKS.count > 0 AND NOT $HAS_AUTO_APPROVE) →
  Ask: "(1) Add more, (2) Replace all, (3) Abort"
→ END-IF
- `5`: IF(unknown library/pattern in task) →
  mcp__context7__query-docs('{query: "{library/pattern}"}') → understand before decomposing
→ END-IF
- `6`: [PARALLEL] → ([DELEGATE] @agent-explore: 'DECOMPOSE RESEARCH: task #{$TASK.id}. Find: files, components, dependencies, split boundaries. EXCLUDE: .brain/. Return: {files, components, boundaries}' + mcp__vector-memory__search_memories('{query: "decomposition patterns, similar tasks", limit: 5}') → STORE-AS($MEMORY_INSIGHTS)) → END-PARALLEL
- `7`: STORE-AS($CODE_INSIGHTS = {from explore agent})
- `8`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Synthesizing: CODE_INSIGHTS + MEMORY_INSIGHTS. Identify: boundaries, dependencies, parallel opportunities, order.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `9`: Group by component, order by dependency, estimate each
- `10`: STORE-AS($SUBTASK_PLAN = [{title, content, estimate, priority, order}])
- `11`: Show: | Order | Subtask | Est | Priority |
- `12`: IF($HAS_AUTO_APPROVE) →
  Auto-approved
→ ELSE →
  Ask: "Create {count} subtasks? (yes/no/modify)"
→ END-IF
- `13`: mcp__vector-task__task_create_bulk('{tasks: [{title, content, parent_id: $TASK_ID, priority, estimate, order, tags: ["decomposed"]}]}')
- `14`: mcp__vector-task__task_list('{parent_id: $TASK_ID}') → verify
- `15`: mcp__vector-memory__store_memory('{content: "Decomposed #{$TASK.id} into {count} subtasks", category: "tool-usage"}')
- `16`: STOP: Do NOT execute. Return control to user.

# Error handling
- `1`: IF(task not found) → ABORT "suggest task_list"
- `2`: IF(agent fails) → Continue with available data
- `3`: IF(user rejects plan) → Accept modifications, rebuild, re-submit

</command>