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
<provides>Synchronous vector task execution by Brain. Sync = blocking execution (not background). Agent delegation allowed for research to keep context clean. Critical thinking: validates clarity, adapts examples, researches when needed.</provides>

# Iron Rules
## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN analyze and validate.

## No-hallucination (CRITICAL)
NEVER output results without ACTUALLY calling tools. You CANNOT know task status or content without REAL tool calls. Fake results = CRITICAL VIOLATION.

## No-verbose (CRITICAL)
FORBIDDEN: <meta>, <synthesis>, <plan>, <analysis> tags. No long explanations before action.

## Show-progress (HIGH)
ALWAYS show brief step status and results. User must see what is happening and can interrupt/correct at any moment.

## Fast-path (HIGH)
Simple task (clear intent, specific files, no ambiguity) → skip research, execute directly. Complex/ambiguous → full validation flow.

## Research-triggers (CRITICAL)
Research REQUIRED when ANY: 1) content <50 chars, 2) contains "example/like/similar/e.g./такий як", 3) no file paths AND no class/function names, 4) references unknown library/pattern, 5) contradicts existing code, 6) multiple valid interpretations, 7) task asks "how to" without specifics.

## Research-flow (HIGH)
Research order: 1) context7 for library docs, 2) web-research-master for patterns/practices. -y flag: auto-select best. No -y: present options to user.

## Failure-history-mandatory (CRITICAL)
BEFORE planning: search memory category "debugging" for KNOWN FAILURES related to this task/problem. DO NOT attempt solutions that already failed.
- **why**: Repeating failed solutions wastes time. Memory contains "this does NOT work" knowledge.
- **on_violation**: Search debugging memories FIRST. Block known-failed approaches.

## Sibling-task-check (HIGH)
BEFORE execution: fetch sibling tasks (same parent_id, status=`completed`/`stopped`). Check comments for what was tried and failed.
- **why**: Previous attempts on same problem contain valuable "what not to do" information.

## Escalate-stuck-problems (HIGH)
If task matches pattern that failed 2+ times (from memory/sibling analysis) → DO NOT attempt same approach. Escalate: research alternatives, ask user, or delegate to web-research-master.
- **why**: Definition of insanity: doing same thing expecting different results.

## Sync-meaning (MEDIUM)
Sync = synchronous/blocking execution (vs async/background). Agent delegation IS allowed for research - keeps main context clean.

## Read-before-edit (CRITICAL)
ALWAYS Read file BEFORE Edit/Write.

## Understand-then-execute (CRITICAL)
Understand INTENT behind task, not just literal text. Adapt examples to actual context.

## Auto-approve-autonomy (HIGH)
-y flag = FULL AUTONOMY. Brain makes ALL decisions without asking. Auto: install dependencies, fix linter issues, run tests, rollback on `failure`, select best approach.
- **why**: User explicitly trusts Brain to complete task end-to-end. Interruptions defeat the purpose.

## Interactive-mode (HIGH)
NO -y flag = INTERACTIVE. Ask before: installing dependencies, major architectural decisions, multiple valid approaches, destructive operations (delete, overwrite), breaking changes.
- **why**: User wants control over significant decisions.

## Dependency-detection (HIGH)
Detect missing dependencies: import/require/use statements that fail, unknown classes/modules, task explicitly mentions "add/install/use {package}". Store list for installation.

## Dependency-install (HIGH)
Install dependencies: detect package manager (composer, npm, pip, cargo, go mod, etc.) from project files. -y: auto-install. No -y: ask "Need to install {packages}. Proceed?"
- **why**: Task cannot complete without required dependencies.

## Dependency-audit (MEDIUM)
After install: run audit if available (npm audit, composer audit, pip-audit, cargo audit). Vulnerabilities found: -y = WARN and continue, no -y = ask user.

## Dependency-dev-vs-prod (MEDIUM)
Dev dependencies (test frameworks, linters, dev tools) install to dev. Production dependencies install to main. Detect from usage context.

## Git-safety-check (HIGH)
Before multi-file changes: check git status. Uncommitted changes exist: -y = auto-stash, no -y = ask "Uncommitted changes. Stash/Commit/Abort?"
- **why**: Protect user work from being mixed with task changes.

## Rollback-on-failure (HIGH)
If execution fails mid-way (step N of M failed, N>1): -y = auto-rollback (git checkout changed files), no -y = ask "Rollback changes? Files: {list}"
- **why**: Partial changes are worse than no changes.

## No-git-fallback (MEDIUM)
No git repo: create backup files (.bak) before edit. Rollback = restore from .bak. Clean .bak files on `success`.

## Security-no-secrets (CRITICAL)
NEVER write hardcoded secrets (passwords, API keys, tokens). Use: env variables, config files (gitignored), secret managers. If task asks to hardcode secret: REFUSE, suggest secure alternative.

## Security-input-validation (HIGH)
Code that receives external input (user, API, file): add validation at boundaries. Validate type, format, length, allowed values. Reject/sanitize invalid input.

## Security-output-escaping (HIGH)
Code that outputs to HTML/JS/SQL/shell: escape appropriately. HTML = htmlspecialchars/equivalent, SQL = parameterized queries, shell = escapeshellarg/equivalent.

## Security-parameterized-queries (CRITICAL)
Database queries with variables: ALWAYS parameterized/prepared statements. NEVER string concatenation. No exceptions.

## Post-exec-syntax (CRITICAL)
After ALL edits: verify syntax. Run language-specific check (php -l, node --check, python -m py_compile, rustc --emit=metadata, go build). Syntax error = fix immediately.

## Post-exec-linter (HIGH)
After syntax OK: run linter if configured (eslint, phpcs, pylint, clippy, golint). Errors: -y = auto-fix if possible, no -y = show and ask. Cannot auto-fix = manual fix.

## Post-exec-tests (HIGH)
After linter OK: run related tests. Detect test files: same directory, *Test/*_test suffix, test/ mirror structure. -y = run automatically, no -y = ask "Run tests?"
- **why**: Code without test verification is not done.

## Post-exec-test-failure (HIGH)
Tests fail: analyze `failure`, attempt fix (max 2 attempts). Still fails: -y = mark task `pending` with error comment, no -y = ask user for guidance.

## Partial-failure-tracking (HIGH)
Track execution state: {completed_steps: [], current_step: N, total_steps: M, changed_files: []}. Persist in task comment for recovery.

## Partial-failure-decision (HIGH)
Step fails after previous steps changed files: 1) Attempt fix (max 2), 2) If unfixable AND -y: rollback all + mark `pending`, 3) If unfixable AND no -y: ask "Rollback/Skip/Manual fix?"

## Partial-success-option (MEDIUM)
If 80%+ steps succeeded and remaining are non-critical: -y = complete with warning comment, no -y = ask "Complete partial or rollback?"

## Retry-limit (HIGH)
Edit conflict: max 3 retries. File locked: wait 2s, retry, max 5 attempts. Network error: retry with backoff, max 3. After max: fail step.

## Timeout-limits (MEDIUM)
Long operations: dependency install 120s, test suite 300s, linter 60s. Timeout exceeded: -y = skip with warning, no -y = ask "Wait/Skip/Abort?"

## Session-recovery-detection (HIGH)
Task status=`in_progress`: check task.comment for execution state. Has completed_steps AND recent timestamp (<1h): crashed session. No state OR old timestamp (>1h): stale session.

## Session-recovery-action (HIGH)
Crashed session: -y = continue from last `completed` step, no -y = ask "Continue from step N or restart?" Stale session: reset to `pending`, start fresh.

## Subtasks-before-parent (HIGH)
Parent task with `pending` subtasks: complete subtasks FIRST. Order by: priority > order field > creation date. -y = execute sequentially, no -y = show list and ask.

## Subtasks-parallel-option (MEDIUM)
Independent subtasks (no dependencies): -y = execute in parallel if possible, no -y = ask "Execute N subtasks in parallel?"

## Breaking-change-detection (HIGH)
Detect breaking changes: public method signature change, removed public API, changed return type, renamed exported symbol. Flag for review.

## Breaking-change-action (HIGH)
Breaking change detected: -y = proceed with deprecation notice in comment + update callers if found, no -y = ask "This is breaking change. Proceed/Modify/Abort?"

## Failure-memory (MEDIUM)
On task `failure`: store to memory with category "debugging". Content: task summary, `failure` reason, attempted fixes, final state. Learnings help future similar tasks.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') STORE-AS($TASK)
- `2`: IF(not found) → ABORT
- `3`: IF(status=`completed`) →
  IF($HAS_AUTO_APPROVE) →
  ABORT "Already `completed`. Use different task ID."
→ END-IF
  ask "Re-execute `completed` task?"
→ END-IF
- `4`: IF(status=`in_progress`) →
  Parse task.comment for execution_state JSON
  IF(has completed_steps AND timestamp <1h) →
  STORE-AS($IS_CRASHED_SESSION = true)
  IF($HAS_AUTO_APPROVE) → Continue from last `completed` step
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Crashed session. Continue from step N or restart?"
→ END-IF
→ END-IF
  IF(no state OR timestamp >1h) →
  Stale session detected
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Stale session reset"}')
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
  STORE-AS($PENDING_SUBTASKS = filter SUBTASKS where status=`pending`, order by priority,order,created_at)
  IF($HAS_AUTO_APPROVE) → Execute subtasks sequentially before parent
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Has N `pending` subtasks. Execute them first?"
→ END-IF
→ END-IF
- `9`: STORE-AS($IS_SIMPLE = task.content >=50 chars AND has specific file/class/function AND no "example/like/similar" AND single clear interpretation)
- `10`: IF(STORE-GET($IS_SIMPLE)) → SKIP to step 4 (Explore & Plan)
- `11`: STORE-AS($NEEDS_RESEARCH = ANY: content <50 chars, contains "example/like/similar/e.g./такий як/як у", no paths AND no class names, unknown lib/pattern, contradicts code, ambiguous, "how to" without specifics)
- `12`: IF(STORE-GET($NEEDS_RESEARCH)) →
  3.1: mcp__context7__resolve-library-id('{libraryName: "{detected_lib}"}') → IF library mentioned
  3.2: mcp__context7__query-docs('{query: "{task question}"}') → get docs
  3.3: IF context7 insufficient → [DELEGATE] @agent-web-research-master: 'Research: {task.title}. Find: implementation patterns, best practices, concrete examples.'
  STORE-AS($RESEARCH_OPTIONS = [{option, source, pros, cons}])
→ END-IF
- `13`: IF(STORE-GET($RESEARCH_OPTIONS) AND $HAS_AUTO_APPROVE) →
  Auto-select BEST: fit with existing code > simplicity > best practices
→ END-IF
- `14`: IF(STORE-GET($RESEARCH_OPTIONS) AND NOT $HAS_AUTO_APPROVE) →
  Present: "Found N approaches: 1)... 2)... Which? (or your variant)"
→ END-IF
- `15`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') → past solutions
- `16`: mcp__vector-memory__search_memories('{query: "{task.title} {problem keywords} failed error not working broken", limit: 5}') STORE-AS($KNOWN_FAILURES) ← CRITICAL: what already FAILED (search by `failure` keywords, not category)
- `17`: mcp__vector-task__task_list('{query: task.title, limit: 3}') → related tasks
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
  BLOCKED APPROACHES: STORE-GET($KNOWN_FAILURES) + STORE-GET($FAILURE_PATTERNS)
  If planned solution matches blocked approach → STOP, research alternative or escalate
→ END-IF
- `20`: Bash('brain docs {keywords}') → project docs
- `21`: IF(docs found) → Read('{doc.path}')
- `22`: Glob(Find relevant files)
- `23`: Grep(Search existing patterns)
- `24`: Read(Read target files)
- `25`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Planning: 1) INTENT (not literal text)? 2) Fit with existing code? 3) Minimal change? 4) Follow existing patterns?",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `26`: STORE-AS($PLAN = [{step, file, action, changes, rationale}])
- `27`: IF($HAS_AUTO_APPROVE) →
  execute immediately
→ ELSE →
  show plan, wait "yes"
→ END-IF
- `28`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Started"}')
- `29`: IF(PLAN requires new dependencies) →
  STORE-AS($DEPS_NEEDED = [{package, version?, dev?}])
  Detect package manager from project (composer.json, package.json, requirements.txt, Cargo.toml, go.mod, etc.)
  IF($HAS_AUTO_APPROVE) →
  Auto-install: run package manager install command
  Run audit if available, WARN on vulnerabilities
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Need to install: {packages}. Proceed?"
→ END-IF
→ END-IF
- `30`: Bash('git status --porcelain 2>/dev/null || echo "NO_GIT"') STORE-AS($GIT_STATUS)
- `31`: IF(STORE-GET($GIT_STATUS) has uncommitted changes) →
  IF($HAS_AUTO_APPROVE) →
  Bash('git stash push -m "brain-task-{id}-backup"')
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Uncommitted changes detected. Stash/Commit WIP/Abort?"
→ END-IF
→ END-IF
- `32`: STORE-AS($CHANGED_FILES = [])
- `33`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress", comment: "Executing..."}')
- `34`: FOREACH(step in STORE-GET($PLAN)) →
  STORE-AS($CURRENT_STEP = {step_index})
  Read('{step.file}')
  Edit('{step.file}', '{old}', '{new}') OR Write('{step.file}', '{content}')
  Append {step.file} to STORE-GET($CHANGED_FILES)
  IF(step fails) →
  Retry up to 2 times with adjusted approach
  IF(still fails) →
  IF($HAS_AUTO_APPROVE AND previous steps changed files) →
  Bash('git checkout -- {changed_files}') OR restore from .bak
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Failed at step N: {error}. Rolled back."}')
  mcp__vector-memory__store_memory('{content: "FAILURE: Task #{id}, step {N}, error: {msg}, attempted: {fixes}", category: "debugging"}')
  ABORT "Step failed, rolled back"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Step N failed: {error}. Retry/Skip/Rollback/Abort?"
→ END-IF
→ END-IF
→ END-IF
  Update task.comment with execution_state JSON for recovery
→ END-FOREACH
- `35`: 7.1 SYNTAX CHECK: Run language-specific syntax validator on STORE-GET($CHANGED_FILES)
- `36`: IF(syntax errors) →
  Attempt auto-fix (max 2 tries)
  IF(still errors) →
  IF($HAS_AUTO_APPROVE) → Rollback + mark `pending`
  IF(NOT $HAS_AUTO_APPROVE) → Show errors, ask for guidance
→ END-IF
→ END-IF
- `37`: 7.2 LINTER: Run project linter if configured
- `38`: IF(linter errors) →
  IF($HAS_AUTO_APPROVE) → Auto-fix if possible (--fix flag)
  IF(NOT $HAS_AUTO_APPROVE) →
  Show issues, ask "Auto-fix/Manual/Ignore?"
→ END-IF
  IF(cannot auto-fix critical errors) → Fix manually or rollback
→ END-IF
- `39`: 7.3 TESTS: Detect related test files for STORE-GET($CHANGED_FILES)
- `40`: STORE-AS($RELATED_TESTS = test files in same dir, *Test suffix, test/ mirror)
- `41`: IF(STORE-GET($RELATED_TESTS) exist) →
  IF($HAS_AUTO_APPROVE) → Run tests automatically
  IF(NOT $HAS_AUTO_APPROVE) → ask "Run related tests? Files: {list}"
  IF(tests fail) →
  Analyze `failure`, attempt fix (max 2 tries)
  IF(still fails) →
  IF($HAS_AUTO_APPROVE) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending", comment: "Tests failing: {failures}"}')
  ABORT "Tests fail, task marked pending"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) → ask "Tests fail. Fix/Skip/Rollback?"
→ END-IF
→ END-IF
→ END-IF
- `42`: IF(STORE-GET($GIT_STATUS) had stash) →
  Bash('git stash pop') (restore user changes)
→ END-IF
- `43`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "Done. Files: {changed_files}. Tests: {pass/skip/none}."}')
- `44`: mcp__vector-memory__store_memory('{content: "Task #{id}: {approach}, files: {list}, patterns used, learnings", category: "code-solution"}')

# Tdd mode
- `1`: IF(task.comment contains "TDD MODE" AND status=`tested`) →
  Execute implementation based on task.content
→ END-IF
- `2`: Implement feature following existing code patterns
- `3`: Run tests: detect test framework from project (jest, pytest, phpunit, pest, cargo test, go test, etc.)
- `4`: IF(all tests pass) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed", comment: "TDD: All tests PASSED"}')
  mcp__vector-memory__store_memory('{content: "TDD `success`: {feature}, implementation approach: {summary}", category: "code-solution"}')
→ END-IF
- `5`: IF(tests fail) →
  Analyze `failure`: assertion error vs exception vs timeout
  Implement fix based on test expectation
  Re-run tests (max 5 iterations)
  IF(still failing after 5 iterations) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "TDD stuck: {failing_tests}. Need guidance."}')
  IF($HAS_AUTO_APPROVE) →
  ABORT "TDD: Cannot pass tests after 5 iterations"
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Cannot pass tests. Show failures for manual review?"
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
  Proceed with best-effort based on existing codebase patterns
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  Ask user for clarification with specific questions
→ END-IF
→ END-IF
- `5`: IF(multiple research options, user chose "other") →
  Ask for details, incorporate into plan
→ END-IF
- `6`: IF(file not found for edit) →
  IF($HAS_AUTO_APPROVE AND file should exist) →
  ABORT "Expected file not found: {path}"
→ END-IF
  IF($HAS_AUTO_APPROVE AND new file needed) → Create file with Write
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "File not found. Create/Specify path/Abort?"
→ END-IF
→ END-IF
- `7`: IF(edit conflict (old_string not found)) →
  Re-read file to get current content
  Adjust old_string to match current state
  Retry edit (max 3 attempts)
  IF(3 failures) →
  IF($HAS_AUTO_APPROVE) → Use Write to replace entire file if safe
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Cannot edit. Show diff for manual resolution?"
→ END-IF
→ END-IF
→ END-IF
- `8`: IF(user rejects plan) →
  Accept modifications, rebuild plan, re-present
→ END-IF
- `9`: IF(dependency install fails) →
  Check: network, permissions, version conflicts
  IF($HAS_AUTO_APPROVE) →
  mcp__vector-task__task_update('{status: "pending", comment: "Dependency install failed: {error}"}') + abort
→ END-IF
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Install failed: {error}. Retry/Skip dependency/Abort?"
→ END-IF
→ END-IF
- `10`: IF(syntax check fails after edit) →
  Parse error message, identify line/column
  Attempt fix (missing semicolon, bracket, import, etc.)
  Re-check (max 2 attempts)
  IF(still fails) → Rollback file, report syntax error
→ END-IF
- `11`: IF(linter finds critical issues) →
  IF(auto-fixable) → Run linter --fix
  IF(not auto-fixable) →
  IF($HAS_AUTO_APPROVE) → Add TODO comment, proceed with warning
  IF(NOT $HAS_AUTO_APPROVE) → Show issues, ask for action
→ END-IF
→ END-IF
- `12`: IF(timeout on long operation) →
  IF($HAS_AUTO_APPROVE) → Skip with warning, continue
  IF(NOT $HAS_AUTO_APPROVE) →
  ask "Operation timed out. Wait longer/Skip/Abort?"
→ END-IF
→ END-IF

</command>