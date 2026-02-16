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
<provides>Validate completed vector task. 4 parallel agents: Completion, Code Quality, Testing, Security & Performance. Creates fix-tasks for functional issues. Cosmetic fixed inline by agents.</provides>

# Iron Rules
## Task-get-first (CRITICAL)
FIRST TOOL CALL = mcp__vector-task__task_get. No text before. Load task, THEN analyze what to validate.

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

## No-interpretation (CRITICAL)
NEVER interpret task content to decide whether to validate. Task ID given = validate it. JUST EXECUTE.

## Task-scope-only (CRITICAL)
Validate ONLY what task.content describes. Do NOT expand scope. Task says "add X" = check X exists and works. Task says "fix Y" = check Y is fixed. NOTHING MORE.

## Task-complete (CRITICAL)
ALL task requirements MUST be done. Parse task.content → list requirements → verify each. Missing = fix-task.

## No-garbage (CRITICAL)
Detect garbage in task scope: unused imports, dead code, debug statements, commented-out code. Garbage = fix-task.

## Cosmetic-inline (CRITICAL)
Cosmetic issues = AGENTS fix inline during validation. NO task created. Cosmetic: whitespace, typos, formatting, comments, docblocks, naming (non-breaking), import sorting.

## Functional-to-task (CRITICAL)
Functional issues = fix-task. Functional: logic bugs, security vulnerabilities, architecture violations, missing tests, broken functionality.

## Fix-task-blocks-validated (CRITICAL)
Fix-task created → status MUST be "pending", NEVER "validated". "validated" = ZERO fix-tasks. NO EXCEPTIONS.
- **why**: MCP auto-propagation: when child task starts (status→`in_progress`), parent auto-reverts to `pending`. Setting "validated" with `pending` children is POINTLESS - system will reset it. Any subtask creation = task NOT done = "pending". Period.
- **on_violation**: ABORT validation. Set status="pending" BEFORE task_create. Never set "validated" if ANY fix-task exists or will be created.

## Parent-readonly (CRITICAL)
$PARENT is READ-ONLY. NEVER task_update on parent. Validator scope = $VECTOR_TASK_ID ONLY.

## Test-coverage (HIGH)
New code MUST have test coverage. Critical paths = 100%. Other code >= 80%. No coverage = fix-task.

## No-breaking-changes (HIGH)
Public API/interface changes = verify backward compatibility OR document breaking change in task comment.

## Slow-test-detection (HIGH)
Slow tests = fix-task. Thresholds: unit >500ms, integration >2s, any >5s = CRITICAL. Causes: missing mocks, real I/O, unoptimized queries.

## Flaky-test-detection (HIGH)
Flaky tests (pass/fail inconsistently) = fix-task. Run test 2-3 times if suspect. Causes: shared state, time-dependent logic, race conditions, external dependencies without mocks.
- **why**: Flaky tests erode trust in test suite and waste CI resources.

## Failure-history-mandatory (CRITICAL)
BEFORE validation: search memory category "debugging" for KNOWN FAILURES related to this task/problem. Pass failures to agents. Agents MUST NOT suggest solutions that already failed.
- **why**: Repeating failed solutions wastes time. Memory contains "this does NOT work" knowledge.
- **on_violation**: Search debugging memories. Include KNOWN_FAILURES in agent prompts.

## Sibling-task-check (HIGH)
BEFORE validation: fetch sibling tasks (same parent_id, status=`completed`/`stopped`). Analyze their comments for what was tried and failed. Pass context to agents.
- **why**: Previous attempts on same problem contain valuable "what not to do" information.
- **on_violation**: task_list with parent_id, extract `failure` patterns from comments.

## No-repeat-failures (CRITICAL)
BEFORE creating fix-task: check if proposed solution matches known `failure`. If memory says "X does NOT work for Y" - DO NOT create task suggesting X. Escalate or research alternative.
- **why**: Creating fix-task with known-failed solution = guaranteed `failure` + wasted effort.
- **on_violation**: Search memory for proposed fix. Match found in debugging = BLOCK task creation, suggest alternative or escalate.

## Security-injection (CRITICAL)
Injection vulnerabilities = fix-task. Check: SQL/NoSQL injection (parameterized queries?), command injection (shell escaping?), template injection, LDAP injection, XPath injection. ANY user input in query/command = suspect.
- **why**: Injection = #1 OWASP. Exploitable = full system compromise.

## Security-xss (CRITICAL)
XSS vulnerabilities = fix-task. Check: output escaping in HTML/JS context, innerHTML usage, dangerouslySetInnerHTML, template literals with user data, URL parameters reflected in page.
- **why**: XSS enables session hijacking, defacement, malware distribution.

## Security-secrets (CRITICAL)
Hardcoded secrets = fix-task. Grep for: password, secret, api_key, token, credential, private_key, AWS_, STRIPE_, DATABASE_URL. Check: .env files not in .gitignore, secrets in logs/comments.
- **why**: Leaked credentials = immediate breach. No exceptions.

## Security-auth (HIGH)
Auth/authz issues = fix-task. Check: missing authentication on endpoints, broken access control (IDOR), privilege escalation paths, session management (secure cookies, expiration).
- **why**: Broken auth = unauthorized access to data/functionality.

## Security-sensitive-data (HIGH)
Sensitive data exposure = fix-task. Check: PII in logs, sensitive data in error messages, missing encryption for data at rest/transit, excessive data in API responses.
- **why**: Data leaks = compliance violations, reputation damage.

## Performance-n-plus-one (HIGH)
N+1 query pattern = fix-task. Detect: loop with DB/API call inside, lazy loading in iteration, missing eager loading/batching. Check query logs or ORM debug output.
- **why**: N+1 destroys performance at scale. 100 items = 101 queries.

## Performance-complexity (MEDIUM)
Algorithmic complexity issues = fix-task. Nested loops on unbounded data, recursive calls without memoization, O(n²) or worse on large datasets. Check: loops inside loops, repeated searches.
- **why**: Bad algorithms fail silently until data grows.

## Performance-memory (MEDIUM)
Memory issues = fix-task. Loading entire dataset into memory, missing pagination, unbounded caches, large object graphs, missing cleanup/disposal.
- **why**: Memory leaks cause OOM crashes in production.

## Type-safety (HIGH)
Type safety violations = fix-task. Missing type annotations on public API, any/unknown overuse, nullable without null checks, implicit type coercion in comparisons, missing runtime validation at boundaries.
- **why**: Type errors are runtime bombs. Static typing catches bugs early.

## Dependency-audit (HIGH)
Dependency vulnerabilities = fix-task. Run package audit tool (npm audit, composer audit, pip-audit, cargo audit, etc.). Known CVEs in dependencies = CRITICAL.
- **why**: Supply chain attacks via vulnerable dependencies are common.

## Dependency-license (MEDIUM)
License compatibility issues = fix-task. New dependencies must have compatible licenses. GPL in proprietary project = problem. Check: SPDX identifiers, license files.
- **why**: License violations = legal liability.

## Test-quality-assertions (HIGH)
Tests without meaningful assertions = fix-task. Empty tests, tests that only check "no exception thrown", mocked everything including SUT. Test MUST verify behavior, not just execute code.
- **why**: High coverage with weak assertions = false confidence.

## Test-quality-edge-cases (HIGH)
Missing edge case tests = fix-task. Check: null/empty inputs, boundary values, error paths, concurrent access, timeout scenarios. Happy path only = incomplete.
- **why**: Bugs hide in edge cases. Production hits all paths.

## Issue-deduplication (HIGH)
Before creating fix-task: deduplicate issues. Same file + same issue type from different agents = ONE fix-task. Merge descriptions. Avoid duplicate work.
- **why**: Multiple agents may find same issue. Duplicate tasks waste effort.
- **on_violation**: Compare issues by file path and issue category before task_create.

## Agent-partial-failure (HIGH)
If agent crashes/times out: retry ONCE. If still fails: continue with remaining agents, mark agent `failure` in report. 2 of 3 agents = still validate, but note incomplete coverage.
- **why**: One agent `failure` should not block entire validation. Partial results > no results.
- **on_violation**: Log failed agent, include warning in final report, suggest manual review of uncovered area.

## Cosmetic-atomic (MEDIUM)
Cosmetic fixes by agents MUST be atomic with validation. If validation creates fix-task (functional issues found), cosmetic changes STILL committed. Cosmetic improvements are always safe to keep.
- **why**: Cosmetic fixes are non-breaking. Discarding them wastes work.

## Light-validation-tag (MEDIUM)
Task with "light validation" tag = SKIP heavy checks (quality gates, full test suite, code quality agents). RUN only: syntax check, file exists, basic format validation.
- **why**: Trivial tasks (docs, typos, comments, config values, formatting) do not need full validation. Explicit tag = conscious decision by task creator.


# Light validation examples
Recognize tags that signal trivial/light validation. Match by INTENT, not exact string.
- light-validation, light, trivial, minor, docs-only, documentation, readme, typo, cosmetic, formatting, config-only, skip-tests, no-validation

# Light validation scope
Light validation appropriate for:
- Documentation changes (README, CHANGELOG, comments, docblocks)
- Typo fixes in text/UI/messages
- Config value changes (not logic)
- Code formatting, import sorting
- Removing dead/unused code
- Adding/updating .gitignore, .editorconfig

# Light validation not for
NEVER light validation for:
- Any logic changes (even "simple" ones)
- API/interface changes
- Database migrations
- Security-related code
- New features or bug fixes

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
  mcp__vector-task__task_get('{task_id: parent_id}') STORE-AS($PARENT) (READ-ONLY context, NEVER modify)
→ END-IF
- `6`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') STORE-AS($SUBTASKS)
- `7`: mcp__vector-memory__search_memories('{query: task.title, limit: 5, category: "code-solution"}') STORE-AS($MEMORY_CONTEXT)
- `8`: mcp__vector-memory__search_memories('{query: "{task.title} {problem keywords} failed error not working broken", limit: 5}') STORE-AS($KNOWN_FAILURES) ← CRITICAL: what already FAILED (search by `failure` keywords, not category)
- `9`: mcp__vector-task__task_list('{query: task.title, limit: 5}') STORE-AS($RELATED_TASKS)
- `10`: IF(STORE-GET($TASK).parent_id) →
  mcp__vector-task__task_list('{parent_id: $TASK.parent_id, limit: 20}') STORE-AS($SIBLING_TASKS) ← previous attempts on same problem
  FOREACH(sibling in STORE-GET($SIBLING_TASKS)) →
  mcp__vector-memory__search_memories('{query: "{sibling.title}", limit: 3}') → ALL memories for this sibling (failures, solutions, insights)
  mcp__vector-memory__search_memories('{query: "{sibling.title} failed error not working", limit: 3}') → specifically `failure`-related memories
  Append results to STORE-AS($SIBLING_MEMORIES)
→ END-FOREACH
→ END-IF
- `11`: Extract from STORE-GET($SIBLING_TASKS) comments + STORE-GET($SIBLING_MEMORIES): what was tried, what failed, what worked
- `12`: STORE-AS($FAILURE_PATTERNS = solutions that were tried and failed (from sibling comments + sibling memories + debugging memories))
- `13`: Bash('brain docs {keywords from task}') STORE-AS($DOCS_INDEX)
- `14`: IF($HAS_AUTO_APPROVE) →
  SKIP(approval)
→ ELSE →
  show task info, wait "yes"
→ END-IF
- `15`: mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress"}')
- `16`: STORE-AS($IS_LIGHT_VALIDATION = task.tags matches light-validation intent (light, trivial, docs-only, minor, cosmetic, etc.))
- `17`: IF(STORE-GET($IS_LIGHT_VALIDATION)) →
  LIGHT VALIDATION MODE: skip quality gates and agent validation
  Check only: files exist, valid syntax/format, no obvious errors
  IF(basic checks pass) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated", comment: "Light validation passed (trivial task)"}')
→ ELSE →
  mcp__vector-task__task_create('{title: "Light validation fixes: #ID", content: basic_issues, parent_id: $VECTOR_TASK_ID, tags: ["validation-fix"]}')
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending"}')
→ END-IF
  OUTPUT(task, light validation result, status)
  SKIP(full validation)
→ END-IF
- `18`: Prepare agent context: KNOWN_FAILURES=STORE-GET($KNOWN_FAILURES), FAILURE_PATTERNS=STORE-GET($FAILURE_PATTERNS)
- `19`: [PARALLEL] → ([DELEGATE] @agent-explore: 'COMPLETION CHECK: Parse task.content → list requirements → verify each done. Check ONLY task files. Detect garbage (unused imports, dead code, debug statements, commented code). Fix cosmetic inline. KNOWN FAILURES (DO NOT SUGGEST THESE): {$KNOWN_FAILURES}. Return JSON: {missing_requirements: [], garbage: [], cosmetic_fixed: []}' + [DELEGATE] @agent-explore: 'CODE QUALITY: Task scope only. Check: logic errors, architecture violations, breaking changes, type safety (missing types, nullable without checks), algorithmic complexity (nested loops, O(n²)). Run quality gates. Fix cosmetic inline. KNOWN FAILURES (DO NOT SUGGEST THESE): {$KNOWN_FAILURES}. PREVIOUS FAILED ATTEMPTS: {$FAILURE_PATTERNS}. Return JSON: {logic_issues: [], architecture_issues: [], type_issues: [], complexity_issues: []}' + [DELEGATE] @agent-explore: 'TESTING: Task scope only. Check: tests exist (coverage >=80%, critical=100%), tests pass, meaningful assertions (not just "no exception"), edge cases covered (null, empty, boundary), slow tests (unit >500ms, integration >2s), flaky tests (run 2x if suspect). KNOWN FAILURES (DO NOT SUGGEST THESE): {$KNOWN_FAILURES}. If test approach in KNOWN_FAILURES - find ALTERNATIVE. Return JSON: {missing_tests: [], failing_tests: [], weak_assertions: [], missing_edge_cases: [], slow_tests: [], flaky_tests: []}' + [DELEGATE] @agent-explore: 'SECURITY & PERFORMANCE: Task scope only. Security: injection (SQL, command, template), XSS (output escaping), hardcoded secrets (grep: password, api_key, token, secret), auth/authz gaps, sensitive data in logs. Performance: N+1 queries (loop+DB call), memory issues (unbounded loading), missing pagination. Dependency audit if new deps added. KNOWN FAILURES: {$KNOWN_FAILURES}. Return JSON: {injection: [], xss: [], secrets: [], auth_issues: [], data_exposure: [], n_plus_one: [], memory_issues: [], dependency_vulnerabilities: []}') → END-PARALLEL
- `20`: MERGE RESULTS: Collect all agent JSON outputs. DEDUPLICATE: same file + same issue type = merge into one. CLASSIFY severity:
- `21`:   CRITICAL: security issues (injection, XSS, secrets, auth), data loss risk, crashes
- `22`:   MAJOR: logic bugs, missing tests for critical paths, N+1 queries, type safety violations, failing tests
- `23`:   MINOR: missing edge case tests, complexity warnings, weak assertions, slow tests
- `24`: FILTER: Remove false positives (issue outside task scope). Store final list STORE-AS($ISSUES)
- `25`: IF(STORE-GET($ISSUES) not empty) →
  For EACH proposed fix in issues:
  mcp__vector-memory__search_memories('{query: "{proposed_fix_description} failed not working broken error", limit: 3}') → check if this fix already failed
  IF(memory says this approach FAILED before) →
  BLOCK this fix from task creation
  Search for ALTERNATIVE approach: mcp__vector-memory__search_memories('{query: "{problem} alternative solution", limit: 5, category: "code-solution"}')
  IF(no alternative found) →
  ESCALATE: "Problem {X} has no known working solution. Previous attempts failed: {list}. Needs research or human decision."
  Add to task comment instead of creating fix-task
→ END-IF
→ END-IF
→ END-IF
- `26`: STORE-AS($FILTERED_ISSUES = issues with known-failed fixes removed, alternatives added where found)
- `27`: IF(STORE-GET($FILTERED_ISSUES)=0 AND no fix-task needed) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "validated"}')
→ ELSE →
  mcp__vector-task__task_create('{title: "Validation fixes: #ID", content: filtered_issues_list, parent_id: $VECTOR_TASK_ID, tags: ["validation-fix"]}')
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "pending"}') ← IRON LAW: always "pending" when fix-task created. MCP will reset anyway.
→ END-IF
- `28`: OUTPUT(task, Critical/Major/Minor counts, cosmetic fixed, status, fix-task ID)
- `29`: mcp__vector-memory__store_memory('{content: validation_summary, category: "code-solution"}')

# Error handling
- `1`: IF(task not found) → ABORT "suggest task_list"
- `2`: IF(task status invalid) → ABORT "Complete first"
- `3`: IF(agent fails) →
  RETRY once with same prompt
  IF(still fails) →
  Mark agent as FAILED in report
  Continue with remaining agents (partial validation > no validation)
  Add warning: "{agent_name} validation incomplete - manual review recommended for {coverage_area}"
→ END-IF
→ END-IF
- `4`: IF(agent timeout (>60s)) →
  Treat as `failure`, apply retry logic above
→ END-IF
- `5`: IF(fix-task creation fails) →
  store issues to memory for manual review, abort with error
→ END-IF
- `6`: IF(user rejects validation) →
  accept modifications, re-validate from step 4
→ END-IF
- `7`: IF(quality gate command not found) →
  WARN and skip that gate, note in report
→ END-IF

</command>