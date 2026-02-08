---
name: "task:create"
description: "Create task from description with analysis and estimation"
---

<command>
<meta>
<id>task:create</id>
<description>Create task from description with analysis and estimation</description>
</meta>
<execute>Create vector task(s) from user description with analysis and estimation.</execute>
<provides>Task creation: analyzes description, researches context (memory, codebase, docs), estimates effort, creates well-structured task after approval. NEVER executes.</provides>

# Iron Rules
## Analyze-first (CRITICAL)
MUST analyze input thoroughly before creating. Extract: objective, scope, requirements, type (feature/bugfix/refactor/research/docs).

## Research-before-create (CRITICAL)
MUST research context: 1) existing tasks (duplicates?), 2) vector memory (prior work), 3) codebase (if code-related), 4) context7 (if unknown lib/pattern).

## Estimate-required (CRITICAL)
MUST provide time estimate. 1-8h normal. >8h = recommend /task:decompose after creation.

## Create-only (CRITICAL)
This command ONLY creates tasks. NEVER execute after creation. User decides via /task:next or /do.

## Comment-with-context (HIGH)
Initial comment MUST contain: memory IDs, relevant file paths, related task IDs. Preserves research for executor.

## Mandatory-user-approval (CRITICAL)
EVERY operation MUST have explicit user approval BEFORE execution. Present plan → WAIT for approval → Execute. NO auto-execution. EXCEPTION: If $HAS_Y_FLAG is true, auto-approve.
- **why**: User maintains control. No surprises. Flag -y enables automated execution.
- **on_violation**: STOP. Wait for explicit user approval (unless $HAS_Y_FLAG is true).

## Fast-path (HIGH)
Simple task (<140 chars, no "architecture/integration/multi-module"): skip heavy research, check duplicates + memory only.

## Auto-approve (HIGH)
-y flag = auto-approve. Skip "Proceed?" but show task spec before creation.


# Input
STORE-AS($RAW_INPUT = $ARGUMENTS)
STORE-AS($TASK_DESCRIPTION = {extracted from RAW_INPUT})

# Workflow
GOAL(Create task: parse → research → analyze → formulate → approve → create)
- `1`: Parse STORE-GET($TASK_DESCRIPTION) → STORE-AS($TASK_SCOPE = {objective, domain, type, requirements})
- `2`: STORE-AS($IS_SIMPLE = description <140 chars AND no architecture/integration/multi-module keywords)
- `3`: IF(STORE-GET($IS_SIMPLE)) →
  mcp__vector-task__task_list('{query: "{objective}", limit: 5}') → check duplicates
  mcp__vector-memory__search_memories('{query: "{domain}", limit: 3}')
→ ELSE →
  [DELEGATE] @agent-explore: 'Search existing tasks for duplicates/related. Objective: {STORE-GET($TASK_SCOPE)}. Return: duplicates, potential parent, dependencies.' → STORE-AS($EXISTING_TASKS)
  mcp__vector-memory__search_memories('{query: "{domain} {objective}", limit: 5, category: "code-solution"}') → STORE-AS($PRIOR_WORK)
  IF(code-related task) →
  [DELEGATE] @agent-explore: 'Scan codebase for {domain}. Find: files, patterns, dependencies. Return: paths, architecture notes.' → STORE-AS($CODEBASE_CONTEXT)
→ END-IF
  IF(unknown library/pattern) →
  mcp__context7__query-docs('{query: "{library}"}') → understand before formulating
→ END-IF
→ END-IF
- `4`: IF(duplicate found) → STOP. Ask: update existing or create new?
- `5`: mcp__sequential-thinking__sequentialthinking('{'."\\n"
    .'                thought: "Analyzing: complexity, estimate, priority, dependencies, acceptance criteria",'."\\n"
    .'                thoughtNumber: 1,'."\\n"
    .'                totalThoughts: 2,'."\\n"
    .'                nextThoughtNeeded: true'."\\n"
    .'            }')
- `6`: STORE-AS($ANALYSIS = {complexity, estimate, priority, dependencies, criteria})
- `7`: STORE-AS($TASK_SPEC = {
                title: "concise, max 10 words",
                content: "objective, context, acceptance criteria, hints",
                priority: "critical|high|medium|low",
                estimate: "hours (1-8, >8 needs decompose)",
                tags: ["category", "domain"],
                comment: "Memory: #IDs. Files: paths. Related: #task_ids."
            })
- `8`: Show: Title, Priority, Estimate, Tags, Content preview
- `9`: IF(estimate > 8) →
  WARN: >8h, recommend /task:decompose after creation
→ END-IF
- `10`: IF($HAS_AUTO_APPROVE) →
  Auto-approved
→ ELSE →
  Ask: "Create? (yes/no/modify)"
→ END-IF
- `11`: mcp__vector-task__task_create('{title, content, priority, tags, estimate, comment}') → STORE-AS($CREATED_ID)
- `12`: mcp__vector-memory__store_memory('{content: "Created task #{id}: {title}, {domain}, {estimate}h", category: "tool-usage"}')
- `13`: IF(estimate > 8) →
  Recommend: /task:decompose STORE-GET($CREATED_ID)
→ END-IF
- `14`: STOP. Do NOT execute. Return control to user.

# Error handling
- `1`: IF(duplicate task found) → Ask: update existing #ID or create new?
- `2`: IF(research fails) → Continue with available data, note gaps
- `3`: IF(user rejects) → Accept modifications, rebuild spec, re-submit

</command>