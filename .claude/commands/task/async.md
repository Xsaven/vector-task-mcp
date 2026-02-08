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
## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN analyze what to delegate.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. You CANNOT know task status or content without REAL tool calls. Fake results = CRITICAL VIOLATION.

## No-verbose (CRITICAL)
FORBIDDEN: <meta>, <synthesis>, <plan>, <analysis> tags. No long explanations before action.

## Show-progress (HIGH)
ALWAYS show brief step status and results. User must see what is happening and can interrupt/correct at any moment.

## Smart-delegation (CRITICAL)
Brain must understand task INTENT before delegating. Agents execute, but Brain decides WHAT to delegate and HOW to split work.

## Research-triggers (CRITICAL)
Research BEFORE delegation when ANY: 1) content <50 chars, 2) contains "example/like/similar/e.g./такий як", 3) no file paths AND no class/function names, 4) references unknown library/pattern, 5) contradicts existing code, 6) multiple valid interpretations, 7) task asks "how to" without specifics.

## Research-flow (HIGH)
Research order: 1) context7 for library docs, 2) web-research-master for patterns. -y flag: auto-select best approach for delegation. No -y: present options to user.

## Failure-history-mandatory (CRITICAL)
BEFORE delegation: search memory category "debugging" for KNOWN FAILURES related to this task/problem. Pass failures to agents. Agents MUST NOT attempt solutions that already failed.
- **why**: Repeating failed solutions wastes time. Memory contains "this does NOT work" knowledge.
- **on_violation**: Search debugging memories FIRST. Include KNOWN_FAILURES in agent prompts.

## Sibling-task-check (HIGH)
BEFORE delegation: fetch sibling tasks (same parent_id, status=`completed`/`stopped`). Check comments for what was tried and failed. Pass context to agents.
- **why**: Previous attempts on same problem contain valuable "what not to do" information.

## Escalate-stuck-problems (HIGH)
If task matches pattern that failed 2+ times (from memory/sibling analysis) → DO NOT delegate same approach. Research alternatives via web-research-master or escalate to user.
- **why**: Definition of insanity: doing same thing expecting different results.

## Never-execute-directly (CRITICAL)
Brain NEVER calls Edit/Write/Glob/Grep/Read for implementation. ALL work via Task() to agents.

## Atomic-tasks (CRITICAL)
Each agent task: 1-2 files (max 3-5 if same feature). NO broad changes.

## Parallel-when-safe (HIGH)
Parallel: independent tasks, different files, no data flow. Multiple Task() in ONE message.

## Auto-approve-autonomy (HIGH)
-y flag = FULL AUTONOMY. Brain delegates ALL work without asking. Auto: select agents, determine parallel vs sequential, handle agent failures, rollback on critical `failure`.
- **why**: User explicitly trusts Brain to orchestrate end-to-end. Interruptions defeat async purpose.

## Interactive-mode (HIGH)
NO -y flag = INTERACTIVE. Ask before: major architectural decisions, multiple valid approaches, selecting between incompatible agent strategies, critical failures.
- **why**: User wants control over significant orchestration decisions.

## Agent-dependency-instruction (HIGH)
Include in agent prompt: "If dependencies needed: detect package manager, install (composer/npm/pip/cargo/go mod). Run audit after install."
- **why**: Agents handle their own dependency installation autonomously.

## Agent-git-instruction (HIGH)
Include in agent prompt: "Before multi-file changes: check git status. Uncommitted changes: stash first. Rollback on `failure`."
- **why**: Agents must protect user work.

## Agent-security-instruction (CRITICAL)
Include in agent prompt: "NEVER hardcode secrets. Validate external input. Escape output. Use parameterized queries."
- **why**: Security rules must propagate to all agents.

## Agent-validation-instruction (HIGH)
Include in agent prompt: "After changes: verify syntax, run linter if configured, run related tests. Fix issues before reporting completion."
- **why**: Agents must validate their own work.

## Pre-delegation-git-check (HIGH)
Before ANY delegation: check git status. Uncommitted changes exist: -y = warn and proceed, no -y = ask "Uncommitted changes. Stash before delegating?"
- **why**: Brain ensures clean state before agents touch files.

## Delegation-context-include (CRITICAL)
Every Task() MUST include: 1) clear task description, 2) file scope, 3) memory search hints, 4) security + validation instructions.
- **why**: Agents need full context to work autonomously.

## Agent-failure-isolation (HIGH)
Agent fails: other parallel agents continue. Failed agent work: -y = auto-rollback its files, no -y = ask "Agent X failed. Rollback its changes/Retry/Skip?"

## Critical-agent-failure (HIGH)
Critical agent (blocker for others) fails: -y = abort remaining + rollback all, no -y = ask "Critical task failed. Abort all/Retry/Manual intervention?"

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

## Subtasks-parallel-assessment (HIGH)
Parent task with subtasks: analyze dependencies. Independent subtasks: delegate in parallel. Dependent: delegate in order. -y = auto-decide, no -y = show plan.

## Subtasks-agent-assignment (MEDIUM)
Each subtask gets dedicated agent delegation. Track: {subtask_id, agent, status, files_touched}. Update parent progress.

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


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
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
- `8`: IF(STORE-GET($SUBTASKS) has `pending` items) →
  Analyze subtask dependencies for parallel/sequential execution
  STORE-AS($INDEPENDENT_SUBTASKS = subtasks with no blockedBy)
  STORE-AS($DEPENDENT_SUBTASKS = subtasks with blockedBy)
  IF($HAS_AUTO_APPROVE) →
  Auto-execute: parallel for independent, sequential for dependent
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Has N subtasks. Execute parallel where possible?"
→ END-IF
→ END-IF
- `9`: STORE-AS($IS_SIMPLE = task.content >=50 chars AND has specific file/class/function AND no "example/like/similar" AND single clear interpretation)
- `10`: IF(STORE-GET($IS_SIMPLE)) → SKIP to step 4 (Context gathering)
- `11`: STORE-AS($NEEDS_RESEARCH = ANY: content <50 chars, contains "example/like/similar/e.g./такий як/як у", no paths AND no class names, unknown lib/pattern, contradicts code, ambiguous, "how to" without specifics)
- `12`: IF(STORE-GET($NEEDS_RESEARCH)) →
  3.1: mcp__context7__resolve-library-id('{libraryName: "{detected_lib}"}') → IF library mentioned
  3.2: mcp__context7__query-docs('{query: "{task question}"}') → get docs
  3.3: IF context7 insufficient → [DELEGATE] @agent-web-research-master: 'Research: {task.title}. Find: implementation patterns, best practices.'
  STORE-AS($RESEARCH_OPTIONS = [{option, source, pros, cons}])
→ END-IF
- `13`: IF(STORE-GET($RESEARCH_OPTIONS) AND $HAS_AUTO_APPROVE) →
  Auto-select BEST approach for delegation
→ END-IF
- `14`: IF(STORE-GET($RESEARCH_OPTIONS) AND NOT $HAS_AUTO_APPROVE) →
  Present: "Found N approaches: 1)... 2)... Which? (or your variant)"
→ END-IF
- `15`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') STORE-AS($MEMORY)
- `16`: mcp__vector-memory__search_memories('{query: "{task.title} {problem keywords} failed error not working broken", limit: 5}') STORE-AS($KNOWN_FAILURES) ← CRITICAL: what already FAILED (search by `failure` keywords, not category)
- `17`: mcp__vector-task__task_list('{query: task.title, limit: 3}') STORE-AS($RELATED)
- `18`: IF(STORE-GET($TASK).parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') STORE-AS($SIBLING_TASKS)
  FOREACH(sibling in STORE-GET($SIBLING_TASKS)) →
  mcp__vector-memory__search_memories('{query: "{sibling.title}", limit: 3}') → ALL memories for this sibling (failures, solutions, insights)
  mcp__vector-memory__search_memories('{query: "{sibling.title} failed error not working", limit: 3}') → specifically `failure`-related memories
  Append results to STORE-AS($SIBLING_MEMORIES)
→ END-FOREACH
  Extract from siblings comments + STORE-GET($SIBLING_MEMORIES): what was tried, what failed, what worked
  STORE-AS($FAILURE_PATTERNS = solutions that were tried and failed (from sibling comments + sibling memories))
→ END-IF
- `19`: IF(STORE-GET($KNOWN_FAILURES) OR STORE-GET($FAILURE_PATTERNS) not empty) →
  STORE-AS($BLOCKED_APPROACHES = STORE-GET($KNOWN_FAILURES) + STORE-GET($FAILURE_PATTERNS))
  If planned delegation uses blocked approach → STOP, research alternative or escalate
  Pass BLOCKED_APPROACHES to ALL agents in their prompts
→ END-IF
- `20`: Bash('brain docs {keywords}') STORE-AS($DOCS)
- `21`: IF(docs found) →
  [DELEGATE] @agent-explore: 'Read docs: {doc.paths}'
→ END-IF
- `22`: Bash('git status --porcelain 2>/dev/null || echo "NO_GIT"') STORE-AS($GIT_STATUS)
- `23`: IF(STORE-GET($GIT_STATUS) has uncommitted changes) →
  IF($HAS_AUTO_APPROVE) →
  WARN: uncommitted changes, proceeding with delegation
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Uncommitted changes. Stash before delegating/Proceed anyway/Abort?"
→ END-IF
→ END-IF
- `24`: Analyze task INTENT → break into atomic agent subtasks
- `25`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Planning delegation: 1) What is the INTENT? 2) Which agents? 3) Parallel or sequential? 4) File scope per agent? 5) What instructions for security/validation?",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `26`: STORE-AS($PLAN = [{agent, subtask, files, parallel: bool, order, is_critical: bool}])
- `27`: Each agent prompt MUST include: task description, file scope, memory hints, security rules, validation requirements
- `28`: IF($HAS_AUTO_APPROVE) →
  execute immediately
→ ELSE →
  show plan, wait "yes"
→ END-IF
- `29`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Delegating to agents...", append_comment: true}')
- `30`: STORE-AS($DELEGATION_STATE = {agent_tasks: [], started_at: timestamp})
- `31`: 6.1 PARALLEL: Independent tasks → multiple [DELEGATE] @agent-{agent}: '{subtask + security + validation instructions}' in ONE message
- `32`: 6.2 SEQUENTIAL: Dependent tasks → one by one, wait for result before next
- `33`: Track each delegation: {agent, status, result, files_touched, errors}
- `34`: IF(agent fails) →
  Retry up to 2 times with same agent
  IF(still fails AND alternative agent exists) →
  Try alternative agent
→ END-IF
  IF(max retries AND is_critical) →
  IF($HAS_AUTO_APPROVE) →
  Abort remaining delegations
  Request rollback from `completed` agents
  mcp__vector-task__task_update('{status: "pending", comment: "Critical agent failed: {error}. Rolled back."}')
  mcp__vector-memory__store_memory('{content: "FAILURE: Task #{id}, agent: {name}, error: {msg}", category: "debugging"}')
  ABORT "Critical agent failed"
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
- `35`: Update task.comment with delegation_state for recovery
- `36`: Collect all agent results
- `37`: Check for conflicts: multiple agents modified same file
- `38`: IF(conflict detected) →
  IF($HAS_AUTO_APPROVE) →
  Merge if possible, prefer later change, WARN
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Conflict in {file}. Show diff/Prefer A/Prefer B?"
→ END-IF
→ END-IF
- `39`: Verify: all expected files modified, no orphaned changes
- `40`: STORE-AS($AGENT_RESULTS = {succeeded: N, failed: M, files: [...], conflicts: [...]})
- `41`: IF(some agents failed) →
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
- `42`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "Done. Agents: {list}. Files: {files}.", append_comment: true}')
- `43`: mcp__vector-memory__store_memory('{content: "Task #{id}: delegation strategy, agents used: {list}, learnings: {summary}", category: "code-solution"}')

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
3. BLOCKED APPROACHES: "KNOWN FAILURES (DO NOT USE): {$BLOCKED_APPROACHES}. If your solution matches - find alternative."
4. MEMORY: "Search memory for: {terms}. Check debugging category for failures. Store learnings after."
5. SECURITY: "No hardcoded secrets. Validate input. Escape output. Parameterized queries."
6. VALIDATION: "Verify syntax. Run linter if configured. Run related tests. Fix before completion."
7. GIT: "Check git status. Stash uncommitted. Rollback on `failure`."
8. DEPS: "If dependencies needed: detect package manager, install, run audit."

</command>