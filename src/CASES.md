# Vector Task MCP - Use Cases

Comprehensive scenarios for AI agents. Use `mcp__vector-task__cookbook(include="cases")` or `mcp__vector-task__cookbook(include="all")` to retrieve.

Search with `query` parameter: `cookbook(include="cases", query="security")`, `cookbook(include="cases", query="parallel")`.

---

## Essential Patterns (CRITICAL)
<!-- description: Core patterns that prevent data loss. Master these first. -->

| # | Pattern | Rule | Why |
|---|---------|------|-----|
| 1 | **Parallel Isolation** | ALL 5 conditions MUST be true | Wrong parallelism = race conditions, lost work |
| 2 | **Safety Escalation** | auth/, payments/, migrations/ → strict:strict | Critical paths need minimum protection |
| 3 | **Parent Status** | NEVER update parent manually | Auto-propagation: child→pending ⟹ parent→pending |
| 4 | **Memory vs Comments** | Memory = PRIMARY, Comments = LINKS | Memory is searchable/persistent, comments are task-local |
| 5 | **File Scope** | Always include `FILES: [...]` in content | Executor needs scope for conflict detection |
| 6 | **Estimate Required** | EVERY task needs estimate (hours) | Enables planning, prioritization, decomposition |
| 7 | **Timestamps Auto** | NEVER set start_at/finish_at manually | System auto-manages, manual values corrupt timeline |

**Quick Search:**
- `query="critical"` - All CRITICAL patterns
- `query="security"` - Safety escalation, blacklist
- `query="parallel"` - Parallel execution patterns
- `query="memory"` - Memory integration patterns

---

## Task Decision Scenarios
<!-- description: When to create a task vs inline fix. Critical for token efficiency. -->

When to create a task vs inline fix. Critical for token efficiency.

### Decision Matrix

| Criteria | Create Task | Inline Fix |
|----------|-------------|------------|
| **Estimate** | > 0.5h | < 0.25h |
| **Files** | > 1 file | 1 file |
| **Complexity** | Multiple methods/logic | Single method/lines |
| **Risk** | Needs testing/approval | Trivial, safe, reversible |
| **Scope** | Affects other code | Isolated change |

### Inline Fix Examples (NO task needed)

```python
# These are INLINE fixes - just do them, don't create tasks:

# Remove unused import
- use App\Services\DeprecatedService;  # DELETE

# Remove unused code/variable
$unused = $this->getOldValue();  # DELETE entire line

# Fix typo in comment
// Valdiate user input  →  // Validate user input

# Update single config value
'timeout' => 30  →  'timeout' => 60

# Delete deprecated line
// @deprecated - remove in v2  →  DELETE

# Rename single variable/method (1 occurrence)
private function proccessData()  →  private function processData()

# Add single import
+ use App\Services\NewService;

# Fix code style (single file)
if($x){  →  if ($x) {
```

### Task Creation Examples (task IS needed)

```python
# These REQUIRE task creation:

# Multiple files affected
mcp__vector-task__task_create(
    title="Add rate limiting to all API endpoints",
    content="FILES: [app/Http/Controllers/Api/*.php, routes/api.php]",
    estimate=3.0,
    tags=["feature", "api", "strict:standard"]
)

# New feature/method
mcp__vector-task__task_create(
    title="Add password strength validation",
    content="Implement zxcvbn validation in RegistrationService",
    estimate=2.0,
    tags=["feature", "auth", "strict:standard"]
)

# Complex refactor
mcp__vector-task__task_create(
    title="Refactor OrderService to use repository pattern",
    content="Extract database logic to OrderRepository",
    estimate=4.0,
    tags=["refactor", "backend", "strict:standard"]
)

# Needs testing
mcp__vector-task__task_create(
    title="Fix race condition in payment processing",
    content="Add mutex lock, requires extensive testing",
    estimate=3.0,
    tags=["bugfix", "payment", "strict:strict"]
)
```

### Validation Inline Decision

During validation, agent should inline fix small issues:

```python
# During task validation:

# Found: 5 lines of unused code
# Decision: INLINE FIX (delete immediately, rerun tests)
# If tests pass → validation complete
# If tests fail → CREATE fix-task

# Found: Missing type hint on 1 method
# Decision: INLINE FIX (add type hint)

# Found: Missing test coverage for 3 methods
# Decision: CREATE TASK (needs multiple tests)
mcp__vector-task__task_create(
    title="Add tests for UserService methods",
    content="Test: register, validate, resetPassword",
    estimate=1.5,
    tags=["test", "backend"],
    parent_id=current_task_id  # Link to validated task
)

# Found: Deprecated pattern in 10 files
# Decision: CREATE TASK (too many files)
mcp__vector-task__task_create(
    title="Replace deprecated helper with service",
    content="FILES: [app/Http/Controllers/*.php] - replace old_helper() with NewService",
    estimate=2.0,
    tags=["refactor", "backend"]
)
```

### Cognitive Level Impact

Higher cognitive = more careful about task creation:

| Cognitive | Inline Threshold | Task Threshold |
|-----------|------------------|----------------|
| `minimal` | < 5 min, 1 line | Everything else |
| `standard` | < 15 min, 1 file | > 15 min OR > 1 file |
| `deep` | < 15 min, trivial | > 15 min OR any complexity |
| `exhaustive` | Almost nothing | Nearly everything |

### Strict Mode Impact

Higher strict = more likely to create task for tracking:

| Strict | Inline Allowed | Must Create Task |
|--------|----------------|------------------|
| `relaxed` | Anything simple | Complex only |
| `standard` | Trivial fixes | Anything affecting logic |
| `strict` | Only comments | Any code change |
| `paranoid` | Nothing inline | ALL changes need task |

### Quick Decision Flowchart

```
Found issue during work/validation
         ↓
   Is it < 5 lines in 1 file?
         ↓
    YES → Can tests verify it's safe?
              ↓
         YES → Is strict:relaxed or strict:standard?
                   ↓
              YES → INLINE FIX → rerun tests
                   ↓
                   NO → CREATE TASK
              ↓
         NO → CREATE TASK
    NO → CREATE TASK
```

### Validation Fix Strategy

```python
# During validation, found bloated test

if bloated_lines < 10 and single_test_file:
    # INLINE: Refactor test immediately
    # Rerun: phpunit tests/Feature/UserTest.php
    # If pass → continue validation
    # If fail → CREATE validation-fix task
    inline_refactor_test()
else:
    # CREATE TASK: Too complex for inline
    mcp__vector-task__task_create(
        title="Refactor bloated UserTest",
        content=f"FILES: [{test_file}]. Remove bloat, simplify assertions.",
        parent_id=validated_task_id,
        estimate=1.0,
        tags=["validation-fix", "test"]
    )
```

---

## Task Creation Scenarios
<!-- description: How to create tasks with all parameters. Parent-child, parallel, tags, estimates. -->

### Basic Task Creation

```python
result = mcp__vector-task__task_create(
    title="Add user authentication",
    content="Implement JWT-based authentication with login/register endpoints",
    priority="high",
    estimate=4.0,
    tags=["feature", "auth"]
)
# Returns: {success: true, task_id: 42, status: "pending"}
```

### Task with Parent (Subtask)

```python
# First create parent
parent = mcp__vector-task__task_create(
    title="User Management System",
    content="Complete user management module",
    estimate=16.0,
    tags=["epic", "auth"]
)

# Then create subtasks with parent_id
mcp__vector-task__task_create_bulk([
    {"title": "User Registration", "content": "Email + password signup flow", "parent_id": parent["task_id"], "estimate": 3.0, "order": 1},
    {"title": "Email Verification", "content": "Verify email after signup", "parent_id": parent["task_id"], "estimate": 2.0, "order": 2},
    {"title": "Password Reset", "content": "Forgot password flow", "parent_id": parent["task_id"], "estimate": 2.0, "order": 3}
])
```

### Task with Initial Comment

```python
mcp__vector-task__task_create(
    title="Fix N+1 query in UserController",
    content="Eager load roles relationship in store method",
    comment="Found during profiling. See memory #15 for query analysis.",
    estimate=0.5,
    tags=["bugfix", "performance"]
)
```

### Parallel Subtasks (Independent)

```python
parent = mcp__vector-task__task_create(title="API Module", content="Build REST API", estimate=8.0)

mcp__vector-task__task_create_bulk([
    {"title": "Users API", "content": "CRUD for users", "parent_id": parent["task_id"], "estimate": 2.0, "order": 1, "parallel": True},
    {"title": "Products API", "content": "CRUD for products", "parent_id": parent["task_id"], "estimate": 2.0, "order": 2, "parallel": True},
    {"title": "Orders API", "content": "CRUD for orders", "parent_id": parent["task_id"], "estimate": 2.0, "order": 3, "parallel": True}
])
# All three can execute concurrently - no file overlap, no dependencies
```

### Sequential Subtasks (Dependent)

```python
parent = mcp__vector-task__task_create(title="Database Migration", content="Migrate to new schema", estimate=6.0)

mcp__vector-task__task_create_bulk([
    {"title": "Create new tables", "content": "Add users_v2, orders_v2", "parent_id": parent["task_id"], "estimate": 2.0, "order": 1, "parallel": False},
    {"title": "Migrate data", "content": "Copy data from old to new tables", "parent_id": parent["task_id"], "estimate": 2.0, "order": 2, "parallel": False},
    {"title": "Update application code", "content": "Point models to new tables", "parent_id": parent["task_id"], "estimate": 2.0, "order": 3, "parallel": False}
])
# Must run sequentially - each depends on previous
```

---

## Task Execution Scenarios
<!-- description: How to execute tasks. Start, complete, blockers, session recovery. -->

### Get Next Task (Smart Selection)

```python
next_task = mcp__vector-task__task_next()
# Returns: in_progress task if exists, otherwise first pending by priority/order
# Use this to pick what to work on next
```

### Start Working on Task

```python
# Get task details
task = mcp__vector-task__task_get(task_id=42)

# Mark as in_progress (auto-sets start_at timestamp)
mcp__vector-task__task_update(task_id=42, status="in_progress")

# ... do the work ...

# Complete with findings
mcp__vector-task__task_update(
    task_id=42,
    status="completed",
    comment="Implemented JWT auth. Tests passing. See memory #50 for token refresh pattern.",
    append_comment=True
)
```

### Task with Blocker

```python
# Encountered blocker during execution
mcp__vector-task__task_update(
    task_id=42,
    status="pending",  # Return to queue, NOT stopped
    comment="BLOCKED: Need API key from DevOps. Cannot proceed without external dependency.",
    append_comment=True
)
# Task returns to pending queue for retry when blocker resolved
```

### Session Recovery (Crashed Session)

```python
task = mcp__vector-task__task_get(task_id=42)
# Status is in_progress but no recent activity in comment

# Check comment for execution state
if "completed_steps: [setup, install]" in task.comment:
    # Crashed session - continue from last completed step
    # ... resume from step 3 ...
else:
    # Stale session - reset
    mcp__vector-task__task_update(task_id=42, status="pending", comment="Stale session reset", append_comment=True)
```

---

## Search & Query Scenarios
<!-- description: How to search tasks. Semantic search, filters, multi-probe patterns. -->

### Semantic Search

```python
# Find tasks by meaning, not keywords
results = mcp__vector-task__task_list(query="authentication flow", limit=10)
# Finds: login, JWT, OAuth, session management - even if "authentication" not in title
```

### Filter by Status

```python
# All pending tasks
pending = mcp__vector-task__task_list(status="pending", limit=50)

# All in progress
active = mcp__vector-task__task_list(status="in_progress")

# Completed this week
completed = mcp__vector-task__task_list(
    status="completed",
    created_after="2026-02-12"
)
```

### Filter by Tags (OR Logic)

```python
# Tasks with auth OR api tags
results = mcp__vector-task__task_list(tags=["auth", "api"], limit=20)
```

### Combined Filters

```python
# Backend auth tasks that are pending
results = mcp__vector-task__task_list(
    query="authentication",
    tags=["backend"],
    status="pending",
    limit=10
)
```

### Get Subtasks of Parent

```python
children = mcp__vector-task__task_list(parent_id=42, limit=50)
# Returns all direct children of task #42
```

### Get Root Tasks Only

```python
# parent_id=0 means no parent (root level)
root_tasks = mcp__vector-task__task_list(parent_id=0, status="pending")
```

### Batch Lookup by IDs

```python
tasks = mcp__vector-task__task_list(ids=[1, 2, 3, 4, 5])
# Get specific tasks by ID (max 50)
```

### Search with Ranking Explanation

```python
# Debug why results ranked as they are
explained = mcp__vector-task__search_explain(query="login", limit=5)
# Shows: similarity scores, tag classifications, IDF weights, variant boosts
```

---

## Tag Normalization Scenarios
<!-- description: How to normalize tags. Preview, apply, predefined mappings, drift prevention. -->

### Preview Tag Merges

```python
# See what would merge WITHOUT modifying data
preview = mcp__vector-task__tag_normalize_preview(threshold=0.90)
# Returns: groups of similar tags, what would be canonical, tags_to_merge count

# Example output:
# groups: [
#   {canonical: "auth", variants: ["authentication", "auth-api", "login"], similarity: 0.92}
# ]
```

### Add Predefined Mappings

```python
# Define known mappings before normalization
mcp__vector-task__canonical_tag_add("auth", "authentication")
mcp__vector-task__canonical_tag_add("auth", "login")
mcp__vector-task__canonical_tag_add("auth", "auth-api")

# These take priority over vector similarity
```

### Apply Normalization

```python
# After preview and predefined mappings
result = mcp__vector-task__tag_normalize_apply(threshold=0.90)
# Returns: {tasks_updated: 15, tags_replaced: 23, mapping: {...}}

# Original tags preserved in tag_variants for search
```

### Drift Prevention (Predefined Only)

```python
# Only apply predefined mappings, ignore vector similarity
result = mcp__vector-task__tag_normalize_apply(threshold=0.90, require_predefined=True)
# Prevents AI drift - only known mappings applied
```

### Check Tag Similarity

```python
sim = mcp__vector-task__tag_similarity("authentication", "auth")
# Returns: {similarity: 0.89}
```

### View Canonical Mappings

```python
mappings = mcp__vector-task__canonical_tag_list()
# Returns: all predefined canonical -> variant mappings
```

---

## Hierarchy & Decomposition Scenarios
<!-- description: How to decompose tasks. Parent-child model, order, parallel marking. -->

### Check Task Hierarchy

```python
task = mcp__vector-task__task_get(task_id=42)

# Check if has parent
if task.parent_id:
    parent = mcp__vector-task__task_get(task_id=task.parent_id)
    # Parent context for understanding broader goal

# Check if has children
children = mcp__vector-task__task_list(parent_id=42)
if children["tasks"]:
    # This is a parent task with subtasks
```

### Decompose Large Task

```python
# Task estimate > 8 hours should be decomposed
large_task = mcp__vector-task__task_get(task_id=42)
if large_task.estimate > 8.0:
    # Create subtasks with distinct file scopes
    mcp__vector-task__task_create_bulk([
        {
            "title": "Backend API",
            "content": "FILES: [src/Api/*.php]. REST endpoints implementation.",
            "parent_id": 42,
            "estimate": 3.0,
            "order": 1,
            "parallel": False
        },
        {
            "title": "Frontend Integration",
            "content": "FILES: [src/Frontend/*.tsx]. API client components.",
            "parent_id": 42,
            "estimate": 3.0,
            "order": 2,
            "parallel": False  # Depends on backend
        }
    ])
```

### Get Full Task Tree

```python
def get_task_tree(task_id, depth=0):
    task = mcp__vector-task__task_get(task_id=task_id)
    children = mcp__vector-task__task_list(parent_id=task_id)
    
    result = {"task": task, "children": []}
    for child in children["tasks"]:
        result["children"].append(get_task_tree(child["id"], depth+1))
    
    return result
```

---

## Status & Time Tracking Scenarios
<!-- description: Status lifecycle, automatic propagation, time tracking in HH.MM format. -->

### Status Lifecycle

```python
# draft → pending → in_progress → completed → validated
#                    ↘ stopped → in_progress

mcp__vector-task__task_update(task_id=42, status="pending")      # Ready to start
mcp__vector-task__task_update(task_id=42, status="in_progress")  # Working (auto-sets start_at)
mcp__vector-task__task_update(task_id=42, status="completed")    # Done (auto-sets finish_at)
mcp__vector-task__task_update(task_id=42, status="validated")    # Quality gates passed
```

### Automatic Status Propagation

```python
# When child goes to pending, parent automatically goes to pending
mcp__vector-task__task_update(task_id=43, status="pending")  # Child
# → Parent #42 automatically becomes pending (even if was completed)

# When ALL children reach finish status, parent auto-completes
# System handles this automatically - NEVER manually update parent status
```

### Time Tracking (Automatic)

```python
# start_at: auto-set when status → in_progress
# finish_at: auto-set when status → completed/validated/stopped
# time_spent: calculated in HH.MM format (1.30 = 1h 30m)

# Time propagates up to parents automatically
task = mcp__vector-task__task_get(task_id=42)
print(f"Time spent: {task.time_spent}")  # "2.30" = 2h 30m
```

### Get Sprint Statistics

```python
stats = mcp__vector-task__task_stats(
    created_after="2026-02-01",
    created_before="2026-02-28",
    status="completed"
)

print(f"Total completed: {stats['total_tasks']}")
print(f"Total time: {stats['total_time_spent']} hours")
print(f"By priority: {stats['by_priority']}")
```

### Status History

```python
task = mcp__vector-task__task_get(task_id=42)
# task.status_history contains last 5 transitions with time per session
```

---

## Error Handling & Recovery Scenarios
<!-- description: How to handle errors. Tool errors, retry circuit breaker, common errors. -->

### Tool Error Recovery

```python
result = mcp__vector-task__task_update(task_id=42, status="completed")

if not result["success"]:
    if "unfinished children" in result.get("message", ""):
        # Complete children first
        children = mcp__vector-task__task_list(parent_id=42, status="pending")
        for child in children["tasks"]:
            mcp__vector-task__task_update(task_id=child["id"], status="completed")
        # Retry parent
        mcp__vector-task__task_update(task_id=42, status="completed")
    elif "Task not found" in result.get("error", ""):
        # Handle missing task
        pass
```

### Retry Circuit Breaker

```python
# Parse comment for attempt count
task = mcp__vector-task__task_get(task_id=42)
attempt_count = task.comment.count("ATTEMPT [exec]:")

if "stuck" in task.tags:
    # Task is stuck - needs human intervention
    # DO NOT retry
    pass
elif attempt_count >= 3:
    # Max retries reached - mark stuck
    mcp__vector-task__task_update(
        task_id=42,
        add_tag="stuck",
        comment="CIRCUIT BREAKER: 3 attempts exhausted. Needs human.",
        append_comment=True
    )
else:
    # Safe to retry
    mcp__vector-task__task_update(
        task_id=42,
        status="in_progress",
        comment=f"ATTEMPT [exec]: {attempt_count + 1}/3",
        append_comment=True
    )
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Task not found` | Invalid ID | Verify with task_get first |
| `Task already exists` | Duplicate title+content | Use existing task_id |
| `Cannot complete with unfinished children` | Children pending | Complete children first |
| `Maximum 10 tags per task` | Tag limit | Remove tags before adding |
| `Invalid tag` | Bad characters | Use lowercase, alphanumeric |

---

## Parallel Execution Scenarios
<!-- description: CRITICAL safety patterns for concurrent execution. Isolation, blacklist, scope. -->

Critical safety patterns for concurrent task execution. Wrong parallelism = data loss.

### [CRITICAL] Parallel Isolation Checklist (5 MUST Conditions)

Before setting `parallel=true`, ALL 5 conditions MUST be verified:

| # | Condition | Check |
|---|-----------|-------|
| 1 | ZERO file overlap | Tasks touch completely different files |
| 2 | ZERO import chain | File A does NOT import/use/require file B |
| 3 | ZERO shared model/table | No same DB table/migration/model |
| 4 | ZERO shared config | No same config key/.env variable |
| 5 | ZERO output→input | Task B does NOT need result of task A |

```python
# ALL 5 TRUE → parallel: true
# ANY 1 FALSE → parallel: false (NO exceptions)
```

### [CRITICAL] Conservative Default Rule

```python
# DEFAULT: parallel=false
# Only set parallel=true when isolation is PROVEN

# Risk analysis:
# - False negative (missing parallelism) = slower execution
# - False positive (wrong parallelism) = data loss, conflicts

# Conclusion: When in doubt, sequential is ALWAYS safe
```

### Creating Parallel Tasks (order + parallel)

```python
# EVERY subtask MUST have unique order AND explicit parallel flag
# NEVER omit either parameter

# Step 1: Analyze dependencies BEFORE creating
# Use SequentialThinking for complex dependencies

# Step 2: List files per task
task_A = {"files": ["src/UserService.php"], "needs": []}
task_B = {"files": ["src/ProductService.php"], "needs": []}
task_C = {"files": ["src/OrderService.php"], "needs": ["ProductService"]}

# Step 3: Cross-reference for overlap
all_files = task_A["files"] + task_B["files"] + task_C["files"]
overlap = [f for f in all_files if all_files.count(f) > 1]
# overlap = [] → no file overlap

# Step 4: Check dependencies
# A: no needs → can start immediately
# B: no needs → can start immediately  
# C: needs ProductService from B → must wait for B

# Step 5: Set order + parallel
mcp__vector-task__task_create_bulk([
    {"title": "User Service", "content": "FILES: [src/UserService.php]", "order": 1, "parallel": True},
    {"title": "Product Service", "content": "FILES: [src/ProductService.php]", "order": 2, "parallel": True},
    {"title": "Order Service", "content": "FILES: [src/OrderService.php]", "order": 3, "parallel": False}  # Depends on #2
])
```

### Execution Flow (Mixed Parallel/Sequential)

```python
# How executor processes tasks with order + parallel:

# Tasks:
# #1 order=1 parallel=true  → Start immediately
# #2 order=2 parallel=true  → Start immediately (concurrent with #1)
# #3 order=3 parallel=true  → Start immediately (concurrent with #1, #2)
# #4 order=4 parallel=false → WAIT for #1, #2, #3 to complete
# #5 order=5 parallel=false → Start after #4
# #6 order=6 parallel=true  → Start immediately (concurrent with #5)

# Execution timeline:
# Time 0:  #1, #2, #3 start concurrently
# Time X:  #1, #2, #3 all complete → #4 starts
# Time Y:  #4 complete → #5 starts
# Time Z:  #5 in progress, #6 can start concurrently

# Rule: adjacent parallel=true run concurrently
#       parallel=false waits for ALL preceding parallel tasks
```

### [CRITICAL] Transitive Dependencies Check

```python
# Check ONE level deep for indirect dependencies

# Task A modifies: src/Models/User.php
# Task B modifies: src/Services/UserService.php
# UserService.php imports User.php

# Analysis:
# - A touches User.php
# - B touches UserService.php
# - UserService IMPORTS User
# - Transitive dependency exists!

# Result: parallel=false for both tasks

def check_transitive_deps(task_A_files, task_B_files, project_imports):
    for file_a in task_A_files:
        for file_b in task_B_files:
            # Check if B imports A
            if file_a in project_imports.get(file_b, []):
                return False  # Transitive dependency found
    return True  # No transitive dependency
```

### [CRITICAL] File Scope in Content (Required)

```python
# When creating subtasks, include FILES in content:

# For sequential task:
mcp__vector-task__task_create(
    title="Update User Model",
    content="Add soft deletes to User model.\nFILES: [app/Models/User.php]",
    parent_id=42,
    order=1,
    parallel=False
)

# For parallel task (add PARALLEL note):
mcp__vector-task__task_create(
    title="Product API",
    content="Implement CRUD for products.\n"
            "FILES: [src/Api/ProductsController.php, src/Services/ProductService.php]\n"
            "PARALLEL: This task may execute concurrently with siblings. Stay within listed file scope.",
    parent_id=42,
    order=2,
    parallel=True
)

# WHY: Executor reads file scopes from content for conflict detection
# Without explicit files, parallel safety chain starts blind
```

### Batch Trivial Operations (Don't Decompose)

```python
# When ALL conditions met, create 1 task with checklist instead of multiple:

conditions = {
    "identical_operation": True,   # Same operation (rename, format, move)
    "trivial": True,               # <5 min each, no logic change
    "independent": True            # No cross-file dependencies
}

if all(conditions.values()):
    # SINGLE task with checklist
    mcp__vector-task__task_create(
        title="Rename 10 controller methods",
        content="Rename process* to handle* in controllers:\n"
                "- [ ] UserController::processLogin → handleLogin\n"
                "- [ ] UserController::processLogout → handleLogout\n"
                "- [ ] ProductController::processCreate → handleCreate\n"
                "- [ ] ... (10 total)",
        estimate=0.5,
        tags=["chore", "batch:trivial", "strict:relaxed", "cognitive:minimal"]
    )
else:
    # Create separate subtasks
    pass

# WHY: 5 identical trivial tasks waste 5x planning overhead
```

### Sequence Analysis Before Creation

```python
# BEFORE creating 2+ subtasks: STOP and THINK

# Use SequentialThinking for complex dependencies:
# 1. List all work items
# 2. Identify dependencies (what needs what)
# 3. Group independent items (can be parallel)
# 4. Order dependent items (dependencies first)
# 5. Set order + parallel flags

# Example analysis:
items = [
    {"name": "Database schema", "needs": [], "files": ["migrations/"]},
    {"name": "User model", "needs": ["Database schema"], "files": ["app/Models/User.php"]},
    {"name": "Product model", "needs": ["Database schema"], "files": ["app/Models/Product.php"]},
    {"name": "User API", "needs": ["User model"], "files": ["app/Api/UsersController.php"]},
    {"name": "Product API", "needs": ["Product model"], "files": ["app/Api/ProductsController.php"]}
]

# Analysis result:
# - Database schema: order=1, parallel=false (foundation)
# - User model + Product model: order=2, parallel=true (both need schema, independent)
# - User API + Product API: order=3, parallel=true (independent, different models)
```

### Logical Order Rule

```python
# Subtasks MUST be in logical execution order
# Dependencies first, dependents after

# WRONG order:
# 1. Use User model (depends on creating it!)
# 2. Create User model

# RIGHT order:
# 1. Create User model
# 2. Use User model

# Order assignment:
order = 1
for item in topological_sort(items_by_dependency):
    item["order"] = order
    order += 1
```

### No Test/Quality Subtasks

```python
# FORBIDDEN: Creating separate subtasks for tests/quality

forbidden_titles = [
    "Write tests",
    "Add test coverage",
    "Run quality gates",
    "Code quality checks",
    "Verify implementation"
]

# WHY:
# - Executors write tests DURING implementation (>=80% coverage)
# - Validators run ALL quality gates automatically
# - Separate test subtasks = redundant (executor says "already done")

# INSTEAD: Tests are part of EACH implementation subtask
```

### File Manifest Before Parallel

```python
# BEFORE marking parallel=true, explicitly list ALL files per task:

task_A_files = ["src/UserService.php", "src/UserRepository.php"]
task_B_files = ["src/ProductService.php", "src/ProductRepository.php"]
task_C_files = ["src/OrderService.php", "tests/OrderTest.php"]

# Cross-reference
all_files = task_A_files + task_B_files + task_C_files
if len(all_files) != len(set(all_files)):
    # Overlap detected → parallel: false for ALL overlapping tasks
    pass
```

### [CRITICAL] Global Blacklist (Never Edit in Parallel)

```python
# These files are FORBIDDEN in parallel context regardless of siblings:

BLACKLIST = [
    # 1. Dependency manifests & locks
    "composer.json", "package.json", "composer.lock", "package-lock.json",
    "Gemfile", "go.mod", "Cargo.toml", "requirements.txt",
    
    # 2. Environment
    ".env", ".env.local", ".env.production",
    
    # 3. Global config
    "config/**", "settings/**",
    
    # 4. Routing
    "routes/**", "routes/web.php", "routes/api.php",
    
    # 5. Schema/Migrations
    "database/migrations/**", "db/migrate/**",
    
    # 6. Infrastructure/CI
    ".github/**", ".gitlab-ci.yml", "Dockerfile", "docker-compose.yml",
    "Makefile", "Jenkinsfile",
    
    # 7. Test/Lint/Build config
    "phpunit.xml", "jest.config.js", "tsconfig.json",
    ".eslintrc.js", "vite.config.js"
]

# If task REQUIRES blacklisted file:
# → Record in comment: "BLOCKED: needs {file} (globally shared)"
# → Complete non-blacklisted work first
# → Blacklisted file handled in sequential phase
```

### Parallel Context Detection

```python
task = mcp__vector-task__task_get(task_id=42)

if task.parallel and task.parent_id:
    # PARALLEL CONTEXT ACTIVE
    # Other agents may be executing siblings RIGHT NOW
    
    # 1. Fetch siblings with same parent
    siblings = mcp__vector-task__task_list(parent_id=task.parent_id)
    
    # 2. Filter parallel siblings (not self)
    parallel_siblings = [
        s for s in siblings["tasks"] 
        if s.parallel and s.id != task.id
    ]
    
    # 3. Filter ACTIVE siblings (in_progress only matters)
    active_siblings = [
        s for s in parallel_siblings 
        if s.status == "in_progress"
    ]
    
    # 4. Extract their scopes from comments
    sibling_scopes = {}
    for sibling in active_siblings:
        if "PARALLEL SCOPE:" in sibling.get("comment", ""):
            # Parse: "PARALLEL SCOPE: [file1.php, file2.php]"
            import re
            match = re.search(r'PARALLEL SCOPE:\s*\[(.*?)\]', sibling["comment"])
            if match:
                files = [f.strip() for f in match.group(1).split(",")]
                sibling_scopes[sibling["id"]] = files
```

### Sibling Status Interpretation

```python
# parallel=true means CAN run concurrently, not IS running

status_threat_level = {
    "pending": "ZERO threat - not started, ignore for conflict detection",
    "completed": "NO threat - files stable, no active conflict",
    "in_progress": "POTENTIAL threat - the ONLY status that matters"
}

# in_progress WITHOUT scope in comment:
# → Sibling still planning, proceed normally (NOT a red flag)

# in_progress WITH scope in comment:
# → REAL concurrent data, cross-reference for conflicts
```

### [CRITICAL] Report Own Scope

```python
# After planning (when actual files known), store scope in comment:

mcp__vector-task__task_update(
    task_id=42,
    comment="PARALLEL SCOPE: [src/Auth/LoginController.php, src/Auth/LoginService.php, tests/Auth/LoginTest.php]",
    append_comment=True
)

# WHY: Siblings read your scope from task comment (already fetched via task_list)
# NO extra MCP calls needed

# DO NOT store scopes in vector memory - scopes are ephemeral, not semantic knowledge
```

### Scope Restriction in Parallel

```python
# In PARALLEL CONTEXT: modify ONLY files in your task scope

task = mcp__vector-task__task_get(task_id=42)

# Files explicitly in task content
my_scope = parse_files_from_content(task.content)

# If need to modify file NOT in scope:
# → DO NOT modify
# → Record: "SCOPE EXTENSION NEEDED: {file} — reason: {why}"
# → Let validation or next sequential task handle it
```

### Check Before Edit (Parallel)

```python
# Before ANY Edit in parallel context:

def safe_edit(file_path, sibling_scopes, blacklist):
    # Check blacklist
    if any(pattern in file_path for pattern in blacklist):
        return "BLOCKED: globally shared file"
    
    # Check sibling scopes
    for sibling_id, files in sibling_scopes.items():
        if file_path in files:
            return f"DEFERRED: file in active sibling #{sibling_id} scope"
    
    # Safe to edit
    return "SAFE"

# If blocked/deferred:
# → Record in comment: "DEFERRED COSMETIC: {file}:{line} — {issue}"
# → Continue with other work
# → Deferred items are NOT failures
```

### Parallel-Safe Task Creation

```python
# SAFE: Different services, no overlap
mcp__vector-task__task_create_bulk([
    {
        "title": "Users API",
        "content": "FILES: [src/Api/UsersController.php, src/Services/UserService.php]",
        "parent_id": 1,
        "estimate": 3.0,
        "order": 1,
        "parallel": True
    },
    {
        "title": "Products API",
        "content": "FILES: [src/Api/ProductsController.php, src/Services/ProductService.php]",
        "parent_id": 1,
        "estimate": 3.0,
        "order": 2,
        "parallel": True
    },
    {
        "title": "Orders API",
        "content": "FILES: [src/Api/OrdersController.php, src/Services/OrderService.php]",
        "parent_id": 1,
        "estimate": 3.0,
        "order": 3,
        "parallel": True
    }
])
# All three run concurrently - zero file overlap

# UNSAFE: Shared model
mcp__vector-task__task_create_bulk([
    {"title": "User API", "content": "FILES: [src/UserController.php, app/Models/User.php]", ...},
    {"title": "Admin API", "content": "FILES: [src/AdminController.php, app/Models/User.php]", ...}
])
# WRONG! Shared User.php → parallel: false for both
```

### Git Safety in Parallel Context

```python
# In PARALLEL CONTEXT with active siblings:
if task.parallel and active_siblings:
    # Stage ONLY task-scope files
    # Excludes memory/ and sibling work
    bash(f"git add {' '.join(my_scope_files)}")

# In NON-PARALLEL context:
else:
    # Full state checkpoint INCLUDING memory/
    bash("git add -A")

# WHY: 
# - Parallel: git add -A stages half-done sibling work + causes conflicts
# - Sequential: git add -A preserves full project state for revert
```

### [CRITICAL] Memory Folder Protection

```python
# memory/ contains SQLite databases (vector memory + tasks)
# SACRED - protect at ALL times

# NEVER in any context:
# git checkout memory/
# git restore memory/
# git reset memory/
# git clean memory/

# These DESTROY all project knowledge irreversibly
```

### Validation During Parallel

```python
# During validation in parallel context:

if task.parallel and active_siblings:
    sibling_scopes = extract_sibling_scopes(active_siblings)
    
    # Before fixing cosmetic issue:
    for file in files_to_fix:
        if file in sibling_scopes.values():
            # DEFER - file belongs to active sibling
            deferred.append(f"{file}: {issue}")
            continue
        
        if is_blacklisted(file):
            # DEFER - globally shared
            deferred.append(f"{file}: {issue} (globally shared)")
            continue
        
        # Safe to fix inline
        fix_issue(file, issue)
    
    # Record deferred items in comment (NOT failures)
    if deferred:
        mcp__vector-task__task_update(
            task_id=task.id,
            comment=f"DEFERRED COSMETIC (parallel):\n" + "\n".join(deferred),
            append_comment=True
        )
```

---

## Validation Scenarios
<!-- description: How to validate tasks. Completion checks, fix-tasks, re-validation. -->

### Validate Completed Task

```python
task = mcp__vector-task__task_get(task_id=42)

if task.status == "completed":
    # Run validation checks
    # - All requirements met
    # - Tests passing
    # - No garbage code
    # - Coverage >= 80%
    
    # If passed:
    mcp__vector-task__task_update(task_id=42, status="validated", comment="All checks passed", append_comment=True)
    
    # If failed, create fix-tasks:
    # mcp__vector-task__task_create(title="Fix: missing tests", parent_id=42, tags=["validation-fix"])
```

### Aggregation Validation (Parent)

```python
# Parent with all subtasks validated - fast path
children = mcp__vector-task__task_list(parent_id=42)
all_validated = all(c["status"] == "validated" for c in children["tasks"])
has_fix_tasks = any("validation-fix" in c.get("tags", []) for c in children["tasks"])

if all_validated and not has_fix_tasks:
    # All children validated, no fix tasks - aggregate results
    mcp__vector-task__task_update(task_id=42, status="validated", comment="Aggregation: all children validated", append_comment=True)
```

### Re-validation After Fixes

```python
# Fix-tasks completed - mandatory full re-validation
fix_tasks = mcp__vector-task__task_list(parent_id=42, tags=["validation-fix"])
all_fixes_done = all(t["status"] == "validated" for t in fix_tasks["tasks"])

if all_fixes_done:
    # Must run full validation again - fixes may introduce new issues
    # ... run validation ...
```

---

## Tag Intelligence Scenarios
<!-- description: Tag frequencies, IDF weights, classification by boost level. -->

### Get Tag Frequencies

```python
freq = mcp__vector-task__tag_frequencies()
# Returns: {tag: {count, frequency, idf_weight}}

# High frequency = low signal (api, backend)
# Low frequency = high signal (vendor:stripe, module:terminal)
```

### Classify Tags by Boost Level

```python
# Single tag
classification = mcp__vector-task__tag_classify(tag="vendor:stripe")
# Returns: {level: "high", boost: 1.5, reason: "Specific vendor identifier"}

# Batch classification
batch = mcp__vector-task__tags_classify_batch(tags=["api", "vendor:stripe", "status:pending"])
# Returns: {high: ["vendor:stripe"], low: ["api"], filter_only: ["status:pending"]}
```

### IDF Weights for Search Ranking

```python
weights = mcp__vector-task__tag_weights()
# Returns: {tag: idf_weight}

# Rare tags (vendor:stripe) → high weight (1.44)
# Common tags (api) → low weight (0.38)
```

---

## Debug & Developer Scenarios
<!-- description: Inspect embeddings, canonical tags, bulk operations, database stats. -->

### Inspect Task Embedding

```python
# Task embeddings are internal but search_explain shows ranking factors
explained = mcp__vector-task__search_explain(query="authentication", limit=5)

for result in explained["results"]:
    print(f"Task #{result['task_id']}: {result['title']}")
    for tc in result["tag_classifications"]:
        print(f"  Tag: {tc['tag']}, Level: {tc['level']}, IDF: {tc['idf_weight']}")
```

### Get All Canonical Tags

```python
canonicals = mcp__vector-task__get_canonical_tags()
# Returns list of all predefined canonical tags
```

### Bulk Operations

```python
# Bulk create (max 50)
mcp__vector-task__task_create_bulk([
    {"title": f"Task {i}", "content": f"Description {i}", "estimate": 1.0}
    for i in range(10)
])

# Bulk delete (max 100)
mcp__vector-task__task_delete_bulk(task_ids=[1, 2, 3, 4, 5])
```

### Database Statistics

```python
stats = mcp__vector-task__task_stats()

print(f"Total tasks: {stats['total_tasks']}")
print(f"By status: {stats['by_status']}")
print(f"With subtasks: {stats['with_subtasks']}")
print(f"Next task ID: {stats['next_task_id']}")
print(f"Unique tags: {stats['unique_tags']}")
```

---

## Tag Selection Scenarios
<!-- description: Cognitive level, strict mode, safety escalation, tag formula. -->

### Cognitive Level Selection

Cognitive level calibrates how much analysis/research the agent performs.

```python
# MINIMAL: Trivial tasks, no research needed
# - Single file rename, typo fix, config change
# - Memory probes: 0-1, Research: none, Agents: 0
mcp__vector-task__task_create(
    title="Fix typo in README",
    content="Change 'teh' to 'the'",
    estimate=0.1,
    tags=["chore", "docs", "cognitive:minimal", "strict:relaxed"]
)

# STANDARD: Normal tasks, some research if needed
# - Feature implementation, bug fix with known solution
# - Memory probes: 2-3, Research: on error/ambiguity, Agents: auto (2-3)
mcp__vector-task__task_create(
    title="Add pagination to users list",
    content="Implement cursor-based pagination",
    estimate=2.0,
    tags=["feature", "api", "cognitive:standard", "strict:standard"]
)

# DEEP: Complex tasks, extensive research
# - New architecture, performance optimization, security feature
# - Memory probes: 3-5, Research: required, Agents: 3-5
mcp__vector-task__task_create(
    title="Implement OAuth2 with PKCE",
    content="Add OAuth2 authorization code flow with PKCE for mobile apps",
    estimate=8.0,
    tags=["feature", "auth", "cognitive:deep", "strict:strict"]
)

# EXHAUSTIVE: Critical/unknown territory
# - Security audit, migration to new stack, debugging complex race condition
# - Memory probes: 5+, Research: exhaustive, Agents: max
mcp__vector-task__task_create(
    title="Debug random production crashes",
    content="Investigate and fix intermittent crashes in payment processing",
    estimate=16.0,
    tags=["bugfix", "database", "cognitive:exhaustive", "strict:paranoid"]
)
```

### Strict Mode Selection

Strict mode calibrates validation intensity and quality gate strictness.

```python
# RELAXED: Low risk, cosmetic changes
# - Skip non-critical tests, allow minor style issues
# - Use for: README updates, comments, formatting
mcp__vector-task__task_create(
    title="Update code comments",
    content="Add PHPDoc to UserController",
    estimate=0.5,
    tags=["chore", "backend", "strict:relaxed", "cognitive:minimal"]
)

# STANDARD: Normal validation
# - Full test suite, standard linting, 80% coverage
# - Use for: Most features, refactors, non-critical fixes
mcp__vector-task__task_create(
    title="Refactor UserService",
    content="Extract validation logic to separate class",
    estimate=3.0,
    tags=["refactor", "backend", "strict:standard", "cognitive:standard"]
)

# STRICT: High risk, critical paths
# - 100% coverage, strict types, no warnings, full static analysis
# - Use for: auth, payments, migrations, API contracts
mcp__vector-task__task_create(
    title="Add Stripe webhook handler",
    content="Handle payment_intent.succeeded events",
    estimate=4.0,
    tags=["feature", "api", "strict:strict", "cognitive:deep"]
)

# PARANOID: Maximum security/correctness
# - Everything in STRICT + manual review required, audit logging
# - Use for: security fixes, credential handling, destructive operations
mcp__vector-task__task_create(
    title="Fix credential leak in logs",
    content="Remove API keys from error logs and audit trail",
    estimate=2.0,
    tags=["bugfix", "security", "strict:paranoid", "cognitive:deep"]
)
```

### [CRITICAL] Safety Escalation (Automatic)

Certain file patterns automatically escalate strict level. Agent tags can RAISE but never LOWER below safety floor.

```python
# File patterns → strict minimum (CANNOT be lowered):

PATTERNS = {
    # CRITICAL (strict:paranoid)
    ".env": "paranoid",              # Environment secrets
    "credentials": "paranoid",        # Credential files
    "secrets": "paranoid",            # Secret files
    "config/auth": "paranoid",        # Auth config
    "private keys": "paranoid",       # .pem, .key files
    "certificates": "paranoid",       # .crt, .cert files
    
    # HIGH (strict:strict)
    "auth/": "strict",                # Authentication code
    "guards/": "strict",              # Authorization guards
    "policies/": "strict",            # Access policies
    "permissions/": "strict",         # Permission system
    "payments/": "strict",            # Payment processing
    "billing/": "strict",             # Billing logic
    "stripe/": "strict",              # Stripe integration
    "subscription/": "strict",        # Subscription management
    "migrations/": "strict",           # Database migrations
    "schema": "strict",               # Schema definitions
    
    # STANDARD (strict:standard)
    "CI/": "standard",                # CI pipelines
    ".github/": "standard",           # GitHub Actions
    "Dockerfile": "standard",         # Container config
    "docker-compose": "standard",     # Docker compose
    "routes/": "standard",            # Routing
    "middleware/": "standard",        # Middleware
    "composer.json": "standard",      # PHP dependencies
    "package.json": "standard",       # JS dependencies
}

# Context patterns → level minimum:
CONTEXT_ESCALATION = {
    "priority=critical": "strict+deep",
    "tag hotfix": "strict+standard",
    "tag production": "strict+standard",
    "touches >10 files": "standard+standard",
    "tag breaking-change": "strict+deep",
    "keyword security": "strict",
    "keyword encryption": "strict",
    "keyword auth": "strict",
    "keyword permission": "strict",
    "keyword migration": "strict",
    "keyword schema": "strict",
    "keyword database drop": "strict",
}

# Example: Task tagged relaxed but touches .env → auto-escalated to paranoid
mcp__vector-task__task_create(
    title="Update database config",
    content="FILES: [.env]. Update DB connection settings.",
    estimate=0.5,
    tags=["chore", "config", "strict:relaxed", "cognitive:minimal"]
    # → Effective level: strict:paranoid (auto-escalated from relaxed)
)

# Example: Task tagged relaxed but touches auth/ → auto-escalated to strict
mcp__vector-task__task_create(
    title="Update login validation",
    content="FILES: [src/auth/LoginValidator.php]. Add rate limiting.",
    estimate=2.0,
    tags=["feature", "auth", "strict:relaxed", "cognitive:standard"]
    # → Effective level: strict:strict (auto-escalated from relaxed)
)
```

### Combined Tag Formula

Every task should follow this formula:

```
1 TYPE + 1 DOMAIN + 0-2 WORKFLOW + 1 STRICT + 1 COGNITIVE [+ 1 BATCH if applicable]
```

```python
# Simple feature
mcp__vector-task__task_create(
    title="Add user avatar upload",
    content="Allow users to upload profile pictures",
    estimate=3.0,
    tags=["feature", "backend", "strict:standard", "cognitive:standard"]
)

# Bug fix with validation issue
mcp__vector-task__task_create(
    title="Fix null pointer in OrderService",
    content="Handle case when order.items is null",
    estimate=1.0,
    tags=["bugfix", "backend", "validation-fix", "strict:strict", "cognitive:standard"]
)

# Complex decomposed task
mcp__vector-task__task_create(
    title="Migrate to PostgreSQL",
    content="Switch from MySQL to PostgreSQL with zero downtime",
    estimate=24.0,
    tags=["refactor", "database", "decomposed", "strict:strict", "cognitive:exhaustive"]
)

# Trivial batch operation
mcp__vector-task__task_create(
    title="Rename 15 controller files",
    content="Rename *Controller.php to *Ctrl.php for consistency",
    estimate=0.5,
    tags=["chore", "backend", "batch:trivial", "strict:relaxed", "cognitive:minimal"]
)

# Parallel-safe subtask
mcp__vector-task__task_create(
    title="Products API endpoints",
    content="FILES: [src/Api/Products/*.php]. CRUD implementation.",
    estimate=3.0,
    parent_id=100,
    order=2,
    parallel=True,
    tags=["feature", "api", "parallel-safe", "strict:standard", "cognitive:standard"]
)
```

### Predefined Tag Categories

| Category | Tags | Usage |
|----------|------|-------|
| **TYPE** | `feature`, `bugfix`, `refactor`, `research`, `docs`, `test`, `chore`, `spike`, `hotfix` | What kind of work |
| **DOMAIN** | `backend`, `frontend`, `database`, `api`, `auth`, `ui`, `config`, `infra`, `ci-cd`, `migration` | Which area |
| **WORKFLOW** | `decomposed`, `validation-fix`, `blocked`, `stuck`, `needs-research`, `light-validation`, `parallel-safe`, `atomic`, `manual-only`, `regression` | Pipeline stage |
| **STRICT** | `strict:relaxed`, `strict:standard`, `strict:strict`, `strict:paranoid` | Validation intensity |
| **COGNITIVE** | `cognitive:minimal`, `cognitive:standard`, `cognitive:deep`, `cognitive:exhaustive` | Analysis depth |
| **BATCH** | `batch:trivial` | Batch operations |

### Tag Search by Category

```python
# Find all tasks needing research
needs_research = mcp__vector-task__task_list(tags=["needs-research"])

# Find all blocked tasks
blocked = mcp__vector-task__task_list(tags=["blocked"], status="pending")

# Find all security-related tasks with high strictness
security = mcp__vector-task__task_list(query="security authentication", tags=["strict:paranoid"])

# Find all parallel-safe subtasks
parallel = mcp__vector-task__task_list(tags=["parallel-safe"], status="pending")
```

---

## Statistics & Reporting Scenarios
<!-- description: Task stats with time filters, grouping by priority/tags/parent, progress tracking. -->

### Default Statistics Overview

```python
stats = mcp__vector-task__task_stats()

print(f"Total tasks: {stats['total_tasks']}")
print(f"Pending: {stats['by_status']['pending']}")
print(f"In Progress: {stats['by_status']['in_progress']}")
print(f"Completed: {stats['by_status']['completed']}")

# Calculate completion percentage
completion_pct = (stats['by_status']['completed'] / stats['total_tasks']) * 100
print(f"Progress: {completion_pct:.1f}%")
```

### Time-Based Filters

```python
# Tasks completed today
today = mcp__vector-task__task_stats(
    finish_after="2026-02-19",
    status="completed"
)

# Tasks completed this week
this_week = mcp__vector-task__task_stats(
    finish_after="2026-02-13",  # Monday
    status="completed"
)

# Tasks created in last 7 days
recent = mcp__vector-task__task_stats(
    created_after="2026-02-12"
)

# Tasks completed yesterday
yesterday = mcp__vector-task__task_stats(
    finish_after="2026-02-18",
    finish_before="2026-02-19",
    status="completed"
)
```

### Group by Priority

```python
# Get all tasks and group by priority
all_tasks = mcp__vector-task__task_list(limit=100)

by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
for task in all_tasks["tasks"]:
    priority = task.get("priority", "medium")
    by_priority[priority] += 1

print(f"Critical: {by_priority['critical']}")
print(f"High: {by_priority['high']}")
print(f"Medium: {by_priority['medium']}")
print(f"Low: {by_priority['low']}")
```

### Group by Tags

```python
# Extract and count unique tags
all_tasks = mcp__vector-task__task_list(limit=100)

tag_counts = {}
for task in all_tasks["tasks"]:
    for tag in task.get("tags", []):
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

# Sort by count descending
sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
for tag, count in sorted_tags[:10]:
    print(f"{tag}: {count}")
```

### Group by Parent

```python
# Root tasks vs subtasks
all_tasks = mcp__vector-task__task_list(limit=100)

root_tasks = [t for t in all_tasks["tasks"] if t.get("parent_id") is None]
child_tasks = [t for t in all_tasks["tasks"] if t.get("parent_id") is not None]

print(f"Root tasks: {len(root_tasks)}")
print(f"Subtasks: {len(child_tasks)}")

# Group children by parent
by_parent = {}
for task in child_tasks:
    parent_id = task["parent_id"]
    by_parent[parent_id] = by_parent.get(parent_id, 0) + 1
```

### Sprint Progress Tracking

```python
# Get sprint statistics
sprint = mcp__vector-task__task_stats(
    created_after="2026-02-01",
    created_before="2026-02-28"
)

total = sprint['total_tasks']
completed = sprint['by_status']['completed']
validated = sprint['by_status']['validated']
pending = sprint['by_status']['pending']

print(f"Sprint Progress:")
print(f"  [{('#' * completed):<{total}}] {completed}/{total} ({completed/total*100:.0f}%)")
print(f"  Validated: {validated}")
print(f"  Remaining: {pending}")
```

---

## Brainstorm & Ideation Scenarios
<!-- description: Iterative ideation loop, creating subtasks from brainstorm outcomes. -->

### Iterative Ideation Loop

```python
# After loading task context, present ideas and iterate
task = mcp__vector-task__task_get(task_id=42)

# Present initial ideas
print("## Approaches")
print("1. Approach A - ...")
print("2. Approach B - ...")

# Ask for user input
user_response = ask("Your thoughts? More ideas? Say 'proceed' when done.")

# Keep iterating until user confirms
while "proceed" not in user_response.lower():
    # Generate more ideas based on user input
    print("## Building on Your Input")
    print("- New idea 1...")
    print("- New idea 2...")
    user_response = ask("More ideas? Or 'proceed' to continue?")

# Proceed to action selection
print("What would you like to do?")
print("1. Update task")
print("2. Create subtasks")
print("3. End session")
```

### Create Subtasks from Brainstorm

```python
# After brainstorm, create actionable subtasks
parent_id = 42

mcp__vector-task__task_create_bulk([
    {
        "title": "Implement Option A",
        "content": "FILES: [src/OptionA.php]. Approach chosen during brainstorm.",
        "parent_id": parent_id,
        "estimate": 3.0,
        "order": 1,
        "parallel": False,
        "tags": ["feature", "backend", "strict:standard", "cognitive:standard"]
    },
    {
        "title": "Add tests for Option A",
        "content": "FILES: [tests/OptionATest.php]. Test coverage for new feature.",
        "parent_id": parent_id,
        "estimate": 2.0,
        "order": 2,
        "parallel": False,
        "tags": ["test", "backend", "strict:standard", "cognitive:minimal"]
    }
])

# Store brainstorm insights to memory
mcp__vector-memory__store_memory(
    content="Brainstorm #42: Chose Option A over B because of performance. Key considerations: caching, error handling.",
    category="architecture",
    tags=["decision", "reusable"]
)
```

---

## Multi-Probe Search Scenarios
<!-- description: Query decomposition, 2-3 focused probes, aspect-based searching. -->

### Query Decomposition

```python
# WRONG: Single query
results = mcp__vector-task__task_list(query="authentication")  # Misses related tasks

# RIGHT: Decompose into 2-3 focused probes
# Probe 1: What
results_1 = mcp__vector-task__task_list(query="authentication login JWT", limit=5)

# Probe 2: How
results_2 = mcp__vector-task__task_list(query="token refresh session", limit=5)

# Probe 3: Why/Context
results_3 = mcp__vector-task__task_list(query="security user verification", limit=5)

# Merge unique insights
all_ids = set()
merged_results = []
for results in [results_1, results_2, results_3]:
    for task in results["tasks"]:
        if task["id"] not in all_ids:
            all_ids.add(task["id"])
            merged_results.append(task)
```

### Aspect-Based Searching

```python
# Complex query: "How to implement user auth with JWT in Laravel"
# Decompose into semantic aspects:

# Probe 1: Implementation
impl = mcp__vector-task__task_list(query="JWT authentication Laravel implementation", limit=3)

# Probe 2: Security concerns
security = mcp__vector-task__task_list(query="user login security token", limit=3)

# Probe 3: Error handling
errors = mcp__vector-task__task_list(query="auth failure error handling", limit=3)

# Combine unique findings
```

### Debugging Multi-Probe

```python
# "Why tests fail" → Too vague
# Decompose:

# Probe 1: Specific module failure
module_failures = mcp__vector-task__task_list(query="test failure {module_name}", limit=3)

# Probe 2: Similar bug fixes
similar_fixes = mcp__vector-task__task_list(query="bug fix test error", limit=3)

# Probe 3: Error message patterns
error_patterns = mcp__vector-task__task_list(query="{error_message}", limit=3)
```

---

## Comment Context Scenarios
<!-- description: Parse accumulated context from comments. Memory IDs, files, failures, blockers. -->

### Parse Accumulated Context

```python
task = mcp__vector-task__task_get(task_id=42)
comment = task.get("comment", "")

# Extract memory IDs (#NNN patterns)
import re
memory_ids = re.findall(r'#(\d+)', comment)

# Extract file paths
file_paths = re.findall(r'(src/[\w/\.]+|tests/[\w/\.]+)', comment)

# Extract execution history
if "completed" in comment or "Done" in comment:
    # Previous work was done
    
# Extract failures
if "failed" in comment or "error" in comment:
    failures = re.findall(r'(?:failed|error):?\s*(.+?)(?:\n|$)', comment, re.IGNORECASE)

# Extract blockers
if "BLOCKED" in comment:
    blockers = re.findall(r'BLOCKED:\s*(.+?)(?:\n|$)', comment)

# Extract decisions
if "DECISION:" in comment or "chose" in comment:
    decisions = re.findall(r'(?:DECISION|chose):\s*(.+?)(?:\n|$)', comment, re.IGNORECASE)

print(f"Memory IDs: {memory_ids}")
print(f"Files: {file_paths}")
print(f"Failures: {failures}")
print(f"Blockers: {blockers}")
```

### Use Comment Context in Execution

```python
task = mcp__vector-task__task_get(task_id=42)

# Parse comment for context
comment_context = parse_comment(task.get("comment", ""))

# If previous memory IDs exist, fetch them
if comment_context["memory_ids"]:
    for mem_id in comment_context["memory_ids"]:
        memory = mcp__vector-memory__get_by_memory_id(memory_id=mem_id)
        # Use memory content for context

# If failures exist, avoid those approaches
if comment_context["failures"]:
    print(f"Avoiding failed approaches: {comment_context['failures']}")

# If blockers exist, check if resolved
if comment_context["blockers"]:
    print(f"Previous blockers: {comment_context['blockers']}")
    # Check if blocker is resolved before proceeding
```

### Store Context Links in Comments

```python
# After task completion, store critical context
mcp__vector-task__task_update(
    task_id=42,
    comment="Done. Key findings:\n"
             "- Memory #45: API design decision\n"
             "- Memory #46: Error handling pattern\n"
             "- Modified: src/Auth/Login.php:45-78\n"
             "- Created: tests/AuthTest.php\n"
             "- DECISION: Chose JWT over sessions (see #45)",
    append_comment=True
)
```

---

## Memory Integration Scenarios
<!-- description: Integration with Vector Memory MCP. Categories, tags, pre-task mining, post-task storage. -->

Integration with Vector Memory MCP (`mcp__vector-memory__*` tools). Memory is PRIMARY storage for reusable knowledge. Task comments contain CRITICAL links only.

### Memory Categories for Tasks

| Category | When to Use | Example Content |
|----------|-------------|-----------------|
| `code-solution` | Working implementations, patterns | "Solution: Use ->with() for eager loading" |
| `bug-fix` | Root causes, fixes applied | "N+1 query in UserController. Fix: eager load roles" |
| `architecture` | Design decisions, trade-offs | "Chose JWT over sessions. Rationale: stateless, scalable" |
| `learning` | Insights, discoveries | "Discovered: sqlite-vec requires explicit cast to blob" |
| `debugging` | Troubleshooting steps | "Steps: 1) Check embedding dims 2) Verify cosine similarity" |
| `performance` | Optimizations, benchmarks | "Query time reduced 80% by adding index on user_id" |
| `security` | Vulnerabilities, fixes | "XSS in user input. Fix: htmlspecialchars() on output" |
| `project-context` | Project-specific conventions | "This project uses TDD: write test first, then code" |

### Memory Tags for Task Integration

| Tag Type | Examples | Usage |
|----------|----------|-------|
| CONTENT | `solution`, `failure`, `decision`, `insight`, `workaround`, `deprecated` | What kind of content |
| SCOPE | `reusable`, `project-wide`, `module-specific`, `temporary` | Breadth of applicability |

Formula: 1 CONTENT + 0-1 SCOPE. Example: `["solution", "reusable"]` or `["failure", "module-specific"]`

### Pre-Task Memory Mining

```python
# BEFORE starting work on task, mine memory aggressively
task = mcp__vector-task__task_get(task_id=42)

# Multi-probe search for solutions
solutions = mcp__vector-memory__search_memories(
    query=f"{task['title']} solution pattern",
    category="code-solution",
    limit=5
)

# Search for related failures (to AVOID these approaches)
failures = mcp__vector-memory__search_memories(
    query=f"{task['title']} failure error bug",
    category="debugging",
    limit=5
)

# Search for architecture decisions (constraints to follow)
decisions = mcp__vector-memory__search_memories(
    query=f"{task['title']} architecture decision",
    category="architecture",
    limit=3
)

# Extract blocked approaches from failures
blocked_approaches = []
for mem in failures["memories"]:
    if "does not work" in mem["content"] or "failed" in mem["content"]:
        blocked_approaches.append(mem["content"][:100])

# Use context in task execution
print(f"Found {len(solutions['memories'])} solutions")
print(f"AVOID these approaches: {blocked_approaches}")
```

### Post-Task Memory Storage

```python
# AFTER task completion, store UNIQUE insights

# ALWAYS search before store to prevent duplicates
existing = mcp__vector-memory__search_memories(
    query="JWT refresh token rotation pattern",
    limit=3
)

if not existing["memories"]:
    # Store new insight with full context
mcp__vector-memory__store_memory(
        content="JWT Refresh Token Rotation:\n"
                "Problem: Tokens don't rotate, security risk\n"
                "Solution: Return new refresh token with each access token refresh\n"
                "Pattern: Store previous token hash, invalidate on next refresh\n"
                "When to use: Any JWT-based auth system\n"
                "Gotchas: Handle concurrent requests with token family tracking\n"
                "Context: Discovered during task #42 for user auth system",
        category="code-solution",
        tags=["solution", "reusable"]
    )
else:
    # Similar exists - skip or update via delete+store
    print(f"Similar memory exists: #{existing['memories'][0]['id']}")
```

### Task-Memory Workflow Cycle

```python
# Complete workflow: Task → Memory Mining → Execute → Store → Link

# 1. Get task
task = mcp__vector-task__task_get(task_id=42)

# 2. Mine memory for context
context = mcp__vector-memory__search_memories(
    query=f"{task['title']} {task['content'][:50]}",
    limit=5
)

# 3. Start task
mcp__vector-task__task_update(
    task_id=42,
    status="in_progress",
    comment=f"Memory context: {[f'#{m[\"id\"]}' for m in context['memories']]}",
    append_comment=True
)

# 4. Execute task (do the work...)
# ... implementation ...

# 5. Store findings to memory
new_memory = mcp__vector-memory__store_memory(
    content="Key insight from task #42...",
    category="code-solution",
    tags=["solution", "reusable"]
)

# 6. Link memory in task comment
mcp__vector-task__task_update(
    task_id=42,
    status="completed",
    comment=f"Completed. Insights stored in memory #{new_memory['memory_id']}",
    append_comment=True
)
```

### Inter-Agent Memory Handoff

```python
# When delegating to another agent, pass memory hints as TEXT
# (agents share memory but not session context)

delegation_prompt = """
TASK: Implement user authentication

MEMORY HINTS (search these in mcp__vector-memory__search_memories):
- "JWT authentication Laravel flow"
- "token refresh pattern"
- "session management security"
- "auth error handling"

CONTEXT FROM PREVIOUS AGENT:
- Memory #45: API design decision (use this approach)
- Memory #46: Error handling pattern (follow this)
- Memory #47: Approach X failed (AVOID)

AFTER COMPLETION:
1. Store your findings to memory (category: code-solution)
2. Update task comment with new memory IDs
"""

# Delegate with context
Task(subagent_type="general", prompt=delegation_prompt)
```

### Link Memory in Task Comments

```python
# During execution, document memory discoveries in task comments

# Link discovered memories
mcp__vector-task__task_update(
    task_id=42,
    comment="Research phase:\n"
            "- Found pattern in memory #30 (caching strategy)\n"
            "- Memory #31 shows why approach X failed (AVOID)\n"
            "- Memory #32 has working solution for similar problem",
    append_comment=True
)

# After completion, store and link
new_mem = mcp__vector-memory__store_memory(
    content="New pattern: eager load with ->with() prevents N+1",
    category="code-solution",
    tags=["solution", "reusable"]
)

mcp__vector-task__task_update(
    task_id=42,
    comment=f"Completed. Pattern stored in memory #{new_mem['memory_id']}",
    append_comment=True,
    status="completed"
)
```

### Memory-Aware Task Decomposition

```python
# Before decomposing, check memory for patterns
task = mcp__vector-task__task_get(task_id=42)

# Search for decomposition patterns
patterns = mcp__vector-memory__search_memories(
    query="task decomposition pattern similar features",
    category="architecture",
    limit=3
)

# Use patterns to inform decomposition
if patterns["memories"]:
    # Apply learned decomposition pattern
    subtasks = apply_decomposition_pattern(patterns["memories"][0])
else:
    # Default decomposition
    subtasks = default_decompose(task)

# Create subtasks
mcp__vector-task__task_create_bulk(subtasks)
```

### Memory Categories by Task Type

```python
# Choose memory category based on task type
task_type_to_category = {
    "feature": "code-solution",     # New implementations
    "bugfix": "bug-fix",            # Bug fixes and root causes
    "refactor": "code-solution",    # Improved patterns
    "research": "learning",         # Discoveries
    "docs": "project-context",      # Documentation conventions
    "test": "code-solution",        # Test patterns
    "chore": "project-context",     # Project maintenance
    "spike": "learning",            # Experiments
    "hotfix": "bug-fix"             # Urgent fixes
}

# Store with appropriate category
task = mcp__vector-task__task_get(task_id=42)
category = task_type_to_category.get(extract_task_type(task), "code-solution")

mcp__vector-memory__store_memory(
    content="Insight content...",
    category=category,
    tags=["solution", "reusable"]
)
```

---
---

## Workflow Scenarios
<!-- description: Multi-step MCP operation sequences with verification. Create-then-validate, update-then-confirm patterns. -->

### Create-Then-Validate

After task_create, immediately task_get to confirm fields persisted correctly. Prevents phantom tasks.

**Priority:** HIGH

```python
# Step 1: Create the task
result = mcp__vector-task__task_create({
    "title": "Add rate limiting to API endpoints",
    "description": "Implement rate limiting middleware for all /api/* routes. Apply to controllers in app/Http/Controllers/Api/.",
    "tags": ["feature", "api", "strict:standard"],
    "estimate": 3.0,
    "priority": "high"
})

# Step 2: Validate by fetching the created task
task = mcp__vector-task__task_get({
    "task_id": result["task_id"]
})

# Step 3: Confirm fields
# task.title == "Add rate limiting to API endpoints" → title persisted
# task.status == "pending" → correct initial status
# "feature" in task.tags → tags persisted
# task.estimate == 3.0 → estimate persisted
# If task_get returns error → creation failed silently
# If fields mismatch → data integrity issue
```

**When to use:**
- After creating tasks with complex tag sets
- After creating subtasks in a hierarchy (verify parent_id linkage)
- When task_create returns success but downstream operations depend on the task existing
- Before starting delegation that references the created task_id

**Iron rule alignment:**
- `explore-before-execute` (CRITICAL): mandates exploring context before execution
- This pattern extends it: execute-then-verify for write operations
- Combined flow: explore (context check) → create → validate (get + confirm)

**Governance:** Uses compile-time preset. No additional cookbook pulls needed.

---

### Create-Subtask-Then-Validate-Hierarchy

For hierarchical tasks: create subtask, verify parent linkage.

```python
# Step 1: Verify parent exists and is accessible
parent = mcp__vector-task__task_get({
    "task_id": "parent-42"
})
# Confirm: parent exists, parent.status allows subtask creation

# Step 2: Create subtask
result = mcp__vector-task__task_create({
    "title": "Implement rate limiter middleware class",
    "description": "Create RateLimiterMiddleware in app/Http/Middleware/",
    "tags": ["feature", "api"],
    "estimate": 1.5,
    "parent_id": "parent-42"
})

# Step 3: Validate subtask + hierarchy
subtask = mcp__vector-task__task_get({
    "task_id": result["task_id"]
})
# Confirm: subtask.parent_id == "parent-42"
# Confirm: subtask.status == "pending"

# Step 4: Verify parent sees child (optional)
parent_refreshed = mcp__vector-task__task_get({
    "task_id": "parent-42"
})
# Confirm: result["task_id"] in parent_refreshed.children
```

**Iron rule alignment:**
- `parent-readonly` (CRITICAL): parent task is READ-ONLY, never update parent status manually
- Status propagation is AUTOMATIC: child→pending implies parent→pending

---
---

## Gates Rules Scenarios
<!-- description: Critical gates and constitutional rules. WHEN to enforce, not HOW to implement. -->

Critical rules and guardrails for task operations. Violations break system integrity.

Use `query="critical"` or `query="high"` to filter by priority.

### Iron Rules

**[CRITICAL] MCP-Only Access**
```
RULE: ALL task operations MUST use MCP tools.
WHY: MCP ensures embedding generation and data integrity.
VIOLATION: Use mcp__vector-task__* tools exclusively.
```

**[CRITICAL] Explore Before Execute**
```
RULE: MUST explore task context (parent, children, related) BEFORE starting execution.
WHY: Prevents duplicate work, ensures alignment with broader goals, discovers dependencies.
VIOLATION: mcp__vector-task__task_get({task_id}) + parent + children BEFORE mcp__vector-task__task_update({status: "in_progress"})
```

**[CRITICAL] Estimate Required**
```
RULE: EVERY task MUST have estimate in hours. No task without estimate.
WHY: Estimates enable planning, prioritization, progress tracking, and decomposition decisions.
VIOLATION: Add estimate parameter. Leaf tasks ≤4h, parent tasks = sum of children.
```

**[CRITICAL] Timestamps Auto**
```
RULE: NEVER set start_at/finish_at manually. Timestamps are AUTO-MANAGED by system.
WHY: System sets start_at when status→in_progress, finish_at when status→completed/stopped.
VIOLATION: Remove start_at/finish_at from task_update call.
```

**[CRITICAL] Parent Readonly**
```
RULE: $PARENT task is READ-ONLY context. NEVER call task_update on parent task.
WHY: Parent task lifecycle is managed externally. Prevents infinite loops, hierarchy corruption.
VIOLATION: ABORT any task_update targeting parent_id. Only task_update on assigned $TASK.
```

---

### Security Rules (CRITICAL)

**[CRITICAL] No Secrets in Task Comments**
```
RULE: NEVER store secrets, credentials, tokens, passwords, API keys, PII, or connection strings in task comments (task_update comment).
WHY: Task comments are persistent, searchable, and shared across agents and sessions. Stored secrets are a permanent exfiltration risk.
VIOLATION: Review content before task_update. Strip all literal secret values. Keep only key names and descriptions.

FORBIDDEN in comments:
  - .env values: DB_HOST=192.168.1.5, API_KEY=sk-abc123
  - Connection strings: mysql://user:pass@host/db
  - Tokens: Bearer eyJhbGciOiJIUzI1NiIs...
  - Passwords: password=Secret123
  - Private URLs: https://user:pass@internal.api/...

ACCEPTABLE:
  - "Updated DB_HOST in .env for production"
  - "Rotated API_KEY for payment service"
  - "Config: see .env for credentials"

BAD:  mcp__vector-task__task_update({comment: "DB_HOST=192.168.1.5"})
GOOD: mcp__vector-task__task_update({comment: "Updated database config in .env"})
```

**[CRITICAL] No Secret Exfiltration**
```
RULE: NEVER output sensitive data to chat/response: .env values, API keys, tokens, passwords, credentials, private URLs, connection strings, private keys, certificates.
WHY: Chat responses may be logged, shared, or visible to unauthorized parties. Secret exposure is an exfiltration vector.
VIOLATION: Redact all secret values before displaying. Show key names only, mask values as "***".

When reading config/.env for CONTEXT:
  - Extract key NAMES and STRUCTURE only
  - Never raw values
  - If user asks to show config: show key names, mask values as "***"

If error output contains secrets:
  - Redact before displaying
  - Strip before storing to task comments

Examples:
  BAD:  task_update({comment: "Error: connection to mysql://admin:Secret123@dbhost failed"})
  GOOD: task_update({comment: "Error: connection to mysql://admin:***@dbhost failed"})
  
  BAD:  task_update({comment: "Set DB_HOST=192.168.1.5"})
  GOOD: task_update({comment: "Updated DB_HOST in .env for production"})
```

---

### High Priority Rules

**[HIGH] Single In-Progress**
```
RULE: Only ONE task should be in_progress at a time per agent.
WHY: Prevents context switching and ensures focus.
VIOLATION: mcp__vector-task__task_update({task_id, status: "completed"}) current before starting new.
```

**[HIGH] Parent-Child Integrity**
```
RULE: Parent cannot be completed while children are pending/in_progress.
WHY: Ensures hierarchical consistency.
VIOLATION: Complete or stop all children first.
```

**[HIGH] Memory Primary, Comments Critical**
```
RULE: Vector memory is PRIMARY storage. Task comments for CRITICAL context links only.
WHY: Memory is searchable, persistent, shared. Comments are task-local.
VIOLATION: Move detailed content to memory. Keep only IDs/paths/references in comments.
```

**[HIGH] Order Siblings**
```
RULE: Sibling tasks MUST have unique order (1,2,3,4). Parallel=true enables concurrent execution.
WHY: Order defines strict sequence. Parallel flag enables concurrent execution.
VIOLATION: Set order (unique, sequential) + parallel (true for independent tasks).
```

**[HIGH] Parallel Marking**
```
RULE: Mark parallel: true ONLY for tasks with NO dependency on adjacent siblings.
WHY: Wrong parallel marking causes race conditions or missed dependencies.
VIOLATION: Analyze dependencies. Only mark parallel: true when independence confirmed.
```

---

### Six Constitutional Gates

Six mandatory gates that protect system integrity. Each gate is a self-contained enforcement point.

---

#### Gate 1: MCP-JSON-ONLY

```
RULE: ALL MCP calls MUST use JSON-RPC via MCP tools. NEVER direct database/file access.
WHY: MCP ensures embedding generation, validation, and data integrity.
TRIGGER: Any task/memory operation.

ENFORCEMENT:
  BEFORE: Verify using mcp__vector-task__* or mcp__vector-memory__*
  AFTER: If direct access detected → REJECT + escalate

BAD:  sqlite3.connect('./memory/tasks.db')
GOOD: mcp__vector-task__task_list({...})
```

---

#### Gate 2: Lightweight Lawyer Gate

```
RULE: ALL proposals MUST pass 5-check verification before storage.
WHY: Prevents low-quality proposals from polluting memory.
TRIGGER: Self-improvement proposals, instruction changes.

CHECKLIST:
  1. Iron Rules: Does NOT violate any → PASS
  2. Measurable: Has specific metric → PASS
  3. Reversible: Has rollback plan → PASS
  4. Scope: Does NOT expand task → PASS
  5. Security: Does NOT weaken (or improves) → PASS

ENFORCEMENT:
  IF 5/5 PASS → Store proposal
  IF security/iron_rules/scope FAIL → REJECT
  ELSE → CLARIFY

See: "Lightweight Lawyer Gate Scenarios" section for full details.
```

---

#### Gate 3: Constitutional Learn Protocol

```
RULE: ALL failures with trigger signals MUST store lessons to memory.
WHY: Captures failure patterns for future prevention.
TRIGGER: retries > 0, stuck tag, validation-fix, blocked, user correction.

STEPS:
  1. Detect trigger signal in task
  2. Search memory for duplicates
  3. IF unique → Store with format:
     FAILURE: {what}
     ROOT CAUSE: {why}
     FIX: {how}
     PREVENTION: {pattern}
     CONTEXT: Task #{id}
  4. Link memory ID in task comment

ENFORCEMENT:
  AFTER task completion: IF trigger detected AND no lesson stored → ESCALATE

See: "Constitutional Learn Protocol Scenarios" section for full details.
```

---

#### Gate 4: Category Discipline Contract

```
RULE: Categories are FIXED. NEVER create new categories dynamically.
WHY: Prevents category drift and search fragmentation.
TRIGGER: Any memory/task storage.

ALLOWED CATEGORIES (Task MCP):
  (None - tasks use tags only)

ALLOWED CATEGORIES (Memory MCP):
  code-solution, bug-fix, architecture, learning, debugging,
  performance, security, project-context, other

ENFORCEMENT:
  BEFORE storage: IF category not in allowed list → REJECT
  AFTER storage: IF category mismatch detected → DELETE + re-store

BAD:  store_memory({category: "new-feature", ...})
GOOD: store_memory({category: "code-solution", ...})
```

---

#### Gate 5: Cookbook-First Gate

```
RULE: When uncertain, CALL cookbook() BEFORE assuming or searching elsewhere.
WHY: Cookbook contains authoritative patterns, tools, and best practices.
TRIGGER: Uncertainty about tools, patterns, rules, or procedures.

STEPS:
  1. IF uncertain → mcp__vector-task__cookbook() or mcp__vector-memory__cookbook()
  2. IF answer found → Apply pattern
  3. IF not found → THEN search memory/docs/web

ENFORCEMENT:
  IF question answered by cookbook BUT not called first → WARN
  IF repeated violations → ESCALATE

PRIORITY ORDER:
  1. cookbook() - authoritative
  2. vector memory - context-specific
  3. external docs - supplementary
```

---

#### Gate 6: Failure Escalation Gate

```
RULE: Failures MUST escalate according to severity. NEVER silently continue.
WHY: Prevents error cascades and ensures visibility.
TRIGGER: Any failure, error, or unexpected state.

ESCALATION LEVELS:

| Severity | Condition | Action |
|----------|-----------|--------|
| CRITICAL | Data loss risk, security breach | STOP + ALERT human immediately |
| HIGH | System integrity at risk | STOP + Log + Store lesson |
| MEDIUM | Task failure, retry possible | RETRY (max 3) + Store lesson |
| LOW | Minor issue, workaround exists | LOG + Continue |

ENFORCEMENT:
  IF CRITICAL failure AND continued → SEVERE VIOLATION
  IF retries > 3 AND no escalation → VIOLATION
  IF lesson stored but no retry/escalation → INCOMPLETE

ESCALATION PATH:
  Agent → Brain → Human (CRITICAL only)
```

---

### Cross-Reference with Memory MCP Rules

| Task Rule | Memory Rule | Coordination |
|-----------|-------------|--------------|
| `no-secrets-in-comments` | `no-secrets-in-storage` | NEVER store secrets - both systems |
| `no-secret-exfiltration` | `no-secret-exfiltration` | NEVER output secrets - both systems |
| `mcp-only-access` | `mcp-only-access` | Same rule, different MCP |
| `memory-primary-comments-critical` | `search-before-store` | Memory = PRIMARY, comments = LINKS |
| `explore-before-execute` | `pre-task-mining` | Search memory before task |
| `comment-strategy` | `actionable-content` | Detailed → memory, reference → comment |

---

## Cookbook Usage Scenarios
<!-- description: How to use the cookbook tool. Init, categories, search, pagination. -->

### First Read (Always Start Here)

```python
# ALWAYS call cookbook() first when loading this MCP
result = mcp__vector-task__cookbook()

# Returns:
# - essential: Critical rules to master first
# - case_categories_full: All categories with keys, names, descriptions
# - cookbook_usage: How to use cookbook
# - next_steps: Recommended exploration path
```

### List All Categories

```python
# Get all categories with keys and descriptions
result = mcp__vector-task__cookbook(include="categories")

# Returns:
# {
#   "categories": [
#     {"key": "task-decision", "name": "Task Decision", "description": "When to create task vs inline fix"},
#     {"key": "parallel-execution", "name": "Parallel Execution", "description": "CRITICAL safety patterns..."},
#     ...
#   ],
#   "keys": ["task-decision", "parallel-execution", ...],
#   "usage": 'cookbook(include="cases", case_category="{key}")'
# }
```

### Get Cases by Category

```python
# Filter by category key (kebab-case)
result = mcp__vector-task__cookbook(
    include="cases",
    case_category="parallel-execution"
)

# Other category keys:
# - task-decision: When to create task vs inline fix
# - task-creation: How to create tasks
# - task-execution: How to execute tasks
# - search-query: How to search tasks
# - tag-normalization: How to normalize tags
# - hierarchy-decomposition: How to decompose tasks
# - status-time-tracking: Status lifecycle, time tracking
# - error-handling-recovery: Error handling patterns
# - parallel-execution: CRITICAL safety patterns
# - validation: How to validate tasks
# - tag-intelligence: Tag frequencies, IDF weights
# - tag-selection: Cognitive level, strict mode
# - statistics-reporting: Task stats, progress tracking
# - memory-integration: Integration with Vector Memory MCP
```

### Keyword Search in Cases

```python
# Search for specific topics
result = mcp__vector-task__cookbook(
    include="cases",
    query="security"  # Returns all sections mentioning "security"
)

# Other useful queries:
# - query="critical": All CRITICAL patterns
# - query="parallel": All parallel execution patterns
# - query="memory": All memory integration patterns
# - query="error": All error handling patterns
# - query="tag": All tag-related patterns
```

### Get Documentation by Level

```python
# Level 0: Quick Reference (tools, limits, status flow)
result = mcp__vector-task__cookbook(include="docs", level=0)

# Level 1: Usage Guide (how it works, patterns, best practices)
result = mcp__vector-task__cookbook(include="docs", level=1)

# Level 2: Extended Docs (tag normalization, IDF, anti-patterns)
result = mcp__vector-task__cookbook(include="docs", level=2)

# Level 3: Developer Reference (full parameters, architecture)
result = mcp__vector-task__cookbook(include="docs", level=3)
```

### Pagination

```python
# Limit results
result = mcp__vector-task__cookbook(
    include="cases",
    query="task",
    limit=5,    # Max 5 results
    offset=0    # Start from first result
)

# Next page
result = mcp__vector-task__cookbook(
    include="cases",
    query="task",
    limit=5,
    offset=5    # Skip first 5 results
)

# Returns:
# - content: Matching sections
# - total_matches: Total matches found
# - has_more: True if more results available
```

### Everything (Deep Dive)

```python
# Get all docs + all cases (for comprehensive understanding)
result = mcp__vector-task__cookbook(
    include="all",
    level=2  # Extended docs level
)
```

### Combined Filters

```python
# Category + query
result = mcp__vector-task__cookbook(
    include="cases",
    case_category="parallel-execution",
    query="critical"  # Search within category
)
```

### Quick Reference

| Call | Purpose |
|------|---------|
| `cookbook()` | Init - first read |
| `cookbook(include="categories")` | List all categories |
| `cookbook(include="cases", case_category="key")` | Filter by category |
| `cookbook(include="cases", query="keyword")` | Keyword search |
| `cookbook(include="docs", level=N)` | Docs by level (0-3) |
| `cookbook(include="all", level=N)` | Everything |

---

## Garbage Collection & Cleanup Scenarios
<!-- description: How to detect and clean garbage code. Inline cleanup vs fix-task. Memory cleanup. -->

### What is Garbage Code

| Type | Examples | Detection |
|------|----------|-----------|
| **Unused imports** | `use App\Services\Deprecated;` | Import not used in file |
| **Dead code** | Unreachable code after refactoring | Code not called anywhere |
| **Orphaned helpers** | Functions no longer called | No references found |
| **Debug statements** | `dd()`, `var_dump()`, `console.log` | Debug helpers in code |
| **Commented blocks** | `// function oldImplementation()` | Commented code blocks |
| **Stale TODOs** | `// TODO: fix this` without context | Non-actionable comments |

### [CRITICAL] No-Garbage Rule

```
RULE: Garbage code in task scope = fix-task
WHY: Garbage accumulates, makes codebase harder to maintain
VIOLATION: Create fix-task with garbage cleanup items
```

### Inline Cleanup (During Execution)

```python
# After completing edits, ALWAYS scan changed files for garbage:

def cleanup_changed_files(changed_files):
    for file in changed_files:
        # 1. Remove unused imports
        remove_unused_imports(file)
        
        # 2. Remove dead code
        remove_unreachable_code(file)
        
        # 3. Remove debug statements
        remove_debug_statements(file)
        
        # 4. Remove commented-out blocks
        remove_commented_code(file)
        
        # 5. Clean stale TODOs
        clean_stale_todos(file)
    
    # Re-run syntax check after cleanup
    run_syntax_check(changed_files)

# During validation:
# - Found: 5 lines of unused code
# - Decision: INLINE FIX (delete immediately, rerun tests)
# - If tests pass → validation complete
# - If tests fail → CREATE fix-task
```

### Fix-Task for Garbage (When Inline Not Enough)

```python
# Create fix-task when garbage is too extensive for inline cleanup

# When to create fix-task:
# - Garbage in >3 files
# - Dead code affects architecture
# - Orphaned helpers in shared modules
# - Extensive commented blocks (>50 lines total)

mcp__vector-task__task_create(
    title="Cleanup garbage in UserService module",
    content="FILES: [app/Services/User*.php]\n"
            "Cleanup items:\n"
            "- Remove unused imports (found: 12)\n"
            "- Remove dead code in UserService.php:150-180\n"
            "- Remove orphaned helper validateOldFormat()\n"
            "- Remove debug dd() statements",
    parent_id=current_task_id,
    estimate=0.5,
    tags=["chore", "cleanup", "strict:relaxed", "cognitive:minimal"]
)
```

### Garbage Detection Checklist

```python
# After any refactoring or significant changes:

garbage_checklist = [
    "Unused imports/use/require statements",
    "Unreachable code after refactoring",
    "Orphaned helper functions no longer called",
    "Commented-out code blocks",
    "Stale TODO/FIXME without actionable context",
    "Debug statements (dd, var_dump, console.log, print_r)",
    "Empty methods/classes",
    "Unused variables"
]

for item in garbage_checklist:
    if detected(item):
        if can_fix_inline(item):
            fix_inline(item)
        else:
            add_to_fix_task(item)
```

### Cosmetic vs Functional Garbage

| Type | Examples | Action |
|------|----------|--------|
| **Cosmetic** | Whitespace, typos, formatting, import sorting | Fix IMMEDIATELY inline (NO task) |
| **Functional** | Dead code, unused imports affecting performance | Fix inline if simple, else fix-task |

### Memory Cleanup

```python
# Vector Memory MCP has built-in cleanup tool

# Bulk cleanup by age
mcp__vector-memory__clear_old_memories(
    days_old=30,      # Delete memories older than 30 days
    max_to_keep=1000  # Keep max 1000 memories
)

# Manual deletion of specific memory
mcp__vector-memory__delete_by_memory_id(memory_id=42)

# When to cleanup:
# - After major refactoring (old patterns no longer relevant)
# - After project pivot (old domain knowledge obsolete)
# - When memory database grows too large (>5000 memories)
```

### Task Cleanup (Automatic)

```python
# Task comments self-clean when task is deleted

# When to delete tasks:
# - Completed tasks older than 30 days
# - Canceled tasks no longer needed
# - Duplicate tasks

# Bulk delete
mcp__vector-task__task_delete_bulk(task_ids=[1, 2, 3, 4, 5])

# Note: Comments are ephemeral, not stored in memory
# Memory = long-term knowledge, Comments = task-local state
```

### Cleanup During Validation

```python
# During task validation, detect garbage in changed files:

# 1. Scan changed files
changed_files = get_changed_files()

# 2. Detect garbage
garbage_found = []
for file in changed_files:
    if has_unused_imports(file):
        garbage_found.append(f"{file}: unused imports")
    if has_dead_code(file):
        garbage_found.append(f"{file}: dead code")
    if has_debug_statements(file):
        garbage_found.append(f"{file}: debug statements")

# 3. Handle garbage
if garbage_found:
    # Check if in parallel context
    if is_parallel_context and file_in_sibling_scope(file):
        # DEFER - file belongs to active sibling
        deferred.append(f"DEFERRED CLEANUP: {garbage}")
    else:
        # FIX inline
        fix_garbage_inline(garbage_found)
        re_run_tests()
```

### Parallel Context Cleanup

```python
# In PARALLEL CONTEXT: check sibling scopes before cleanup

if task.parallel and active_siblings:
    for file in changed_files:
        if file in sibling_scopes.values():
            # DEFER cleanup - file in active sibling scope
            mcp__vector-task__task_update(
                task_id=task.id,
                comment=f"DEFERRED CLEANUP: {file} in active sibling scope",
                append_comment=True
            )
        else:
            # Safe to cleanup
            cleanup_file(file)

# Deferred cleanups are NOT failures
```

### Common Garbage Patterns

```python
# PHP unused import
use App\Services\DeprecatedService;  # DELETE

# PHP dead code after refactoring
public function oldImplementation()  # DELETE entire method
{
    // ... no longer called ...
}

# PHP debug statement
dd($userData);  # DELETE
var_dump($result);  # DELETE

# PHP commented block
// public function validateOldFormat()
// {
//     return $this->oldValidator->check();
// }
# DELETE entire block

# PHP stale TODO
// TODO: fix this later  # DELETE (no context, not actionable)

# PHP orphaned helper
private function formatLegacyData($data)  # DELETE (no callers)
{
    // ...
}
```

---

## Anti-Pattern Examples
<!-- description: What NOT to do. Wrong patterns with explanations and correct approaches. -->

### WRONG: Manual Parent Status Update

```python
# NEVER do this
mcp__vector-task__task_update(task_id=parent_id, status="completed")  # WRONG!
```

### WRONG: No Estimate

```python
# NEVER do this
mcp__vector-task__task_create(title="Fix bug", content="...")  # Missing estimate - WRONG!
```

### WRONG: Wrong Parallel Marking

```python
# NEVER mark parallel if files overlap
mcp__vector-task__task_create_bulk([
    {"title": "Task A", "content": "FILES: [src/User.php]", "parallel": True},  # WRONG!
    {"title": "Task B", "content": "FILES: [src/User.php]", "parallel": True}   # Same file!
])
```

### WRONG: Manual Timestamps

```python
# NEVER set start_at/finish_at manually
mcp__vector-task__task_update(task_id=42, start_at="2026-02-19T10:00:00")  # WRONG!
# Let system auto-manage timestamps
```

### WRONG: Using tested Status

```python
# tested is deprecated - use completed → validated
mcp__vector-task__task_update(task_id=42, status="tested")  # WRONG - use validated
```

### CORRECT: Proper Workflow

```python
# 1. Create with estimate
task = mcp__vector-task__task_create(title="Fix bug", content="...", estimate=2.0)

# 2. Start (auto-sets start_at)
mcp__vector-task__task_update(task_id=task["task_id"], status="in_progress")

# 3. Complete (auto-sets finish_at, calculates time_spent)
mcp__vector-task__task_update(task_id=task["task_id"], status="completed", comment="Done", append_comment=True)

# 4. Validate (after quality gates pass)
mcp__vector-task__task_update(task_id=task["task_id"], status="validated", append_comment=True)
```

---

## Technical Debt Management Scenarios
<!-- description: Complete lifecycle for detecting, prioritizing, preventing, and repaying technical debt. -->

Comprehensive patterns for managing technical debt across its entire lifecycle: detection → prioritization → repayment → prevention.

### 1. Detection & Identification

Find and catalog technical debt in the codebase.

```python
# Search for code smells using semantic search
debt_tasks = mcp__vector-task__task_list(query="N+1 query performance slow loading", limit=10)

# Create debt tracking task
mcp__vector-task__task_create(
    title="Detect N+1 queries in API controllers",
    content="""FILES: [app/Http/Controllers/Api/*.php]

Scan all API controllers for:
- Missing eager loading (::with(), ->load())
- Queries in loops
- Lazy loading in serialization

Output: List of files with line numbers and severity.""",
    estimate=3.0,
    tags=["debt:detection", "performance", "backend", "strict:standard"],
    priority="high"
)
```

**Detection Tag Patterns:**

| Pattern | Usage |
|---------|-------|
| `debt:detection` | Active debt hunting tasks |
| `debt:identified` | Confirmed debt locations |
| `smell:*` | Specific code smells (smell:god-object, smell:dead-code) |
| `deprecated:*` | Deprecated patterns found |

**Multi-probe Search for Debt:**

```python
# Find related debt patterns
debt_query_1 = mcp__vector-task__task_list(query="circular dependency", tags=["debt"], limit=5)
debt_query_2 = mcp__vector-task__task_list(query="tight coupling refactoring", tags=["debt"], limit=5)
debt_query_3 = mcp__vector-task__task_list(query="god object too large class", tags=["debt"], limit=5)
```

### 2. Prioritization

Rank debt by impact and effort.

```python
# Impact × Effort Matrix via tags
mcp__vector-task__task_create(
    title="Prioritize PaymentService refactoring",
    content="""Current state: 2000 lines, 45 methods, circular deps

Impact Assessment:
- Blocks: 3 planned features
- Bugs: 2 related incidents this month
- Team velocity: -20% due to this module

Effort: 40h estimated

Recommendation: HIGH priority - blocking feature delivery""",
    estimate=1.0,
    tags=["debt:priority", "debt:high-impact", "backend", "strict:strict"],
    priority="high"
)
```

**Priority Matrix by Tags:**

| Impact | Effort | Priority | Tags |
|--------|--------|----------|------|
| High | Low | **CRITICAL** | `debt:critical`, `strict:strict` |
| High | High | HIGH | `debt:high-impact`, `strict:standard` |
| Low | Low | LOW | `debt:low`, `strict:relaxed` |
| Low | High | MEDIUM | `debt:medium`, `strict:standard` |

**Cognitive Level for Prioritization:**

| Cognitive | Approach |
|-----------|----------|
| `minimal` | Quick scan, tag obvious issues |
| `standard` | Impact/effort matrix |
| `deep` | Cost-of-delay calculation, dependency analysis |
| `exhaustive` | Full debt inventory, velocity impact |

### 3. Prevention

How to avoid creating new debt.

```python
# Definition of Done checklist task
mcp__vector-task__task_create(
    title="Implement DoD checklist for PRs",
    content="""Create PR template with debt prevention:

- [ ] No TODO without linked task
- [ ] All new code has tests (>80% coverage)
- [ ] No deprecated patterns used
- [ ] Dependencies up to date
- [ ] Performance impact assessed
- [ ] Documentation updated

Files: .github/pull_request_template.md""",
    estimate=2.0,
    tags=["debt:prevention", "process", "ci-cd", "strict:standard"],
    priority="medium"
)

# Tag new debt at creation time
mcp__vector-task__task_create(
    title="Add debt-introduced tracking",
    content="""When intentionally adding debt:

1. Create task with tag: debt:intentional
2. Link to feature task via parent_id
3. Add repayment timeline in content
4. Set strict:standard minimum

This makes invisible debt visible.""",
    estimate=1.5,
    tags=["debt:prevention", "process", "strict:relaxed"]
)
```

**Prevention Tag Patterns:**

| Tag | Usage |
|-----|-------|
| `debt:prevention` | Debt prevention measures |
| `debt:intentional` | Knowingly added debt (track it) |
| `dod:*` | Definition of Done items |
| `review:*` | Review checklist items |

### 4. Repayment Strategies

Methods to eliminate accumulated debt.

```python
# Strategy 1: Incremental Refactoring (parallel subtasks)
parent = mcp__vector-task__task_create(
    title="Refactor UserService - Phase 1",
    content="Extract repository pattern, reduce from 800 to 300 lines",
    estimate=12.0,
    tags=["debt:repayment", "refactor", "backend", "strict:strict"]
)

mcp__vector-task__task_create_bulk([
    {"title": "Extract UserRepository", "content": "Move DB queries to repository", "parent_id": parent["task_id"], "estimate": 3.0, "order": 1, "parallel": False, "tags": ["debt:repayment"]},
    {"title": "Update UserService to use repo", "content": "Inject repository, remove direct DB calls", "parent_id": parent["task_id"], "estimate": 2.0, "order": 2, "parallel": False, "tags": ["debt:repayment"]},
    {"title": "Add unit tests for repo", "content": "Test all repository methods", "parent_id": parent["task_id"], "estimate": 2.0, "order": 3, "parallel": True, "tags": ["debt:repayment", "test"]},
    {"title": "Update integration tests", "content": "Verify UserService still works", "parent_id": parent["task_id"], "estimate": 2.0, "order": 3, "parallel": True, "tags": ["debt:repayment", "test"]}
])

# Strategy 2: Boy Scout Rule (inline during other work)
# When working on related task, leave code better than found
# See "Task Decision Scenarios" for inline threshold

# Strategy 3: Quarantine Pattern
mcp__vector-task__task_create(
    title="Quarantine LegacyPaymentService",
    content="""Strategy: Isolate → Rewrite → Migrate

Phase 1: Quarantine (2h)
- Move to Legacy/ namespace
- Add deprecation warnings
- Block new usage via static analysis

Phase 2: Rewrite (16h)
- Create NewPaymentService
- Full test coverage
- Feature parity verification

Phase 3: Migrate (8h)
- Update all call sites
- Feature flags for rollback
- Remove legacy after 2 weeks""",
    estimate=26.0,
    tags=["debt:repayment", "quarantine", "backend", "strict:paranoid"],
    priority="high"
)
```

**Repayment Strategy Selection:**

| Debt Type | Strategy | Parallel? |
|-----------|----------|-----------|
| Scattered small issues | Boy Scout Rule | Inline |
| Large single class | Incremental | Sequential |
| Legacy module | Quarantine | Phased |
| Cross-cutting concern | Parallel refactor | Parallel |

### 5. Emergency Response

When debt causes production incidents.

```python
# Production incident from debt
incident = mcp__vector-task__task_create(
    title="[INCIDENT] Payment timeout - debt root cause",
    content="""INCIDENT: Payment timeouts affecting 15% of transactions

Root Cause: N+1 query in PaymentService (known debt #42)

Immediate Fix: Add eager loading (1h)
Long-term: Full refactoring (link to debt task)

Post-mortem required.""",
    estimate=1.0,
    tags=["incident", "debt:emergency", "payment", "strict:paranoid"],
    priority="critical"
)

# Link to debt task for context
mcp__vector-task__task_update(
    task_id=incident["task_id"],
    comment="Related to debt task #42. This is WHY we track debt.",
    append_comment=True
)

# Create follow-up debt task if not exists
mcp__vector-task__task_create(
    title="Post-mortem: Payment timeout debt",
    content="Document why debt was deprioritized, update debt scoring",
    parent_id=incident["task_id"],
    estimate=1.0,
    tags=["post-mortem", "debt:learning", "strict:standard"]
)
```

**Emergency Escalation:**

| Severity | Action | Strict Level |
|----------|--------|--------------|
| Critical (production down) | Immediate fix + post-mortem | `strict:paranoid` |
| High (degraded) | Fix this sprint | `strict:strict` |
| Medium (workaround exists) | Queue in backlog | `strict:standard` |

### 6. Tracking & Visibility

Keep debt visible and measurable.

```python
# Create debt tracking epic
debt_epic = mcp__vector-task__task_create(
    title="Q1 2026 Debt Reduction Initiative",
    content="Target: Reduce high-priority debt by 50%

Metrics:
- Debt tasks in backlog: X
- Critical debt: X
- Debt velocity: X tasks/week

Weekly review in sprint planning.""",
    estimate=40.0,
    tags=["debt:tracking", "epic", "strict:relaxed"],
    priority="medium"
)

# Get debt statistics
stats = mcp__vector-task__task_stats(tags=["debt"])
# Returns: total, by_status, etc.

# Track debt velocity over time
mcp__vector-memory__store_memory(
    content="Debt Velocity Week 8: 3 repaid, 1 introduced, net -2. Velocity improving vs Week 7 (+1). Trend: positive.",
    category="project-context",
    tags=["debt:velocity", "metrics", "week-8"]
)
```

**Visibility Patterns:**

| Method | Tool | Frequency |
|--------|------|-----------|
| Debt dashboard | `task_stats(tags=["debt"])` | Weekly |
| Trend tracking | Memory MCP store | Weekly |
| Sprint review | Task list by priority | Per sprint |
| Team awareness | Tag debt:visible on all | Continuous |

### 7. Balance Decisions

Feature delivery vs debt reduction.

```python
# Feature vs Debt decision framework
mcp__vector-task__task_create(
    title="Sprint 9 Planning: Feature vs Debt Balance",
    content="""Framework for 80/20 split:

Feature Capacity: 32h
Debt Capacity: 8h (20%)

Debt Candidates (pick by priority):
1. [CRITICAL] PaymentService N+1 - blocks scaling (3h)
2. [HIGH] UserService refactoring - slows features (4h)
3. [MEDIUM] Test coverage gaps - risk (2h)

Decision: #1 + #2 = 7h, within budget.""",
    estimate=1.0,
    tags=["debt:balance", "planning", "strict:standard"],
    priority="medium"
)

# Cost of Delay calculation
mcp__vector-task__task_create(
    title="Calculate CoD for top 5 debt items",
    content="""Cost of Delay = Impact × Urgency × Risk

For each debt item:
- Impact: How much velocity lost? (1-10)
- Urgency: When does it block something? (1-10)
- Risk: Probability of incident? (1-10)

Score = I × U × R (max 1000)

Rank by score, not by gut feeling.""",
    estimate=2.0,
    tags=["debt:balance", "debt:priority", "cognitive:deep"],
    priority="medium"
)
```

**Balance Rules:**

| Rule | Application |
|------|-------------|
| 20% time | Reserve capacity for debt each sprint |
| CoD ranking | Prioritize by cost of delay, not age |
| Blocking rule | Debt blocking features = CRITICAL |
| Incident rule | Debt causing incidents = immediate |

### 8. Dependency Debt

Outdated packages, security vulnerabilities.

```python
# Security vulnerability from outdated dependency
mcp__vector-task__task_create(
    title="[SECURITY] CVE-2026-1234 in lodash 4.17.15",
    content="""Vulnerability: Prototype pollution (CVSS 7.5)
Current: 4.17.15
Required: 4.17.21+
Breaking changes: None identified

Action: Update + verify tests""",
    estimate=1.0,
    tags=["debt:dependency", "security", "strict:paranoid"],
    priority="critical"
)

# Dependency audit task
mcp__vector-task__task_create(
    title="Monthly dependency audit",
    content="""Run: npm audit / composer audit

For each finding:
- Critical/High: Create task immediately
- Medium: Batch for next sprint
- Low: Track in backlog

Files: package.json, composer.json""",
    estimate=2.0,
    tags=["debt:dependency", "process", "strict:standard"],
    priority="medium"
)
```

**Dependency Debt Patterns:**

| Tag | Usage |
|-----|-------|
| `debt:dependency` | Outdated packages |
| `debt:security` | Security vulnerabilities |
| `debt:breaking` | Breaking change blockers |

### 9. Testing Debt

Missing tests, flaky tests, coverage gaps.

```python
# Testing debt identification
mcp__vector-task__task_create(
    title="Testing debt audit: Payment module",
    content="""Coverage: 45% (target: 80%)

Gaps:
- PaymentService::process(): 0%
- RefundService::calculate(): 12%
- WebhookController: 23%

Priority: PaymentService (handles money)

Estimate: 8h for 80% coverage""",
    estimate=1.0,
    tags=["debt:testing", "test", "payment", "strict:strict"],
    priority="high"
)

# Flaky test tracking
mcp__vector-task__task_create(
    title="Fix flaky UserIntegrationTest",
    content="""Flaky rate: 15% (3 failures in 20 runs)

Pattern: Race condition in async email test

Fix: Add proper async wait or mock email service""",
    estimate=2.0,
    tags=["debt:testing", "debt:flaky", "test", "strict:standard"],
    priority="medium"
)

# Test debt prevents refactoring
mcp__vector-task__task_create(
    title="Add tests BEFORE OrderService refactor",
    content="""Blocking: OrderService refactoring (debt #15)

Current coverage: 30%
Required before refactor: 70%

Characterization tests first, then refactor.""",
    estimate=6.0,
    tags=["debt:testing", "debt:blocking", "test", "strict:strict"],
    priority="high"
)
```

**Testing Debt Priority:**

| Scenario | Priority | Reason |
|----------|----------|--------|
| No tests on payment code | CRITICAL | Money handling |
| Flaky tests blocking CI | HIGH | CI reliability |
| Low coverage on new code | MEDIUM | Quality gate |
| Legacy code without tests | LOW | Characterize first |

### Quick Reference: Debt Tag Taxonomy

```
debt:detection      - Active debt hunting
debt:identified     - Confirmed debt locations
debt:priority       - Prioritization tasks
debt:prevention     - Prevention measures
debt:intentional    - Knowingly added debt
debt:repayment      - Active refactoring
debt:emergency      - Incident from debt
debt:tracking       - Visibility/metrics
debt:balance        - Feature vs debt decisions
debt:dependency     - Package updates needed
debt:security       - Security vulnerabilities
debt:testing        - Test coverage gaps
debt:flaky          - Flaky tests
debt:blocking       - Debt blocking other work
debt:velocity       - Debt trend tracking
debt:learning       - Post-mortem insights
debt:critical       - High impact, low effort
debt:high-impact    - Blocks features
debt:low            - Minor issues
debt:medium         - Standard priority
```

---

## Constitutional Learn Protocol Scenarios
<!-- description: Mandatory failure pattern capture. Trigger signals, format, category discipline. -->

Critical protocol for learning from mistakes. NOT optional philosophy—mandatory execution step.

### [CRITICAL] Trigger Detection

Learn Protocol activates when ANY signal present:

| Signal | Detection | Memory Tag |
|--------|-----------|------------|
| `retries > 0` | Comment contains "ATTEMPT [exec]: N/3" where N > 0 | `signal:retry` |
| `stuck` tag | Task has tag `stuck` | `signal:stuck` |
| `validation-fix` | Subtask created for validation issues | `signal:validation-fix` |
| `blocked` | Comment contains "BLOCKED:" | `signal:blocked` |
| User correction | User explicitly corrected output | `signal:correction` |

### [CRITICAL] Execution Format

```python
# After task completion WITH trigger signals:

# Step 1: Check for duplicates
existing = mcp__vector-memory__search_memories({
    "query": "{failure_summary}",
    "category": "bug-fix",
    "limit": 3
})

if not existing["results"]:
    # Step 2: Store lesson
    mcp__vector-memory__store_memory({
        "content": """FAILURE: {what_failed}
ROOT CAUSE: {why_it_failed}
FIX: {how_fixed}
PREVENTION: {pattern_to_prevent}
CONTEXT: Task #{id}, {area}""",
        "category": "bug-fix",
        "tags": ["type:lesson", "signal:{trigger}", "{domain}"]
    })

# Step 3: Link in task comment
mcp__vector-task__task_update({
    "task_id": 42,
    "comment": "Lesson stored: memory #ID (signal:{trigger})",
    "append_comment": True
})
```

### [CRITICAL] Category Assignment

| Signal | Category | Why |
|--------|----------|-----|
| retry, stuck, validation-fix | `bug-fix` | Execution failure |
| blocked | `debugging` | Investigation pattern |
| correction | `learning` | Misunderstanding |

### Non-Triggers

```python
# DO NOT trigger Learn Protocol when:

# Clean execution
task.status == "completed" and retries == 0 and "stuck" not in task.tags

# User cancellation
task.status == "stopped" and user_requested_stop

# Relaxed mode without signals
task.tags contains "strict:relaxed" and "cognitive:minimal" and no_other_signals
```

### Example Scenarios

**Retry Pattern:**

```python
# Task completed after 2 retries
task = mcp__vector-task__task_get(task_id=42)
# Comment: "ATTEMPT [exec]: 2/3\nFixed: added mutex lock"

# Trigger detected: retries > 0
mcp__vector-memory__store_memory({
    "content": """FAILURE: Race condition in OrderService
ROOT CAUSE: Concurrent requests modifying same order
FIX: Added mutex lock around order update
PREVENTION: Always use locks for concurrent mutations in payment flows
CONTEXT: Task #42, OrderService::update""",
    "category": "bug-fix",
    "tags": ["type:lesson", "signal:retry", "race-condition", "payment"]
})
```

**Stuck Pattern:**

```python
# Task marked stuck after 3 attempts
task = mcp__vector-task__task_get(task_id=43)
# Tags: ["stuck", "api", "external"]

# Trigger detected: stuck tag
mcp__vector-memory__store_memory({
    "content": """FAILURE: External API timeout unreachable
ROOT CAUSE: Third-party service dependency without fallback
FIX: Escalated to human, switched to alternative provider
PREVENTION: Always implement circuit breaker for external APIs
CONTEXT: Task #43, PaymentProvider integration""",
    "category": "debugging",
    "tags": ["type:lesson", "signal:stuck", "external-api", "circuit-breaker"]
})
```

---

## Self Improvement Scenarios
<!-- description: Trigger-based suggestion mode for proposing instruction improvements. -->

Allow agents to propose improvements. NOT continuous—only when triggered.

### [HIGH] Activation Triggers

| Trigger | Condition | Example |
|---------|-----------|---------|
| Mode flags | `strict:paranoid` OR `cognitive:exhaustive` | Deep analysis mode |
| User request | "How to improve?" / "Can we optimize?" | Explicit ask |
| High cost | `time_spent` > 200% of `estimate` | Inefficient workflow |
| Pattern repeat | Same failure 3+ times | Systemic issue |

### Budget Constraints

| Constraint | Value |
|------------|-------|
| Max proposals/session | 3 |
| Max content length | 500 characters |
| Initial status | `status:pending` |
| Acceptance | Human review required |

### Proposal Format

```python
# After detecting trigger + passing Lawyer Gate:

mcp__vector-memory__store_memory({
    "content": """PROPOSAL: Add parallel safety checklist to decompose command
PROBLEM: 3 tasks had race conditions this week from wrong parallel marking
SOLUTION: Add 5-condition checklist verification before parallel=true
BENEFIT: Reduce race conditions by 80%, estimated 2h saved per incident
CONTEXT: .claude/commands/task/decompose.md, Task #50""",
    "category": "architecture",
    "tags": ["type:proposal", "status:pending", "source:self", "parallel"]
})
```

### Lifecycle Flow

```
TRIGGER detected
    ↓
LAWYER GATE checks (5/5 required)
    ↓
    ├─→ PASS: Store with status:pending
    │       ↓
    │   Human/Brain review
    │       ↓
    │   ├─→ ACCEPT: Update instruction, status:accepted
    │   └─→ REJECT: Add reason, status:rejected
    │
    └─→ FAIL: Store rejection for learning
            category: learning, status:rejected
```

### Example Scenarios

**High Time Cost Trigger:**

```python
# Task took 6h, estimate was 2h
task = mcp__vector-task__task_get(task_id=45)
# time_spent: 6.0, estimate: 2.0

# Ratio: 300% > 200% threshold
# Trigger: high cost

# After Lawyer Gate passes:
mcp__vector-memory__store_memory({
    "content": """PROPOSAL: Split auth module into smaller submodules
PROBLEM: Auth tasks consistently 3x over estimate due to module complexity
SOLUTION: Decompose into login, register, password modules
BENEFIT: 50% reduction in auth task time, clearer scope
CONTEXT: Task #45, auth module""",
    "category": "architecture",
    "tags": ["type:proposal", "status:pending", "source:self", "auth", "decomposition"]
})
```

**Pattern Repeat Trigger:**

```python
# Same N+1 query pattern in 3 tasks
failures = mcp__vector-memory__search_memories({
    "category": "bug-fix",
    "query": "N+1 query",
    "limit": 10
})
# 3 results with same pattern

# Trigger: pattern repeat

mcp__vector-memory__store_memory({
    "content": """PROPOSAL: Add eager loading verification to validation
PROBLEM: N+1 query pattern repeated 3 times in 2 weeks
SOLUTION: Auto-check for ->with() in controllers during validation
BENEFIT: Prevent 90% of N+1 issues before merge
CONTEXT: Validation flow, Tasks #40, #42, #45""",
    "category": "architecture",
    "tags": ["type:proposal", "status:pending", "source:self", "validation", "n+1"]
})
```

---

## Lightweight Lawyer Gate Scenarios
<!-- description: Self-verification before proposals. 5-check gate without tools. -->

Filter proposals before storage. Text-based self-verify, no tools.

### [HIGH] Verification Checklist

Before storing ANY proposal, verify ALL 5 checks:

| # | Check | Pass Condition | Fail Action |
|---|-------|----------------|-------------|
| 1 | Iron Rules | Does NOT violate any | REJECT |
| 2 | Measurable | Has specific metric | Clarify |
| 3 | Reversible | Can be rolled back | Add rollback |
| 4 | Scope | Does NOT expand task | REJECT |
| 5 | Security | Does NOT weaken (or improves) | REJECT |

### Decision Logic

```python
def lawyer_gate(proposal):
    checks = {
        "iron_rules": not violates_any_iron_rule(proposal),
        "measurable": has_specific_metric(proposal),
        "reversible": has_rollback_plan(proposal),
        "scope": same_or_narrower_scope(proposal),
        "security": security_ok_or_improved(proposal)
    }
    
    passed = sum(checks.values())
    
    if passed == 5:
        return "PASS", None
    elif not checks["security"]:
        return "REJECT", "Security violation"
    elif not checks["iron_rules"]:
        return "REJECT", "Iron Rule violation"
    elif not checks["scope"]:
        return "REJECT", "Scope expansion"
    else:
        return "CLARIFY", f"Missing: {[k for k,v in checks.items() if not v]}"
```

### Pass Example

```python
proposal = {
    "what": "Add parallel safety checklist",
    "problem": "3 race conditions from wrong parallel marking",
    "solution": "5-condition verification before parallel=true",
    "benefit": "80% reduction, 2h saved per incident",
    "rollback": "Remove checklist lines",
    "scope": "Same (decompose command only)"
}

# Gate check:
# 1. Iron Rules: ✓ No violation
# 2. Measurable: ✓ "80% reduction, 2h saved"
# 3. Reversible: ✓ "Remove checklist lines"
# 4. Scope: ✓ Same command
# 5. Security: ✓ N/A (no security impact)

# Result: 5/5 PASS → Store proposal
```

### Fail Examples

```python
# FAIL: Iron Rule violation
proposal = {
    "what": "Auto-complete parent tasks when children done",
    # ...
}

# Gate check:
# Iron Rules: ✗ "Parent-readonly: NEVER update parent manually"
# Result: REJECT

# FAIL: Security violation
proposal = {
    "what": "Disable token expiration for convenience",
    # ...
}

# Gate check:
# Security: ✗ Weakens authentication
# Result: REJECT

# FAIL: Scope expansion
proposal = {
    "what": "Rewrite entire validation system",
    "context": "Task was to fix single test"
}

# Gate check:
# Scope: ✗ Expands from 1 test to entire system
# Result: REJECT
```

### Rejection Storage

```python
# When gate fails, store rejection for learning:

mcp__vector-memory__store_memory({
    "content": """PROPOSAL: {what}
GATE FAILED: {check_name}
REASON: {why_failed}
LESSON: Proposals must pass all 5 checks. Common failure: {pattern}
CONTEXT: Task #{id}""",
    "category": "learning",
    "tags": ["type:proposal", "status:rejected", "gate:failed"]
})
```

---

## Task Folder Workflow Scenarios
<!-- description: Per-root-task filesystem folder lifecycle: create, rename on status, archive on done, read APIs. Requires --task-folder. -->

When the server is launched with `--task-folder /path`, every ROOT task gets a folder
on disk. Subtasks NEVER receive folders. The folder lifecycle mirrors the task status
lifecycle. Filesystem failures are logged and never block DB operations.

### Create Root Task with Auto-Generated Code

```python
# tags drive prefix: feature → FEAT-N, bugfix → FIX-N, refactor → REFACTOR-N, ...
mcp__vector-task__task_create({
  "title": "Implement OAuth2 flow",
  "content": "Add OAuth2 with refresh tokens. FILES: src/auth/oauth.py, tests/test_oauth.py",
  "tags": ["feature", "auth", "strict:strict", "cognitive:deep"],
  "estimate": 6.0
})
# → result.code == "FEAT-44" (next free FEAT-N)
# → folder created at {--task-folder}/FEAT-44/task.md (template populated with title + Vector ID)
```

### Create Root Task with Custom Code (Jira / Linear)

```python
mcp__vector-task__task_create({
  "title": "Migrate billing to Stripe v2",
  "content": "Per OLOM ticket. FILES: src/billing/*",
  "tags": ["feature", "backend", "strict:strict", "cognitive:deep"],
  "estimate": 12.0,
  "code": "OLOM-460"   # honored verbatim, must match ^[A-Z]+-\d+$
})
# → folder created at {--task-folder}/OLOM-460/
```

### Adding Files to a Task Folder

```bash
# Agent / human writes design notes, screenshots, or scratch files into the folder.
# These are part of the task's working set and surface via task_get / task_folder_files.
echo "## Decision log" > {--task-folder}/FEAT-44/decisions.md
cp screenshot.png      {--task-folder}/FEAT-44/
```

### Status Transitions and Folder Rename Behavior

| Transition                       | Folder action                              |
|----------------------------------|--------------------------------------------|
| `* → in_progress`                | none (folder stays at `{code}/`)           |
| `in_progress → completed`        | rename `{code}` → `{code}-on-review`       |
| `completed → in_progress`        | revert: `{code}-on-review` → `{code}`      |
| `completed → tested`             | none (folder stays at `{code}-on-review`)  |
| `tested → validated`             | none                                       |
| `completed/tested/validated → done` | move into top-level `Archive/{code}/` (jump-to-done supported) |

Reverting from `tested`/`validated` back to `in_progress` follows the same revert path.
Subtasks NEVER trigger folder operations regardless of status.

### Archive Lifecycle on `done`

```python
# Walk a task to terminal state, or jump directly from completed/tested/validated:
mcp__vector-task__task_update({"task_id": 44, "status": "done"})
# → folder structure becomes:
#   {--task-folder}/
#       Archive/
#           FEAT-44/
#               task.md
#               decisions.md
#               ... (everything that was at the source)
#       FIX-7/                ← other active tasks unaffected
#       OLOM-460/             ← other active tasks unaffected
```

`Archive/` is a single top-level shared directory at the root of `--task-folder`. Every
archived task lands directly under it as `Archive/{code}/`. The active root never leaves
an empty `{code}/` container behind — the source folder is moved cleanly. `_resolve_existing_folder`
probes in order: `{code}` (active), `{code}-on-review` (review), `Archive/{code}` (done).

### Reading Folder Files via `task_get`

```python
mcp__vector-task__task_get({"task_id": 44})
# →
# {
#   "success": true,
#   "task": { "id": 44, "code": "FEAT-44", "parent_id": null, ... },
#   "folder_path": "tasks/FEAT-44",                # relative to --working-dir when inside
#   "folder_files": [
#     {"path": "tasks/FEAT-44/task.md",      "relative": true},
#     {"path": "tasks/FEAT-44/decisions.md", "relative": true}
#   ],
#   "message": "Task retrieved successfully"
# }
```

`folder_path` / `folder_files` are present ONLY when ALL hold:
1. `--task-folder` is enabled (server-side feature opt-in),
2. `task.parent_id IS NULL` (root task),
3. `task.code` is set (legacy NULL-code rows are skipped).

### Reading Folder Files via `task_folder_files`

```python
# By task ID:
mcp__vector-task__task_folder_files({"task_id": 44})

# Or by code (no DB lookup needed):
mcp__vector-task__task_folder_files({"code": "FEAT-44"})

# Errors (the call is rejected, not silently empty):
mcp__vector-task__task_folder_files({})                          # → "Provide exactly one of task_id or code"
mcp__vector-task__task_folder_files({"task_id": 44, "code": "X"}) # → same error (XOR)
mcp__vector-task__task_folder_files({"task_id": 99})              # → "Subtasks have no folders" (if 99 has parent)
# Note: when --task-folder is OFF, the tool is NOT registered with the MCP server at all.
# Clients see a smaller tool list (no task_folder_files), not a runtime "feature disabled" error.
```

### `project://info` Resource Overview

```python
# MCP resource — read-only project metadata.
# Clients (Claude Desktop, FastMCP-aware tools) read it via the resource URI:
#   project://info
# Returns:
# {
#   "working_dir": "/path/to/project",
#   "task_folder": "/path/to/project/tasks",     # null when feature off
#   "task_folder_enabled": true,
#   "task_folders": [
#     {"code": "FEAT-44", "title": "...", "folder_path": "tasks/FEAT-44",
#      "files_count": 3, "status_suffix": "none"},                 # active root
#     {"code": "FIX-12",  "title": "...", "folder_path": "tasks/FIX-12-on-review",
#      "files_count": 2, "status_suffix": "-on-review"},           # completed root
#     {"code": "OLOM-460","title": "...", "folder_path": "tasks/Archive/OLOM-460",
#      "files_count": 5, "status_suffix": "-done"}                 # archived root
#   ]
# }
```

`status_suffix` is derived from on-disk folder location:
- `none` → folder is at `{code}/` (active),
- `-on-review` → folder is at `{code}-on-review/` (completed, awaiting review),
- `-done` → folder is at `Archive/{code}/` (archived under the top-level `Archive/`).

Canceled tasks and tasks without a code are excluded.

### Resilience Contract

- All FS operations in `TaskFolderManager` catch exceptions and return `False`
  (or `None` for `list_files`). They NEVER raise to the caller.
- `task_create` / `task_update` commit DB rows BEFORE invoking folder hooks —
  a filesystem failure leaves the DB row intact and the response unchanged.
- `task_get` and `task_folder_files` are read-only and best-effort: any FS
  exception leaves the response either silent (folder_path/folder_files omitted
  from `task_get`) or empty (`folder_files: []` from `task_folder_files`).
- Bulk creates isolate per-task FS failures: a `OSError` for one row never
  aborts the rest of the batch.

---

## Standard Search Patterns Quick Reference
<!-- description: Canonical category + query patterns for Memory MCP searches. -->

### Lesson Search

```python
# Find lessons about X (what to AVOID)
mcp__vector-memory__search_memories({
    "category": "bug-fix",
    "query": "type:lesson {domain}",
    "limit": 10
})
```

### Proposal Search

```python
# Find pending proposals
mcp__vector-memory__search_memories({
    "category": "architecture",
    "query": "type:proposal status:pending",
    "limit": 10
})

# Find accepted proposals
mcp__vector-memory__search_memories({
    "category": "architecture",
    "query": "type:proposal status:accepted",
    "limit": 10
})
```

### Pattern Search

```python
# Find working patterns for reuse
mcp__vector-memory__search_memories({
    "category": "code-solution",
    "query": "type:pattern {feature}",
    "limit": 5
})
```

### Signal Search

```python
# Find lessons by trigger signal
mcp__vector-memory__search_memories({
    "category": "debugging",
    "query": "type:lesson signal:stuck",
    "limit": 10
})
```

### Category + Domain Matrix

| Find | Category | Query Pattern |
|------|----------|---------------|
| Failure lessons | `bug-fix` | `type:lesson {domain}` |
| Debug patterns | `debugging` | `type:lesson signal:{X}` |
| Pending proposals | `architecture` | `type:proposal status:pending` |
| Accepted proposals | `architecture` | `type:proposal status:accepted` |
| Working patterns | `code-solution` | `type:pattern {feature}` |
| Decisions | `architecture` | `type:decision {topic}` |
| Insights | `learning` | `type:insight {topic}` |
| Conventions | `project-context` | `type:convention {area}` |

---

## Tag Taxonomy Quick Reference
<!-- description: Standard prefixes for consistent tagging across MCPs. -->

### Prefix Standards

| Prefix | Purpose | Values |
|--------|---------|--------|
| `type:` | Content classification | `lesson`, `proposal`, `pattern`, `decision`, `insight`, `convention` |
| `status:` | Lifecycle state | `pending`, `accepted`, `rejected`, `deprecated` |
| `signal:` | Trigger indicator | `retry`, `stuck`, `validation-fix`, `blocked`, `correction` |
| `source:` | Origin | `self`, `user`, `agent`, `external` |
| `gate:` | Verification result | `passed`, `failed` |

### Tag Combination Rules

```python
# Lesson from retry (minimum)
["type:lesson", "signal:retry", "{domain}"]

# Lesson from stuck with context
["type:lesson", "signal:stuck", "{domain}", "{subdomain}"]

# Pending proposal from self
["type:proposal", "status:pending", "source:self", "{area}"]

# Accepted proposal
["type:proposal", "status:accepted", "source:self", "{area}"]

# Rejected proposal (gate failed)
["type:proposal", "status:rejected", "gate:failed"]

# Working pattern
["type:pattern", "{feature}", "{domain}"]

# Architecture decision
["type:decision", "{topic}", "{area}"]
```

### Tag Interactions

```
type:lesson + status:* → INVALID (lessons don't have status)
type:proposal + status:* → REQUIRED (proposals need status)
type:pattern + status:* → OPTIONAL (patterns can be deprecated)
type:decision + status:* → INVALID (decisions are final)
```

### Max Tags

- **Hard limit:** 10 tags per entry (Memory MCP constraint)
- **Minimum:** 2 tags (`type:` + domain)
- **Recommended:** `type:` + `status:/signal:` + 1-2 domain tags

