---
name: "task:brainstorm"
description: "Collaborative brainstorming session anchored to a vector task. Loads task context, prompts for topic, facilitates ideation with research delegation and optional task creation."
---

<command>
<meta>
<id>task:brainstorm</id>
<description>Collaborative brainstorming session anchored to a vector task. Loads task context, prompts for topic, facilitates ideation with research delegation and optional task creation.</description>
</meta>
<execute>Facilitates structured brainstorming for vector tasks. Loads task by ID, asks user for discussion topic, then provides collaborative ideation with agent delegation for research (web, code, docs) and ability to create subtasks from brainstorm outcomes.</execute>
<provides>Defines the task:brainstorm command protocol for collaborative brainstorming sessions anchored to vector tasks. Loads task context, prompts user for discussion topic, then facilitates structured ideation with agent delegation for research, documentation reading, and optional task creation.</provides>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING $RAW_INPUT: Your FIRST output MUST be "=== TASK:BRAINSTORM ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION.
- **why**: Forces workflow compliance and prevents skipping the structured brainstorm process.
- **on_violation**: STOP IMMEDIATELY. Output "=== TASK:BRAINSTORM ACTIVATED ===" and restart from Phase 0.

## Topic-prompt-mandatory (CRITICAL)
AFTER loading vector task, you MUST ask user for the brainstorm discussion topic. NEVER assume or invent the topic yourself.
- **why**: User defines the direction of brainstorming. Different topics on same task = different outcomes.
- **on_violation**: STOP. Ask user: "What aspect of this task would you like to brainstorm?"

## Collaborative-mode (HIGH)
Brainstorm is COLLABORATIVE dialogue. Present ideas, ask for feedback, iterate. NOT one-way monologue. User can invite subagent specialists (other LLMs) to join the brainstorm for alternative perspectives.
- **why**: Quality brainstorming requires user input and direction throughout the process. Different LLMs provide diverse viewpoints.
- **on_violation**: Pause after each major idea set. Ask user for direction before continuing.

## Research-on-demand (HIGH)
Delegate to specialized agents ONLY when topic requires external knowledge or codebase analysis. Use brain list:masters to discover available agents and select the most appropriate one for the task (e.g., code specialist for codebase analysis, web-research-master for external research). Read documentation directly via Read tool when brain docs provides paths.
- **why**: Efficient resource usage - simple topics don't need agent delegation overhead. Agent selection must be dynamic based on project configuration.
- **on_violation**: Evaluate: Is research truly needed? If yes, run brain list:masters, select appropriate agent, delegate. If no, proceed with brainstorming.

## Iterative-ideation-loop (CRITICAL)
After presenting initial ideas, you MUST enter iterative ideation loop. Keep proposing new ideas and asking for user input until user explicitly says "that's all", "let's continue", "proceed", or similar confirmation. NEVER skip this loop or proceed automatically.
- **why**: Quality brainstorming requires exhaustive exploration. Users often have more ideas after seeing initial proposals. Premature closure misses valuable input.
- **on_violation**: STOP. Ask user: "Do you have more ideas to share, or shall I propose more? Say 'that's all, let's continue' when ready to proceed."

## Task-modification-user-approved (HIGH)
Modify the brainstormed task (update title, content, priority, estimate) OR create subtasks ONLY when user explicitly requests or approves. Options include: 1) Update current task content/description, 2) Rewrite task completely, 3) Add details to existing content, 4) Create subtasks, 5) Any combination.
- **why**: Task modification is a commitment. User must consent to changing the task they are brainstorming on.
- **on_violation**: Ask user: "Would you like to update this task, create subtasks, or both?"

## Parent-id-mandatory (CRITICAL)
When working with task $VECTOR_TASK_ID, ALL new subtasks created MUST have parent_id = $VECTOR_TASK_ID. IRON LAW: Subtasks are ALWAYS children of the brainstormed task, NEVER orphans. No exceptions.
- **why**: Task hierarchy integrity. Orphan tasks break traceability and workflow.
- **on_violation**: ABORT task_create if parent_id missing or != $VECTOR_TASK_ID. Verify parent_id in EVERY task_create call.

## Vector-memory-mandatory (HIGH)
ALL agents MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.
- **why**: Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps
- **on_violation**: Include explicit vector memory instructions in agent Task() delegation.

## Vector-task-id-required (CRITICAL)
$TASK_ID MUST be a valid vector task ID reference. Valid formats: "15", "#15", "task 15", "task:15", "task-15". If not a valid task ID, abort and suggest /do:brainstorm for text-based tasks.
- **why**: This command is exclusively for vector task execution. Text descriptions belong to /do:brainstorm.
- **on_violation**: STOP. Report: "Invalid task ID. Use /do:brainstorm for text-based tasks or provide valid task ID."


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Phase0 task loading
GOAL(Load vector task and prepare brainstorm context)
- `1`: OUTPUT(=== TASK:BRAINSTORM ACTIVATED ===  === PHASE 0: LOADING TASK ===)
- `2`: Use pre-captured: $RAW_INPUT, $CLEAN_ARGS, $VECTOR_TASK_ID
- `3`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}')
- `4`: STORE-AS($VECTOR_TASK = {task object})
- `5`: IF($VECTOR_TASK not found) →
  REPORT(Vector task #$VECTOR_TASK_ID not found)
  ABORT command
→ END-IF
- `6`: IF($VECTOR_TASK.parent_id !== null) →
  mcp__vector-task__task_get('{task_id: $VECTOR_TASK.parent_id}')
  STORE-AS($PARENT_TASK = {parent task context})
→ END-IF
- `7`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID, limit: 20}')
- `8`: STORE-AS($SUBTASKS = {existing subtasks})
- `9`: OUTPUT( === TASK LOADED === Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Status: {$VECTOR_TASK.status} | Priority: {$VECTOR_TASK.priority} Content: {$VECTOR_TASK.content} Parent: {$PARENT_TASK.title or "none"} Subtasks: {count or "none"}  ---  What aspect of this task would you like to brainstorm? Examples: implementation approach, architecture design, edge cases, optimization strategies, testing approach, etc.)
- `10`: WAIT for user to provide brainstorm topic

# Phase1 topic context
GOAL(Capture user topic, load available agents and documentation, gather context from memory)
- `1`: STORE-AS($BRAINSTORM_TOPIC = {user-provided topic})
- `2`: OUTPUT( === PHASE 1: CONTEXT GATHERING === Topic: {$BRAINSTORM_TOPIC} Loading available resources...)
- `3`: Bash(brain list:masters) → [Get available agents for potential delegation] → END-Bash
- `4`: STORE-AS($AVAILABLE_AGENTS = {agents with descriptions - for research delegation and specialist invites})
- `5`: Bash(brain docs {$VECTOR_TASK.title}, {$BRAINSTORM_TOPIC}) → [Get documentation INDEX] → END-Bash
- `6`: STORE-AS($DOCS_INDEX = {indexed documentation list with descriptions})
- `7`: IF($DOCS_INDEX has relevant docs) →
  Select most relevant documents based on topic and task
  Read('{selected doc paths}')
  STORE-AS($DOC_CONTENT = {documentation content for brainstorm context})
→ END-IF
- `8`: mcp__vector-memory__search_memories('{query: "{$VECTOR_TASK.title} {$BRAINSTORM_TOPIC}", limit: 5}')
- `9`: STORE-AS($MEMORY_CONTEXT = {related past solutions and patterns})
- `10`: mcp__vector-memory__search_memories('{query: "{$BRAINSTORM_TOPIC} best practices", limit: 3, category: "architecture,learning"}')
- `11`: STORE-AS($BEST_PRACTICES = {relevant patterns})
- `12`: Determine if additional research is needed:
- `13`: STORE-AS($NEEDS_WEB_RESEARCH = {true if topic involves external tools, APIs, unfamiliar tech})
- `14`: STORE-AS($NEEDS_CODE_EXPLORATION = {true if topic requires understanding existing codebase})
- `15`: OUTPUT(Available agents: {count} ({list names}) Documentation: {count} relevant docs loaded Memory context: {found or none} Additional research needed: Web={$NEEDS_WEB_RESEARCH}, Code={$NEEDS_CODE_EXPLORATION})

# Phase2 research
GOAL(Delegate to specialized agents for deep research when needed. Agents already loaded in $AVAILABLE_AGENTS.)
- `1`: IF($NEEDS_WEB_RESEARCH === true) →
  OUTPUT(Researching external resources...)
  Select agent: prefer @web-research-master if available in $AVAILABLE_AGENTS, otherwise use general agent
  Task(Task(@{selected-web-agent}, Research: {$BRAINSTORM_TOPIC} for {$VECTOR_TASK.title}. Find best practices, common patterns, potential pitfalls. Store findings to vector memory.))
  STORE-AS($WEB_RESEARCH = {agent findings})
→ END-IF
- `2`: IF($NEEDS_CODE_EXPLORATION === true) →
  OUTPUT(Exploring codebase for context...)
  Select agent: find agent specialized for this codebase/domain from $AVAILABLE_AGENTS. If project has dedicated code agent (e.g., laravel-master, react-master), use it. Otherwise use @explore.
  Task(Task(@{selected-code-agent}, Analyze codebase for: {$BRAINSTORM_TOPIC} related to {$VECTOR_TASK.title}. Find relevant files, patterns, existing implementations. Store to vector memory.))
  STORE-AS($CODE_CONTEXT = {agent findings})
→ END-IF
- `3`: STORE-AS($RESEARCH_COMPLETE = {all gathered context})

# Phase3 brainstorm session
GOAL(Facilitate structured ideation with user collaboration)
- `1`: OUTPUT( === PHASE 3: BRAINSTORM SESSION === Task: {$VECTOR_TASK.title} Topic: {$BRAINSTORM_TOPIC}  --- )
- `2`: Present ideas structured by category:
- `3`: OUTPUT(## Approaches {List 2-4 potential approaches based on context}  ## Pros/Cons Analysis {For each approach: advantages, disadvantages, complexity, risk}  ## Recommendations {Top recommendation with rationale}  ## Open Questions {Questions that need user input or further research})

# Phase3a iterative ideation
GOAL(Continuously generate and refine ideas until user confirms completion. Keep proposing new angles until user says to proceed.)
- `1`: STORE-AS($IDEATION_COMPLETE = false)
- `2`: OUTPUT( ---  These are my initial ideas based on the context gathered.  Do you have any thoughts, additions, or alternative ideas to share? I can also propose more ideas from different angles.  **Reply with your ideas, or say "that's all, let's continue" to proceed.**)
- `3`: WAIT for user response
- `4`: FOREACH(WHILE $IDEATION_COMPLETE === false) →
  IF(user says "that's all" OR "let's continue" OR "proceed" OR similar confirmation) →
  STORE-AS($IDEATION_COMPLETE = true)
  OUTPUT(Great! Moving forward with collected ideas...)
→ END-IF
  IF(user provides new ideas OR asks for more) →
  STORE-AS($USER_IDEAS = {append user ideas to collection})
  Generate 2-3 MORE ideas inspired by user input or from new angle:
  OUTPUT( ## Additional Ideas {New approaches inspired by user input or unexplored angles}  ## Building on Your Input {How user ideas could be extended or combined}  ---  Any more thoughts? Or shall we proceed? ("that's all, let's continue"))
  WAIT for user response
→ END-IF
  IF(user asks to explore specific idea deeper) →
  Expand on requested idea with more detail
  OUTPUT( ## Deep Dive: {idea} {Detailed analysis, implementation considerations, edge cases}  ---  More ideas to add? Or ready to proceed?)
  WAIT for user response
→ END-IF
→ END-FOREACH
- `5`: STORE-AS($ALL_IDEAS = {merged: initial ideas + user ideas + additional generated ideas})

# Phase3b action selection
GOAL(After ideation complete, present action options)
- `1`: OUTPUT( === IDEATION COMPLETE ===  ## Collected Ideas Summary {Summary of all ideas discussed}  ---  What would you like to do next? 1. Invite a specialist agent for alternative perspective 2. Update this task based on insights 3. Create subtasks from brainstorm outcomes 4. Research a specific aspect further 5. End session and save insights)
- `2`: WAIT for user to select action

# Phase3c invite specialist
GOAL(Invite subagent as additional specialist for alternative perspective (different LLM = different viewpoint))
- `1`: IF(user requests specialist agent) →
  OUTPUT( === INVITE SPECIALIST === Available agents from $AVAILABLE_AGENTS: {list agent names with descriptions}  Which agent would you like to invite for their perspective on this topic?)
  WAIT for user to select agent
  STORE-AS($INVITED_SPECIALIST = {selected agent id})
  OUTPUT(Consulting @{$INVITED_SPECIALIST} for their perspective...)
  Task(Task(@{$INVITED_SPECIALIST}, You are invited as specialist to brainstorm session.\\n\\nTask: {$VECTOR_TASK.title}\\nTopic: {$BRAINSTORM_TOPIC}\\n\\nCurrent approaches discussed:\\n{approaches_summary}\\n\\nProvide your perspective: alternative approaches, potential issues with discussed approaches, additional considerations, recommendations. Be specific and actionable.))
  STORE-AS($SPECIALIST_INPUT = {agent perspective})
  OUTPUT( ## Specialist Perspective (@{$INVITED_SPECIALIST}) {$SPECIALIST_INPUT}  ---  Continue brainstorming with this input?)
→ END-IF

# Phase4 task modification
GOAL(Update the brainstormed task based on session insights when requested)
- `1`: IF(user requests task update) →
  OUTPUT( === PHASE 4A: TASK MODIFICATION === Preparing task update based on brainstorm insights...)
  Compile proposed changes from brainstorm session
  STORE-AS($PROPOSED_CHANGES = {new_title?, new_content?, append_content?, new_priority?, new_estimate?})
  OUTPUT(Current task: - Title: {$VECTOR_TASK.title} - Content: {$VECTOR_TASK.content} - Priority: {$VECTOR_TASK.priority} | Estimate: {$VECTOR_TASK.estimate}h  Proposed changes: {show proposed changes with diff-style comparison}  Options: 1. Apply changes as shown 2. Rewrite task completely (replace all content) 3. Append insights to existing content 4. Modify proposed changes first 5. Cancel task update)
  WAIT for user choice
  IF(user chooses apply or rewrite) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, title: "{new_title}", content: "{new_content}", priority: "{new_priority}", estimate: {new_estimate}}')
  OUTPUT(Task #{$VECTOR_TASK_ID} updated successfully)
→ END-IF
  IF(user chooses append) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, content: "{$VECTOR_TASK.content}\\\\n\\\\n---\\\\n\\\\n## Brainstorm Insights ({$BRAINSTORM_TOPIC})\\\\n\\\\n{insights_to_append}"}')
  OUTPUT(Insights appended to task #{$VECTOR_TASK_ID})
→ END-IF
→ END-IF

# Phase4b subtask creation
GOAL(Convert brainstorm outcomes to actionable subtasks when requested)
- `1`: IF(user requests subtask creation) →
  OUTPUT( === PHASE 4B: SUBTASK CREATION === Converting brainstorm outcomes to subtasks...)
  Compile actionable items from brainstorm session
  STORE-AS($ACTIONABLE_ITEMS = [{title, description, priority, estimate}, ...])
  OUTPUT(Proposed subtasks for #{$VECTOR_TASK_ID}: {list actionable items with estimates}  Create these subtasks? (yes/no/modify))
  WAIT for user confirmation
  IF(user confirmed) →
  FOREACH(item in $ACTIONABLE_ITEMS) →
  mcp__vector-task__task_create('{title: "{item.title}", content: "{item.description}", parent_id: $VECTOR_TASK_ID, priority: "{item.priority}", estimate: {item.estimate}}')
→ END-FOREACH
  OUTPUT(Created {count} subtasks under #{$VECTOR_TASK_ID})
→ END-IF
→ END-IF

# Phase5 completion
GOAL(Summarize session and store insights to vector memory)
- `1`: STORE-AS($SESSION_SUMMARY = {key decisions, insights, changes made, next steps})
- `2`: STORE-AS($TASK_MODIFIED = {true/false})
- `3`: STORE-AS($SUBTASKS_CREATED = {count or 0})
- `4`: mcp__vector-memory__store_memory('{content: "Brainstorm: {$VECTOR_TASK.title}\\\\nTopic: {$BRAINSTORM_TOPIC}\\\\n\\\\nKey Insights:\\\\n{insights}\\\\n\\\\nDecisions:\\\\n{decisions}\\\\n\\\\nTask Modified: {$TASK_MODIFIED}\\\\nSubtasks Created: {$SUBTASKS_CREATED}\\\\n\\\\nNext Steps:\\\\n{next_steps}", category: "architecture", tags: ["brainstorm", "task-{$VECTOR_TASK_ID}"]}')
- `5`: IF($TASK_MODIFIED OR $SUBTASKS_CREATED > 0) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "Brainstorm session `completed`. Topic: {$BRAINSTORM_TOPIC}. Task modified: {$TASK_MODIFIED}. Subtasks created: {$SUBTASKS_CREATED}.", append_comment: true}')
→ END-IF
- `6`: OUTPUT( === BRAINSTORM COMPLETE === Task #{$VECTOR_TASK_ID}: {$VECTOR_TASK.title} Topic: {$BRAINSTORM_TOPIC} Task modified: {$TASK_MODIFIED} Subtasks created: {$SUBTASKS_CREATED} Insights stored to memory)

# Error handling
Graceful error handling for brainstorm sessions
- `1`: IF(vector task not found) →
  Report: "Task #{id} not found"
  Suggest: Use /do:brainstorm for topic-only brainstorming
  ABORT
→ END-IF
- `2`: IF(user provides empty topic) →
  Re-prompt: "Please specify what aspect you want to brainstorm"
  WAIT for valid topic
→ END-IF
- `3`: IF(research agent fails) →
  Log `failure`
  Continue with available context
  Note limitation to user
→ END-IF
- `4`: IF(task creation fails) →
  Log error
  Report to user which tasks failed
  Suggest manual creation
→ END-IF

</command>