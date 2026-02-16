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
<provides>Collaborative brainstorming anchored to vector task. Loads task, asks user for topic, facilitates ideation with research delegation, optional task modification/subtask creation.</provides>

# Iron Rules
## Task-get-first (CRITICAL)
FIRST action = mcp__vector-task__task_get. Load task context before anything.

## Topic-prompt-mandatory (CRITICAL)
MUST ask user for brainstorm topic after loading task. NEVER assume or invent topic.

## Collaborative-mode (HIGH)
Brainstorm is DIALOGUE. Present ideas → ask feedback → iterate. NOT monologue. User can invite specialist agents.

## Iterative-ideation (CRITICAL)
After initial ideas, keep proposing until user says "that's all" / "proceed". NEVER skip this loop.

## Research-on-demand (HIGH)
Delegate research ONLY when needed. Unknown tech → context7. Codebase analysis → explore agent. Simple topics → no delegation.

## Modification-user-approved (HIGH)
Modify task or create subtasks ONLY when user explicitly requests. Options: update content, rewrite, append, create subtasks.

## Parent-id-mandatory (CRITICAL)
ALL subtasks MUST have parent_id = $VECTOR_TASK_ID. No orphan tasks.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with flags removed})
STORE-AS($VECTOR_TASK_ID = {numeric ID extracted from $CLEAN_ARGS})

# Workflow
GOAL(Brainstorm: load task → ask topic → gather context → ideate → iterate → actions)
- `1`: mcp__vector-task__task_get('{task_id: $VECTOR_TASK_ID}') → STORE-AS($TASK)
- `2`: IF(not found) →
  ABORT "Task not found. Use /do:brainstorm for topic-only."
→ END-IF
- `3`: IF(TASK.parent_id) →
  mcp__vector-task__task_get('{task_id: parent_id}') → STORE-AS($PARENT)
→ END-IF
- `4`: mcp__vector-task__task_list('{parent_id: $VECTOR_TASK_ID}') → STORE-AS($SUBTASKS)
- `5`: Show: Task #{id}, title, status, content, parent, subtasks count
- `6`: Ask: "What aspect would you like to brainstorm?"
- `7`: WAIT for user topic → STORE-AS($TOPIC)
- `8`: mcp__vector-memory__search_memories('{query: "{TASK.title} {TOPIC}", limit: 5}') → STORE-AS($MEMORY)
- `9`: Bash('brain docs {TOPIC}') → STORE-AS($DOCS)
- `10`: IF(unknown library/tech in TOPIC) →
  mcp__context7__query-docs('{query: "{library}"}') → understand first
→ END-IF
- `11`: IF(needs codebase analysis) →
  [DELEGATE] @agent-explore: 'Analyze codebase for {TOPIC}. Find: relevant files, patterns, implementations.' → STORE-AS($CODE_CONTEXT)
→ END-IF
- `12`: IF(needs external research) →
  [DELEGATE] @agent-web-research-master: 'Research {TOPIC}: best practices, patterns, pitfalls.' → STORE-AS($WEB_RESEARCH)
→ END-IF
- `13`: Present structured ideas:
- `14`: ## Approaches - 2-4 potential approaches ## Pros/Cons - for each approach ## Recommendation - top choice with rationale ## Open Questions - needs user input
- `15`: STORE-AS($IDEATION_DONE = false)
- `16`: Ask: "Your thoughts? More ideas? Say 'proceed' when done."
- `17`: FOREACH(WHILE NOT IDEATION_DONE) →
  IF(user says proceed/done) → STORE-AS($IDEATION_DONE = true)
  IF(user shares ideas) → Build on them, propose 2-3 more, ask again
  IF(user wants deep dive) → Expand specific idea, then ask again
→ END-FOREACH
- `18`: Show options: 1) Invite specialist, 2) Update task, 3) Create subtasks, 4) Research more, 5) End session
- `19`: WAIT for user choice
- `20`: IF(user wants specialist) →
  Bash('brain list:masters') → show available
  WAIT for selection
  [DELEGATE] @agent-{selected}: 'Specialist perspective on {TOPIC} for task {TASK.title}. Current approaches: {summary}. Provide: alternatives, issues, recommendations.'
  Present specialist input, continue brainstorm
→ END-IF
- `21`: IF(user wants task update) →
  Show current vs proposed changes
  Options: apply, rewrite, append, cancel
  IF(confirmed) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, content: "{new}", comment: "Brainstorm: {TOPIC}"}')
→ END-IF
→ END-IF
- `22`: IF(user wants subtasks) →
  List actionable items from brainstorm
  Ask: "Create these subtasks? (yes/no/modify)"
  IF(confirmed) →
  mcp__vector-task__task_create_bulk('{tasks: [{title, content, parent_id: $VECTOR_TASK_ID, priority, estimate}]}')
→ END-IF
→ END-IF
- `23`: mcp__vector-memory__store_memory('{content: "Brainstorm #{TASK.id}: {TOPIC}. Insights: {summary}. Modified: {yes/no}. Subtasks: {count}.", category: "architecture", tags: ["brainstorm"]}')
- `24`: IF(task modified OR subtasks created) →
  mcp__vector-task__task_update('{task_id: $VECTOR_TASK_ID, comment: "Brainstorm `completed`: {TOPIC}"}')
→ END-IF
- `25`: Report: task, topic, modifications, subtasks created

# Error handling
- `1`: IF(task not found) → ABORT "Use /do:brainstorm for topic-only"
- `2`: IF(empty topic) → Re-prompt: "Please specify aspect to brainstorm"
- `3`: IF(research agent fails) →
  Continue with available context, note limitation
→ END-IF
- `4`: IF(task creation fails) →
  Report which failed, suggest manual creation
→ END-IF

</command>