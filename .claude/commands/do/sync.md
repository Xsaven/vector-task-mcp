---
name: do:sync
description: "Direct execution command - Brain executes tasks directly without agent delegation"
---

<command>
<meta>
<id>do:sync</id>
<description>Direct execution command - Brain executes tasks directly without agent delegation</description>
</meta>
<purpose>Direct synchronous task execution by Brain without agent delegation. Uses Read/Edit/Write/Glob/Grep tools directly. Single approval gate. Best for: simple tasks, quick fixes, single-file changes, when agent overhead is unnecessary. Accepts $ARGUMENTS task description. Zero distractions, atomic execution, strict plan adherence.</purpose>
<purpose>Direct synchronous task execution by Brain without agent delegation. Uses Read/Edit/Write/Glob/Grep tools directly. Single approval gate. Best for: simple tasks, quick fixes, single-file changes, when agent overhead is unnecessary. Accepts $ARGUMENTS task description. Zero distractions, atomic execution, strict plan adherence.</purpose>
<iron_rules>
<rule id="zero-distractions" severity="critical">
<text>ZERO distractions - implement ONLY specified task from $ARGUMENTS. NO creative additions, NO unapproved features, NO scope creep.</text>
<why>Ensures focused execution and prevents feature drift</why>
<on_violation>Abort immediately. Return to approved plan.</on_violation>
</rule>
<rule id="no-delegation" severity="critical">
<text>Brain executes ALL steps directly. NO Task() delegation to agents. Use ONLY direct tools: Read, Edit, Write, Glob, Grep, Bash.</text>
<why>Sync mode is for direct execution without agent overhead</why>
<on_violation>Remove Task() calls. Execute directly.</on_violation>
</rule>
<rule id="single-approval-gate" severity="critical">
<text>User approval REQUIRED before execution. Present plan, WAIT for confirmation, then execute without interruption.</text>
<why>Single checkpoint for simple tasks - approve once, execute fully</why>
<on_violation>STOP. Wait for user approval before execution.</on_violation>
</rule>
<rule id="atomic-execution" severity="critical">
<text>Execute ONLY approved plan steps. NO improvisation, NO "while we're here" additions. Atomic changes only.</text>
<why>Maintains plan integrity and predictability</why>
<on_violation>Revert to approved plan. Resume approved steps only.</on_violation>
</rule>
<rule id="read-before-edit" severity="high">
<text>ALWAYS Read file BEFORE Edit/Write. Never modify files blindly.</text>
<why>Ensures accurate edits based on current file state</why>
<on_violation>Read file first, then proceed with edit.</on_violation>
</rule>
<rule id="vector-memory-integration" severity="high">
<text>Search vector memory BEFORE planning. Store learnings AFTER completion.</text>
<why>Leverages past solutions, builds knowledge base</why>
<on_violation>Include memory search in analysis, store insights after.</on_violation>
</rule>
<rule id="vector-task-workflow-mandatory" severity="critical">
<text>When $ARGUMENTS references a vector task (e.g., "task 15", "task:15", "task #15"), MUST: 1) Fetch task via task_get, 2) Fetch parent if exists, 3) Use task_start before execution, 4) Use task_finish on completion.</text>
<why>Vector tasks have structured workflow with status tracking. Ignoring statuses breaks task management.</why>
<on_violation>STOP. Fetch vector task first. Follow task lifecycle: start → execute → finish.</on_violation>
</rule>
</iron_rules>
<guidelines>
<guideline id="phase0-task-detection">
GOAL(Detect if $ARGUMENTS is a vector task reference and fetch task details)
<example>
<phase name="1">Parse $ARGUMENTS for task reference patterns: "task N", "task:N", "task #N", "task-N", "#N"</phase>
<phase name="2">IF($ARGUMENTS matches task reference pattern) → THEN → [Extract task_id from pattern → STORE-AS($IS_VECTOR_TASK = 'true') → STORE-AS($VECTOR_TASK_ID = '{extracted_id}') → mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → STORE-AS($VECTOR_TASK = '{task object with title, content, status, parent_id, priority, tags}') → IF($VECTOR_TASK.parent_id !== null) → THEN → [mcp__vector-task__task_get('{task_id: $VECTOR_TASK.parent_id}') → STORE-AS($PARENT_TASK = '{parent task for context}')] → END-IF → STORE-AS($TASK = '$VECTOR_TASK.title + $VECTOR_TASK.content') → OUTPUT(=== VECTOR TASK LOADED === Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Status: {$VECTOR_TASK.status} | Priority: {$VECTOR_TASK.priority} Parent: {$PARENT_TASK.title or "none"})] → END-IF</phase>
<phase name="3">IF($ARGUMENTS is plain description) → THEN → [STORE-AS($IS_VECTOR_TASK = 'false') → STORE-AS($TASK = '$ARGUMENTS')] → END-IF</phase>
</example>
</guideline>
<guideline id="phase1-context-analysis">
GOAL(Analyze task and gather context from conversation + memory)
<example>
<phase name="1">STORE-AS($TASK = 'User task from $ARGUMENTS')</phase>
<phase name="2">Analyze conversation: requirements, constraints, preferences, prior decisions</phase>
<phase name="3">mcp__vector-memory__search_memories('{query: "similar: {$TASK}", limit: 5, category: "code-solution"}')</phase>
<phase name="4">STORE-AS($PRIOR_SOLUTIONS = 'Relevant past approaches')</phase>
<phase name="5">OUTPUT(=== CONTEXT === Task: {$TASK} Prior solutions: {summary or "none found"})</phase>
</example>
</guideline>
<guideline id="phase1.5-material-gathering">
GOAL(Collect materials per plan and store to vector memory. NOTE: command `brain docs` returns file index (Path, Name, Description, etc.), then Read relevant files)
<example>
<phase name="1">FOREACH(scan_target in $REQUIREMENTS_PLAN.scan_targets) → [Context extraction from {scan_target} → STORE-AS($GATHERED_MATERIALS[{target}] = 'Extracted context')] → END-FOREACH</phase>
<phase name="2">IF($DOCS_SCAN_NEEDED === true) → THEN → [Bash(brain docs {keywords}) → [Find documentation index (returns: Path, Name, Description)] → END-Bash → STORE-AS($DOCS_INDEX = 'Documentation file index') → FOREACH(doc in $DOCS_INDEX) → [Read('{doc.path}')] → END-FOREACH → STORE-AS($DOCS_SCAN_FINDINGS = 'Documentation content')] → END-IF</phase>
<phase name="3">IF($WEB_RESEARCH_NEEDED === true) → THEN → [WebSearch(Research best practices for {$TASK}) → STORE-AS($WEB_RESEARCH_FINDINGS = 'External knowledge')] → END-IF</phase>
<phase name="4">mcp__vector-memory__store_memory('{content: "Context for {$TASK}\\n\\nMaterials: {summary}", category: "tool-usage", tags: ["do-command", "context-gathering"]}')</phase>
<phase name="5">OUTPUT(=== PHASE 1.5: MATERIALS GATHERED === Materials: {count} | Docs: {status} | Web: {status} Context stored to vector memory ✓)</phase>
</example>
</guideline>
<guideline id="phase2-exploration-planning">
GOAL(Explore codebase, identify targets, create execution plan)
<example>
<phase name="1">Identify files to examine based on task description</phase>
<phase name="2">Glob(Find relevant files: patterns based on task)</phase>
<phase name="3">Grep(Search for relevant code patterns)</phase>
<phase name="4">Read(Read identified files for context)</phase>
<phase name="5">STORE-AS($CONTEXT = '{files_found, code_patterns, current_state}')</phase>
<phase name="6">Create atomic execution plan: specific edits with exact changes</phase>
<phase name="7">STORE-AS($PLAN = '[{step_N, file, action: read|edit|write, description, exact_changes}, ...]')</phase>
<phase name="8">OUTPUT( === EXECUTION PLAN === Files: {list} Steps: {numbered_steps_with_descriptions}  ⚠️ APPROVAL REQUIRED ✅ approved/yes | ❌ no/modifications)</phase>
<phase name="9">WAIT for user approval</phase>
<phase name="10">VERIFY-SUCCESS(User approved)</phase>
<phase name="11">IF(rejected) → THEN → [Modify plan → Re-present → WAIT] → END-IF</phase>
</example>
</guideline>
<guideline id="phase3-direct-execution">
GOAL(Execute plan directly using Brain tools - no delegation)
<example>
<phase name="1">IF($IS_VECTOR_TASK === true) → THEN → [mcp__vector-task__task_start('{task_id: $VECTOR_TASK_ID}') → OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} started)] → END-IF</phase>
<phase name="2">FOREACH(step in $PLAN) → [OUTPUT(▶️ Step {N}: {step.description}) → IF(step.action === "read") → THEN → [Read('{step.file}') → STORE-AS($FILE_CONTENT[{N}] = 'File content')] → END-IF → IF(step.action === "edit") → THEN → [Read('{step.file}') → Edit('{step.file}', '{old_string}', '{new_string}')] → END-IF → IF(step.action === "write") → THEN → [Write('{step.file}', '{content}')] → END-IF → STORE-AS($STEP_RESULTS[{N}] = 'Result') → OUTPUT(✅ Step {N} complete)] → END-FOREACH</phase>
<phase name="3">IF(step fails) → THEN → [Log error → Offer: Retry / Skip / Abort → WAIT for user decision] → END-IF</phase>
</example>
</guideline>
<guideline id="phase4-completion">
GOAL(Report results and store learnings to vector memory)
<example>
<phase name="1">STORE-AS($SUMMARY = '{completed_steps, files_modified, outcome}')</phase>
<phase name="2">mcp__vector-memory__store_memory('{content: "Completed: {$TASK}\\n\\nApproach: {steps}\\n\\nFiles: {list}\\n\\nLearnings: {insights}", category: "code-solution", tags: ["do:sync", "completed"]}')</phase>
<phase name="3">IF($IS_VECTOR_TASK === true AND status === SUCCESS) → THEN → [mcp__vector-task__task_finish('{task_id: $VECTOR_TASK_ID}') → OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} completed ✓)] → END-IF</phase>
<phase name="4">IF($IS_VECTOR_TASK === true AND status === PARTIAL) → THEN → [mcp__vector-task__task_comment('{task_id: $VECTOR_TASK_ID, comment: "Partial completion: {completed}/{total} steps. Remaining: {list}", append: true}') → OUTPUT(📋 Vector task #{$VECTOR_TASK_ID} progress saved (partial))] → END-IF</phase>
<phase name="5">OUTPUT( === COMPLETE === Task: {$TASK} | Status: {SUCCESS/PARTIAL/FAILED} ✓ Steps: {completed}/{total} | 📁 Files: {count} {outcomes})</phase>
</example>
</guideline>
<guideline id="error-handling">
<text>Direct error handling without agent fallback</text>
<example>
<phase name="1">IF(vector task not found) → THEN → [Report: "Vector task #{id} not found" → Suggest: Check task ID with mcp__vector-task__task_list → Abort command] → END-IF</phase>
<phase name="2">IF(vector task already completed) → THEN → [Report: "Vector task #{id} already has status: completed" → Ask user: "Do you want to re-execute this task?" → WAIT for user decision] → END-IF</phase>
<phase name="3">IF(file not found) → THEN → [Report: "File not found: {path}" → Offer: Create new file / Specify correct path / Abort] → END-IF</phase>
<phase name="4">IF(edit conflict) → THEN → [Report: "old_string not found in file" → Re-read file, adjust edit, retry] → END-IF</phase>
<phase name="5">IF(user rejects plan) → THEN → [Accept modifications → Rebuild plan → Re-present for approval] → END-IF</phase>
</example>
</guideline>
<guideline id="example-simple-fix">
SCENARIO(Simple bug fix)
<example>
<phase name="input">"Fix typo in UserController.php line 42"</phase>
<phase name="plan">1 step: Edit UserController.php</phase>
<phase name="execution">Read → Edit → Done</phase>
<phase name="result">1/1 ✓</phase>
</example>
</guideline>
<guideline id="example-add-method">
SCENARIO(Add method to existing class)
<example>
<phase name="input">"Add getFullName() method to User model"</phase>
<phase name="plan">2 steps: Read User.php → Edit to add method</phase>
<phase name="execution">Read → Edit → Done</phase>
<phase name="result">2/2 ✓</phase>
</example>
</guideline>
<guideline id="example-config-change">
SCENARIO(Configuration update)
<example>
<phase name="input">"Change cache driver to redis in config"</phase>
<phase name="plan">2 steps: Read config/cache.php → Edit driver value</phase>
<phase name="execution">Read → Edit → Done</phase>
<phase name="result">2/2 ✓</phase>
</example>
</guideline>
<guideline id="example-vector-task">
SCENARIO(Execute from vector task reference)
<example>
<phase name="input">"task 5" or "task:5" or "#5"</phase>
<phase name="detection">Pattern matched → task_get(5) → Load task + parent</phase>
<phase name="context">Task: "Fix null check in helper" | Parent: "Bug fixes sprint"</phase>
<phase name="flow">Task Detection → Context → Plan ✓ → task_start → Execute → task_finish → Complete</phase>
<phase name="result">Vector task #5 completed ✓</phase>
</example>
</guideline>
<guideline id="sync-vs-async">
<text>When to use /do:sync vs /do:async</text>
<example>
<phase name="USE /do:sync">Simple tasks, single-file changes, quick fixes, config updates, typo fixes, adding small methods</phase>
<phase name="USE /do:async">Complex multi-file tasks, tasks requiring research, architecture changes, tasks benefiting from specialized agents</phase>
</example>
</guideline>
<guideline id="response-format">
<text>=== headers | ⚠️ single approval | ▶️✅ progress | 📁 files | Direct execution, no filler</text>
</guideline>
</guidelines>
</command>