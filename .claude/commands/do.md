---
name: "do"
description: "Multi-agent orchestration command for flexible task execution (sequential\/parallel) with user approval gates"
---

<command>
<meta>
<id>do</id>
<description>Multi-agent orchestration command for flexible task execution (sequential/parallel) with user approval gates</description>
</meta>
<purpose>Coordinates flexible agent execution (sequential by default, parallel when beneficial) with approval checkpoints and comprehensive vector memory integration. Agents communicate through vector memory for knowledge continuity. Accepts $ARGUMENTS task description. Zero distractions, atomic tasks only, strict plan adherence.</purpose>

# Iron Rules
## Zero-distractions (CRITICAL)
ZERO distractions - implement ONLY specified task from $ARGUMENTS. NO creative additions, NO unapproved features, NO scope creep.
- why: Ensures focused execution and prevents feature drift
- on_violation: Abort immediately. Return to approved plan.

## Approval-gates-mandatory (CRITICAL)
User approval REQUIRED at Requirements Analysis gate and Execution Planning gate. NEVER proceed without explicit confirmation.
- why: Maintains user control and prevents unauthorized execution
- on_violation: STOP. Wait for user approval before continuing.

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


# Phase0 context analysis
GOAL(Extract task insights from conversation history before planning)
## Examples
- STORE-AS($TASK_DESCRIPTION = 'User task from $ARGUMENTS')
- Analyze conversation context: requirements mentioned, constraints discussed, user preferences, prior decisions, related code/files referenced
- STORE-AS($CONVERSATION_CONTEXT = '{requirements, constraints, preferences, decisions, references}')
- IF(conversation has relevant context) → THEN → [Integrate context into task understanding → Note: Use conversation insights throughout all phases] → END-IF
- OUTPUT(=== PHASE 0: CONTEXT ANALYSIS === Task: {$TASK_DESCRIPTION} Context: {summary of relevant conversation info})

# Phase1 agent discovery
GOAL(Discover agents leveraging conversation context + vector memory)
## Examples
- mcp__vector-memory__search_memories(query: "similar: {$TASK_DESCRIPTION}", limit: 5, category: "code-solution,architecture")
- STORE-AS($PAST_SOLUTIONS = 'Past approaches')
- Bash(brain list:masters) → [brain list:masters] → END-Bash
- STORE-AS($AVAILABLE_AGENTS = 'Agents list')
- Match task to agents: $TASK_DESCRIPTION + $CONVERSATION_CONTEXT + $PAST_SOLUTIONS
- STORE-AS($RELEVANT_AGENTS = '[{agent, capability, rationale}, ...]')
- OUTPUT(=== PHASE 1: AGENT DISCOVERY === Agents: {selected} | Context: {conversation insights applied})

# Phase2 requirements analysis approval
GOAL(Create requirements plan leveraging conversation + memory + GET USER APPROVAL)
## Examples
- mcp__vector-memory__search_memories(query: "patterns: {task_domain}", limit: 5, category: "learning,architecture")
- STORE-AS($IMPLEMENTATION_PATTERNS = 'Past patterns')
- Analyze: $TASK_DESCRIPTION + $CONVERSATION_CONTEXT + $PAST_SOLUTIONS + $IMPLEMENTATION_PATTERNS
- Determine needs: scan targets, web research (if non-trivial), docs scan (if architecture-related)
- STORE-AS($REQUIREMENTS_PLAN = '{scan_targets, web_research, docs_scan, conversation_insights, memory_learnings}')
- OUTPUT( === PHASE 2: REQUIREMENTS ANALYSIS === Context: {conversation insights} | Memory: {key learnings} Scanning: {targets} | Research: {status} | Docs: {status}  ⚠️  APPROVAL CHECKPOINT #1 ✅ approved/yes | ❌ no/modifications)
- WAIT for user approval
- VERIFY-SUCCESS(User approved)
- IF(rejected) → THEN → [Modify plan → Re-present → WAIT] → END-IF

# Phase3 material gathering
GOAL(Collect materials per plan and store to vector memory. NOTE: brain docs returns file index (Path, Name, Description, etc.), then Read relevant files)
## Examples
- FOREACH(scan_target in $REQUIREMENTS_PLAN.scan_targets) → [Task(Delegate to agent for context extraction from {scan_target}) → STORE-AS($GATHERED_MATERIALS[{target}] = 'Extracted context')] → END-FOREACH
- IF($DOCS_SCAN_NEEDED === true) → THEN → [Task(@agent-documentation-master: Use brain docs {keywords} to find relevant documentation, then Read files) → STORE-AS($DOCS_SCAN_FINDINGS = 'Documentation content from brain docs')] → END-IF
- IF($WEB_RESEARCH_NEEDED === true) → THEN → [Task(@agent-web-research-master: Research best practices for {$TASK_DESCRIPTION}) → STORE-AS($WEB_RESEARCH_FINDINGS = 'External knowledge')] → END-IF
- STORE-AS($CONTEXT_PACKAGES = '{agent_name: {context, materials, task_domain}, ...}')
- Store gathered context: mcp__vector-memory__store_memory(content: "Context for {$TASK_DESCRIPTION}\\n\\nMaterials: {summary}", category: "tool-usage", tags: ["do-command", "context-gathering"])
- OUTPUT(=== PHASE 3: MATERIALS GATHERED === Materials: {count} | Docs: {status} | Web: {status} Context stored to vector memory ✓)

# Phase4 execution planning approval
GOAL(Create atomic plan leveraging past execution patterns, analyze dependencies, and GET USER APPROVAL)
## Examples
- Search vector memory: mcp__vector-memory__search_memories(query: "execution approach for {task_type}", limit: 5, category: "code-solution")
- STORE-AS($EXECUTION_PATTERNS = 'Past successful execution approaches')
- Create plan: atomic steps (≤2 files each), logical order, informed by $EXECUTION_PATTERNS
- Analyze step dependencies: file conflicts, context dependencies, data flow
- Determine execution mode: sequential (default/safe) OR parallel (independent tasks/user request/optimization)
- IF(parallel possible AND beneficial) → THEN → [Group independent steps into parallel batches → Ensure NO file conflicts within groups → Ensure NO context dependencies within groups → STORE-AS($EXECUTION_MODE = 'parallel') → STORE-AS($PARALLEL_GROUPS = '[[step1, step2], [step3], ...]')] → END-IF
- IF(NOT parallel OR dependencies detected) → THEN → [STORE-AS($EXECUTION_MODE = 'sequential')] → END-IF
- STORE-AS($EXECUTION_PLAN = '{steps: [{step_number, agent_name, task_description, file_scope: [≤2 files], memory_search_query, expected_outcome}, ...], total_steps: N, execution_mode: "sequential|parallel", parallel_groups: [...]}')
- VERIFY-SUCCESS(Each step has ≤ 2 files)
- VERIFY-SUCCESS(Parallel groups have NO conflicts)
- OUTPUT( === PHASE 4: EXECUTION PLAN === Task: {$TASK_DESCRIPTION} | Steps: {N} | Mode: {execution_mode} Learned from: {$EXECUTION_PATTERNS summary}  {Step-by-step breakdown with files and memory search queries} {If parallel: show grouped batches}  ⚠️  APPROVAL CHECKPOINT #2 ✅ Type "approved" or "yes" to begin. ❌ Type "no" or provide modifications.)
- WAIT for user approval
- VERIFY-SUCCESS(User confirmed approval)
- IF(user rejected) → THEN → [Accept modifications → Update plan → Verify atomic + dependencies → Re-present → WAIT] → END-IF

# Phase5 flexible execution
GOAL(Execute plan with optimal mode (sequential OR parallel) with agents communicating through vector memory)
## Examples
- Initialize: current_step = 1
- IF($EXECUTION_PLAN.execution_mode === "sequential") → THEN → [SEQUENTIAL MODE: Execute steps one-by-one → FOREACH(step in $EXECUTION_PLAN.steps) → [OUTPUT(▶️  Step {current_step}/{total_steps}: @agent-{step.agent_name} 📝 {step.task_description} | 📁 {step.file_scope}) → Delegate via Task() with MANDATORY vector memory instructions: →   📥 BEFORE: You MUST execute: mcp__vector-memory__search_memories(query: "{step.memory_search_query}", limit: 5, category: "code-solution,learning") and review results →   🔧 DURING: Execute task: {step.task_description} | Context: {$CONTEXT_PACKAGES} | Files: {step.file_scope} (ATOMIC - no expansion) →   📤 AFTER: You MUST execute: mcp__vector-memory__store_memory(content: "Step {N}: {outcome}\\n\\nApproach: {what_worked}\\n\\nLearnings: {insights}", category: "code-solution", tags: ["do-command", "step-{N}"]) → Task(Task(@agent-{name}, {task_with_MANDATORY_memory_instructions})) → STORE-AS($STEP_RESULTS[{N}] = 'Result with memory trace') → VERIFY-SUCCESS(Step completed AND memory stored) → OUTPUT(✅ Step {N} complete | Memory updated ✓) → current_step++] → END-FOREACH] → END-IF
- IF($EXECUTION_PLAN.execution_mode === "parallel") → THEN → [PARALLEL MODE: Execute independent steps concurrently in batches → FOREACH(group in $EXECUTION_PLAN.parallel_groups) → [OUTPUT(🚀 Parallel Batch {batch_number}: {count} steps) → Launch ALL steps in group CONCURRENTLY via multiple Task() calls in single message: → FOREACH(step in group) → [  📥 BEFORE: mcp__vector-memory__search_memories(query: "{step.memory_search_query}", limit: 5) →   🔧 DURING: Execute task: {step.task_description} | Context: {$CONTEXT_PACKAGES} | Files: {step.file_scope} →   📤 AFTER: mcp__vector-memory__store_memory(content: "Step {N}: {outcome}\\n\\n{insights}", category: "code-solution", tags: ["do-command", "step-{N}"]) → Task(Task(@agent-{name}, {task_with_memory_instructions}))] → END-FOREACH → WAIT for ALL tasks in batch to complete → VERIFY-SUCCESS(All batch steps completed AND memory stored) → STORE-AS($BATCH_RESULTS[{batch}] = 'All results from parallel batch') → OUTPUT(✅ Batch {batch} complete ({count} steps) | Memory updated ✓)] → END-FOREACH] → END-IF
- IF(step fails) → THEN → [mcp__vector-memory__store_memory(content: "Failure at step {N}: {error}", category: "debugging", tags: ["do-command", "failure"]) → Offer: Retry / Skip / Abort → WAIT] → END-IF

# Phase6 completion report
GOAL(Report results and store comprehensive learnings to vector memory)
## Examples
- STORE-AS($COMPLETION_SUMMARY = '{completed_steps, files_modified, outcomes, learnings}')
- Store final summary: mcp__vector-memory__store_memory(content: "Completed: {$TASK_DESCRIPTION}\\n\\nApproach: {summary}\\n\\nSteps: {outcomes}\\n\\nLearnings: {insights}\\n\\nFiles: {list}", category: "code-solution", tags: ["do-command", "completed"])
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
- Before Requirements Analysis: Verify $ARGUMENTS is not empty
- Before Phase 2 → Phase 3 transition: Verify user approval received
- Before Phase 4 → Phase 5 transition: Verify user approval received
- During Execution Planning: Verify each step has ≤ 2 files in scope
- During Execution: Verify dependencies respected (sequential: step order, parallel: no conflicts)
- Throughout: NO unapproved steps allowed
- VERIFY-SUCCESS(approval_checkpoints_passed = 2 all_tasks_atomic = true (≤ 2 files each) execution_mode = sequential OR parallel (validated) improvisation_count = 0)

# Example 0 conversation context
SCENARIO(Task with conversation context)
## Examples
- conversation: User: "I want to use Redis for caching" → "Prefer atomic commits" → "Follow PSR-12"
- input: $ARGUMENTS = "Add caching to product catalog"
- phase0: Context: Redis requirement, atomic commits preference, PSR-12 standard
- phase1-6: Execute with conversation insights: Redis driver, atomic steps, PSR-12 formatting

# Example 1 simple task
SCENARIO(Simple single-agent task)
## Examples
- input: $ARGUMENTS = "Fix authentication bug in LoginController.php"
- phases: Discovery → Requirements (approved) → Gather → Plan (approved) → Execute → Complete: 1/1 ✓

# Example 2 multi step task
SCENARIO(Complex multi-agent task with web research)
## Examples
- input: $ARGUMENTS = "Add Laravel rate limiting to API endpoints"
- phase1: Agents: @agent-web-research-master, @agent-code-master, @agent-documentation-master
- phase2: Requirements Plan: Research Laravel rate limiting, scan API routes, identify endpoints
- approval1: User approves (including web research)
- phase3: Gather: Web research findings, routes/api.php, middleware list
- phase4: 
Execution Plan:
(Step 1: @agent-code-master - Create RateLimitMiddleware.php + Step 2: @agent-code-master - Update app/Http/Kernel.php + Step 3: @agent-code-master - Apply middleware to routes/api.php + Step 4: @agent-documentation-master - Update API docs)

- approval2: User approves execution plan
- phase5: Sequential execution: Steps 1→2→3→4
- phase6: Report: 4/4 steps complete - rate limiting implemented ✓

# Example 3 approval rejection
SCENARIO(User rejects execution plan, requests modifications)
## Examples
- input: $ARGUMENTS = "Refactor UserService to use repository pattern"
- phase1-4: Standard flow through execution planning
- approval2: User responds: "No, split Step 3 into smaller pieces"
- revision: Rebuild execution plan with Step 3 split into 3a, 3b, 3c
- re-approval: Re-present plan → User approves
- phase5: Execute revised plan
- phase6: Report: Completed with revised plan ✓

# Example 4 documentation scan
SCENARIO(Task requiring project documentation context)
## Examples
- input: $ARGUMENTS = "Implement feature based on architecture described in documentation"
- phase1: Agent Discovery: Selected @agent-documentation-master, @agent-code-master
- phase2: Requirements Plan: Search documentation via brain docs, identify feature requirements
- approval1: User approves (including documentation scan)
- phase3: Gather: Documentation results from brain docs, related code files
- phase4: 
Execution Plan:
(Step 1: @agent-code-master - Create FeatureService.php based on docs + Step 2: @agent-code-master - Integrate with existing architecture)

- approval2: User approves execution plan
- phase5: Sequential execution: Steps 1→2
- phase6: Report: 2/2 steps complete - feature implemented per documentation ✓

# Example 5 parallel execution
SCENARIO(Parallel execution for independent tasks)
## Examples
- input: $ARGUMENTS = "Add validation to UserController, ProductController, and OrderController"
- phase1: Agent Discovery: Selected @agent-code-master (for all 3 tasks)
- phase2: Requirements Plan: Scan controllers, identify validation needs
- approval1: User approves requirements plan
- phase3: Gather: Controller files, validation rules patterns
- phase4: 
Execution Plan:
(Mode: PARALLEL (tasks are independent, no file conflicts) + Batch 1 (parallel): +   Step 1: @agent-code-master - Add validation to UserController.php +   Step 2: @agent-code-master - Add validation to ProductController.php +   Step 3: @agent-code-master - Add validation to OrderController.php)

- approval2: User approves parallel execution plan
- phase5: Parallel execution: Batch 1 (3 steps concurrently)
- phase6: Report: 3/3 steps complete (parallel) - validation implemented ✓

# Response format
Structured output format for each phase
## Examples
- Phase headers with === markers
- Bullet-point plans with clear structure
- Approval checkpoints with ⚠️  and clear instructions
- Progress indicators: ▶️ ✅ ❌ 📋 📁 ⏱️
- File scope explicitly listed for each step
- No extraneous commentary during execution
- Clear status indicators for completion

# Directive
Execute ONLY specified task! Get approvals at checkpoints! Atomic tasks ONLY! Flexible execution (sequential by default, parallel when beneficial)! Vector memory MANDATORY for ALL agents! NO improvisation! Zero distractions! Strict plan adherence!

</command>