# Vector Task MCP - Agent Documentation

Comprehensive guide for AI agents. Use `mcp__vector-task__cookbook()` tool to retrieve documentation and use cases.

---

<!-- LEVEL:0 -->
## Level 0: Quick Reference

Minimal reference for agents familiar with the system. Tables, limits, quick lookups.

### Tools Summary (22 tools)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `cookbook` | Docs & use cases | include, level, case_category, query, limit, offset |
| `task_create` | Create task | title, content, parent_id, estimate, tags, priority, order, parallel |
| `task_create_bulk` | Batch create | tasks[] (max 50) |
| `task_update` | Update task | task_id, status, comment, append_comment, tags, add_tag, remove_tag |
| `task_delete` | Delete task | task_id |
| `task_delete_bulk` | Batch delete | task_ids[] (max 100) |
| `task_list` | List/search | query, status, tags, parent_id, ids, limit, offset |
| `task_get` | Get by ID | task_id |
| `task_next` | Smart select | - (returns in_progress or next pending) |
| `task_stats` | Statistics | date filters, status, priority, tags, parent_id |
| `tag_normalize_preview` | Preview merges | threshold (0.85-0.90), require_predefined |
| `tag_normalize_apply` | Apply merges | threshold, dry_run, require_predefined |
| `canonical_tag_add` | Add mapping | canonical_tag, variant_tag |
| `canonical_tag_remove` | Remove mapping | variant_tag |
| `canonical_tag_list` | List mappings | - |
| `tag_similarity` | Compare tags | tag1, tag2 |
| `get_canonical_tags` | List canonicals | - |
| `tag_frequencies` | Usage stats | - |
| `tag_weights` | IDF weights | - |
| `tag_classify` | Classify tag | tag |
| `tags_classify_batch` | Batch classify | tags[] |
| `search_explain` | Debug search | query, limit |

### Status Values

| Status | Meaning | Transitions |
|--------|---------|-------------|
| `draft` | Not ready | → pending |
| `pending` | Ready to start | → in_progress |
| `in_progress` | Working | → completed, validated, stopped |
| `completed` | Implementation done | → validated |
| `validated` | Passed quality gates | (final) |
| `stopped` | Paused/blocked | → in_progress |
| `canceled` | Won't do | (final) |

### Limits

| Resource | Limit |
|----------|-------|
| Task title | 200 chars |
| Task content | 10,000 chars |
| Tags per task | 10 |
| Tag length | 50 chars |
| Bulk create | 50 tasks |
| Bulk delete | 100 tasks |
| Search results | 50 |
| Status history | 5 entries |

### Priority Order

```
critical > high > medium > low
```

### Tag Regex

```
^[a-z0-9\-_\s:.]+$
```

Allowed: lowercase letters, numbers, hyphen, underscore, space, colon, dot

### Response Format

```json
{"success": true, ...data}
{"success": false, "error": "Error type", "message": "Details"}
```

<!-- /LEVEL:0 -->

<!-- LEVEL:1 -->
## Level 1: Usage Guide

How to use the system effectively. Best practices, common patterns, workflows.

### Core Concept

Vector Task MCP is a **hierarchical task manager with semantic search**. Every task gets a 384-dimensional vector embedding that enables finding related tasks by meaning, not just keywords.

### Task Creation Flow

```
Input: title + content (+ optional: tags, parent_id, priority, estimate, order, parallel)
   ↓
Validation: sanitize input, validate tags, check limits
   ↓
Embedding: generate 384D vector from "title\ncontent\ntags"
   ↓
Storage: SQLite with sqlite-vec for vector index
   ↓
Output: task_id, status=pending, timestamps
```

### Search Flow

```
Input: query (+ optional filters: status, parent_id, tags, ids)
   ↓
Embedding: convert query to 384D vector
   ↓
Vector Search: cosine similarity against all task vectors
   ↓
IDF Rerank: boost rare tags, penalize common tags
   ↓
Output: ranked task list with similarity scores
```

### Why Vectors?

Traditional search finds "authentication" only if that word exists. Vector search finds:
- "authentication" → login, JWT, OAuth, user verification
- "database optimization" → SQL queries, indexing, performance
- "frontend components" → React, UI elements, styling

### Automatic Status Propagation

**CRITICAL: The system propagates status automatically. NEVER manually update parent status.**

| Trigger | Effect |
|---------|--------|
| Child → `pending` | Parent → `pending` (immediate, even if parent was completed) |
| ALL children → finish status | Parent → `completed` (recursive up the chain) |

Example:
```
Parent[completed]
  ├── Child1[completed]
  └── Child2[completed]

Validation fails → Child2 → pending ⟹ Parent → pending
Fix → Child2 → completed ⟹ ALL finished ⟹ Parent → completed (again)
```

### Best Practices

#### Task Hygiene

1. **Always set estimate**: Every task needs time estimate for planning
2. **Use consistent tags**: Prefer canonical forms (auth not authentication)
3. **Add predefined mappings**: Before bulk normalize, add known mappings
4. **Mark parallel correctly**: Only if truly independent

#### Content Quality

Good task content includes:
- **What**: Clear description of deliverable
- **Why**: Context and motivation
- **Context**: Related files, dependencies, constraints

Bad: "Fix the bug"
Good: "Fix N+1 query in UserController@store when loading roles. Add ->with('roles') eager loading. Affects /api/users endpoint."

#### Search Strategy

1. **Use semantic queries**: "authentication flow" finds more than "auth"
2. **Filter by tags first**: Narrow down, then search
3. **Use search_explain**: Understand why results ranked as they did

#### Hierarchy Strategy

1. **Decompose large tasks**: If estimate > 8h, create subtasks
2. **Keep leaf tasks small**: Each subtask ≤ 4h estimate
3. **Order matters**: Use explicit order for sequence-dependent tasks
4. **Parallel for independence**: Mark siblings parallel only if truly independent

#### Tag Strategy

1. **Use facets**: `vendor:stripe`, `module:terminal`, `type:refactor`
2. **Avoid duplicates**: Run `tag_normalize_preview` periodically
3. **Add mappings early**: `canonical_tag_add` before first normalize
4. **Check frequencies**: `tag_frequencies()` to find overused tags

### Common Patterns

#### Create Task Hierarchy

```python
# 1. Create parent
result = mcp__vector-task__task_create(
    title="User Management System",
    content="Complete user management with auth, roles, permissions",
    estimate=16.0,
    tags=["epic", "auth"]
)
parent_id = result["task_id"]

# 2. Create children with parent_id
mcp__vector-task__task_create_bulk([
    {"title": "User Registration", "content": "Email + password signup", "parent_id": parent_id, "estimate": 3.0, "order": 1},
    {"title": "Email Verification", "content": "Verify email after signup", "parent_id": parent_id, "estimate": 2.0, "order": 2},
    {"title": "Password Reset", "content": "Forgot password flow", "parent_id": parent_id, "estimate": 2.0, "order": 3}
])
```

#### Track Task Progress

```python
# Get next task
next_task = mcp__vector-task__task_next()

# Start working
mcp__vector-task__task_update(task_id=next_task["task"]["id"], status="in_progress")

# ... do work ...

# Complete with comment
mcp__vector-task__task_update(
    task_id=next_task["task"]["id"],
    status="completed",
    comment="Implemented OAuth2 with Google and GitHub providers. Tests passing."
)
```

#### Find Related Tasks

```python
# Semantic search
results = mcp__vector-task__task_list(query="authentication", limit=10)

# Filter by tag
results = mcp__vector-task__task_list(tags=["auth", "security"], status="pending")

# Combined
results = mcp__vector-task__task_list(query="login flow", tags=["backend"], status="in_progress")
```

#### Normalize Tags

```python
# 1. Preview
preview = mcp__vector-task__tag_normalize_preview(threshold=0.90)

# 2. Add known mappings
mcp__vector-task__canonical_tag_add("auth", "authentication")
mcp__vector-task__canonical_tag_add("auth", "login")

# 3. Preview again
preview = mcp__vector-task__tag_normalize_preview(threshold=0.90)

# 4. Apply
result = mcp__vector-task__tag_normalize_apply(threshold=0.90)
```

#### Get Sprint Stats

```python
stats = mcp__vector-task__task_stats(
    created_after="2024-01-01",
    created_before="2024-01-31",
    status="completed"
)

print(f"Completed: {stats['completed_count']}")
print(f"Total time: {stats['total_time_spent']} hours")
```

### Error Handling

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Task not found` | Invalid task_id | Check task exists with task_get |
| `Task already exists` | Duplicate title+content | Use existing task_id from response |
| `Cannot complete task with unfinished children` | Children still pending | Complete children first |
| `Invalid tag` | Tag fails validation | Use lowercase, allowed chars only |
| `Maximum 10 tags per task` | Tag limit exceeded | Remove tags before adding |
| `Security validation failed` | Input sanitization failed | Check for special characters |

#### Error Recovery

```python
result = mcp__vector-task__task_update(task_id=123, status="completed")

if not result["success"]:
    if "unfinished children" in result.get("message", ""):
        children = mcp__vector-task__task_list(parent_id=123, status="pending")
        for child in children["tasks"]:
            mcp__vector-task__task_update(task_id=child["id"], status="completed")
        mcp__vector-task__task_update(task_id=123, status="completed")
```

<!-- /LEVEL:1 -->

<!-- LEVEL:2 -->
## Level 2: Extended Docs

Deep dive into tag normalization, IDF weights, time tracking, and anti-patterns.

### Task Hierarchy Deep Dive

#### Parent-Child Model

```
Task #1 (Parent): "User Management System"
├── Task #2 (Child): "User Registration"     [parent_id=1, order=1]
├── Task #3 (Child): "Email Verification"    [parent_id=1, order=2]
└── Task #4 (Child): "Password Reset"        [parent_id=1, order=3]
```

#### Key Rules

1. **parent_id**: Links child to parent (null = root task)
2. **order**: Position among siblings (1, 2, 3...). Auto-assigned if not provided
3. **parallel**: If true, task CAN run concurrently with adjacent parallel siblings

#### Order & Parallel Execution

| Task | Order | Parallel | Execution |
|------|-------|----------|-----------|
| A | 1 | false | Sequential (must complete first) |
| B | 2 | true | Parallel with C |
| C | 3 | true | Parallel with B |
| D | 4 | false | Sequential (waits for B+C) |

**Rule**: Mark `parallel=true` ONLY when tasks have NO dependency on each other.

### Time Tracking

#### How Time is Calculated

1. **start_at**: Set automatically when status → `in_progress`
2. **finish_at**: Set automatically when status → finish status (completed/tested/validated/stopped)
3. **time_spent**: Cumulative time in HH.MM format (e.g., 1.30 = 1h 30m)

#### Time Propagation

When a child task is finished, its `time_spent` is **automatically added** to all parent tasks up the chain.

```
Parent task time_spent = sum of all children's time_spent
```

#### Time Format: HH.MM

- 1.30 = 1 hour 30 minutes (NOT 1.5 hours!)
- 2.45 = 2 hours 45 minutes
- 0.15 = 15 minutes

### Tag Normalization Deep Dive

#### Why Normalize?

Tag fragmentation hurts search. Without normalization:
- auth, authentication, auth-api, login → 4 separate tags
- With normalization → 1 canonical tag: `auth`

#### Algorithm

1. **Predefined mappings** (from `canonical_tag_add`) take priority
2. **Vector similarity** groups semantically similar tags
3. **Hard guards** prevent wrong merges
4. **Substring boost** helps "laravel" match "laravel framework"

#### Hard Guards (Block Merging)

| Guard | Rule | Example |
|-------|------|---------|
| **Version** | Different versions never merge | `php8` ≠ `php7`, `v2` ≠ `v1` |
| **Numeric** | Different numbers never merge | `api1` ≠ `api2`, `level3` ≠ `level4` |
| **Facet** | Different prefixes never merge | `type:*` ≠ `domain:*` |
| **Prefix** | Structured ≠ plain | `type:refactor` ≠ `refactor` |

#### Facet Model (Colon Tags)

Tags with `:` are structured facets:

```
type:refactor      ← facet: "type", value: "refactor"
vendor:stripe      ← facet: "vendor", value: "stripe"
module:terminal    ← facet: "module", value: "terminal"
```

Rules:
- Same prefix CAN merge: `type:refactor` ↔ `type:refactoring` ✅
- Different prefixes NEVER merge: `type:*` ↔ `domain:*` ❌
- Structured NEVER merges with plain: `type:*` ↔ `refactor` ❌

#### Substring Boost

When one tag is a substring of another:
- Raw similarity: 0.85-0.90
- After boost: +0.05 (if conditions met)

Conditions:
- Same version context (both have version or both don't)
- Shorter tag ≥ 4 characters
- Shorter tag not in stop-words: api, ui, db, test, auth, infra, ci, cd, web, app, lib...

Examples:
- "laravel" ⊂ "laravel framework" → boost ✅
- "api" ⊂ "rest api" → NO boost (stop-word) ❌
- "php" ⊂ "php8" → NO boost (version asymmetry) ❌

#### Tag Variants (Alias Scent)

When tags are merged, original variants are preserved in `tag_variants`:

```json
{
  "tags": ["auth"],
  "tag_variants": ["authentication", "auth-api", "login"]
}
```

Benefits:
- Search still finds tasks by original variant names
- UI can explain: "auth (was: authentication, login)"
- Reranking signal for queries

#### Normalization Workflow

```
1. Preview: tag_normalize_preview(threshold=0.90)
   → See what would merge WITHOUT modifying data

2. Add predefined mappings (optional):
   → canonical_tag_add("auth", "authentication")
   → canonical_tag_add("auth", "login")

3. Apply: tag_normalize_apply(threshold=0.90)
   → Merges variants, stores in tag_variants
```

#### Drift Prevention

Use `require_predefined=True` to ONLY apply predefined mappings, ignoring vector-based grouping:

```python
tag_normalize_apply(require_predefined=True)  # Only predefined, no AI drift
```

### IDF Tag Weights & Classification

#### IDF (Inverse Document Frequency)

Rare tags boost relevance more than common tags:

```
idf_weight = 1 / log(1 + frequency)
```

| Tag | Count | Frequency | IDF Weight | Signal |
|-----|-------|-----------|------------|--------|
| `api` | 70% | 0.70 | 0.38 | Low (too common) |
| `backend` | 40% | 0.40 | 0.62 | Medium |
| `vendor:stripe` | 3% | 0.03 | 1.44 | High (specific) |

#### Tag Classification

Tags are classified by boost level for search ranking:

| Level | Boost | Examples | Use Case |
|-------|-------|----------|----------|
| `high` | 1.5 | `vendor:*`, `module:*`, `service:*`, `package:*` | Specific identifiers |
| `medium` | 1.0 | `type:*`, `domain:*`, other specific tags | Normal relevance |
| `low` | 0.5 | `api`, `backend`, `frontend`, `test`, `auth` | Common/generic |
| `filter_only` | 0.1 | `status:*`, `priority:*`, `batch:*` | For filtering only |

#### Search Ranking Formula

```
final_score = vector_similarity
            × idf_weight
            × tag_boost
            + variant_bonus
```

### Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|--------------|--------------|------------------|
| `task_update(parent_id, status="completed")` | Parent status is auto-propagated | Only update children, parent updates automatically |
| `task_create` without `estimate` | Breaks planning, decomposition decisions | Always set estimate (leaf ≤4h, parent = sum) |
| `parallel=true` for dependent siblings | Causes race conditions, missed dependencies | Only mark parallel if NO file/data dependency |
| Manual `start_at` / `finish_at` | Corrupts timeline, breaks time tracking | Let system auto-manage timestamps |
| `tag_normalize_apply` without preview | Unexpected merges, data corruption | Always `tag_normalize_preview` first |
| Tags like `status:pending`, `priority:high` | Treated as filter_only (boost=0.1) | Use native status/priority fields |
| Creating duplicate tasks | Wastes tokens, fragments work | Check if exists, reuse task_id |
| `task_delete` with active children | Orphans children, breaks hierarchy | Delete children first or use bulk delete |

<!-- /LEVEL:2 -->

<!-- LEVEL:3 -->
## Level 3: Developer Reference

Complete reference with all parameters, architecture, and internal details.

### MCP Tools Reference (Full Parameters)

#### `cookbook(level, include, case_category, query, limit, offset)`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `level` | int | No | 0 | Docs verbosity level 0-3 (cumulative) |
| `include` | str | No | "init" | What to return: init, docs, cases, all, categories |
| `case_category` | str | No | None | Filter cases by category key (e.g., "task-decision") |
| `query` | str | No | None | Keyword search in content |
| `limit` | int | No | 10 | Max results (1-50) |
| `offset` | int | No | 0 | Pagination offset |

**Returns** (by include):
- `init`: Essential first-read, categories list, quick reference
- `docs`: Documentation by level (0-3)
- `cases`: Use cases (all or filtered by case_category/query)
- `all`: Documentation + use cases combined
- `categories`: List of `{key, name, description}` objects

**Usage**:
```python
cookbook()  # init (default)
cookbook(include="categories")  # list all categories with descriptions
cookbook(include="cases", case_category="parallel-execution")  # by category key
cookbook(include="cases", query="security")  # keyword search
cookbook(include="docs", level=2)  # extended docs
cookbook(include="all", level=3)  # everything
```

#### `task_create(title, content, ...)`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | str | Yes | - | Task title (max 200 chars) |
| `content` | str | Yes | - | Task description (max 10K chars) |
| `parent_id` | int | No | None | Parent task ID for subtasks |
| `comment` | str | No | None | Initial comment |
| `priority` | str | No | "medium" | low/medium/high/critical |
| `estimate` | float | No | None | Time estimate in hours |
| `order` | int | No | auto | Position among siblings |
| `tags` | list | No | [] | List of tags (max 10) |
| `parallel` | bool | No | False | Can run concurrently with siblings |

**Returns**: `{success, task_id, title, content, status, created_at, order}`

**Behavior**:
- Duplicate check: same title+content → returns existing task_id with success=false
- Auto-sets status to "pending"
- Auto-assigns order if not provided

#### `task_create_bulk(tasks)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tasks` | list | Yes | List of task objects (max 50) |

**Returns**: `{success, created_task_ids, count, skipped}`

**Behavior**:
- Batch embedding generation (faster than individual creates)
- Skips duplicates, reports in `skipped` array

#### `task_update(task_id, ...)`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | int | Yes | - | Task ID to update |
| `title` | str | No | - | New title |
| `content` | str | No | - | New content |
| `status` | str | No | - | New status |
| `parent_id` | int | No | - | New parent (validates no cycles) |
| `comment` | str | No | - | Comment text |
| `append_comment` | bool | No | True | True=append, False=replace |
| `start_at` | str | No | - | Start timestamp (ISO 8601) |
| `finish_at` | str | No | - | Finish timestamp (ISO 8601) |
| `priority` | str | No | - | New priority |
| `estimate` | float | No | - | Time estimate in hours |
| `order` | int | No | - | New position (triggers sibling reorder) |
| `tags` | list | No | - | Replace all tags |
| `add_tag` | str | No | - | Add single tag |
| `remove_tag` | str | No | - | Remove single tag |
| `parallel` | bool | No | - | Parallel execution flag |

**Returns**: `{success, task}`

**Behavior**:
- Cannot set finish status if has unfinished children
- start_at auto-set when status → in_progress
- finish_at auto-set when status → finish status
- time_spent calculated when task finishes

#### `task_list(query, ...)`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | No | None | Semantic search query |
| `limit` | int | No | 10 | Max results (1-50) |
| `offset` | int | No | 0 | Pagination offset |
| `status` | str | No | None | Filter by status |
| `parent_id` | int | No | None | Filter by parent |
| `tags` | list | No | None | Filter by tags (OR logic) |
| `ids` | list | No | None | Filter by IDs (max 50) |

**Returns**: `{success, tasks, total, count}`

#### `task_get(task_id)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | int | Yes | Task ID to retrieve |

**Returns**: `{success, task, subtask_ids?, next_child?}`

**Behavior**:
- If task has children, includes `subtask_ids` and `next_child`

#### `task_next()`

**Returns**: `{success, task}`

**Behavior**:
- Priority: in_progress > pending (by created_at, oldest first)
- Returns error if no tasks found

#### `task_delete(task_id)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | int | Yes | Task ID to delete |

**Returns**: `{success, task_id, message}`

#### `task_delete_bulk(task_ids)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_ids` | list | Yes | List of IDs (max 100) |

**Returns**: `{success, deleted_count, deleted_task_ids, not_found}`

#### `task_stats(...)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `created_after` | str | Filter tasks created after date (ISO 8601) |
| `created_before` | str | Filter tasks created before date |
| `start_after` | str | Filter tasks started after date |
| `start_before` | str | Filter tasks started before date |
| `finish_after` | str | Filter tasks finished after date |
| `finish_before` | str | Filter tasks finished before date |
| `status` | str | Filter by status |
| `priority` | str | Filter by priority |
| `tags` | list | Filter by tags (OR logic) |
| `parent_id` | int | Filter by parent (0 = root tasks only) |

**Returns**:
```json
{
  "success": true,
  "total_tasks": 45,
  "by_status": {"pending": 20, "in_progress": 3, "completed": 20, ...},
  "by_priority": {"low": 5, "medium": 30, "high": 10},
  "with_subtasks": 5,
  "next_task_id": 12,
  "unique_tags": ["api", "backend", ...],
  "total_estimate": 45.5,
  "total_time_spent": 12.30
}
```

#### `tag_normalize_preview(threshold, require_predefined)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | float | 0.90 | Similarity threshold (0.85=aggressive) |
| `require_predefined` | bool | False | Only show predefined mappings |

**Returns**: `{success, groups, total_tags, unique_tags_after, tags_to_merge}`

#### `tag_normalize_apply(threshold, dry_run, require_predefined)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | float | 0.90 | Similarity threshold |
| `dry_run` | bool | False | Preview without applying |
| `require_predefined` | bool | False | Only predefined mappings |

**Returns**: `{success, tasks_updated, tags_replaced, mapping}`

#### `canonical_tag_add(canonical_tag, variant_tag)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `canonical_tag` | str | Yes | The canonical (preferred) form |
| `variant_tag` | str | Yes | The variant to map |

**Returns**: `{success, canonical_tag, variant_tag}`

#### `canonical_tag_remove(variant_tag)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `variant_tag` | str | Yes | The variant to remove |

**Returns**: `{success, removed}`

#### `canonical_tag_list()`

**Returns**: `{success, canonical_tags, total_mappings}`

#### `tag_similarity(tag1, tag2)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tag1` | str | Yes | First tag |
| `tag2` | str | Yes | Second tag |

**Returns**: `{success, tag1, tag2, similarity}` (0.0-1.0)

#### `get_canonical_tags()`

**Returns**: `{success, tags, count}`

#### `tag_frequencies()`

**Returns**:
```json
{
  "success": true,
  "tags": {
    "api": {"count": 35, "frequency": 0.7, "idf_weight": 0.38},
    "vendor:stripe": {"count": 2, "frequency": 0.04, "idf_weight": 1.44}
  }
}
```

#### `tag_weights()`

**Returns**: `{success, weights: {"api": 0.38, "vendor:stripe": 1.44}}`

#### `tag_classify(tag)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tag` | str | Yes | Tag to classify |

**Returns**: `{success, tag, level, boost, reason}`

#### `tags_classify_batch(tags)`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tags` | list | Yes | Tags to classify |

**Returns**: `{success, high: [...], medium: [...], low: [...], filter_only: [...]}`

#### `search_explain(query, limit)`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | Yes | - | Search query |
| `limit` | int | No | 5 | Max results |

**Returns**:
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "task_id": 42,
      "title": "...",
      "tags": ["vendor:stripe"],
      "tag_classifications": [{"tag": "vendor:stripe", "level": "high", "boost": 1.5, "idf_weight": 1.44}],
      "variant_boost": 0.04
    }
  ]
}
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Layer                           │
│  FastMCP server with 21 tools                          │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  TaskStore (task_store.py)              │
│  - CRUD operations                                      │
│  - Vector search                                        │
│  - Status propagation                                   │
│  - Time tracking                                        │
└─────────────────────────────────────────────────────────┘
          │                    │                    │
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Embeddings     │ │  Normalization   │ │    Security      │
│ (embeddings.py)  │ │ (normalization.py)│ │  (security.py)   │
│                  │ │                  │ │                  │
│ all-MiniLM-L6-v2 │ │ TagNormalizer    │ │ Input validation │
│ 384 dimensions   │ │ Tag guards       │ │ Path sanitization│
│ cosine similarity│ │ IDF weights      │ │ Content limits   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              Storage (SQLite + sqlite-vec)              │
│  - tasks table (core data + tags + tag_variants)        │
│  - task_vectors table (384D embeddings)                 │
│  - canonical_tags table (predefined mappings)           │
│  - task_time_log table (session tracking)               │
└─────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | MCP server entry point, all tool definitions |
| `src/task_store.py` | Core storage logic, search, propagation |
| `src/normalization.py` | Tag normalization, classification, IDF |
| `src/embeddings.py` | Embedding model wrapper, similarity |
| `src/models.py` | Task, TaskStats, Config dataclasses |
| `src/security.py` | Input validation, sanitization |

### Status History

Every task has `status_history` showing last 5 transitions with time spent per session.

<!-- /LEVEL:3 -->

---

## Remember

1. **NEVER update parent status manually** - system propagates automatically
2. **Always set estimate** - enables planning and decomposition decisions
3. **Use tag_normalize_preview before apply** - preview changes first
4. **Mark parallel=true only for independent tasks** - prevents race conditions
5. **Check search_explain if results seem wrong** - understand ranking
6. **Use facets for structured tags** - `vendor:stripe`, `type:refactor`
7. **Time format is HH.MM** - 1.30 = 1h 30m, NOT 1.5h
