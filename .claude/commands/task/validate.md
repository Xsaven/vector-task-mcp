---
name: "task:validate"
description: "Async validation of vector task with 3 parallel agents"
---

<command>
<meta>
<id>task:validate</id>
<description>Async validation of vector task with 3 parallel agents</description>
</meta>
<execute>Validate completed vector task with async workflow.</execute>
<provides>Validate vector task. 3 parallel agents: Code Quality, Testing, Documentation. Creates fix-tasks for issues. Cosmetic fixed inline.</provides>

# Iron Rules
## Tool-call-first (CRITICAL)
YOUR VERY FIRST RESPONSE MUST BE A TOOL CALL. No text before tools. No analysis. No thinking out loud. CALL mcp__vector-task__task_get IMMEDIATELY.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. You CANNOT know task status, validation results, or issues without REAL tool calls. Fake results = CRITICAL VIOLATION.

## No-verbose (CRITICAL)
FORBIDDEN: <meta>, <synthesis>, <plan>, <analysis> tags. No long explanations before action.

## Show-progress (HIGH)
ALWAYS show brief step status and results. User must see what is happening and can interrupt/correct at any moment.

## Auto-approve (HIGH)
-y flag = auto-approve. Skip "Proceed?" questions, but STILL show progress. User sees everything, just no approval prompts.

## Parent-id-mandatory (CRITICAL)
When working with task $VECTOR_TASK_ID, ALL new tasks created MUST have parent_id = $VECTOR_TASK_ID. No exceptions. Every fix-task, subtask, or related task MUST be a child of the task being `validated`.
- **why**: Task hierarchy integrity. Orphan tasks break traceability and workflow.
- **on_violation**: ABORT task_create if parent_id missing or wrong. Verify parent_id = $VECTOR_TASK_ID in EVERY task_create call.

## Execute-always (CRITICAL)
NEVER skip validation. Status "validated" = re-validate.

## No-interpretation (CRITICAL)
NEVER interpret task content to decide whether to validate. Task ID given = validate it. No excuses. JUST EXECUTE.

## Task-scope-only (CRITICAL)
Validate ONLY what task.content describes. Do NOT check unrelated code/files. Do NOT expand scope. Task says "add X" = check X exists and works. Task says "fix Y" = check Y is fixed. NOTHING MORE.

## Task-complete (CRITICAL)
ALL task requirements MUST be done. Parse task.content for requirements list. Each requirement = verified. Missing requirement = fix-task.

## No-garbage (CRITICAL)
Detect garbage: unused imports, dead code, debug statements, commented-out code, orphan files, test artifacts. Garbage in task scope = fix-task.

## Cosmetic-inline (CRITICAL)
Cosmetic = fix inline, NEVER create task. Cosmetic includes: whitespace, typos, formatting, code comments (add/update/remove), docblocks, docstrings, variable naming (non-breaking), import sorting. Metadata tags = IGNORE.

## Functional-to-task (CRITICAL)
Functional issues ONLY = create fix-task. Functional: logic bugs, security vulnerabilities, architecture violations, missing tests, broken functionality. NOT functional: comments, docs, naming, formatting.

## Fix-task-blocks-validated (CRITICAL)
If fix-task created → parent status MUST be "pending", NEVER "validated". "validated" = ZERO fix-tasks. NO EXCEPTIONS. "NOT blocking" still requires fix-task and `pending` status.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') STORE-AS($TASK)
- `2`: IF(not found) → ABORT
- `3`: IF(status NOT IN [`completed`, `tested`, `validated`, `in_progress`]) →
  ABORT "Complete first"
→ END-IF
- `4`: IF(status=`in_progress`) →
  SESSION RECOVERY: check if crashed session (no `active` work)
→ ELSE →
  ABORT "another session active"
→ END-IF
- `5`: IF(STORE-GET($TASK).parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') STORE-AS($PARENT)
→ END-IF
- `6`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') STORE-AS($SUBTASKS)
- `7`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') STORE-AS($MEMORY_CONTEXT)
- `8`: mcp__vector-task__task_list('{query: task.title, limit: 5}') STORE-AS($RELATED_TASKS)
- `9`: Bash('brain docs {keywords from task}') STORE-AS($DOCS_INDEX)
- `10`: IF($HAS_AUTO_APPROVE) →
  SKIP(approval)
→ ELSE →
  show task info, wait "yes"
→ END-IF
- `11`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress"}')
- `12`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Analyzing task requirements for validation. Parsing task.content to extract: explicit requirements, acceptance criteria, affected files, expected behaviors.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `13`: [PARALLEL] → ([DELEGATE] @agent-explore: 'TASK COMPLETION: Read task.content. List ALL requirements. Verify EACH requirement is done. Check ONLY files mentioned/created by task. Detect garbage: unused imports, dead code, debug statements. COSMETIC=fix inline. Return: missing requirements, garbage found.' + [DELEGATE] @agent-explore: 'CODE QUALITY: Check ONLY task-related code. No scope expansion. Verify: logic correct, no security issues, architecture ok. Run quality gates. COSMETIC=fix inline. Return: functional issues in task scope ONLY.' + [DELEGATE] @agent-explore: 'TESTING: Run tests for task scope ONLY. Verify: tests exist for new code, tests pass, edge cases covered. COSMETIC=fix inline. Return: missing tests, failing tests.') → END-PARALLEL
- `14`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Merging validation agent results. Analyzing: issue severity, duplicates, false positives, fix priority, task scope compliance.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `15`: Merge agent results STORE-AS($ISSUES) categorize: Critical/Major/Minor
- `16`: IF(issues=0 AND no fix-task needed) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated"}')
→ ELSE →
  mcp__vector-task__task_create('{title: "Validation fixes: #ID", content: issues_list, parent_id: $VECTOR_TASK_ID, tags: ["validation-fix"]}')
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending"}') ← MANDATORY when fix-task created
→ END-IF
- `17`: OUTPUT(task, Critical/Major/Minor counts, cosmetic fixed, status, fix-task ID)
- `18`: mcp__vector-memory__store_memory('{content: validation_summary, category: "code-solution"}')

# Error handling
- `1`: IF(task not found) → ABORT "suggest task_list"
- `2`: IF(task status invalid) → ABORT "Complete first"
- `3`: IF(agent fails) → retry | ELSE → continue with remaining agents
- `4`: IF(fix-task creation fails) → store to memory for manual review
- `5`: IF(user rejects validation) → accept modifications, re-validate

</command>