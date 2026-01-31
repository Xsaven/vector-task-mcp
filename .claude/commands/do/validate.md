---
name: "do:validate"
description: "Comprehensive task\/work validation with parallel agent orchestration"
---

<command>
<meta>
<id>do:validate</id>
<description>Comprehensive task/work validation with parallel agent orchestration</description>
</meta>
<execute>Validates completed tasks or work against documentation requirements, code consistency, and completeness. Uses 5-6 parallel agents for thorough validation. Creates follow-up tasks for gaps found. For vector tasks: requires status "completed", sets to "in_progress" during validation, returns to "completed" with findings. Idempotent - can be run multiple times safely. Accepts $ARGUMENTS: vector task reference (task N, task:N, #N) or plain description.</execute>
<provides>Text-based work validation with parallel agent orchestration. Accepts text description (example: "validate user authentication"). Validates work against documentation requirements, code consistency, and completeness. Creates follow-up tasks for gaps. Idempotent. For vector task validation use /task:validate.</provides>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING $RAW_INPUT: Your FIRST output MUST be "=== DO:VALIDATE ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain list:masters), code generation, file analysis.
- **why**: Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.
- **on_violation**: STOP IMMEDIATELY. Delete any tool calls. Output "=== DO:VALIDATE ACTIVATED ===" and restart from Phase 0.

## Validation-only-no-execution (CRITICAL)
VALIDATION command validates EXISTING work. NEVER implement, fix, or create code directly. Only validate and CREATE TASKS for issues found.
- **why**: Validation is read-only audit. Execution belongs to do:async.
- **on_violation**: Abort any implementation. Create task instead of fixing directly.

## Text-description-required (CRITICAL)
$RAW_INPUT MUST be a text description of work to validate. Optional flags (-y, --yes) may be appended. Extract flags first, then verify remaining text is NOT a task ID pattern (15, #15, task 15). Examples: "validate auth -y", "check user module --yes".
- **why**: This command is exclusively for text-based validation. Vector task validation belongs to /task:validate.
- **on_violation**: STOP. Report: "For vector task validation, use /task:validate {id}. This command accepts text descriptions only."

## Parallel-agent-orchestration (HIGH)
Validation phases MUST use parallel agent orchestration (5-6 agents simultaneously) for efficiency. Each agent validates one aspect.
- **why**: Parallel validation reduces time and maximizes coverage.
- **on_violation**: Restructure validation into parallel Task() calls.

## Idempotent-validation (HIGH)
Validation is IDEMPOTENT. Running multiple times produces same result (no duplicate tasks, no repeated fixes).
- **why**: Allows safe re-runs without side effects.
- **on_violation**: Check existing tasks before creating. Skip duplicates.

## No-direct-fixes (CRITICAL)
VALIDATION command NEVER fixes issues directly. ALL issues (critical, major, minor) MUST become tasks. No exceptions.
- **why**: Traceability and audit trail. Every change must be tracked via task system.
- **on_violation**: Create task for the issue instead of fixing directly.

## Vector-memory-mandatory (HIGH)
ALL validation results MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.
- **why**: Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps
- **on_violation**: Include explicit vector memory instructions in agent Task() delegation.

## Phase-sequence-strict (CRITICAL)
Phases MUST execute in STRICT sequential order: Phase 0 → ... → Phase 7. NO phase may start until previous phase is FULLY COMPLETED. Each phase MUST output its header "=== PHASE N: NAME ===" before any actions.
- **why**: Sequential execution ensures data dependencies are satisfied. Each phase depends on variables stored by previous phases.
- **on_violation**: STOP. Return to last `completed` phase. Execute current phase fully before proceeding.

## No-phase-skip (CRITICAL)
FORBIDDEN: Skipping phases. ALL phases 0-7 MUST execute even if a phase has no issues to report. Empty results are valid; skipped phases are VIOLATION.
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

## Output-status-report (HIGH)
Output validation status: PASSED (no critical issues, no missing requirements) or NEEDS_WORK (issues found). Report all findings with severity.
- **why**: Clear status enables informed decision-making on next steps.
- **on_violation**: Include explicit status in validation report.

## Task-size-5-8h (HIGH)
Each created task MUST have estimate between 5-8 hours. Never create tasks < 5h (consolidate) or > 8h (split).
- **why**: Optimal task size for focused work sessions. Too small = context switching overhead. Too large = hard to track progress.
- **on_violation**: Merge small issues into consolidated task OR split large task into 5-8h batches.

## Task-comprehensive-context (CRITICAL)
Each task MUST include: all file:line references, memory IDs, documentation paths, detailed issue descriptions with suggestions, evidence from validation.
- **why**: Enables full context restoration without re-exploration. Saves agent time on task pickup.
- **on_violation**: Add missing context references before creating task.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($VALIDATION_TARGET = {target to validate extracted from $RAW_INPUT})

# Phase0 context setup
GOAL(Process $RAW_INPUT (already captured), extract flags, store task context)
- `1`: OUTPUT(=== DO:VALIDATE ACTIVATED ===)
- `2`: STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags (-y, --yes) removed, trimmed})
- `3`: Parse $CLEAN_ARGS - verify it is TEXT description, not task ID pattern
- `4`: IF($CLEAN_ARGS matches task ID pattern (15, #15, task 15, task:15, task-15)) →
  OUTPUT(=== WRONG COMMAND === Detected vector task ID pattern in $RAW_INPUT. Use /task:validate {id} for vector task validation. This command accepts text descriptions only.)
  ABORT command
→ END-IF
- `5`: STORE-AS($TASK_DESCRIPTION = $CLEAN_ARGS)
- `6`: OUTPUT( === PHASE 0: CONTEXT SETUP === Validation target: {$TASK_DESCRIPTION} {IF $HAS_AUTO_APPROVE: "Auto-approve: enabled (-y flag)"})

# Phase1 context preview
GOAL(Discover available agents and present validation scope for approval)
- `1`: OUTPUT( === PHASE 1: VALIDATION PREVIEW ===)
- `2`: Bash(brain list:masters) → [Get available agents with capabilities] → END-Bash
- `3`: STORE-AS($AVAILABLE_AGENTS = {agent_id: description mapping})
- `4`: Bash(brain docs {keywords from $TASK_DESCRIPTION}) → [Get documentation INDEX preview] → END-Bash
- `5`: STORE-AS($DOCS_PREVIEW = Documentation files available)
- `6`: OUTPUT(Task: {$TASK_DESCRIPTION} Available agents: {$AVAILABLE_AGENTS.COUNT} Documentation files: {$DOCS_PREVIEW.COUNT}  Validation will delegate to agents: 1. VectorMaster - deep memory research for context 2. DocumentationMaster - requirements extraction 3. Selected agents - parallel validation (5 aspects)  ⚠️  APPROVAL REQUIRED ✅ approved/yes - start validation | ❌ no/modifications)
- `7`: IF($HAS_AUTO_APPROVE === true) →
  OUTPUT(✅ Auto-approved via -y flag)
→ END-IF
- `8`: IF($HAS_AUTO_APPROVE === false) →
  WAIT for user approval
  VERIFY-SUCCESS(User approved)
  IF(rejected) → Accept modifications → Re-present → WAIT
→ END-IF

# Phase2 context gathering
GOAL(Delegate deep memory research to VectorMaster agent)
- `1`: OUTPUT( === PHASE 2: DEEP CONTEXT GATHERING === Delegating to VectorMaster for deep memory research...)
- `2`: SELECT vector-master from $AVAILABLE_AGENTS
- `3`: STORE-AS($CONTEXT_AGENT = {vector-master agent_id})
- `4`: [DELEGATE] @agent-{$CONTEXT_AGENT}: 'DEEP MEMORY RESEARCH for validation of "$TASK_DESCRIPTION": 1) Multi-probe search: implementation patterns, requirements, architecture decisions, past validations, bug fixes 2) Search across categories: code-solution, architecture, learning, bug-fix 3) Extract actionable insights for validation 4) Return: {implementations: [...], requirements: [...], patterns: [...], past_validations: [...], key_insights: [...]}. Store consolidated context.'
- `5`: STORE-AS($MEMORY_CONTEXT = {VectorMaster agent results})
- `6`: mcp__vector-memory__search_memories('{query: "$TASK_DESCRIPTION", limit: 10, category: "code-solution"}')
- `7`: STORE-AS($RELATED_SOLUTIONS = Related solutions from memory)
- `8`: OUTPUT(Context gathered via {$CONTEXT_AGENT}: - Memory insights: {$MEMORY_CONTEXT.KEY_INSIGHTS.COUNT} - Related solutions: {$RELATED_SOLUTIONS.COUNT})

# Phase3 documentation extraction
GOAL(Extract ALL requirements from .docs/ via DocumentationMaster)
- `1`: OUTPUT( === PHASE 3: DOCUMENTATION REQUIREMENTS ===)
- `2`: Bash(brain docs {keywords from $TASK_DESCRIPTION}) → [Get documentation INDEX] → END-Bash
- `3`: STORE-AS($DOCS_INDEX = Documentation file paths)
- `4`: IF({$DOCS_INDEX} not empty) →
  [DELEGATE] @agent-documentation-master: 'Extract ALL requirements, acceptance criteria, constraints, and specifications from documentation files: {$DOCS_INDEX paths}. Return structured list: [{requirement_id, description, acceptance_criteria, related_files, priority}]. Store to vector memory.'
  STORE-AS($DOCUMENTATION_REQUIREMENTS = {structured requirements list})
→ END-IF
- `5`: IF({$DOCS_INDEX} empty) →
  STORE-AS($DOCUMENTATION_REQUIREMENTS = [])
  OUTPUT(WARNING: No documentation found. Validation will be limited.)
→ END-IF
- `6`: OUTPUT(Requirements extracted: {$DOCUMENTATION_REQUIREMENTS.COUNT} {requirements summary})

# Phase4 parallel validation
GOAL(Select best agents from $AVAILABLE_AGENTS and launch parallel validation)
- `1`: OUTPUT( === PHASE 4: PARALLEL VALIDATION ===)
- `2`: AGENT SELECTION: Analyze $AVAILABLE_AGENTS descriptions and select BEST agent for each validation aspect:
- `3`: ASPECT 1 - COMPLETENESS: Select agent best suited for requirements verification (vector-master for memory research, explore for codebase) ASPECT 2 - CODE CONSISTENCY: Select agent for code pattern analysis (explore for codebase scanning) ASPECT 3 - TEST COVERAGE: Select agent for test analysis (explore for test file discovery) ASPECT 4 - DOCUMENTATION SYNC: Select agent for documentation analysis (documentation-master if docs-focused, explore otherwise) ASPECT 5 - DEPENDENCIES: Select agent for dependency analysis (explore for import scanning)
- `4`: STORE-AS($SELECTED_AGENTS = {aspect: agent_id mapping based on $AVAILABLE_AGENTS})
- `5`: OUTPUT(Selected agents for validation: {$SELECTED_AGENTS mapping}  Launching validation agents in parallel...)
- `6`: PARALLEL BATCH: Launch selected agents simultaneously with DEEP RESEARCH tasks
- `7`: [DELEGATE] @agent-{$SELECTED_AGENTS.COMPLETENESS}: 'DEEP RESEARCH - COMPLETENESS: For "$TASK_DESCRIPTION": 1) Search vector memory for past implementations and requirements 2) Scan codebase for implementation evidence 3) Map each requirement from {$DOCUMENTATION_REQUIREMENTS} to code 4) Return: [{requirement_id, status: implemented|partial|missing, evidence: file:line, memory_refs: [...]}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.CONSISTENCY}: 'DEEP RESEARCH - CODE CONSISTENCY: For "$TASK_DESCRIPTION": 1) Search memory for project coding standards 2) Scan related files for pattern violations 3) Check naming, architecture, style consistency 4) Return: [{file, issue_type, severity, description, suggestion}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.TESTS}: 'DEEP RESEARCH - TEST COVERAGE: For "$TASK_DESCRIPTION": 1) Search memory for test patterns 2) Discover all related test files 3) Analyze coverage gaps 4) Run tests if possible 5) Return: [{test_file, coverage_status, missing_scenarios}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.DOCS}: 'DEEP RESEARCH - DOCUMENTATION SYNC: For "$TASK_DESCRIPTION": 1) Search memory for documentation standards 2) Compare code vs documentation 3) Check docblocks, README, API docs 4) Return: [{doc_type, sync_status, gaps}]. Store findings.' [DELEGATE] @agent-{$SELECTED_AGENTS.DEPS}: 'DEEP RESEARCH - DEPENDENCIES: For "$TASK_DESCRIPTION": 1) Search memory for dependency issues 2) Scan imports and dependencies 3) Check for broken/unused/circular refs 4) Return: [{file, dependency_issue, severity}]. Store findings.'
- `8`: STORE-AS($VALIDATION_BATCH = {results from all agents})
- `9`: OUTPUT(Batch complete: {$SELECTED_AGENTS.COUNT} validation checks finished)

# Phase5 results aggregation
GOAL(Aggregate all validation results and categorize issues)
- `1`: OUTPUT( === PHASE 5: RESULTS AGGREGATION ===)
- `2`: Merge results from all validation agents
- `3`: STORE-AS($ALL_ISSUES = {merged issues from all agents})
- `4`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Analyzing validation results. Categorizing by: severity (critical/major/minor), type (functional/cosmetic), impact, fix effort, dependencies between issues.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 3,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `5`: Categorize issues:
- `6`: STORE-AS($CRITICAL_ISSUES = {issues with severity: critical})
- `7`: STORE-AS($MAJOR_ISSUES = {issues with severity: major})
- `8`: STORE-AS($MINOR_ISSUES = {issues with severity: minor})
- `9`: STORE-AS($MISSING_REQUIREMENTS = {requirements not implemented})
- `10`: OUTPUT(Validation results: - Critical issues: {$CRITICAL_ISSUES.COUNT} - Major issues: {$MAJOR_ISSUES.COUNT} - Minor issues: {$MINOR_ISSUES.COUNT} - Missing requirements: {$MISSING_REQUIREMENTS.COUNT})

# Phase6 task creation
GOAL(Create consolidated tasks (5-8h each) for issues with comprehensive context)
- `1`: OUTPUT( === PHASE 6: TASK CREATION (CONSOLIDATED) ===)
- `2`: Check existing tasks in memory to avoid duplicates
- `3`: mcp__vector-memory__search_memories('{query: "fix issues $TASK_DESCRIPTION", limit: 20, category: "code-solution"}')
- `4`: STORE-AS($EXISTING_FIX_MEMORIES = Existing fix task memories)
- `5`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Planning task consolidation strategy. Analyzing: total effort, issue grouping, dependencies, optimal batch sizes (5-8h), priority ordering.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `6`: CONSOLIDATION STRATEGY: Group issues into 5-8 hour task batches
- `7`: Calculate total estimate for ALL issues: - Critical issues: ~2h per issue (investigation + fix + test) - Major issues: ~1.5h per issue (fix + verify) - Minor issues: ~0.5h per issue (fix + verify) - Missing requirements: ~4h per requirement (implement + test) STORE-AS($TOTAL_ESTIMATE = {sum of all issue estimates in hours})
- `8`: IF({$TOTAL_ESTIMATE} <= 8) →
  ALL issues fit into ONE consolidated task (5-8h range)
  IF(({$CRITICAL_ISSUES.COUNT} + {$MAJOR_ISSUES.COUNT} + {$MINOR_ISSUES.COUNT} + {$MISSING_REQUIREMENTS.COUNT}) > 0 AND NOT exists similar in $EXISTING_FIX_MEMORIES) →
  mcp__vector-memory__store_memory('{content: "Validation fix task: $TASK_DESCRIPTION\\\\n\\\\nTotal estimate: {$TOTAL_ESTIMATE}h\\\\n\\\\n## Critical Issues ({$CRITICAL_ISSUES.COUNT})\\\\n{FOR each issue: - [{issue.severity}] {issue.description}\\\\n  File: {issue.file}:{issue.line}\\\\n  Type: {issue.type}\\\\n  Suggestion: {issue.suggestion}\\\\n}\\\\n\\\\n## Major Issues ({$MAJOR_ISSUES.COUNT})\\\\n{FOR each issue: - [{issue.severity}] {issue.description}\\\\n  File: {issue.file}:{issue.line}\\\\n}\\\\n\\\\n## Minor Issues ({$MINOR_ISSUES.COUNT})\\\\n{FOR each issue: - [{issue.severity}] {issue.description}\\\\n}\\\\n\\\\n## Missing Requirements ({$MISSING_REQUIREMENTS.COUNT})\\\\n{FOR each req: - {req.description}\\\\n  Acceptance criteria: {req.acceptance_criteria}\\\\n}\\\\n\\\\n## Context References\\\\n- Memory IDs: {$MEMORY_CONTEXT.MEMORY_IDS}\\\\n- Documentation: {$DOCS_INDEX.PATHS}\\\\n- Validation agents used: {$SELECTED_AGENTS}", category: "code-solution", tags: ["validation-fix", "consolidated", "do:validate"]}')
  STORE-AS($CREATED_TASKS[] = {memory_id})
  OUTPUT(Created consolidated fix task in memory ({$TOTAL_ESTIMATE}h, {issues_count} issues))
→ END-IF
→ END-IF
- `9`: IF({$TOTAL_ESTIMATE} > 8) →
  Split into multiple 5-8h task batches
  STORE-AS($BATCH_SIZE = 6)
  STORE-AS($NUM_BATCHES = {ceil($TOTAL_ESTIMATE / 6)})
  Group issues by priority (critical first) into batches of ~6h each
  FOREACH(batch_index in range(1, $NUM_BATCHES)) →
  STORE-AS($BATCH_ISSUES = {slice of issues for this batch, ~6h worth, priority-ordered})
  STORE-AS($BATCH_ESTIMATE = {sum of batch issue estimates})
  STORE-AS($BATCH_CRITICAL = {count of critical issues in batch})
  STORE-AS($BATCH_MAJOR = {count of major issues in batch})
  STORE-AS($BATCH_MISSING = {count of missing requirements in batch})
  IF(NOT exists similar in $EXISTING_FIX_MEMORIES) →
  mcp__vector-memory__store_memory('{content: "Validation fix batch {batch_index}/{$NUM_BATCHES}: $TASK_DESCRIPTION\\\\n\\\\nBatch estimate: {$BATCH_ESTIMATE}h\\\\nBatch composition: {$BATCH_CRITICAL} critical, {$BATCH_MAJOR} major, {$BATCH_MISSING} missing reqs\\\\n\\\\n## Issues in this batch\\\\n{FOR each issue in $BATCH_ISSUES:\\\\n### [{issue.severity}] {issue.title}\\\\n- File: {issue.file}:{issue.line}\\\\n- Description: {issue.description}\\\\n- Suggestion: {issue.suggestion}\\\\n}\\\\n\\\\n## Context References\\\\n- Memory IDs: {$MEMORY_CONTEXT.MEMORY_IDS}\\\\n- Documentation: {$DOCS_INDEX.PATHS}\\\\n- Total batches: {$NUM_BATCHES} ({$TOTAL_ESTIMATE}h total)\\\\n- Validation agents: {$SELECTED_AGENTS}", category: "code-solution", tags: ["validation-fix", "batch-{batch_index}", "do:validate"]}')
  STORE-AS($CREATED_TASKS[] = {memory_id})
  OUTPUT(Created batch {batch_index}/{$NUM_BATCHES}: {$BATCH_ESTIMATE}h ({$BATCH_ISSUES.COUNT} issues))
→ END-IF
→ END-FOREACH
→ END-IF
- `10`: OUTPUT(Fix tasks created: {$CREATED_TASKS.COUNT} (total estimate: {$TOTAL_ESTIMATE}h))

# Phase7 completion
GOAL(Complete validation, store summary to memory)
- `1`: OUTPUT( === PHASE 7: VALIDATION COMPLETE ===)
- `2`: STORE-AS($VALIDATION_SUMMARY = {all_issues_count, tasks_created_count, pass_rate})
- `3`: STORE-AS($VALIDATION_STATUS = IF({$CRITICAL_ISSUES.COUNT} === 0 AND {$MISSING_REQUIREMENTS.COUNT} === 0) →
  PASSED
→ ELSE →
  NEEDS_WORK
→ END-IF)
- `4`: mcp__vector-memory__store_memory('{content: "Validation of $TASK_DESCRIPTION\\\\n\\\\nStatus: {$VALIDATION_STATUS}\\\\nCritical: {$CRITICAL_ISSUES.COUNT}\\\\nMajor: {$MAJOR_ISSUES.COUNT}\\\\nMinor: {$MINOR_ISSUES.COUNT}\\\\nTasks created: {$CREATED_TASKS.COUNT}\\\\n\\\\nFindings:\\\\n{summary of key findings}", category: "code-solution", tags: ["validation", "audit", "do:validate"]}')
- `5`: OUTPUT( === VALIDATION REPORT === Task: {$TASK_DESCRIPTION} Status: {$VALIDATION_STATUS}  | Metric | Count | |--------|-------| | Critical issues | {$CRITICAL_ISSUES.COUNT} | | Major issues | {$MAJOR_ISSUES.COUNT} | | Minor issues | {$MINOR_ISSUES.COUNT} | | Missing requirements | {$MISSING_REQUIREMENTS.COUNT} | | Fix tasks created | {$CREATED_TASKS.COUNT} |  {IF $CREATED_TASKS.COUNT > 0: "Follow-up fix memories: {$CREATED_TASKS}"}  Validation stored to vector memory.)

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

# Constraints
Validation constraints and limits
- `1`: Max 6 parallel validation agents per batch
- `2`: Max 20 fix tasks created per validation run
- `3`: Validation timeout: 5 minutes per agent
- `4`: VERIFY-SUCCESS(text_description_validated = true parallel_agents_used = true documentation_checked = true results_stored_to_memory = true no_direct_fixes = true)

# Example text validation
SCENARIO(Validate work by text description)
- `input`: "validate user authentication implementation"
- `flow`: Context from memory → Docs requirements → Parallel Validation → Aggregate → Store Findings → Report
- `result`: Validation report with findings and fix task memories

# Example feature validation
SCENARIO(Validate specific feature)
- `input`: "validate payment processing module"
- `flow`: Search memory for payment patterns → Docs → 5 parallel agents → Aggregate → Create fix tasks → Report
- `result`: Validation PASSED/NEEDS_WORK, N fix task memories created

# Example rerun
SCENARIO(Re-run validation (idempotent))
- `input`: "validate user authentication" (already `validated` before)
- `behavior`: Skips existing memories, only creates NEW issues found
- `result`: Same/updated validation report, no duplicate memories

# Do validate vs task validate
When to use /do:validate vs /task:validate
- `USE /do:validate`: Text-based validation ("validate user authentication"). Best for: ad-hoc validation, exploratory checks, no existing vector task.
- `USE /task:validate`: Vector task validation (15, #15, task 15). Best for: systematic task workflow, hierarchical task management, fix task creation as children.

# Response format
=== headers | Parallel: agent batch indicators | Tables: validation results | No filler | Created memories listed

</command>