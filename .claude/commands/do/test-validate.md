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
<provides>Text-based test validation with parallel agent orchestration. Accepts text description (example: "test-validate user authentication"). Validates test coverage against documentation requirements, test quality (no bloat, real workflows), test consistency, and completeness. Creates vector tasks for gaps. Idempotent. For vector task test validation use /task:test-validate.</provides>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING $RAW_INPUT: Your FIRST output MUST be "=== DO:TEST-VALIDATE ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain list:masters), code generation, file analysis.
- **why**: Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.
- **on_violation**: STOP IMMEDIATELY. Delete any tool calls. Output "=== DO:TEST-VALIDATE ACTIVATED ===" and restart from Phase 0.

## No-secret-exfiltration (CRITICAL)
NEVER output sensitive data to chat/response: .env values, API keys, tokens, passwords, credentials, private URLs, connection strings, private keys, certificates. When reading config/.env for CONTEXT: extract key NAMES and STRUCTURE only, never raw values. If user asks to show .env or config with secrets: show key names, mask values as "***". If error output contains secrets: redact before displaying.
- **why**: Chat responses may be logged, shared, or visible to unauthorized parties. Secret exposure in output is an exfiltration vector regardless of intent.
- **on_violation**: REDACT immediately. Replace value with "***" or "[REDACTED]". Show key names only.

## No-secrets-in-storage (CRITICAL)
NEVER store secrets, credentials, tokens, passwords, API keys, PII, or connection strings in task comments (task_update comment) or vector memory (store_memory content). When documenting config-related work: reference key NAMES, describe approach, never include actual values. If error log contains secrets: strip sensitive values before storing. Acceptable: "Updated DB_HOST in .env", "Rotated API_KEY for service X". Forbidden: "Set DB_HOST=192.168.1.5", "API_KEY=sk-abc123...".
- **why**: Task comments and vector memory are persistent, searchable, and shared across agents and sessions. Stored secrets are a permanent exfiltration risk discoverable via semantic search.
- **on_violation**: Review content before store_memory/task_update. Strip all literal secret values. Keep only key names and descriptions.

## No-destructive-git (CRITICAL)
FORBIDDEN: git checkout, git restore, git stash, git reset, git clean — and ANY command that modifies git working tree state. These destroy uncommitted work from parallel agents, user WIP, and memory/ SQLite databases (vector memory + tasks). Rollback = Read original content + Write/Edit back. Git is READ-ONLY: status, diff, log, blame only.
- **why**: memory/ folder contains project SQLite databases tracked in git. git checkout/stash/reset reverts these databases, destroying ALL tasks and memories. Parallel agents have uncommitted changes — any working tree modification wipes their work. Unrecoverable data loss.
- **on_violation**: ABORT git command. Use Read to get original content, Write/Edit to restore specific files. Never touch git working tree state.

## No-destructive-git-in-agents (CRITICAL)
When delegating to agents: ALWAYS include in prompt: "FORBIDDEN: git checkout, git restore, git stash, git reset, git clean. Rollback = Read + Write. Git is READ-ONLY."
- **why**: Sub-agents do not inherit parent rules. Without explicit prohibition, agents will use git for rollback and destroy parallel work.
- **on_violation**: Add git prohibition to agent prompt before delegation.

## Memory-folder-sacred (CRITICAL)
memory/ folder contains SQLite databases (vector memory + tasks). SACRED — protect at ALL times. NEVER git checkout/restore/reset/clean memory/ — these DESTROY all project knowledge irreversibly. In PARALLEL CONTEXT: use "git add {specific_files}" (task-scope only) — memory/ excluded implicitly because it is not in task files. In NON-PARALLEL context: "git add -A" is safe and DESIRED — includes memory/ for full state checkpoint preserving knowledge base alongside code.
- **why**: memory/ is the project persistent brain. Destructive git commands on memory/ = total knowledge loss. In parallel mode, concurrent SQLite writes + git add -A = binary merge conflicts and staged half-done sibling work. In sequential mode, committing memory/ preserves full project state for safe revert.
- **on_violation**: NEVER destructive git on memory/. Parallel: git add specific files only (memory/ not in scope). Non-parallel: git add -A (full checkpoint with memory/).

## Task-tags-predefined-only (CRITICAL)
Task tags MUST use ONLY predefined values. FORBIDDEN: inventing new tags, synonyms, variations. Allowed: decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression, feature, bugfix, refactor, research, docs, test, chore, spike, hotfix, backend, frontend, database, api, auth, ui, config, infra, ci-cd, migration, strict:relaxed, strict:standard, strict:strict, strict:paranoid, cognitive:minimal, cognitive:standard, cognitive:deep, cognitive:exhaustive, batch:trivial.
- **why**: Ad-hoc tags cause explosion ("user-auth", "authentication", "auth" = same thing, search finds none). Predefined list = consistent search.
- **on_violation**: Replace with closest predefined match. No match = skip tag, put context in content.

## Memory-tags-predefined-only (CRITICAL)
Memory tags MUST use ONLY predefined values. Allowed: pattern, solution, `failure`, decision, insight, workaround, deprecated, project-wide, module-specific, temporary, reusable.
- **why**: Unknown tags = unsearchable memories. Predefined = discoverable.
- **on_violation**: Replace with closest predefined match.

## Memory-categories-predefined-only (CRITICAL)
Memory category MUST be one of: code-solution, bug-fix, architecture, learning, debugging, performance, security, project-context. FORBIDDEN: "other", "general", "misc", or unlisted.
- **why**: "other" is garbage nobody searches. Every memory needs meaningful category.
- **on_violation**: Choose most relevant from predefined list.

## Mandatory-level-tags (CRITICAL)
EVERY task MUST have exactly ONE strict:* tag AND ONE cognitive:* tag. Allowed strict: strict:relaxed, strict:standard, strict:strict, strict:paranoid. Allowed cognitive: cognitive:minimal, cognitive:standard, cognitive:deep, cognitive:exhaustive. Missing level tags = assign based on task scope analysis.
- **why**: Level tags enable per-task compilation and cognitive load calibration. Without them, system defaults apply blindly regardless of task complexity.
- **on_violation**: Analyze task scope and assign: strict:{level} + cognitive:{level}. Simple rename = strict:relaxed + cognitive:minimal. Production auth = strict:strict + cognitive:deep.

## Safety-escalation-non-overridable (CRITICAL)
After loading task, check file paths in task.content/comment. If files match safety patterns → effective level MUST be >= pattern minimum, regardless of task tags or .env default. Agent tags are suggestions UPWARD only — can raise above safety floor, never lower below it.
- **why**: Safety patterns guarantee minimum protection for critical code areas. Agent cannot "cheat" by under-tagging a task touching auth/ or payments/.
- **on_violation**: Raise effective level to safety floor. Log escalation in task comment.

## Failure-policy-tool-error (CRITICAL)
TOOL ERROR / MCP FAILURE: 1) Retry ONCE with same parameters. 2) Still fails → STOP current step. 3) Store `failure` to memory (category: "debugging", tags: ["failure"]). 4) Update task comment: "BLOCKED: {tool} failed after retry. Error: {msg}", append_comment: true. 5) -y mode: set status "pending" (return to queue for retry), abort current workflow. Interactive: ask user "Tool failed. Retry/Skip/Abort?". NEVER set "stopped" on `failure` — "stopped" = permanently cancelled.
- **why**: Consistent tool `failure` handling across all commands. One retry catches transient issues. Failed task returns to `pending` queue — it is NOT cancelled, just needs another attempt or manual intervention.
- **on_violation**: Follow 5-step sequence. Max 1 retry for same tool call. Always store `failure` to memory. Status → `pending`, NEVER `stopped`.

## Failure-policy-missing-docs (HIGH)
MISSING DOCS: 1) Apply aggressive-docs-search (3+ keyword variations). 2) All variations exhausted → conclude "no docs". 3) Proceed using: task.content (primary spec) + vector memory context + parent task context. 4) Log in task comment: "No documentation found after {N} search attempts. Proceeding with task.content.", append_comment: true. NOT a blocker — absence of docs is information, not `failure`.
- **why**: Missing docs must not block execution. task.content is the minimum viable specification. Blocking on missing docs causes pipeline stalls for tasks that never had docs.
- **on_violation**: Never block on missing docs. Search aggressively, then proceed with available context.

## Failure-policy-ambiguous-spec (HIGH)
AMBIGUOUS SPEC: 1) Identify SPECIFIC ambiguity (not "task is unclear" but "field X: type A or B?"). 2) -y mode: choose conservative/safe interpretation, log decision in task comment: "DECISION: interpreted {X} as {Y} because {reason}", append_comment: true. 3) Interactive: ask ONE targeted question about the SPECIFIC gap. 4) After 1 clarification → proceed. NEVER ask open-ended "what did you mean?" or multiple follow-ups.
- **why**: Ambiguity paralysis wastes more time than conservative interpretation. One precise question is enough — if user wanted detailed spec, they would have written docs.
- **on_violation**: Identify specific gap. One question or auto-decide. Proceed.

## Test-validation-only (CRITICAL)
TEST VALIDATION command validates EXISTING tests. NEVER write tests directly. Only validate and CREATE VECTOR TASKS for missing/broken tests.
- **why**: Validation is read-only audit. Test writing belongs to do:async.
- **on_violation**: Abort any test writing. Create vector task instead.

## Text-description-required (CRITICAL)
$RAW_INPUT MUST be a text description of work to test-validate. Optional flags (-y, --yes) may be appended. Extract flags first, then verify remaining text is NOT a task ID pattern (15, #15, task 15). Examples: "test-validate auth -y", "check user module --yes".
- **why**: This command is exclusively for text-based validation. Vector task validation belongs to /task:test-validate.
- **on_violation**: STOP. Report: "For vector task validation, use /task:test-validate {id}. This command accepts text descriptions only."

## Real-workflow-tests-only (CRITICAL)
Tests MUST cover REAL workflows end-to-end. Reject bloated tests that test implementation details instead of behavior. Quality over quantity.
- **why**: Bloated tests are maintenance burden, break on refactoring, provide false confidence.
- **on_violation**: Flag bloated tests for refactoring. Create memory entry to simplify.

## Documentation-requirements-coverage (CRITICAL)
EVERY requirement in .docs/ MUST have corresponding test coverage. Missing coverage = vector task creation for uncovered requirements.
- **why**: Documentation defines expected behavior. Untested requirements are unverified.
- **on_violation**: Create vector task for uncovered requirements.

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

## Phase-sequence-strict (CRITICAL)
Phases MUST execute in STRICT sequential order: Phase 0 → ... → Phase 8. NO phase may start until previous phase is FULLY COMPLETED. Each phase MUST output its header "=== PHASE N: NAME ===" before any actions.
- **why**: Sequential execution ensures data dependencies are satisfied. Each phase depends on variables stored by previous phases.
- **on_violation**: STOP. Return to last `completed` phase. Execute current phase fully before proceeding.

## No-phase-skip (CRITICAL)
FORBIDDEN: Skipping phases. ALL phases 0-8 MUST execute even if a phase has no issues to report. Empty results are valid; skipped phases are VIOLATION.
- **why**: Phase skipping breaks data flow. Later phases expect variables from earlier phases.
- **on_violation**: ABORT. Return to first skipped phase. Execute ALL phases in sequence.

## Phase-completion-marker (HIGH)
Each phase MUST end with its output block before next phase begins. Phase N output MUST appear before "=== PHASE N+1 ===" header.
- **why**: Output markers confirm phase completion. Missing output = incomplete phase.
- **on_violation**: Complete current phase output before starting next phase.

## No-parallel-phases (CRITICAL)
FORBIDDEN: Executing multiple phases simultaneously. Only Phase 4/5 allows parallel AGENTS within the phase. Phase-level parallelism is NEVER allowed.
- **why**: Phase parallelism causes race conditions on shared variables.
- **on_violation**: Serialize phase execution. Wait for phase completion before starting next.

## Do-machine-readable-progress (HIGH)
ALL progress output MUST follow structured format. DURING EXECUTION: emit "STATUS: [phase_name] description" at each major workflow phase. AT COMPLETION: emit "RESULT: SUCCESS|PARTIAL|FAILED|PASSED|NEEDS_WORK — key=value, key=value" followed by "NEXT: recommended_command". No free-form progress — only STATUS/RESULT/NEXT lines. Examples: "STATUS: [context] Analyzing task scope" | "STATUS: [execution] Step 3/5 complete" | "RESULT: SUCCESS — steps=5/5, files=3" | "NEXT: /do:validate {description}".
- **why**: Structured format enables UI rendering, orchestrator parsing, and consistent user experience. Matches Task command output contract for uniform tooling.
- **on_violation**: Reformat to STATUS/RESULT/NEXT structure. Replace free-form text with structured lines.

## Do-failure-awareness (CRITICAL)
BEFORE starting work: search memory category "debugging" for KNOWN FAILURES related to $TASK_DESCRIPTION. Found → extract failed approaches and BLOCK them. Pass blocked approaches to agents (async) or exclude from plan (sync). Do NOT attempt solutions that already failed.
- **why**: Repeating failed solutions wastes time and context. Memory contains "this does NOT work" knowledge from previous sessions.
- **on_violation**: Search debugging memories FIRST. Block known-failed approaches in plan/delegation.


# Task tag selection
GOAL(Select tags per task. Combine dimensions for precision.)
WORKFLOW (pipeline stage): decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression
TYPE (work kind): feature, bugfix, refactor, research, docs, test, chore, spike, hotfix
DOMAIN (area): backend, frontend, database, api, auth, ui, config, infra, ci-cd, migration
STRICT LEVEL: strict:relaxed, strict:standard, strict:strict, strict:paranoid
COGNITIVE LEVEL: cognitive:minimal, cognitive:standard, cognitive:deep, cognitive:exhaustive
BATCH: batch:trivial
Formula: 1 TYPE + 1 DOMAIN + 0-2 WORKFLOW + 1 STRICT + 1 COGNITIVE. Example: ["feature", "api", "strict:standard", "cognitive:standard"] or ["bugfix", "auth", "validation-fix", "strict:strict", "cognitive:deep"].

# Memory tag selection
GOAL(Select 1-3 tags per memory. Combine dimensions.)
CONTENT (kind): pattern, solution, `failure`, decision, insight, workaround, deprecated
SCOPE (breadth): project-wide, module-specific, temporary, reusable
Formula: 1 CONTENT + 0-1 SCOPE. Example: ["solution", "reusable"] or ["failure", "module-specific"]. Max 3 tags.

# Safety escalation patterns
GOAL(Automatic level escalation based on file patterns and context)
File patterns → strict minimum: auth/, guards/, policies/, permissions/ → strict. payments/, billing/, stripe/, subscription/ → strict. .env, credentials, secrets, config/auth → paranoid. migrations/, schema → strict. composer.json, package.json, *.lock → standard. CI/, .github/, Dockerfile, docker-compose → strict. routes/, middleware/ → standard.
Context patterns → level minimum: priority=critical → strict+deep. tag hotfix or production → strict+standard. touches >10 files → standard+standard. tag breaking-change → strict+deep. Keywords security/encryption/auth/permission → strict. Keywords migration/schema/database/drop → strict.

# Cognitive level
GOAL(Cognitive level: standard — calibrate analysis depth accordingly)
Memory probes per phase: 2-3 targeted
Failure history: recent only
Research (context7/web): on error/ambiguity
Agent scaling: auto (2-3)
Comment parsing: basic parse

# Aggressive docs search
GOAL(Find documentation even if named differently than task/code)
- `1`: Generate keyword variations from task title/content:
- `2`:   1. Original: "FocusModeTest" → search "FocusModeTest"
- `3`:   2. Split CamelCase: "FocusModeTest" → search "FocusMode", "Focus Mode"
- `4`:   3. Remove suffix: "FocusModeTest" → search "Focus" (remove Mode, Test)
- `5`:   4. Domain words: extract meaningful nouns → search each
- `6`:   5. Parent context: if task has parent → include parent title keywords
- `7`: Common suffixes to STRIP: Test, Tests, Controller, Service, Repository, Command, Handler, Provider, Factory, Manager, Helper, Validator, Processor
- `8`: Search ORDER: most specific → most general. STOP when found.
- `9`: Minimum 3 search attempts before concluding "no documentation".
- `10`: WRONG: brain docs "UserAuthenticationServiceTest" → not found → done
- `11`: RIGHT: brain docs "UserAuthenticationServiceTest" → not found → brain docs "UserAuthentication" → not found → brain docs "Authentication" → FOUND!

# Do failure awareness
GOAL(Mine failure history before execution to avoid repeating mistakes)
- `1`: mcp__vector-memory__search_memories('{query: "$TASK_DESCRIPTION failure", limit: 5, category: "debugging"}')
- `2`: STORE-AS($KNOWN_FAILURES = {failed approaches, errors, blocked patterns})
- `3`: IF($KNOWN_FAILURES not empty) →
  STORE-AS($BLOCKED_APPROACHES = {extracted approaches that MUST NOT be attempted})
  OUTPUT(Known failures found: {$KNOWN_FAILURES.count}. Blocked approaches: {$BLOCKED_APPROACHES})
→ END-IF
- `4`: IF($KNOWN_FAILURES empty) →
  STORE-AS($BLOCKED_APPROACHES = [])
  No known failures — proceed freely.
→ END-IF

# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with -y/--yes flags removed})
STORE-AS($VALIDATION_TARGET = {target to validate extracted from $CLEAN_ARGS})

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

# Phase7 fix task creation
GOAL(Create root-level vector tasks for test gaps (consolidated 5-8h batches))
- `1`: OUTPUT( === PHASE 7: FIX TASK CREATION ===)
- `2`: Check existing `pending` tasks to avoid duplicates
- `3`: mcp__vector-task__task_list('{query: "test fix $TASK_DESCRIPTION", status: "pending", limit: 20}')
- `4`: STORE-AS($EXISTING_FIX_TASKS = Existing `pending` test fix tasks)
- `5`: Calculate total estimate for ALL test issues:
- `6`: - Missing coverage: ~3h per requirement (write tests + verify) - Failing tests: ~1h per test (debug + fix) - Bloated tests: ~1h per test (refactor) - Missing workflows: ~4h per workflow (design + write e2e test) - Isolation issues: ~0.5h per test (fix isolation) STORE-AS($TOTAL_ESTIMATE = {sum of all issue estimates in hours})
- `7`: IF($ALL_TEST_ISSUES.count > 0 AND $TOTAL_ESTIMATE <= 8) →
  ALL issues fit into ONE consolidated task
  IF(NOT duplicate in $EXISTING_FIX_TASKS) →
  mcp__vector-task__task_create('{title: "Test fix: $TASK_DESCRIPTION (test-validation)", content: "## Test Validation Fix Task\\\\n\\\\nTotal estimate: {$TOTAL_ESTIMATE}h\\\\n\\\\n## Missing Coverage ({$MISSING_COVERAGE.count})\\\\n{FOR each req: - {req.description} | Type: {req.expected_test_type} | Scenarios: {req.testable_scenarios}}\\\\n\\\\n## Failing Tests ({$FAILING_TESTS.count})\\\\n{FOR each test: - {test.test_file}:{test.test_method} | Error: {test.error_message}}\\\\n\\\\n## Bloated Tests ({$BLOATED_TESTS.count})\\\\n{FOR each test: - {test.test_file}:{test.test_method} | Bloat: {test.bloat_type} | Suggestion: {test.suggestion}}\\\\n\\\\n## Missing Workflows ({$MISSING_WORKFLOWS.count})\\\\n{FOR each wf: - {wf.workflow} | Missing: {wf.missing_scenarios}}\\\\n\\\\n## Isolation Issues ({$ISOLATION_ISSUES.count})\\\\n{FOR each test: - {test.test_file} | Issue: {test.isolation_issue}}\\\\n\\\\n## Context\\\\n- Memory IDs: {$TEST_MEMORY_CONTEXT.memory_ids}\\\\n- Documentation: {$DOCS_INDEX.paths}", priority: "high", estimate: {$TOTAL_ESTIMATE}, tags: ["validation-fix", "test", "manual-only"]}')
  STORE-AS($CREATED_TASKS[] = {created task_id})
  OUTPUT(Created consolidated test fix task #{task_id} ({$TOTAL_ESTIMATE}h))
→ END-IF
→ END-IF
- `8`: IF($ALL_TEST_ISSUES.count > 0 AND $TOTAL_ESTIMATE > 8) →
  Split into multiple 5-8h task batches
  STORE-AS($NUM_BATCHES = {ceil($TOTAL_ESTIMATE / 6)})
  Group issues by priority into batches of ~6h each
  FOREACH(batch_index in range(1, $NUM_BATCHES)) →
  STORE-AS($BATCH_ISSUES = {slice of issues for this batch, ~6h worth})
  STORE-AS($BATCH_ESTIMATE = {sum of batch issue estimates})
  IF(NOT duplicate in $EXISTING_FIX_TASKS) →
  mcp__vector-task__task_create('{title: "Test fix batch {batch_index}/$NUM_BATCHES: $TASK_DESCRIPTION", content: "## Test Fix Batch {batch_index}\\\\n\\\\nBatch estimate: {$BATCH_ESTIMATE}h\\\\n\\\\n## Issues\\\\n{FOR each issue: - [{issue.type}] {issue.description}\\\\n  File: {issue.file}\\\\n  Suggestion: {issue.suggestion}}\\\\n\\\\n## Context\\\\n- Total batches: $NUM_BATCHES ($TOTAL_ESTIMATE h total)", priority: "high", estimate: {$BATCH_ESTIMATE}, order: {batch_index}, tags: ["validation-fix", "test", "manual-only"]}')
  STORE-AS($CREATED_TASKS[] = {created task_id})
  OUTPUT(Created batch {batch_index}/$NUM_BATCHES: {$BATCH_ESTIMATE}h)
→ END-IF
→ END-FOREACH
→ END-IF
- `9`: OUTPUT(Fix tasks created: {$CREATED_TASKS.count} (total estimate: {$TOTAL_ESTIMATE}h))

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
- `5`: mcp__vector-memory__store_memory('{content: "Test validation of {$TASK_DESCRIPTION}\\\\n\\\\nStatus: {$VALIDATION_STATUS}\\\\nCoverage rate: {$COVERAGE_RATE}\\\\nTest health: {$TEST_HEALTH_SCORE}\\\\n\\\\nMissing coverage: {$MISSING_COVERAGE.count}\\\\nFailing tests: {$FAILING_TESTS.count}\\\\nBloated tests: {$BLOATED_TESTS.count}\\\\nTasks created: {$CREATED_TASKS.count}\\\\n\\\\nKey findings: {summary}", category: "code-solution", tags: ["decision", "reusable"]}')
- `6`: OUTPUT( === TEST VALIDATION REPORT === Target: {$TASK_DESCRIPTION} Status: {$VALIDATION_STATUS}  | Metric | Value | |--------|-------| | Requirements coverage | {$COVERAGE_RATE} | | Test health score | {$TEST_HEALTH_SCORE} | | Total tests | {$DISCOVERED_TESTS.count} | | Passing tests | {passing_count} | | Failing/flaky tests | {$FAILING_TESTS.count} |  | Issue Type | Count | |------------|-------| | Missing coverage | {$MISSING_COVERAGE.count} | | Partial coverage | {$PARTIAL_COVERAGE.count} | | Bloated tests | {$BLOATED_TESTS.count} | | Missing workflows | {$MISSING_WORKFLOWS.count} | | Isolation issues | {$ISOLATION_ISSUES.count} |  {IF $CREATED_TASKS.count > 0: "Created task IDs: {$CREATED_TASKS}"}  RESULT: {$VALIDATION_STATUS} — coverage={$COVERAGE_RATE}, health={$TEST_HEALTH_SCORE}, tasks_created={$CREATED_TASKS.count} NEXT: {IF $CREATED_TASKS.count > 0: "/task:async #{first_task_id} [-y]" ELSE: "No test issues found."})

# Error recovery
Graceful error handling with recovery options
- `1`: IF(user rejects plan) →
  Accept modifications
  Rebuild plan
  Re-submit for approval
→ END-IF
- `2`: IF(task ID pattern detected) →
  Report: "Detected vector task ID. Use /task:test-validate for vector tasks."
  Abort command
→ END-IF
- `3`: IF(no agents available) →
  Report: "No agents found via brain list:masters"
  Suggest: Run /init-agents first
  Abort command
→ END-IF
- `4`: IF(agent execution fails) →
  Log: "Test validation agent {N} failed: {error}"
  Offer options:
    1. Retry current agent
    2. Skip and continue
    3. Abort remaining validation
  WAIT for user decision
→ END-IF
- `5`: IF(no tests found) →
  Report: "No tests found for {$TASK_DESCRIPTION}"
  Store to memory: "Write initial tests for {$TASK_DESCRIPTION}"
  Continue with documentation requirements analysis
→ END-IF
- `6`: IF(test execution fails) →
  Log: "Test execution failed: {error}"
  Mark tests as "execution_unknown"
  Continue with static analysis
→ END-IF
- `7`: IF(documentation scan fails) →
  Log: "brain docs command failed or no documentation found"
  Proceed without documentation context
→ END-IF
- `8`: IF(memory storage fails) →
  Log: "Failed to store to memory: {error}"
  Report findings in output instead
  Continue with report
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