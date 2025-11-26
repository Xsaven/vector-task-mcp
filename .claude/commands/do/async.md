---
name: do:async
description: "Multi-agent orchestration command for flexible task execution (sequential/parallel) with user approval gates"
---

<command>
<meta>
<id>do:async</id>
<description>Multi-agent orchestration command for flexible task execution (sequential/parallel) with user approval gates</description>
</meta>
<purpose>Coordinates flexible agent execution (sequential by default, parallel when beneficial) with approval checkpoints and comprehensive vector memory integration. Agents communicate through vector memory for knowledge continuity. Accepts $ARGUMENTS task description. Zero distractions, atomic tasks only, strict plan adherence.</purpose>
<purpose>Defines the do:async command protocol for multi-agent orchestration with flexible execution modes, user approval gates, and vector memory integration. Ensures zero distractions, atomic tasks, and strict plan adherence for reliable task execution.</purpose>
<iron_rules>
<rule id="entry-point-blocking" severity="critical">
<text>ON RECEIVING $ARGUMENTS: Your FIRST output MUST be "=== DO:ASYNC ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain list:masters), code generation, file analysis, problem solving, implementation thinking.</text>
<why>Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.</why>
<on_violation>STOP IMMEDIATELY. Delete any tool calls. Output "=== DO:ASYNC ACTIVATED ===" and restart from Phase 0.</on_violation>
</rule>
<rule id="zero-distractions" severity="critical">
<text>ZERO distractions - implement ONLY specified task from $ARGUMENTS. NO creative additions, NO unapproved features, NO scope creep.</text>
<why>Ensures focused execution and prevents feature drift</why>
<on_violation>Abort immediately. Return to approved plan.</on_violation>
</rule>
<rule id="approval-gates-mandatory" severity="critical">
<text>User approval REQUIRED at Requirements Analysis gate and Execution Planning gate. NEVER proceed without explicit confirmation.</text>
<why>Maintains user control and prevents unauthorized execution</why>
<on_violation>STOP. Wait for user approval before continuing.</on_violation>
</rule>
<rule id="atomic-tasks-only" severity="critical">
<text>Each agent task MUST be small and focused: maximum 1-2 files per agent invocation. NO large multi-file changes.</text>
<why>Prevents complexity, improves reliability, enables precise tracking</why>
<on_violation>Break task into smaller pieces. Re-plan with atomic steps.</on_violation>
</rule>
<rule id="no-improvisation" severity="critical">
<text>Execute ONLY approved plan steps. NO improvisation, NO "while we're here" additions, NO proactive suggestions during execution.</text>
<why>Maintains plan integrity and predictability</why>
<on_violation>Revert to last approved checkpoint. Resume approved steps only.</on_violation>
</rule>
<rule id="execution-mode-flexible" severity="high">
<text>Execute agents sequentially BY DEFAULT. Allow parallel execution when: 1) tasks are independent (no file/context conflicts), 2) user explicitly requests parallel mode, 3) optimization benefits outweigh tracking complexity.</text>
<why>Balances safety with performance optimization</why>
<on_violation>Validate task independence before parallel execution. Fallback to sequential if conflicts detected.</on_violation>
</rule>
<rule id="vector-memory-mandatory" severity="high">
<text>ALL agents MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.</text>
<why>Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps</why>
<on_violation>Include explicit vector memory instructions in agent Task() delegation.</on_violation>
</rule>
<rule id="conversation-context-awareness" severity="high">
<text>ALWAYS analyze conversation context BEFORE planning. User may have discussed requirements, constraints, preferences, or decisions in previous messages.</text>
<why>Prevents ignoring critical information already provided by user in conversation</why>
<on_violation>Review conversation history before proceeding with task analysis.</on_violation>
</rule>
<rule id="vector-task-workflow-mandatory" severity="critical">
<text>When $ARGUMENTS references a vector task (e.g., "task 15", "task:15", "task #15"), MUST: 1) Fetch task via task_get, 2) Fetch parent if exists, 3) Use task_start before execution, 4) Use task_finish on completion.</text>
<why>Vector tasks have structured workflow with status tracking. Ignoring statuses breaks task management.</why>
<on_violation>STOP. Fetch vector task first. Follow task lifecycle: start → execute → finish.</on_violation>
</rule>
<rule id="full-workflow-mandatory" severity="critical">
<text>ALL requests (vector task OR plain description) MUST follow complete workflow: Phase 0 (Context) → Phase 1 (Discovery) → Phase 2 (Requirements + APPROVAL) → Phase 3 (Gathering) → Phase 4 (Planning + APPROVAL) → Phase 5 (Execution via agents) → Phase 6 (Completion). NEVER skip phases. NEVER execute directly without agent delegation.</text>
<why>Workflow ensures quality, user control, and proper orchestration. Skipping phases leads to poor results, missed context, and violated user trust.</why>
<on_violation>STOP. Return to Phase 0. Follow workflow sequentially. Present approval gates. Delegate via Task().</on_violation>
</rule>
<rule id="never-execute-directly" severity="critical">
<text>Brain NEVER executes implementation tasks directly. For ANY $ARGUMENTS (vector task or plain text): MUST delegate to agents via Task(). Brain only: analyzes, plans, presents approvals, delegates, validates results.</text>
<why>Direct execution violates orchestration model, bypasses agent expertise, wastes Brain tokens on execution instead of coordination.</why>
<on_violation>STOP. Identify required agent from brain list:masters. Delegate via Task(@agent-name, task).</on_violation>
</rule>
<rule id="no-direct-file-tools" severity="critical">
<text>FORBIDDEN: Brain NEVER calls Glob, Grep, Read, Edit, Write directly. ALL file operations MUST be delegated to agents via Task().</text>
<why>Direct tool calls are expensive, bypass agent expertise, and violate orchestration model. Each file operation costs tokens that agents handle more efficiently.</why>
<on_violation>STOP. Remove direct tool call. Delegate to appropriate agent: ExploreMaster (search/read), code agents (edit/write).</on_violation>
</rule>
<rule id="orchestration-only" severity="critical">
<text>Brain role is ORCHESTRATION ONLY. Permitted: Task(), vector MCP, brain CLI (docs, list:masters). Everything else → delegate.</text>
<why>Brain is conductor, not musician. Agents execute, Brain coordinates.</why>
<on_violation>Identify task type → Select agent → Delegate via Task().</on_violation>
</rule>
<rule id="one-agent-one-file" severity="critical">
<text>Each programming subtask = separate agent invocation. One agent, one file change. NO multi-file edits in single delegation.</text>
<why>Atomic changes enable precise tracking, easier rollback, clear accountability.</why>
<on_violation>Split into multiple Task() calls. One agent per file modification.</on_violation>
</rule>
</iron_rules>
<guidelines>
<guideline id="phase-minus1-task-detection">
GOAL(Detect if $ARGUMENTS is a vector task reference and fetch task details)
<example>
<phase name="1">Parse $ARGUMENTS for task reference patterns: "task N", "task:N", "task #N", "task-N", "#N"</phase>
<phase name="2">IF($ARGUMENTS matches task reference pattern) → THEN → [Extract task_id from pattern → STORE-AS($IS_VECTOR_TASK = 'true') → STORE-AS($VECTOR_TASK_ID = '{extracted_id}') → mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → STORE-AS($VECTOR_TASK = '{task object with title, content, status, parent_id, priority, tags}') → IF($VECTOR_TASK.parent_id !== null) → THEN → [mcp__vector-task__task_get('{task_id: $VECTOR_TASK.parent_id}') → STORE-AS($PARENT_TASK = '{parent task for context}')] → END-IF → STORE-AS($TASK_DESCRIPTION = '$VECTOR_TASK.title + $VECTOR_TASK.content') → OUTPUT(=== VECTOR TASK LOADED === Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Status: {$VECTOR_TASK.status} | Priority: {$VECTOR_TASK.priority} Parent: {$PARENT_TASK.title or "none"})] → END-IF</phase>
<phase name="3">IF($ARGUMENTS is plain description) → THEN → [STORE-AS($IS_VECTOR_TASK = 'false') → STORE-AS($TASK_DESCRIPTION = '$ARGUMENTS')] → END-IF</phase>
</example>
</guideline>
<guideline id="phase0-context-analysis">
GOAL(Extract task insights from conversation history before planning)
<example>
<phase name="1">STORE-AS($TASK_DESCRIPTION = 'User task from $ARGUMENTS')</phase>
<phase name="2">Analyze conversation context: requirements mentioned, constraints discussed, user preferences, prior decisions, related code/files referenced</phase>
<phase name="3">STORE-AS($CONVERSATION_CONTEXT = '{requirements, constraints, preferences, decisions, references}')</phase>
<phase name="4">IF(conversation has relevant context) → THEN → [Integrate context into task understanding → Note: Use conversation insights throughout all phases] → END-IF</phase>
<phase name="5">OUTPUT(=== PHASE 0: CONTEXT ANALYSIS === Task: {$TASK_DESCRIPTION} Context: {summary of relevant conversation info})</phase>
</example>
</guideline>
<guideline id="phase1-agent-discovery">
GOAL(Discover agents leveraging conversation context + vector memory)
<example>
<phase name="1">mcp__vector-memory__search_memories('{query: "similar: {$TASK_DESCRIPTION}", limit: 5, category: "code-solution,architecture"}')</phase>
<phase name="2">STORE-AS($PAST_SOLUTIONS = 'Past approaches')</phase>
<phase name="3">Bash(brain list:masters) → [brain list:masters] → END-Bash</phase>
<phase name="4">STORE-AS($AVAILABLE_AGENTS = 'Agents list')</phase>
<phase name="5">Match task to agents: $TASK_DESCRIPTION + $CONVERSATION_CONTEXT + $PAST_SOLUTIONS</phase>
<phase name="6">STORE-AS($RELEVANT_AGENTS = '[{agent, capability, rationale}, ...]')</phase>
<phase name="7">OUTPUT(=== PHASE 1: AGENT DISCOVERY === Agents: {selected} | Context: {conversation insights applied})</phase>
</example>
</guideline>
<guideline id="phase2-requirements-analysis-approval">
GOAL(Create requirements plan leveraging conversation + memory + GET USER APPROVAL)
<example>
<phase name="1">mcp__vector-memory__search_memories('{query: "patterns: {task_domain}", limit: 5, category: "learning,architecture"}')</phase>
<phase name="2">STORE-AS($IMPLEMENTATION_PATTERNS = 'Past patterns')</phase>
<phase name="3">Analyze: $TASK_DESCRIPTION + $CONVERSATION_CONTEXT + $PAST_SOLUTIONS + $IMPLEMENTATION_PATTERNS</phase>
<phase name="4">Determine needs: scan targets, web research (if non-trivial), docs scan (if architecture-related)</phase>
<phase name="5">STORE-AS($REQUIREMENTS_PLAN = '{scan_targets, web_research, docs_scan, conversation_insights, memory_learnings}')</phase>
<phase name="6">OUTPUT( === PHASE 2: REQUIREMENTS ANALYSIS === Context: {conversation insights} | Memory: {key learnings} Scanning: {targets} | Research: {status} | Docs: {status}  ⚠️  APPROVAL CHECKPOINT #1 ✅ approved/yes | ❌ no/modifications)</phase>
<phase name="7">WAIT for user approval</phase>
<phase name="8">VERIFY-SUCCESS(User approved)</phase>
<phase name="9">IF(rejected) → THEN → [Modify plan → Re-present → WAIT] → END-IF</phase>
</example>
</guideline>
<guideline id="phase3-material-gathering">
GOAL(Collect materials via agents. Brain permitted: brain docs (index only, few tokens). ALL file reading → delegate to agents.)
<example>
<phase name="1">FOREACH(scan_target in $REQUIREMENTS_PLAN.scan_targets) → [Task(@agent-explore 'Extract context from {scan_target}. Store findings to vector memory.') → STORE-AS($GATHERED_MATERIALS[{target}] = 'Agent-extracted context')] → END-FOREACH</phase>
<phase name="2">IF($DOCS_SCAN_NEEDED === true) → THEN → [Bash(brain docs {keywords}) → [Get documentation INDEX only (Path, Name, Description)] → END-Bash → STORE-AS($DOCS_INDEX = 'Documentation file paths') → Task(@agent-explore 'Read and summarize documentation files: {$DOCS_INDEX paths}. Store to vector memory.') → STORE-AS($DOCS_SCAN_FINDINGS = 'Agent-summarized documentation')] → END-IF</phase>
<phase name="3">IF($WEB_RESEARCH_NEEDED === true) → THEN → [Task(@agent-web-research-master 'Research best practices for {$TASK_DESCRIPTION}. Store findings to vector memory.') → STORE-AS($WEB_RESEARCH_FINDINGS = 'External knowledge')] → END-IF</phase>
<phase name="4">STORE-AS($CONTEXT_PACKAGES = '{agent_name: {context, materials, task_domain}, ...}')</phase>
<phase name="5">mcp__vector-memory__store_memory('{content: "Context for {$TASK_DESCRIPTION}\\n\\nMaterials: {summary}", category: "tool-usage", tags: ["do-command", "context-gathering"]}')</phase>
<phase name="6">OUTPUT(=== PHASE 3: MATERIALS GATHERED === Materials: {count} | Docs: {status} | Web: {status} Context stored to vector memory ✓)</phase>
</example>
</guideline>
<guideline id="phase4-execution-planning-approval">
GOAL(Create atomic plan leveraging past execution patterns, analyze dependencies, and GET USER APPROVAL)
<example>
<phase name="1">mcp__vector-memory__search_memories('{query: "execution approach for {task_type}", limit: 5, category: "code-solution"}')</phase>
<phase name="2">STORE-AS($EXECUTION_PATTERNS = 'Past successful execution approaches')</phase>
<phase name="3">Create plan: atomic steps (≤2 files each), logical order, informed by $EXECUTION_PATTERNS</phase>
<phase name="4">Analyze step dependencies: file conflicts, context dependencies, data flow</phase>
<phase name="5">Determine execution mode: sequential (default/safe) OR parallel (independent tasks/user request/optimization)</phase>
<phase name="6">IF(parallel possible AND beneficial) → THEN → [Group independent steps into parallel batches → Validate NO conflicts: 1) File: same file in multiple steps, 2) Context: step B needs output of step A, 3) Resource: same API/DB/external → STORE-AS($EXECUTION_MODE = 'parallel') → STORE-AS($PARALLEL_GROUPS = '[[step1, step2], [step3], ...]')] → END-IF</phase>
<phase name="7">IF(NOT parallel OR dependencies detected) → THEN → [STORE-AS($EXECUTION_MODE = 'sequential')] → END-IF</phase>
<phase name="8">STORE-AS($EXECUTION_PLAN = '{steps: [{step_number, agent_name, task_description, file_scope: [≤2 files], memory_search_query, expected_outcome}, ...], total_steps: N, execution_mode: "sequential|parallel", parallel_groups: [...]}')</phase>
<phase name="9">VERIFY-SUCCESS(Each step has ≤ 2 files)</phase>
<phase name="10">VERIFY-SUCCESS(Parallel groups have NO conflicts)</phase>
<phase name="11">OUTPUT( === PHASE 4: EXECUTION PLAN === Task: {$TASK_DESCRIPTION} | Steps: {N} | Mode: {execution_mode} Learned from: {$EXECUTION_PATTERNS summary}  {Step-by-step breakdown with files and memory search queries} {If parallel: show grouped batches}  ⚠️  APPROVAL CHECKPOINT #2 ✅ Type "approved" or "yes" to begin. ❌ Type "no" or provide modifications.)</phase>
<phase name="12">WAIT for user approval</phase>
<phase name="13">VERIFY-SUCCESS(User confirmed approval)</phase>
<phase name="14">IF(user rejected) → THEN → [Accept modifications → Update plan → Verify atomic + dependencies → Re-present → WAIT] → END-IF</phase>
</example>
</guideline>
<guideline id="phase5-flexible-execution">
GOAL(Execute plan with optimal mode (sequential OR parallel))
<example>
<phase name="1">IF($IS_VECTOR_TASK === true) → THEN → [mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "in_progress"}') → OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} started)] → END-IF</phase>
<phase name="2">Initialize: current_step = 1</phase>
<phase name="3">IF($EXECUTION_PLAN.execution_mode === "sequential") → THEN → [SEQUENTIAL MODE: Execute steps one-by-one → FOREACH(step in $EXECUTION_PLAN.steps) → [OUTPUT(▶️ Step {N}/{total}: @agent-{step.agent_name} | 📁 {step.file_scope}) → Delegate via Task() with agent-memory-pattern (BEFORE→DURING→AFTER) → Task(Task(@agent-{name}, {task + memory_search_query + context})) → STORE-AS($STEP_RESULTS[{N}] = 'Result') → OUTPUT(✅ Step {N} complete)] → END-FOREACH] → END-IF</phase>
<phase name="4">IF($EXECUTION_PLAN.execution_mode === "parallel") → THEN → [PARALLEL MODE: Execute independent steps concurrently → FOREACH(group in $EXECUTION_PLAN.parallel_groups) → [OUTPUT(🚀 Batch {N}: {count} steps) → Launch ALL steps CONCURRENTLY via multiple Task() calls → Each task follows agent-memory-pattern → WAIT for ALL tasks in batch to complete → STORE-AS($BATCH_RESULTS[{N}] = 'Batch results') → OUTPUT(✅ Batch {N} complete)] → END-FOREACH] → END-IF</phase>
<phase name="5">IF(step fails) → THEN → [Store failure to memory → Offer: Retry / Skip / Abort] → END-IF</phase>
</example>
</guideline>
<guideline id="phase6-completion-report">
GOAL(Report results and store comprehensive learnings to vector memory)
<example>
<phase name="1">STORE-AS($COMPLETION_SUMMARY = '{completed_steps, files_modified, outcomes, learnings}')</phase>
<phase name="2">mcp__vector-memory__store_memory('{content: "Completed: {$TASK_DESCRIPTION}\\n\\nApproach: {summary}\\n\\nSteps: {outcomes}\\n\\nLearnings: {insights}\\n\\nFiles: {list}", category: "code-solution", tags: ["do-command", "completed"]}')</phase>
<phase name="3">IF($IS_VECTOR_TASK === true AND status === SUCCESS) → THEN → [mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, status: "completed"}') → OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} completed ✓)] → END-IF</phase>
<phase name="4">IF($IS_VECTOR_TASK === true AND status === PARTIAL) → THEN → [mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "Partial completion: {completed}/{total} steps. Remaining: {list}", append_comment: true}') → OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} progress saved (partial))] → END-IF</phase>
<phase name="5">OUTPUT( === EXECUTION COMPLETE === Task: {$TASK_DESCRIPTION} | Status: {SUCCESS/PARTIAL/FAILED} ✓ Steps: {completed}/{total} | 📁 Files: {count} | 💾 Learnings stored to memory {step_outcomes})</phase>
<phase name="6">IF(partial) → THEN → [Store partial state → List remaining → Suggest resumption] → END-IF</phase>
</example>
</guideline>
<guideline id="agent-memory-instructions">
<text>MANDATORY vector memory pattern for ALL agents</text>
<example>
<phase name="1">
BEFORE TASK:
(Execute: mcp__vector-memory__search_memories(query: "{relevant}", limit: 5) + Review: Analyze results for patterns, solutions, learnings + Apply: Incorporate insights into approach)
</phase>
<phase name="2">
DURING TASK:
(Focus: Execute ONLY assigned task within file scope + Atomic: Respect 1-2 file limit strictly)
</phase>
<phase name="3">
AFTER TASK:
(Document: Summarize what was done, how it worked, key insights + Execute: mcp__vector-memory__store_memory(content: "{what+how+insights}", category: "{appropriate}", tags: [...]) + Verify: Confirm storage successful)
</phase>
<phase name="4">CRITICAL: Vector memory is the communication channel between agents. Your learnings enable the next agent!</phase>
</example>
</guideline>
<guideline id="error-handling">
<text>Graceful error handling with recovery options</text>
<example>
<phase name="1">IF(vector task not found) → THEN → [Report: "Vector task #{id} not found" → Suggest: Check task ID with mcp__vector-task__task_list → Abort command] → END-IF</phase>
<phase name="2">IF(vector task already completed) → THEN → [Report: "Vector task #{id} already has status: completed" → Ask user: "Do you want to re-execute this task?" → WAIT for user decision] → END-IF</phase>
<phase name="3">IF(no agents available) → THEN → [Report: "No agents found via brain list:masters" → Suggest: Run /init-agents first → Abort command] → END-IF</phase>
<phase name="4">IF(user rejects requirements plan) → THEN → [Accept modifications → Rebuild requirements plan → Re-submit for approval] → END-IF</phase>
<phase name="5">IF(user rejects execution plan) → THEN → [Accept modifications → Rebuild execution plan → Verify atomic task constraints → Re-submit for approval] → END-IF</phase>
<phase name="6">IF(agent execution fails) → THEN → [Log: "Step {N} failed: {error}" → Offer options: →   1. Retry current step →   2. Skip and continue →   3. Abort remaining steps → WAIT for user decision] → END-IF</phase>
<phase name="7">IF(documentation scan fails) → THEN → [Log: "brain docs command failed or no documentation found" → Proceed without documentation context → Note: "Documentation context unavailable"] → END-IF</phase>
<phase name="8">IF(web research timeout) → THEN → [Log: "Web research timed out - continuing without external knowledge" → Proceed with local context only] → END-IF</phase>
<phase name="9">IF(context gathering fails) → THEN → [Log: "Failed to gather {context_type}" → Proceed with available context → Warn: "Limited context may affect quality"] → END-IF</phase>
</example>
</guideline>
<guideline id="constraints-validation">
<text>Enforcement of critical constraints throughout execution</text>
<example>
<phase name="1">Before Requirements Analysis: Verify $ARGUMENTS is not empty</phase>
<phase name="2">Before Phase 2 → Phase 3 transition: Verify user approval received</phase>
<phase name="3">Before Phase 4 → Phase 5 transition: Verify user approval received</phase>
<phase name="4">During Execution Planning: Verify each step has ≤ 2 files in scope</phase>
<phase name="5">During Execution: Verify dependencies respected (sequential: step order, parallel: no conflicts)</phase>
<phase name="6">Throughout: NO unapproved steps allowed</phase>
<phase name="7">VERIFY-SUCCESS(approval_checkpoints_passed = 2 all_tasks_atomic = true (≤ 2 files each) execution_mode = sequential OR parallel (validated) improvisation_count = 0)</phase>
</example>
</guideline>
<guideline id="example-simple">
SCENARIO(Simple single-agent task)
<example>
<phase name="input">"Fix authentication bug in LoginController.php"</phase>
<phase name="flow">Context → Discovery → Requirements ✓ → Gather → Plan ✓ → Execute (1 step) → Complete</phase>
</example>
</guideline>
<guideline id="example-sequential">
SCENARIO(Complex multi-agent sequential task)
<example>
<phase name="input">"Add Laravel rate limiting to API endpoints"</phase>
<phase name="agents">@web-research-master, @code-master, @documentation-master</phase>
<phase name="plan">4 steps: Middleware → Kernel → Routes → Docs</phase>
<phase name="execution">Sequential: 1→2→3→4 (dependencies between steps)</phase>
<phase name="result">4/4 ✓</phase>
</example>
</guideline>
<guideline id="example-parallel">
SCENARIO(Parallel execution for independent tasks)
<example>
<phase name="input">"Add validation to UserController, ProductController, OrderController"</phase>
<phase name="analysis">3 independent files, no conflicts</phase>
<phase name="plan">Mode: PARALLEL, Batch 1: [Step1, Step2, Step3]</phase>
<phase name="execution">Concurrent: 3 agents simultaneously</phase>
<phase name="result">3/3 ✓ (faster than sequential)</phase>
</example>
</guideline>
<guideline id="example-vector-task">
SCENARIO(Execute from vector task reference)
<example>
<phase name="input">"task 15" or "task:15" or "#15"</phase>
<phase name="detection">Pattern matched → task_get(15) → Load task + parent</phase>
<phase name="context">Task: "Add user avatar upload" | Parent: "User profile feature"</phase>
<phase name="flow">Task Detection → Context → Discovery → Requirements ✓ → Gather → Plan ✓ → task_start → Execute → task_finish → Complete</phase>
<phase name="result">Vector task #15 completed ✓</phase>
</example>
</guideline>
<guideline id="response-format">
<text>=== headers | ⚠️ approval gates | ▶️✅❌ progress | 📁 file scope | No filler</text>
</guideline>
</guidelines>
</command>