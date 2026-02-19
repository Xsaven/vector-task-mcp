---
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
SCENARIO(Project with 30 modules needs per-module filtering → use CUSTOM_TASK_TAGS in .env for project-specific tags, not 30 new constants in core.)
SCENARIO(Task about "user login flow" → tag: auth (NOT: login, authentication, user-auth). MCP normalizes at storage, but use canonical form at reasoning time.)
- **why**: Ad-hoc tags cause tag explosion ("user-auth", "authentication", "auth" = same concept, search finds none). Predefined list = consistent search. MCP normalizes aliases at storage layer, but reasoning-time canonical usage prevents drift.
- **on_violation**: Normalize via NOT-list (e.g. authentication→auth, db→database). No canonical match → skip tag, put context in task content. Silent fix, no memory storage.

## Memory-tags-predefined-only (CRITICAL)
Memory tags MUST use ONLY predefined values. Allowed: pattern, solution, `failure`, decision, insight, workaround, deprecated, project-wide, module-specific, temporary, reusable.
- **why**: Unknown tags = unsearchable memories. Predefined = discoverable. MCP normalizes at storage, but use canonical form at reasoning time.
- **on_violation**: Normalize to closest canonical tag. No match → skip tag.

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
SCENARIO(Task tagged strict:relaxed touches auth/guards/LoginController.php → escalate to strict:strict minimum regardless of tag.)
SCENARIO(Simple rename across 12 files → cognitive escalates to standard (>10 files rule), strict stays as tagged.)
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
SCENARIO(Task says "add validation". Client-side, server-side, or both? → In -y mode: choose server-side (conservative, safer). In interactive: ask ONE question about this specific gap.)
- **why**: Ambiguity paralysis wastes more time than conservative interpretation. One precise question is enough — if user wanted detailed spec, they would have written docs.
- **on_violation**: Identify specific gap. One question or auto-decide. Proceed.

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


# Task tag selection
GOAL(Select tags per task. Combine dimensions for precision.)
WORKFLOW (pipeline stage): decomposed, validation-fix, blocked, stuck, needs-research, light-validation, parallel-safe, atomic, manual-only, regression
TYPE (work kind): feature (NOT: feat, enhancement), bugfix (NOT: fix, bug), refactor (NOT: refactoring, cleanup), research, docs (NOT: documentation), test (NOT: testing, tests), chore (NOT: maintenance), spike, hotfix
DOMAIN (area): backend, frontend, database (NOT: db, mysql, postgres, sqlite), api (NOT: rest, graphql, endpoint), auth (NOT: authentication, authorization, login, authn, authz), ui, config, infra (NOT: docker, deploy, server), ci-cd (NOT: github-actions, pipeline), migration (NOT: schema, migrate)
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
GOAL(Cognitive level: exhaustive — calibrate analysis depth accordingly)
Memory probes per phase: 5+ cross-referenced
Failure history: full + pattern analysis
Research (context7/web): always + cross-reference
Agent scaling: maximum (4+)
Comment parsing: parse + validate

# Aggressive docs search
GOAL(Find documentation even if named differently than task/code)
- `1`: Generate 3-5 keyword variations: split CamelCase, strip suffixes (Test, Controller, Service, Repository, Handler), extract domain words, try parent context keywords
- `2`: Search ORDER: most specific → most general. Minimum 3 attempts before concluding "no docs"
- `3`: WRONG: brain docs "UserAuthServiceTest" → not found → done
- `4`: RIGHT: brain docs "UserAuthServiceTest" → brain docs "UserAuth" → brain docs "Authentication" → FOUND!
- `5`: STILL not found after 3+ attempts? → brain docs --undocumented → check if class exists but lacks documentation

# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($HAS_AUTO_APPROVE = {true if $RAW_INPUT contains "-y" or "--yes"})
STORE-AS($CLEAN_ARGS = {$RAW_INPUT with -y/--yes flags removed})
STORE-AS($BRAINSTORM_TOPIC = {brainstorm topic extracted from $CLEAN_ARGS})

# Input brainstorm fallback
GOAL(Handle empty brainstorm topic)
- `1`: IF($BRAINSTORM_TOPIC is empty OR $CLEAN_ARGS is empty) →
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
- `2`: mcp__sequential-thinking__sequentialthinking({
                thought: "Analyzing brainstorm topic: {$BRAINSTORM_TOPIC}. Considering: problem space, constraints, stakeholders, `success` criteria, potential approaches.",
                thoughtNumber: 1,
                totalThoughts: 4,
                nextThoughtNeeded: true
            })
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
- `1`: mcp__sequential-thinking__sequentialthinking({
                thought: "Synthesizing all collected ideas from brainstorm session. Evaluating: feasibility, priority, dependencies, risks, actionability.",
                thoughtNumber: 1,
                totalThoughts: 3,
                nextThoughtNeeded: true
            })
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
  mcp__sequential-thinking__sequentialthinking({
                    thought: "Converting brainstorm ideas to tasks. Analyzing: task boundaries, dependencies, optimal order, effort estimation, priority assignment.",
                    thoughtNumber: 1,
                    totalThoughts: 3,
                    nextThoughtNeeded: true
                })
  Compile actionable items from brainstorm session
  Analyze independence: items targeting different files/components with no shared state = parallel: true
  STORE-AS($ACTIONABLE_ITEMS = [{title, description, priority, estimate, order, parallel}, ...])
  OUTPUT(Proposed tasks:  {For each item:} - **{title}** (Priority: {priority}, Est: {estimate}h)   {description}  ---  Options: 1. Create as standalone tasks (no parent) 2. Create under existing task (provide task ID) 3. Modify task list first 4. Cancel task creation)
  WAIT for user choice
  IF(user chooses standalone) →
  FOREACH(item in $ACTIONABLE_ITEMS) →
  mcp__vector-task__task_create('{title: "{item.title}", content: "{item.description}", priority: "{item.priority}", estimate: {item.estimate}, order: {item.order}, parallel: {item.parallel}, tags: ["spike"]}')
→ END-FOREACH
  STORE-AS($CREATED_TASK_IDS = [ids...])
  OUTPUT(Created {count} standalone tasks: {ids})
→ END-IF
  IF(user provides parent task ID) →
  STORE-AS($PARENT_TASK_ID = {user-provided ID})
  FOREACH(item in $ACTIONABLE_ITEMS) →
  mcp__vector-task__task_create('{title: "{item.title}", content: "{item.description}", parent_id: $PARENT_TASK_ID, priority: "{item.priority}", estimate: {item.estimate}, order: {item.order}, parallel: {item.parallel}, tags: ["spike"]}')
→ END-FOREACH
  STORE-AS($CREATED_TASK_IDS = [ids...])
  OUTPUT(Created {count} subtasks under #{$PARENT_TASK_ID}: {ids})
→ END-IF
→ END-IF

# Phase4 completion
GOAL(Summarize session and store insights to vector memory)
- `1`: STORE-AS($SESSION_SUMMARY = {key decisions, insights, approaches discussed, next steps})
- `2`: mcp__vector-memory__store_memory('{content: "Brainstorm Session: {$BRAINSTORM_TOPIC}\\\\n\\\\nContext:\\\\n{context_summary}\\\\n\\\\nApproaches Discussed:\\\\n{approaches}\\\\n\\\\nKey Insights:\\\\n{insights}\\\\n\\\\nDecisions Made:\\\\n{decisions}\\\\n\\\\nNext Steps:\\\\n{next_steps}\\\\n\\\\nTasks Created: {task_ids or none}", category: "architecture", tags: ["decision", "reusable"]}')
- `3`: OUTPUT( === BRAINSTORM COMPLETE === Topic: {$BRAINSTORM_TOPIC} Session insights stored to vector memory Tasks created: {count or "none"}  Use /task:brainstorm #{id} to brainstorm specific aspects of created tasks.)

# Error recovery
Graceful error handling with recovery options
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
- `4`: IF(no agents available) →
  Report: "No agents found via brain list:masters"
  Suggest: Run /init-agents first
  Abort command
→ END-IF
- `5`: IF(agent execution fails) →
  Log: "Agent {name} failed: {error}"
  Proceed without agent input
  Note: "Agent consultation unavailable"
→ END-IF
- `6`: IF(documentation scan fails) →
  Log: "brain docs command failed or no documentation found"
  Proceed without documentation context
→ END-IF
- `7`: IF(memory storage fails) →
  Log: "Failed to store to memory: {error}"
  Report findings in output instead
  Continue with report
→ END-IF

# Response format
=== headers | ## sections | structured analysis | options list | collaborative prompts

</command>