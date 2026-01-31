---
name: "do:test-validate"
description: "Comprehensive test validation with parallel agent orchestration"
---

<command>
<meta>
<id>do:test-validate</id>
<description>Comprehensive test validation with parallel agent orchestration</description>
</meta>
<execute>Validates test coverage against documentation requirements, test quality (no bloat, real workflows), test consistency, and completeness. Uses 6 parallel agents for thorough validation. Creates follow-up tasks for missing tests, failing tests, and refactoring needs. For vector tasks: requires status "completed", sets to "in_progress" during validation, returns to "completed" with findings. Idempotent - can be run multiple times safely. Accepts $ARGUMENTS: vector task reference (task N, task:N, #N) or plain description.</execute>
<provides>Text-based test validation with parallel agent orchestration. Accepts text description (example: "test-validate user authentication"). Validates test coverage against documentation requirements, test quality (no bloat, real workflows), test consistency, and completeness. Creates memory entries for gaps. Idempotent. For vector task test validation use /task:test-validate.</provides>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING $RAW_INPUT: Your FIRST output MUST be "=== DO:TEST-VALIDATE ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain list:masters), code generation, file analysis.
- **why**: Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.
- **on_violation**: STOP IMMEDIATELY. Delete any tool calls. Output "=== DO:TEST-VALIDATE ACTIVATED ===" and restart from Phase 0.

## Test-validation-only (CRITICAL)
TEST VALIDATION command validates EXISTING tests. NEVER write tests directly. Only validate and CREATE MEMORY ENTRIES for missing/broken tests.
- **why**: Validation is read-only audit. Test writing belongs to do:async.
- **on_violation**: Abort any test writing. Create memory entry instead.

## Text-description-required (CRITICAL)
$RAW_INPUT MUST be a text description of work to test-validate. Optional flags (-y, --yes) may be appended. Extract flags first, then verify remaining text is NOT a task ID pattern (15, #15, task 15). Examples: "test-validate auth -y", "check user module --yes".
- **why**: This command is exclusively for text-based validation. Vector task validation belongs to /task:test-validate.
- **on_violation**: STOP. Report: "For vector task validation, use /task:test-validate {id}. This command accepts text descriptions only."

## Real-workflow-tests-only (CRITICAL)
Tests MUST cover REAL workflows end-to-end. Reject bloated tests that test implementation details instead of behavior. Quality over quantity.
- **why**: Bloated tests are maintenance burden, break on refactoring, provide false confidence.
- **on_violation**: Flag bloated tests for refactoring. Create memory entry to simplify.

## Documentation-requirements-coverage (CRITICAL)
EVERY requirement in .docs/ MUST have corresponding test coverage. Missing coverage = immediate memory entry creation.
- **why**: Documentation defines expected behavior. Untested requirements are unverified.
- **on_violation**: Create memory entry for each uncovered requirement.

## Parallel-agent-orchestration (HIGH)
Validation phases MUST use parallel agent orchestration (5-6 agents simultaneously) for efficiency. Each agent validates one aspect.
- **why**: Parallel validation reduces time and maximizes coverage.
- **on_violation**: Restructure validation into parallel Task() calls.

## Idempotent-validation (HIGH)
Validation is IDEMPOTENT. Running multiple times produces same result (no duplicate entries, no repeated fixes).
- **why**: Allows safe re-runs without side effects.
- **on_violation**: Check existing entries before creating. Skip duplicates.

## Vector-memory-mandatory (HIGH)
ALL test validation results MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.
- **why**: Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps
- **on_violation**: Include explicit vector memory instructions in agent Task() delegation.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($VALIDATION_TARGET = {target to validate extracted from $RAW_INPUT})

# Phase0 context setup
GOAL(Detect task ID patterns and reject, set up test validation context from $RAW_INPUT)
- `1`: OUTPUT(=== DO:TEST-VALIDATE ACTIVATED ===  === PHASE 0: CONTEXT SETUP === Processing input...)
- `2`: STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags (-y, --yes) removed, trimmed})
- `3`: Parse $CLEAN_ARGS for task ID patterns: "N", "#N", "task N", "task:N", "task-N"
- `4`: IF($CLEAN_ARGS matches task ID pattern) →
  OUTPUT(=== DO:TEST-VALIDATE BLOCKED === Detected task ID pattern in arguments: {$RAW_INPUT} This command is for TEXT-BASED test validation only.  Use /task:test-validate {task_id} for vector task test validation.)
  ABORT command
→ END-IF
- `5`: STORE-AS($TASK_DESCRIPTION = $CLEAN_ARGS)
- `6`: OUTPUT(Test validation target: {$TASK_DESCRIPTION} Mode: Text-based (no vector task) {IF $HAS_AUTO_APPROVE: "Auto-approve: enabled (-y flag)"})

# Phase1 validation preview
GOAL(Discover available agents and present test validation scope for approval)
- `1`: OUTPUT( === PHASE 1: TEST VALIDATION PREVIEW ===)
- `2`: Bash(brain list:masters) → [Get available agents with capabilities] → END-Bash
- `3`: STORE-AS($AVAILABLE_AGENTS = {agent_id: description mapping})
- `4`: Bash(brain docs {keywords from $TASK_DESCRIPTION}) → [Get documentation INDEX preview] → END-Bash
- `5`: STORE-AS($DOCS_PREVIEW = Documentation files available)
- `6`: OUTPUT(Test validation: {$TASK_DESCRIPTION} Available agents: {$AVAILABLE_AGENTS.count} Documentation files: {$DOCS_PREVIEW.count}  Test validation will delegate to agents: 1. VectorMaster - deep memory research for test context 2. DocumentationMaster - testable requirements extraction 3. Selected agents - test discovery + parallel validation (6 aspects)  ⚠️  APPROVAL REQUIRED ✅ approved/yes - start test validation | ❌ no/modifications)
- `7`: IF($HAS_AUTO_APPROVE === true) →
  AUTO-APPROVED (unattended mode)
  OUTPUT(Auto-approved via -y flag)
→ END-IF
- `8`: IF($HAS_AUTO_APPROVE === false) →
  WAIT for user approval
  VERIFY-SUCCESS(User approved)
  IF(rejected) → Accept modifications → Re-present → WAIT
→ END-IF

# Phase2 context gathering
GOAL(Delegate deep test context research to VectorMaster agent)
- `1`: OUTPUT( === PHASE 2: DEEP TEST CONTEXT === Delegating to VectorMaster for deep memory research...)
- `2`: SELECT vector-master from $AVAILABLE_AGENTS
- `3`: STORE-AS($CONTEXT_AGENT = {vector-master agent_id})
- `4`: [DELEGATE] @agent-{$CONTEXT_AGENT}: 'DEEP MEMORY RESEARCH for test validation of "{$TASK_DESCRIPTION}": 1) Multi-probe search: past test implementations, test patterns, testing best practices, test failures, coverage gaps 2) Search across categories: code-solution, learning, bug-fix 3) Extract test-specific insights: what worked, what failed, patterns used 4) Return: {test_history: [...], test_patterns: [...], past_failures: [...], quality_standards: [...], key_insights: [...]}. Store consolidated test context.'
- `5`: STORE-AS($TEST_MEMORY_CONTEXT = {VectorMaster agent results})
- `6`: mcp__vector-memory__search_memories('{query: "test $TASK_DESCRIPTION", limit: 10}')
- `7`: STORE-AS($RELATED_TEST_MEMORIES = Related test memories)
- `8`: OUTPUT(Context gathered via {$CONTEXT_AGENT}: - Test insights: {$TEST_MEMORY_CONTEXT.key_insights.count} - Related test memories: {$RELATED_TEST_MEMORIES.count})

# Phase3 documentation extraction
GOAL(Extract ALL testable requirements from .docs/ via DocumentationMaster)
- `1`: OUTPUT( === PHASE 3: DOCUMENTATION REQUIREMENTS ===)
- `2`: Bash(brain docs {keywords from $TASK_DESCRIPTION}) → [Get documentation INDEX] → END-Bash
- `3`: STORE-AS($DOCS_INDEX = Documentation file paths)
- `4`: IF($DOCS_INDEX not empty) →
  [DELEGATE] @agent-documentation-master: 'Extract ALL TESTABLE requirements from documentation files: {$DOCS_INDEX paths}. For each requirement identify: [{requirement_id, description, testable_scenarios: [...], acceptance_criteria, expected_test_type: unit|feature|integration|e2e, priority}]. Focus on BEHAVIOR not implementation. Store to vector memory.'
  STORE-AS($DOCUMENTATION_REQUIREMENTS = {structured testable requirements list})
→ END-IF
- `5`: IF($DOCS_INDEX empty) →
  STORE-AS($DOCUMENTATION_REQUIREMENTS = [])
  OUTPUT(WARNING: No documentation found. Test validation will be limited to existing tests only.)
→ END-IF
- `6`: OUTPUT(Testable requirements extracted: {$DOCUMENTATION_REQUIREMENTS.count} {requirements summary with test types})

# Phase4 test discovery
GOAL(Select best agent from $AVAILABLE_AGENTS and discover all existing tests)
- `1`: OUTPUT( === PHASE 4: TEST DISCOVERY ===)
- `2`: SELECT AGENT for test discovery from {$AVAILABLE_AGENTS} (prefer explore for codebase scanning)
- `3`: STORE-AS($DISCOVERY_AGENT = {selected agent_id based on descriptions})
- `4`: [DELEGATE] @agent-{$DISCOVERY_AGENT}: 'DEEP RESEARCH - TEST DISCOVERY for "{$TASK_DESCRIPTION}": 1) Search vector memory for past test patterns and locations 2) Scan codebase for test directories (tests/, spec/, __tests__) 3) Find ALL related test files: unit, feature, integration, e2e 4) Analyze test structure and coverage 5) Return: [{test_file, test_type, test_classes, test_methods, related_source_files}]. Store findings to vector memory.'
- `5`: STORE-AS($DISCOVERED_TESTS = {list of test files with metadata})
- `6`: OUTPUT(Tests discovered via {$DISCOVERY_AGENT}: {$DISCOVERED_TESTS.count} files {test files summary by type})

# Phase5 parallel validation
GOAL(Select best agents from $AVAILABLE_AGENTS and launch parallel test validation)
- `1`: OUTPUT( === PHASE 5: PARALLEL TEST VALIDATION ===)
- `2`: AGENT SELECTION: Analyze $AVAILABLE_AGENTS descriptions and select BEST agent for each test validation aspect:
- `3`: ASPECT 1 - REQUIREMENTS COVERAGE: Select agent for requirements-to-test mapping (vector-master for memory, explore for codebase) ASPECT 2 - TEST QUALITY: Select agent for code quality analysis (explore for pattern detection) ASPECT 3 - WORKFLOW COVERAGE: Select agent for workflow analysis (explore for flow tracing) ASPECT 4 - TEST CONSISTENCY: Select agent for consistency analysis (explore for pattern matching) ASPECT 5 - TEST ISOLATION: Select agent for isolation analysis (explore for dependency scanning) ASPECT 6 - TEST EXECUTION: Select agent capable of running tests (explore with bash access)
- `4`: STORE-AS($SELECTED_AGENTS = {aspect: agent_id mapping based on $AVAILABLE_AGENTS})
- `5`: OUTPUT(Selected agents for test validation: {$SELECTED_AGENTS mapping}  Launching test validation agents in parallel...)
- `6`: PARALLEL BATCH: Launch selected agents simultaneously with DEEP RESEARCH tasks
- `7`: [DELEGATE] @agent-{$SELECTED_AGENTS.coverage}: 'DEEP RESEARCH - REQUIREMENTS COVERAGE for "{$TASK_DESCRIPTION}": 1) Search vector memory for past requirement-test mappings 2) Compare {$DOCUMENTATION_REQUIREMENTS} against {$DISCOVERED_TESTS} 3) For each requirement verify test exists 4) Return: [{requirement_id, coverage_status: covered|partial|missing, test_file, test_method, gap_description, memory_refs}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.quality}: 'DEEP RESEARCH - TEST QUALITY for "{$TASK_DESCRIPTION}": 1) Search memory for test quality standards 2) Analyze {$DISCOVERED_TESTS} for bloat indicators 3) Check: excessive mocking, implementation testing, redundant assertions, copy-paste 4) Return: [{test_file, test_method, bloat_type, severity, suggestion}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.workflow}: 'DEEP RESEARCH - WORKFLOW COVERAGE for "{$TASK_DESCRIPTION}": 1) Search memory for workflow patterns 2) Verify {$DISCOVERED_TESTS} cover complete user workflows 3) Check: happy path, error paths, edge cases, boundaries 4) Return: [{workflow, coverage_status, missing_scenarios}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.consistency}: 'DEEP RESEARCH - TEST CONSISTENCY for "{$TASK_DESCRIPTION}": 1) Search memory for project test conventions 2) Check {$DISCOVERED_TESTS} for consistency 3) Verify: naming, structure, assertions, fixtures, setup/teardown 4) Return: [{test_file, inconsistency_type, description, suggestion}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.isolation}: 'DEEP RESEARCH - TEST ISOLATION for "{$TASK_DESCRIPTION}": 1) Search memory for isolation issues 2) Verify {$DISCOVERED_TESTS} are properly isolated 3) Check: shared state, order dependency, external calls, cleanup 4) Return: [{test_file, isolation_issue, severity, suggestion}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.execution}: 'DEEP RESEARCH - TEST EXECUTION for "{$TASK_DESCRIPTION}": 1) Search memory for past test failures 2) Run tests related to task 3) Identify flaky tests 4) Return: [{test_file, execution_status: pass|fail|flaky, error_message, execution_time}]. Store findings.'
- `8`: STORE-AS($VALIDATION_BATCH = {results from all agents})
- `9`: OUTPUT(Batch complete: {$SELECTED_AGENTS.count} test validation checks finished)

# Phase6 results aggregation
GOAL(Aggregate all test validation results and categorize issues)
- `1`: OUTPUT( === PHASE 6: RESULTS AGGREGATION ===)
- `2`: Merge results from all validation agents
- `3`: STORE-AS($ALL_TEST_ISSUES = {merged issues from all agents})
- `4`: Categorize issues:
- `5`: STORE-AS($MISSING_COVERAGE = {requirements without tests})
- `6`: STORE-AS($PARTIAL_COVERAGE = {requirements with incomplete tests})
- `7`: STORE-AS($BLOATED_TESTS = {tests flagged for bloat})
- `8`: STORE-AS($MISSING_WORKFLOWS = {workflows without end-to-end coverage})
- `9`: STORE-AS($INCONSISTENT_TESTS = {tests with consistency issues})
- `10`: STORE-AS($ISOLATION_ISSUES = {tests with isolation problems})
- `11`: STORE-AS($FAILING_TESTS = {tests that fail or are flaky})
- `12`: OUTPUT(Test validation results: - Missing coverage: {$MISSING_COVERAGE.count} requirements - Partial coverage: {$PARTIAL_COVERAGE.count} requirements - Bloated tests: {$BLOATED_TESTS.count} tests - Missing workflows: {$MISSING_WORKFLOWS.count} workflows - Inconsistent tests: {$INCONSISTENT_TESTS.count} tests - Isolation issues: {$ISOLATION_ISSUES.count} tests - Failing/flaky tests: {$FAILING_TESTS.count} tests)

# Phase7 memory storage
GOAL(Store test gap findings to vector memory for future reference)
- `1`: OUTPUT( === PHASE 7: MEMORY STORAGE ===)
- `2`: Check existing memory entries to avoid duplicates
- `3`: mcp__vector-memory__search_memories('{query: "test gaps $TASK_DESCRIPTION", limit: 10}')
- `4`: STORE-AS($EXISTING_TEST_MEMORIES = Existing test gap memories)
- `5`: IF($ALL_TEST_ISSUES.count > 0) →
  mcp__vector-memory__store_memory('{content: "Test validation gaps for {$TASK_DESCRIPTION}:\\\\n\\\\n## Missing Coverage ({$MISSING_COVERAGE.count})\\\\n{FOR each req: - {req.description} | Type: {req.expected_test_type} | Scenarios: {req.testable_scenarios}}\\\\n\\\\n## Failing Tests ({$FAILING_TESTS.count})\\\\n{FOR each test: - {test.test_file}:{test.test_method} | Error: {test.error_message}}\\\\n\\\\n## Bloated Tests ({$BLOATED_TESTS.count})\\\\n{FOR each test: - {test.test_file}:{test.test_method} | Bloat: {test.bloat_type} | Suggestion: {test.suggestion}}\\\\n\\\\n## Missing Workflows ({$MISSING_WORKFLOWS.count})\\\\n{FOR each wf: - {wf.workflow} | Missing: {wf.missing_scenarios}}\\\\n\\\\n## Isolation Issues ({$ISOLATION_ISSUES.count})\\\\n{FOR each test: - {test.test_file} | Issue: {test.isolation_issue}}\\\\n\\\\n## Context\\\\n- Memory IDs: {$TEST_MEMORY_CONTEXT.memory_ids}\\\\n- Documentation: {$DOCS_INDEX.paths}", category: "code-solution", tags: ["test-validation", "test-gaps", "do:test-validate"]}')
  STORE-AS($STORED_MEMORY_ID = {memory_id})
  OUTPUT(Stored test gaps to memory #{$STORED_MEMORY_ID})
→ END-IF
- `6`: OUTPUT(Memory entries created: {$ALL_TEST_ISSUES.count > 0 ? 1 : 0})

# Phase8 completion
GOAL(Complete test validation and store summary to memory)
- `1`: OUTPUT( === PHASE 8: TEST VALIDATION COMPLETE ===)
- `2`: STORE-AS($COVERAGE_RATE = {covered_requirements / total_requirements * 100}%)
- `3`: STORE-AS($TEST_HEALTH_SCORE = {100 - (bloat_count + isolation_count + failing_count) / total_tests * 100}%)
- `4`: STORE-AS($VALIDATION_STATUS = IF($MISSING_COVERAGE.count === 0 AND $FAILING_TESTS.count === 0) →
  PASSED
→ ELSE →
  NEEDS_WORK
→ END-IF)
- `5`: mcp__vector-memory__store_memory('{content: "Test validation of {$TASK_DESCRIPTION}\\\\n\\\\nStatus: {$VALIDATION_STATUS}\\\\nCoverage rate: {$COVERAGE_RATE}\\\\nTest health: {$TEST_HEALTH_SCORE}\\\\n\\\\nMissing coverage: {$MISSING_COVERAGE.count}\\\\nFailing tests: {$FAILING_TESTS.count}\\\\nBloated tests: {$BLOATED_TESTS.count}\\\\n\\\\nKey findings: {summary}", category: "code-solution", tags: ["test-validation", "audit", "do:test-validate"]}')
- `6`: OUTPUT( === TEST VALIDATION REPORT === Target: {$TASK_DESCRIPTION} Status: {$VALIDATION_STATUS}  | Metric | Value | |--------|-------| | Requirements coverage | {$COVERAGE_RATE} | | Test health score | {$TEST_HEALTH_SCORE} | | Total tests | {$DISCOVERED_TESTS.count} | | Passing tests | {passing_count} | | Failing/flaky tests | {$FAILING_TESTS.count} |  | Issue Type | Count | |------------|-------| | Missing coverage | {$MISSING_COVERAGE.count} | | Partial coverage | {$PARTIAL_COVERAGE.count} | | Bloated tests | {$BLOATED_TESTS.count} | | Missing workflows | {$MISSING_WORKFLOWS.count} | | Isolation issues | {$ISOLATION_ISSUES.count} |  Test validation stored to vector memory.  Next steps: - Use /do:async to implement missing tests - Or create vector tasks with /task:create for systematic tracking)

# Error handling
Graceful error handling with recovery options
- `1`: IF(user rejects plan) →
  Accept modifications
  Rebuild plan
  Re-submit for approval
→ END-IF
- `2`: IF(task ID pattern detected) →
  Report: "Detected vector task ID. Use /task:validate for vector tasks."
  Abort command
→ END-IF
- `3`: IF(no agents available) →
  Report: "No agents found via brain list:masters"
  Suggest: Run /init-agents first
  Abort command
→ END-IF
- `4`: IF(agent execution fails) →
  Log: "Step/Agent {N} failed: {error}"
  Offer options:
    1. Retry current step
    2. Skip and continue
    3. Abort remaining steps
  WAIT for user decision
→ END-IF
- `5`: IF(documentation scan fails) →
  Log: "brain docs command failed or no documentation found"
  Proceed without documentation context
  Note: "Documentation context unavailable"
→ END-IF
- `6`: IF(memory storage fails) →
  Log: "Failed to store to memory: {error}"
  Report findings in output instead
  Continue with report
→ END-IF

# Error handling test specific
Additional error handling for test validation
- `1`: IF(no tests found) →
  Report: "No tests found for {$TASK_DESCRIPTION}"
  Store to memory: "Write initial tests for {$TASK_DESCRIPTION}"
  Continue with documentation requirements analysis
→ END-IF
- `2`: IF(test execution fails) →
  Log: "Test execution failed: {error}"
  Mark tests as "execution_unknown"
  Continue with static analysis
→ END-IF

# Test quality criteria
Criteria for evaluating test quality (bloat detection)
- `1`: 
BLOAT INDICATORS (flag for refactoring):
Excessive mocking (>3 mocks per test) Testing private methods directly Testing getters/setters without logic Copy-paste test code (>80% similarity) Single assertion tests without context Testing framework internals Hard-coded magic values without explanation Test method >50 lines Setup >30 lines

- `2`: 
QUALITY INDICATORS (good tests):
Tests behavior, not implementation Readable test names (given_when_then) Single responsibility per test Proper use of fixtures/factories Edge cases covered Error paths `tested` Fast execution (<100ms per test) No external dependencies without mocks


# Constraints
Test validation constraints and limits
- `1`: Max 6 parallel validation agents per batch
- `2`: Test execution timeout: 5 minutes total
- `3`: Bloat threshold: >50% bloated = critical warning
- `4`: VERIFY-SUCCESS(text_description_validated = true parallel_agents_used = true documentation_checked = true tests_executed = true results_stored_to_memory = true)

# Example text validation
SCENARIO(Test validate work by description)
- `input`: "test-validate user authentication"
- `flow`: Context setup → Memory research → Docs → Test Discovery → Parallel Validation → Aggregate → Store → Report
- `result`: Test validation report with coverage metrics, issues stored to memory

# Example rerun
SCENARIO(Re-run test validation (idempotent))
- `input`: "test-validate user authentication" (already `validated` before)
- `behavior`: Checks existing memory entries, skips duplicates
- `result`: Same/updated validation report, no duplicate memory entries

# Do test validate vs task test validate
When to use /do:test-validate vs /task:test-validate
- `USE /do:test-validate`: Validate tests by text description ("test-validate user authentication"). Best for: ad-hoc test validation, exploratory validation, no existing vector task.
- `USE /task:test-validate`: Validate tests for specific vector task by ID (15, #15, task 15). Best for: systematic task-based workflow, hierarchical task management, fix task creation as children.

# Response format
=== headers | Parallel: agent batch indicators | Tables: coverage metrics + issue counts | Coverage % | Health score | Memory storage confirmation

</command>