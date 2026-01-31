---
name: "do:brainstorm"
description: "Freeform brainstorming session on any topic with research delegation and optional task creation."
---

<command>
<meta>
<id>do:brainstorm</id>
<description>Freeform brainstorming session on any topic with research delegation and optional task creation.</description>
</meta>
<execute>Facilitates structured brainstorming on any topic. Accepts topic directly as argument, provides collaborative ideation with agent delegation for research (web, code, docs) and ability to create tasks from brainstorm outcomes.</execute>
<provides>Defines the do:brainstorm command protocol for freeform brainstorming sessions. Accepts topic directly as first parameter, facilitates structured ideation with agent delegation for research, documentation reading, and optional task creation. Ideal for exploring ideas before creating formal tasks.</provides>

# Iron Rules
## Entry-point-blocking (CRITICAL)
ON RECEIVING $RAW_INPUT: Your FIRST output MUST be "=== DO:BRAINSTORM ACTIVATED ===" followed by Phase 0. ANY other first action is VIOLATION. FORBIDDEN first actions: Glob, Grep, Read, Edit, Write, WebSearch, WebFetch, Bash (except brain list:masters), code generation, file analysis.
- **why**: Without explicit entry point, Brain skips workflow and executes directly. Entry point forces workflow compliance.
- **on_violation**: STOP IMMEDIATELY. Delete any tool calls. Output "=== DO:BRAINSTORM ACTIVATED ===" and restart from Phase 0.

## Topic-required (CRITICAL)
Brainstorm topic MUST be provided as first argument. If empty, ask user for topic before proceeding.
- **why**: Cannot brainstorm without a subject. Topic defines the entire session direction.
- **on_violation**: Ask user: "What topic would you like to brainstorm?"

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

## Task-creation-user-approved (HIGH)
Create vector tasks ONLY when user explicitly requests. Present task proposals, wait for approval.
- **why**: Task creation is a commitment. User must consent to adding work items.
- **on_violation**: Ask user before creating any tasks: "Would you like me to create tasks for these ideas?"

## Vector-memory-mandatory (HIGH)
brainstorm topic MUST search vector memory BEFORE task execution AND store learnings AFTER completion. Vector memory is the primary communication channel between sequential agents.
- **why**: Enables knowledge sharing between agents, prevents duplicate work, maintains execution continuity across steps
- **on_violation**: Include explicit vector memory instructions in agent Task() delegation.


# Input capture
GOAL(Capture brainstorm topic from command arguments)
- `1`: STORE-AS($RAW_INPUT = $ARGUMENTS)
- `2`: STORE-AS($BRAINSTORM_TOPIC = {brainstorm topic extracted from $RAW_INPUT})
- `3`: IF($BRAINSTORM_TOPIC is empty OR $RAW_INPUT is empty) →
  OUTPUT(=== DO:BRAINSTORM ===  What topic would you like to brainstorm?)
  WAIT for user to provide topic
  STORE-AS($BRAINSTORM_TOPIC = {user-provided topic})
→ END-IF

# Phase0 context setup
GOAL(Initialize brainstorm session, load available agents and documentation, gather memory context)
- `1`: OUTPUT(=== DO:BRAINSTORM ACTIVATED ===  === PHASE 0: CONTEXT SETUP === Topic: {$BRAINSTORM_TOPIC} Loading available resources...)
- `2`: Bash(brain list:masters) → [Get available agents for potential delegation and specialist invites] → END-Bash
- `3`: STORE-AS($AVAILABLE_AGENTS = {agents with descriptions})
- `4`: Bash(brain docs {$BRAINSTORM_TOPIC}) → [Get documentation INDEX] → END-Bash
- `5`: STORE-AS($DOCS_INDEX = {indexed documentation list with descriptions})
- `6`: IF($DOCS_INDEX has relevant docs) →
  Select most relevant documents based on topic
  Read('{selected doc paths}')
  STORE-AS($DOC_CONTENT = {documentation content for brainstorm context})
→ END-IF
- `7`: mcp__vector-memory__search_memories('{query: "{$BRAINSTORM_TOPIC}", limit: 5}')
- `8`: STORE-AS($MEMORY_CONTEXT = {related past solutions and patterns})
- `9`: mcp__vector-memory__search_memories('{query: "{$BRAINSTORM_TOPIC} best practices architecture", limit: 3, category: "architecture,learning"}')
- `10`: STORE-AS($BEST_PRACTICES = {relevant patterns})
- `11`: Analyze topic to determine additional research needs:
- `12`: STORE-AS($NEEDS_WEB_RESEARCH = {true if topic involves external tools, APIs, unfamiliar tech, industry standards})
- `13`: STORE-AS($NEEDS_CODE_EXPLORATION = {true if topic requires understanding existing codebase structure})
- `14`: STORE-AS($RELATED_TASK_ID = {null or task ID if topic mentions specific task})
- `15`: OUTPUT(Available agents: {count} ({list names}) Documentation: {count} relevant docs loaded Memory context: {summary or none} Additional research needed: Web={$NEEDS_WEB_RESEARCH}, Code={$NEEDS_CODE_EXPLORATION})

# Phase1 research
GOAL(Delegate to specialized agents for deep research when needed. Agents already loaded in $AVAILABLE_AGENTS.)
- `1`: IF($NEEDS_WEB_RESEARCH === true) →
  OUTPUT(Researching external resources...)
  Select agent: prefer @web-research-master if available in $AVAILABLE_AGENTS, otherwise use general agent
  Task(Task(@{selected-web-agent}, Research: {$BRAINSTORM_TOPIC}. Find best practices, common patterns, potential pitfalls, real-world examples. Store findings to vector memory.))
  STORE-AS($WEB_RESEARCH = {agent findings})
→ END-IF
- `2`: IF($NEEDS_CODE_EXPLORATION === true) →
  OUTPUT(Exploring codebase for context...)
  Select agent: find agent specialized for this codebase/domain from $AVAILABLE_AGENTS. If project has dedicated code agent (e.g., laravel-master, react-master), use it. Otherwise use @explore.
  Task(Task(@{selected-code-agent}, Analyze codebase for: {$BRAINSTORM_TOPIC}. Find relevant files, existing patterns, similar implementations. Store to vector memory.))
  STORE-AS($CODE_CONTEXT = {agent findings})
→ END-IF
- `3`: STORE-AS($RESEARCH_COMPLETE = {all gathered context merged})

# Phase2 brainstorm session
GOAL(Facilitate structured ideation with user collaboration)
- `1`: OUTPUT( === PHASE 2: BRAINSTORM SESSION === Topic: {$BRAINSTORM_TOPIC}  ---)
- `2`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Analyzing brainstorm topic: {$BRAINSTORM_TOPIC}. Considering: problem space, constraints, stakeholders, `success` criteria, potential approaches.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 4,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `3`: Present ideas structured by category:
- `4`: OUTPUT(## Context {Relevant findings from memory, research, documentation}  ## Approaches {List 2-4 potential approaches with brief descriptions}  ## Analysis  ### Approach 1: {name} - Pros: {advantages} - Cons: {disadvantages} - Complexity: {low/medium/high} - Risk: {low/medium/high}  ### Approach 2: {name} {same structure...}  ## Recommendation {Top recommendation with rationale}  ## Open Questions {Questions that need user input or further exploration})

# Phase2a iterative ideation
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

# Phase2b action selection
GOAL(After ideation complete, present action options)
- `1`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Synthesizing all collected ideas from brainstorm session. Evaluating: feasibility, priority, dependencies, risks, actionability.",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 3,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `2`: OUTPUT( === IDEATION COMPLETE ===  ## Collected Ideas Summary {Summary of all ideas discussed}  ---  What would you like to do next? 1. Invite a specialist agent for alternative perspective 2. Research a specific aspect further 3. Create tasks from these ideas 4. Wrap up and save insights)
- `3`: WAIT for user to select action

# Phase2c invite specialist
GOAL(Invite subagent as additional specialist for alternative perspective (different LLM = different viewpoint))
- `1`: IF(user requests specialist agent) →
  OUTPUT( === INVITE SPECIALIST === Available agents from $AVAILABLE_AGENTS: {list agent names with descriptions}  Which agent would you like to invite for their perspective on this topic?)
  WAIT for user to select agent
  STORE-AS($INVITED_SPECIALIST = {selected agent id})
  OUTPUT(Consulting @{$INVITED_SPECIALIST} for their perspective...)
  Task(Task(@{$INVITED_SPECIALIST}, You are invited as specialist to brainstorm session.\\n\\nTopic: {$BRAINSTORM_TOPIC}\\n\\nCurrent approaches discussed:\\n{approaches_summary}\\n\\nProvide your perspective: alternative approaches, potential issues with discussed approaches, additional considerations, recommendations. Be specific and actionable.))
  STORE-AS($SPECIALIST_INPUT = {agent perspective})
  OUTPUT( ## Specialist Perspective (@{$INVITED_SPECIALIST}) {$SPECIALIST_INPUT}  ---  Continue brainstorming with this input?)
→ END-IF

# Phase3 task creation
GOAL(Convert brainstorm outcomes to actionable vector tasks when requested)
- `1`: IF(user requests task creation) →
  OUTPUT( === PHASE 3: TASK CREATION === Converting brainstorm outcomes to tasks...)
  mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                    thought: "Converting brainstorm ideas to tasks. Analyzing: task boundaries, dependencies, optimal order, effort estimation, priority assignment.",'."\\n"
    .'                    thoughtNumber: 1,'."\\n"
    .'                    totalThoughts: 3,'."\\n"
    .'                    nextThoughtNeeded: true'."\\n"
    .'                }')
  Compile actionable items from brainstorm session
  STORE-AS($ACTIONABLE_ITEMS = [{title, description, priority, estimate, order}, ...])
  OUTPUT(Proposed tasks:  {For each item:} - **{title}** (Priority: {priority}, Est: {estimate}h)   {description}  ---  Options: 1. Create as standalone tasks (no parent) 2. Create under existing task (provide task ID) 3. Modify task list first 4. Cancel task creation)
  WAIT for user choice
  IF(user chooses standalone) →
  FOREACH(item in $ACTIONABLE_ITEMS) →
  mcp__vector-task__task_create('{title: "{item.title}", content: "{item.description}", priority: "{item.priority}", estimate: {item.estimate}, tags: ["brainstorm"]}')
→ END-FOREACH
  STORE-AS($CREATED_TASK_IDS = [ids...])
  OUTPUT(Created {count} standalone tasks: {ids})
→ END-IF
  IF(user provides parent task ID) →
  STORE-AS($PARENT_TASK_ID = {user-provided ID})
  FOREACH(item in $ACTIONABLE_ITEMS) →
  mcp__vector-task__task_create('{title: "{item.title}", content: "{item.description}", parent_id: $PARENT_TASK_ID, priority: "{item.priority}", estimate: {item.estimate}, tags: ["brainstorm"]}')
→ END-FOREACH
  STORE-AS($CREATED_TASK_IDS = [ids...])
  OUTPUT(Created {count} subtasks under #{$PARENT_TASK_ID}: {ids})
→ END-IF
→ END-IF

# Phase4 completion
GOAL(Summarize session and store insights to vector memory)
- `1`: STORE-AS($SESSION_SUMMARY = {key decisions, insights, approaches discussed, next steps})
- `2`: mcp__vector-memory__store_memory('{content: "Brainstorm Session: {$BRAINSTORM_TOPIC}\\\\n\\\\nContext:\\\\n{context_summary}\\\\n\\\\nApproaches Discussed:\\\\n{approaches}\\\\n\\\\nKey Insights:\\\\n{insights}\\\\n\\\\nDecisions Made:\\\\n{decisions}\\\\n\\\\nNext Steps:\\\\n{next_steps}\\\\n\\\\nTasks Created: {task_ids or none}", category: "architecture", tags: ["brainstorm", "{topic_tag}"]}')
- `3`: OUTPUT( === BRAINSTORM COMPLETE === Topic: {$BRAINSTORM_TOPIC} Session insights stored to vector memory Tasks created: {count or "none"}  Use /task:brainstorm #{id} to brainstorm specific aspects of created tasks.)

# Error handling
Graceful error handling with recovery options
- `1`: IF(user rejects plan) →
  Accept modifications
  Rebuild plan
  Re-submit for approval
→ END-IF
- `2`: IF(no agents available) →
  Report: "No agents found via brain list:masters"
  Suggest: Run /init-agents first
  Abort command
→ END-IF
- `3`: IF(agent execution fails) →
  Log: "Step/Agent {N} failed: {error}"
  Offer options:
    1. Retry current step
    2. Skip and continue
    3. Abort remaining steps
  WAIT for user decision
→ END-IF
- `4`: IF(documentation scan fails) →
  Log: "brain docs command failed or no documentation found"
  Proceed without documentation context
  Note: "Documentation context unavailable"
→ END-IF
- `5`: IF(memory storage fails) →
  Log: "Failed to store to memory: {error}"
  Report findings in output instead
  Continue with report
→ END-IF

# Error handling brainstorm
Brainstorm-specific error handling
- `1`: IF(topic is too vague) →
  Ask for clarification: "Could you be more specific? E.g., architecture for X, implementation of Y"
  WAIT for refined topic
→ END-IF
- `2`: IF(user provides task ID in topic) →
  Suggest: "Did you mean /task:brainstorm #{id}? That command loads task context first."
  Continue with freeform brainstorm if user confirms
→ END-IF
- `3`: IF(no relevant memory/research found) →
  Proceed with general knowledge
  Note to user: "No prior context found. Starting fresh brainstorm."
→ END-IF

# Response format
=== headers | ## sections | structured analysis | options list | collaborative prompts

</command>