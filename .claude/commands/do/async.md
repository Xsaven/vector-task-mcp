---
name: "do:async"
description: "Multi-agent orchestration command for flexible task execution (sequential\/parallel) with user approval gates"
---

<command>
<meta>
<id>do:async</id>
<description>Multi-agent orchestration command for flexible task execution (sequential/parallel) with user approval gates</description>
</meta>
<purpose>Coordinates flexible agent execution (sequential by default, parallel when beneficial) with approval checkpoints and comprehensive vector memory integration. Agents communicate through vector memory for knowledge continuity. Accepts $ARGUMENTS task description. Zero distractions, atomic tasks only, strict plan adherence.</purpose>
<purpose>Defines the do:async command protocol for multi-agent orchestration with flexible execution modes, user approval gates, and vector memory integration. Ensures zero distractions, atomic tasks, and strict plan adherence for reliable task execution.</purpose>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING $RAW_INPUT: Your FIRST output MUST be "=== DO:ASYNC ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain list:masters), code generation, file analysis, problem solving, implementation thinking.
- why: Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.
- on_violation: STOP IMMEDIATELY. Delete any tool calls. Output "=== DO:ASYNC ACTIVATED ===" and restart from Phase 0.

## Zero-distractions (CRITICAL)
ZERO distractions - implement ONLY specified task from $TASK_DESCRIPTION. NO creative additions, NO unapproved features, NO scope creep.
- why: Ensures focused execution and prevents feature drift
- on_violation: Abort immediately. Return to approved plan.

## Approval-gates-mandatory (CRITICAL)
User approval REQUIRED at Requirements Analysis gate and Execution Planning gate. NEVER proceed without explicit confirmation. EXCEPTION: If $HAS_Y_FLAG is true, auto-approve all gates (skip waiting for user confirmation).
- why: Maintains user control and prevents unauthorized execution. The -y flag enables unattended/scripted execution.
- on_violation: STOP. Wait for user approval before continuing (unless $HAS_Y_FLAG is true).

## Atomic-tasks-only (CRITICAL)
Each agent task MUST be small and focused: maximum 1-2 files per agent invocation. NO large multi-file changes.
- why: Prevents complexity, improves reliability, enables precise tracking
- on_violation: Break task into smaller pieces. Re-plan with atomic steps.

## No-improvisation (CRITICAL)
Execute ONLY approved plan steps. NO improvisation, NO "while we're here" additions, NO proactive suggestions during execution.
- why: Maintains plan integrity and predictability
- on_violation: Revert to last approved checkpoint. Resume approved steps only.

## Execution-mode-flexible (HIGH)
Execute agents sequentially BY DEFAULT. Allow parallel execution when: 1) tasks are independent (no file/context conflicts), 2) user explicitly requests parallel mode, 3) optimization benefits outweigh tracking complexity.
- why: Balances safety with performance optimization
- on_violation: Validate task independence before parallel execution. Fallback to sequential if conflicts detected.

## Vector-memory-mandatory (HIGH)
ALL agents MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.
- why: Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps
- on_violation: Include explicit vector memory instructions in agent Task() delegation.

## Conversation-context-awareness (HIGH)
ALWAYS analyze conversation context BEFORE planning. User may have discussed requirements, constraints, preferences, or decisions in previous messages.
- why: Prevents ignoring critical information already provided by user in conversation
- on_violation: Review conversation history before proceeding with task analysis.

## Full-workflow-mandatory (CRITICAL)
ALL requests MUST follow complete workflow: Phase 0 (Context) → Phase 1 (Discovery) → Phase 2 (Requirements + APPROVAL) → Phase 3 (Gathering) → Phase 4 (Planning + APPROVAL) → Phase 5 (Execution via agents) → Phase 6 (Completion). NEVER skip phases. NEVER execute directly without agent delegation.
- why: Workflow ensures quality, user control, and proper orchestration. Skipping phases leads to poor results, missed context, and violated user trust.
- on_violation: STOP. Return to Phase 0. Follow workflow sequentially. Present approval gates. Delegate via Task().

## Never-execute-directly (CRITICAL)
Brain NEVER executes implementation tasks directly. For ANY $TASK_DESCRIPTION: MUST delegate to agents via Task(). Brain only: analyzes, plans, presents approvals, delegates, validates results.
- why: Direct execution violates orchestration model, bypasses agent expertise, wastes Brain tokens on execution instead of coordination.
- on_violation: STOP. Identify required agent from brain list:masters. Delegate via Task(@agent-name, task).

## No-direct-file-tools (CRITICAL)
FORBIDDEN: Brain NEVER calls Glob, Grep, Read, Edit, Write directly. ALL file operations MUST be delegated to agents via Task().
- why: Direct tool calls are expensive, bypass agent expertise, and violate orchestration model. Each file operation costs tokens that agents handle more efficiently.
- on_violation: STOP. Remove direct tool call. Delegate to appropriate agent: ExploreMaster (search/read), code agents (edit/write).

## Orchestration-only (CRITICAL)
Brain role is ORCHESTRATION ONLY. Permitted: Task(), vector MCP, brain CLI (docs, list:masters). Everything else → delegate.
- why: Brain is conductor, not musician. Agents execute, Brain coordinates.
- on_violation: Identify task type → Select agent → Delegate via Task().

## One-agent-one-file (CRITICAL)
Each programming subtask = separate agent invocation. One agent, one file change. NO multi-file edits in single delegation.
- why: Atomic changes enable precise tracking, easier rollback, clear accountability.
- on_violation: Split into multiple Task() calls. One agent per file modification.


# Input
STORE-AS($RAW_INPUT = '$ARGUMENTS')
STORE-AS($HAS_Y_FLAG = '{true if $RAW_INPUT contains "-y" or "--yes"}')
STORE-AS($TASK_DESCRIPTION = '{$RAW_INPUT with flags removed}')

# Phase0 context analysis
GOAL(Extract task insights from conversation history before planning)
## Examples
- Analyze conversation context: requirements mentioned, constraints discussed, user preferences, prior decisions, related code/files referenced
- STORE-AS($CONVERSATION_CONTEXT = '{requirements, constraints, preferences, decisions, references}')
- IF(conversation has relevant context) → THEN → [Integrate context into task understanding → Note: Use conversation insights throughout all phases] → END-IF
- OUTPUT(=== PHASE 0: CONTEXT ANALYSIS === Task: {$TASK_DESCRIPTION} Context: {summary of relevant conversation info})

# Phase1 agent discovery
GOAL(Discover agents leveraging conversation context + vector memory)
## Examples
- mcp__vector-memory__search_memories('{query: "similar: {$TASK_DESCRIPTION}", limit: 5, category: "code-solution,architecture"}')
- STORE-AS($PAST_SOLUTIONS = 'Past approaches')
- Bash(brain list:masters) → [brain list:masters] → END-Bash
- STORE-AS($AVAILABLE_AGENTS = 'Agents list')
- Match task to agents: $TASK_DESCRIPTION + $CONVERSATION_CONTEXT + $PAST_SOLUTIONS
- STORE-AS($RELEVANT_AGENTS = '[{agent, capability, rationale}, ...]')
- OUTPUT(=== PHASE 1: AGENT DISCOVERY === Agents: {selected} | Context: {conversation insights applied})

# Phase2 requirements analysis approval
GOAL(Create requirements plan leveraging conversation + memory + GET USER APPROVAL + START TASK)
## Examples
- mcp__vector-memory__search_memories('{query: "patterns: {task_domain}", limit: 5, category: "learning,architecture"}')
- STORE-AS($IMPLEMENTATION_PATTERNS = 'Past patterns')
- Analyze: $TASK_DESCRIPTION + $CONVERSATION_CONTEXT + $PAST_SOLUTIONS + $IMPLEMENTATION_PATTERNS
- Determine needs: scan targets, web research (if non-trivial), docs scan (if architecture-related)
- STORE-AS($REQUIREMENTS_PLAN = '{scan_targets, web_research, docs_scan, conversation_insights, memory_learnings}')
- OUTPUT( === PHASE 2: REQUIREMENTS ANALYSIS === Context: {conversation insights} | Memory: {key learnings} Scanning: {targets} | Research: {status} | Docs: {status}  ⚠️  APPROVAL CHECKPOINT #1 ✅ approved/yes | ❌ no/modifications)
- IF($HAS_Y_FLAG === true) → THEN → [AUTO-APPROVED (unattended mode) → OUTPUT(🤖 Auto-approved via -y flag)] → END-IF
- IF($HAS_Y_FLAG === false) → THEN → [WAIT for user approval → VERIFY-SUCCESS(User approved) → IF(rejected) → THEN → [Modify plan → Re-present → WAIT] → END-IF] → END-IF

# Phase3 material gathering
GOAL(Collect materials via agents. Brain permitted: brain docs (index only, few tokens). ALL file reading → delegate to agents.)
## Examples
- FOREACH(scan_target in $REQUIREMENTS_PLAN.scan_targets) → [Task(@agent-explore 'Extract context from {scan_target}. Store findings to vector memory.') → STORE-AS($GATHERED_MATERIALS[{target}] = 'Agent-extracted context')] → END-FOREACH
- IF($DOCS_SCAN_NEEDED === true) → THEN → [Bash(brain docs {keywords}) → [Get documentation INDEX only (Path, Name, Description)] → END-Bash → STORE-AS($DOCS_INDEX = 'Documentation file paths') → Task(@agent-explore 'Read and summarize documentation files: {$DOCS_INDEX paths}. Store to vector memory.') → STORE-AS($DOCS_SCAN_FINDINGS = 'Agent-summarized documentation')] → END-IF
- IF($WEB_RESEARCH_NEEDED === true) → THEN → [Task(@agent-web-research-master 'Research best practices for {$TASK_DESCRIPTION}. Store findings to vector memory.') → STORE-AS($WEB_RESEARCH_FINDINGS = 'External knowledge')] → END-IF
- STORE-AS($CONTEXT_PACKAGES = '{agent_name: {context, materials, task_domain}, ...}')
- mcp__vector-memory__store_memory('{content: "Context for {$TASK_DESCRIPTION}\\\\n\\\\nMaterials: {summary}", category: "tool-usage", tags: ["do-command", "context-gathering"]}')
- OUTPUT(=== PHASE 3: MATERIALS GATHERED === Materials: {count} | Docs: {status} | Web: {status} Context stored to vector memory ✓)

# Phase4 execution planning approval
GOAL(Create atomic plan leveraging past execution patterns, analyze dependencies, and GET USER APPROVAL)
## Examples
- mcp__vector-memory__search_memories('{query: "execution approach for {task_type}", limit: 5, category: "code-solution"}')
- STORE-AS($EXECUTION_PATTERNS = 'Past successful execution approaches')
- Create plan: atomic steps (≤2 files each), logical order, informed by $EXECUTION_PATTERNS
- Analyze step dependencies: file conflicts, context dependencies, data flow
- Determine execution mode: sequential (default/safe) OR parallel (independent tasks/user request/optimization)
- IF(parallel possible AND beneficial) → THEN → [Group independent steps into parallel batches → Validate NO conflicts: 1) File: same file in multiple steps, 2) Context: step B needs output of step A, 3) Resource: same API/DB/external → STORE-AS($EXECUTION_MODE = 'parallel') → STORE-AS($PARALLEL_GROUPS = '[[step1, step2], [step3], ...]')] → END-IF
- IF(NOT parallel OR dependencies detected) → THEN → [STORE-AS($EXECUTION_MODE = 'sequential')] → END-IF
- STORE-AS($EXECUTION_PLAN = '{steps: [{step_number, agent_name, task_description, file_scope: [≤2 files], memory_search_query, expected_outcome}, ...], total_steps: N, execution_mode: "sequential|parallel", parallel_groups: [...]}')
- VERIFY-SUCCESS(Each step has ≤ 2 files)
- VERIFY-SUCCESS(Parallel groups have NO conflicts)
- OUTPUT( === PHASE 4: EXECUTION PLAN === Task: {$TASK_DESCRIPTION} | Steps: {N} | Mode: {execution_mode} Learned from: {$EXECUTION_PATTERNS summary}  {Step-by-step breakdown with files and memory search queries} {If parallel: show grouped batches}  ⚠️  APPROVAL CHECKPOINT #2 ✅ Type "approved" or "yes" to begin. ❌ Type "no" or provide modifications.)
- IF($HAS_Y_FLAG === true) → THEN → [AUTO-APPROVED (unattended mode) → OUTPUT(🤖 Auto-approved via -y flag)] → END-IF
- IF($HAS_Y_FLAG === false) → THEN → [WAIT for user approval → VERIFY-SUCCESS(User confirmed approval) → IF(user rejected) → THEN → [Accept modifications → Update plan → Verify atomic + dependencies → Re-present → WAIT] → END-IF] → END-IF

# Phase5 flexible execution
GOAL(Execute plan with optimal mode (sequential OR parallel))
## Examples
- Initialize: current_step = 1
- IF($EXECUTION_PLAN.execution_mode === "sequential") → THEN → [SEQUENTIAL MODE: Execute steps one-by-one → FOREACH(step in $EXECUTION_PLAN.steps) → [OUTPUT(▶️ Step {N}/{total}: @agent-{step.agent_name} | 📁 {step.file_scope}) → Delegate via Task() with agent-memory-pattern (BEFORE→DURING→AFTER) → Task(Task(@agent-{name}, {task + memory_search_query + context})) → STORE-AS($STEP_RESULTS[{N}] = 'Result') → OUTPUT(✅ Step {N} complete)] → END-FOREACH] → END-IF
- IF($EXECUTION_PLAN.execution_mode === "parallel") → THEN → [PARALLEL MODE: Execute independent steps concurrently → FOREACH(group in $EXECUTION_PLAN.parallel_groups) → [OUTPUT(🚀 Batch {N}: {count} steps) → Launch ALL steps CONCURRENTLY via multiple Task() calls → Each task follows agent-memory-pattern → WAIT for ALL tasks in batch to complete → STORE-AS($BATCH_RESULTS[{N}] = 'Batch results') → OUTPUT(✅ Batch {N} complete)] → END-FOREACH] → END-IF
- IF(step fails) → THEN → [Store failure to memory → Offer: Retry / Skip / Abort] → END-IF

# Phase6 completion report
GOAL(Report results and store comprehensive learnings to vector memory)
## Examples
- STORE-AS($COMPLETION_SUMMARY = '{completed_steps, files_modified, outcomes, learnings}')
- mcp__vector-memory__store_memory('{content: "Completed: {$TASK_DESCRIPTION}\\\\n\\\\nApproach: {summary}\\\\n\\\\nSteps: {outcomes}\\\\n\\\\nLearnings: {insights}\\\\n\\\\nFiles: {list}", category: "code-solution", tags: ["do-command", "completed"]}')
- OUTPUT( === EXECUTION COMPLETE === Task: {$TASK_DESCRIPTION} | Status: {SUCCESS/PARTIAL/FAILED} ✓ Steps: {completed}/{total} | 📁 Files: {count} | 💾 Learnings stored to memory {step_outcomes})
- IF(partial) → THEN → [Store partial state → List remaining → Suggest resumption] → END-IF

# Agent memory instructions
MANDATORY vector memory pattern for ALL agents
## Examples
- 
BEFORE TASK:
(Execute: mcp__vector-memory__search_memories(query: "{relevant}", limit: 5) + Review: Analyze results for patterns, solutions, learnings + Apply: Incorporate insights into approach)

- 
DURING TASK:
(Focus: Execute ONLY assigned task within file scope + Atomic: Respect 1-2 file limit strictly)

- 
AFTER TASK:
(Document: Summarize what was done, how it worked, key insights + Execute: mcp__vector-memory__store_memory(content: "{what+how+insights}", category: "{appropriate}", tags: [...]) + Verify: Confirm storage successful)

- CRITICAL: Vector memory is the communication channel between agents. Your learnings enable the next agent!

# Error handling
Graceful error handling with recovery options
## Examples
- IF(no agents available) → THEN → [Report: "No agents found via brain list:masters" → Suggest: Run /init-agents first → Abort command] → END-IF
- IF(user rejects requirements plan) → THEN → [Accept modifications → Rebuild requirements plan → Re-submit for approval] → END-IF
- IF(user rejects execution plan) → THEN → [Accept modifications → Rebuild execution plan → Verify atomic task constraints → Re-submit for approval] → END-IF
- IF(agent execution fails) → THEN → [Log: "Step {N} failed: {error}" → Offer options: →   1. Retry current step →   2. Skip and continue →   3. Abort remaining steps → WAIT for user decision] → END-IF
- IF(documentation scan fails) → THEN → [Log: "brain docs command failed or no documentation found" → Proceed without documentation context → Note: "Documentation context unavailable"] → END-IF
- IF(web research timeout) → THEN → [Log: "Web research timed out - continuing without external knowledge" → Proceed with local context only] → END-IF
- IF(context gathering fails) → THEN → [Log: "Failed to gather {context_type}" → Proceed with available context → Warn: "Limited context may affect quality"] → END-IF

# Constraints validation
Enforcement of critical constraints throughout execution
## Examples
- Before Requirements Analysis: Verify $TASK_DESCRIPTION is not empty
- Before Phase 2 → Phase 3 transition: Verify user approval received
- Before Phase 4 → Phase 5 transition: Verify user approval received
- During Execution Planning: Verify each step has ≤ 2 files in scope
- During Execution: Verify dependencies respected (sequential: step order, parallel: no conflicts)
- Throughout: NO unapproved steps allowed
- VERIFY-SUCCESS(approval_checkpoints_passed = 2 all_tasks_atomic = true (≤ 2 files each) execution_mode = sequential OR parallel (validated) improvisation_count = 0)

# Example simple
SCENARIO(Simple single-agent task)
## Examples
- input: "Fix authentication bug in LoginController.php"
- flow: Context → Discovery → Requirements ✓ → Gather → Plan ✓ → Execute (1 step) → Complete

# Example sequential
SCENARIO(Complex multi-agent sequential task)
## Examples
- input: "Add Laravel rate limiting to API endpoints"
- agents: @web-research-master, @code-master, @documentation-master
- plan: 4 steps: Middleware → Kernel → Routes → Docs
- execution: Sequential: 1→2→3→4 (dependencies between steps)
- result: 4/4 ✓

# Example parallel
SCENARIO(Parallel execution for independent tasks)
## Examples
- input: "Add validation to UserController, ProductController, OrderController"
- analysis: 3 independent files, no conflicts
- plan: Mode: PARALLEL, Batch 1: [Step1, Step2, Step3]
- execution: Concurrent: 3 agents simultaneously
- result: 3/3 ✓ (faster than sequential)

# Response format
=== headers | ⚠️ approval gates | ▶️✅❌ progress | 📁 file scope | No filler

</command>