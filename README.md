# Vector Task MCP Server

A **secure, vector-based task management server** for Claude Desktop using `sqlite-vec` and `sentence-transformers`. This MCP server provides intelligent task tracking with semantic search capabilities that enhance AI coding assistants by organizing and retrieving development tasks efficiently.

## ✨ Features

- **🔍 Semantic Search**: Vector-based task search using 384-dimensional embeddings
- **💾 Persistent Storage**: SQLite database with vector indexing via `sqlite-vec`
- **🏷️ Smart Organization**: Priorities, tags, and subtasks for better task management
- **📋 Task Lifecycle**: Track tasks from pending → in_progress → completed → tested → validated (or stopped)
- **🔐 Tag Normalization**: Automatic tag deduplication with semantic similarity
- **📊 IDF Weights**: Rare tags boost search relevance more than common tags
- **🎯 Tag Classification**: Filter tags vs boost tags for smart ranking
- **🔄 Alias Scent**: Original tag variants preserved for search context
- **🔒 Security First**: Input validation, path sanitization, and resource limits
- **⚡ High Performance**: Fast embedding generation with `sentence-transformers`
- **📈 Rich Statistics**: Comprehensive task analytics and progress tracking
- **🔄 Hierarchical Tasks**: Support for parent-child task relationships
- **📊 Priority Management**: Organize tasks by priority (low, medium, high, critical)
- **💬 Task Comments**: Add notes and updates to tasks without changing content

## 🛠️ Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Vector DB** | sqlite-vec | Vector storage and similarity search |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | 384D text embeddings |
| **MCP Framework** | FastMCP | High-level tools-only server |
| **Tag Normalization** | Custom (src/normalization.py) | Semantic tag deduplication |
| **Dependencies** | uv script headers | Self-contained deployment |
| **Security** | Custom validation | Path/input sanitization |
| **Testing** | pytest + coverage | Comprehensive test suite |

## 📁 Project Structure

```
vector-task-mcp/
├── main.py                              # Main MCP server entry point
├── README.md                            # This documentation
├── requirements.txt                     # Python dependencies
├── pyproject.toml                       # Modern Python project config
├── .python-version                      # Python version specification
├── claude-desktop-config.example.json  # Claude Desktop config example
│
├── src/                                # Core package modules
│   ├── __init__.py                    # Package initialization
│   ├── models.py                      # Data models & configuration
│   ├── security.py                    # Security validation & sanitization
│   ├── task_store.py                  # SQLite-vec task operations
│   ├── embeddings.py                  # Embedding model wrapper
│   └── normalization.py               # Tag normalization & classification
│
├── tests/                             # Test suite
│   ├── test_task_store.py            # Task store tests
│   └── test_normalization.py         # Normalization tests
│
└── .gitignore                         # Git exclusions
```

## 🗂️ Organization Guide

This project is organized for clarity and ease of use:

- **`main.py`** - Start here! Main server entry point
- **`src/`** - Core implementation (security, task storage)
- **`claude-desktop-config.example.json`** - Configuration template

**New here?** Start with `main.py` and `claude-desktop-config.example.json`

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher (recommended: 3.11)
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Desktop app

**Installing uv** (if not already installed):

macOS and Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:
```bash
uv --version
```

### Installation

#### Option 1: Quick Install via uvx (Recommended)

The easiest way to use this MCP server - no cloning or setup required!

**Once published to PyPI**, you can use it directly:

```bash
# Run without installation (like npx)
uvx vector-task-mcp --working-dir /path/to/your/project
```

**Claude Desktop Configuration** (using uvx):
```json
{
  "mcpServers": {
    "vector-task": {
      "command": "uvx",
      "args": [
        "vector-task-mcp",
        "--working-dir",
        "/absolute/path/to/your/project"
      ]
    }
  }
}
```

> **Note**: Publishing to PyPI is in progress.

#### Option 2: Install from Source (For Development)

1. **Clone the project**:
   ```bash
   git clone <repository-url>
   cd vector-task-mcp
   ```

2. **Install dependencies** (automatic with uv):
   Dependencies are automatically managed via inline metadata in main.py. No manual installation needed.

   To verify dependencies:
   ```bash
   uv pip list
   ```

3. **Test the server**:
   ```bash
   # Test with sample working directory
   uv run main.py --working-dir ./test-tasks
   ```

4. **Configure Claude Desktop**:

   Copy the example configuration:
   ```bash
   cp claude-desktop-config.example.json ~/path/to/your/config/
   ```

   Open Claude Desktop Settings → Developer → Edit Config, and add (replace paths with absolute paths):

   ```json
   {
     "mcpServers": {
       "vector-task": {
         "command": "uv",
         "args": [
           "run",
           "/absolute/path/to/vector-task-mcp/main.py",
           "--working-dir",
           "/your/project/path"
         ]
       }
     }
   }
   ```

   Important:
   - Use absolute paths, not relative paths

5. **Restart Claude Desktop** and look for the MCP integration icon.

#### Option 3: Install with pipx (Alternative)

```bash
# Install globally (once published to PyPI)
pipx install vector-task-mcp

# Run
vector-task-mcp --working-dir /path/to/your/project
```

**Claude Desktop Configuration** (using pipx):
```json
{
  "mcpServers": {
    "vector-task": {
      "command": "vector-task-mcp",
      "args": [
        "--working-dir",
        "/absolute/path/to/your/project"
      ]
    }
  }
}
```

## 📚 Usage Guide

### Available Tools

#### Task Creation & Management

**1. `task_create` - Create New Task**
```
Create a new task:
Title: "Implement user authentication"
Content: "Add JWT-based authentication with refresh tokens"
Priority: high
Tags: ["auth", "backend", "security"]
```

**2. `task_create_bulk` - Create Multiple Tasks**
```
Create multiple tasks at once for batch operations
```

**3. `task_update` - Update Task Fields**
```
Update task 123:
- Status: in_progress
- Priority: critical
- Title: "Updated title"
```

**4. `task_delete` - Delete Task**
```
Delete task with ID 123
```

**5. `task_delete_bulk` - Delete Multiple Tasks**
```
Delete tasks: [123, 124, 125]
```

#### Task Retrieval

**6. `task_list` - List Tasks with Filters**
```
List tasks:
- Status: pending
- Query: "authentication"
- Limit: 10
```

**7. `task_get` - Get Specific Task**
```
Get task with ID 123
```

**8. `task_last` - Get Last Created Task**
```
Show me the last task I created
```

**9. `task_next` - Get Next Task to Work On**
```
What should I work on next?
```
Returns in_progress task if any, otherwise next pending task.

#### Task Lifecycle

**10. `task_start` - Start Task**
```
Start working on task 123
```
Sets status to in_progress and records start time.

**11. `task_finish` - Complete Task**
```
Mark task 123 as completed
```
Sets status to completed and records finish time.

**12. `task_stop` - Stop Task**
```
Stop working on task 123
```
Sets status to stopped (can be resumed later).

**13. `task_resume` - Resume Stopped Task**
```
Resume task 123
```
Sets status back to in_progress.

#### Task Metadata

**14. `task_comment` - Add/Update Comment**
```
Add comment to task 123:
"Updated API endpoint to use v2, all tests passing"
```

**15. `task_add_tag` - Add Tag**
```
Add tag "urgent" to task 123
```

**16. `task_remove_tag` - Remove Tag**
```
Remove tag "urgent" from task 123
```

**17. `task_get_all_tags` - List All Tags**
```
Show all tags used in tasks
```

#### Task Statistics

**18. `task_stats` - Get Task Statistics**
```
Show task statistics
```

Returns:
```json
{
  "total_tasks": 45,
  "by_status": {
    "pending": 20,
    "in_progress": 3,
    "completed": 20,
    "stopped": 2
  },
  "with_subtasks": 5,
  "next_task_id": 12
}
```

### Tag Normalization Tools

**19. `tag_normalize_preview` - Preview Tag Merges**
```
Preview which tags can be merged:
- threshold: 0.90 (strict) or 0.85 (aggressive)
```

Shows similar tags that can be merged into canonical forms.

**20. `tag_normalize_apply` - Apply Tag Normalization**
```
Apply tag normalization with optional dry_run
```

Merges variant tags into canonical forms and stores original variants in `tag_variants`.

**21. `tag_similarity` - Compare Two Tags**
```
Compare similarity between "auth" and "authentication"
```

Returns cosine similarity score (0.0-1.0).

**22. `canonical_tag_add` - Add Canonical Mapping**
```
Add mapping: "authentication" → "auth"
```

**23. `canonical_tag_remove` - Remove Mapping**
```
Remove mapping for "authentication"
```

**24. `canonical_tag_list` - List All Mappings**
```
List all canonical tag mappings
```

**25. `get_canonical_tags` - List Canonical Tags**
```
List all canonical tags only
```

### Tag Intelligence Tools

**26. `tag_frequencies` - Get Tag Frequencies & IDF Weights**
```
Get tag frequencies with IDF weights
```

Returns frequency statistics and IDF weights for search ranking:
```json
{
  "api": {"count": 10, "frequency": 0.4, "idf_weight": 0.621},
  "vendor:stripe": {"count": 1, "frequency": 0.04, "idf_weight": 1.443}
}
```

**27. `tag_weights` - Get Simplified IDF Weights**
```
Get IDF weights for all tags (for search ranking)
```

**28. `tag_classify` - Classify Single Tag**
```
Classify tag "vendor:stripe"
```

Returns boost level (high/medium/low/filter_only) for ranking.

**29. `tags_classify_batch` - Classify Multiple Tags**
```
Classify tags: ["vendor:stripe", "api", "status:pending"]
```

**30. `search_explain` - Search with Ranking Explanation**
```
Search for "authentication" with ranking explanation
```

Shows how IDF weights, classification, and variants affect ranking.

### Task Priorities

| Priority | Use Cases |
|----------|-----------|
| `critical` | Production bugs, security issues, blockers |
| `high` | Important features, major improvements |
| `medium` | Regular features, enhancements (default) |
| `low` | Nice-to-have, refactoring, documentation |

### Task Status Lifecycle

**Available statuses**: `pending`, `in_progress`, `completed`, `tested`, `validated`, `stopped`

```
pending → in_progress → completed → tested → validated
              ↓
           stopped → (resume) → in_progress
```

| Status | Description |
|--------|-------------|
| `pending` | Task not yet started |
| `in_progress` | Currently being worked on |
| `completed` | Task finished (basic completion) |
| `tested` | Task completed and tested |
| `validated` | Task completed, tested, and validated |
| `stopped` | Task paused/blocked (can be resumed) |

## 🔧 Configuration

### Command Line Arguments

```bash
# Run with uv (recommended)
uv run main.py --working-dir /path/to/project

# Working directory is where task database will be stored
uv run main.py --working-dir ~/projects/my-project
```

**Available Options:**
- `--working-dir` (required): Directory where task database will be stored

### Working Directory Structure

```
your-project/
├── memory/
│   └── tasks.db              # SQLite database with task vectors
├── src/                      # Your project files
└── other-files...
```

### Database Schema

**tasks table**:
- Core task data + `tags` (canonical) + `tag_variants` (original variants)

**canonical_tags table**:
- Predefined tag mappings (variant → canonical)

**task_vectors table**:
- 384-dimensional embeddings for semantic search

### Security Limits

- **Max task content**: 10,000 characters
- **Max bulk create**: 50 tasks per operation
- **Max bulk delete**: 100 tasks per operation
- **Max tags per task**: 10 tags
- **Path validation**: Blocks suspicious characters

## 🎯 Use Cases

### For Individual Developers

```
# Track feature development
"Implement OAuth2 integration with Google and GitHub providers"

# Track bug fixes
"Fix memory leak in WebSocket connection handler"

# Track learning tasks
"Learn and implement Redis caching for API responses"
```

### For Team Workflows

```
# Sprint planning
"Sprint 23: Redesign user dashboard with new analytics"

# Code review tasks
"Review PR #456: Database migration for user preferences"

# Infrastructure tasks
"Set up CI/CD pipeline for automated testing and deployment"
```

### For Project Management

```
# Epic-level tasks
"User Management System" (parent task)
  → "User registration" (subtask)
  → "Email verification" (subtask)
  → "Password reset" (subtask)

# Milestone tracking
"v2.0 Release Preparation"

# Technical debt
"Refactor legacy authentication module to use new security library"
```

## 🏷️ Tag Normalization

### Overview

Tag normalization reduces tag fragmentation by merging semantically similar tags:

| Before | After |
|--------|-------|
| auth, authentication, auth-api, login | → **auth** |
| db, database, database-setup | → **database** |
| api, rest api, API | → **api** |

### Hard Guards (Prevent Wrong Merges)

| Guard | Rule | Example |
|-------|------|---------|
| **Version** | Different versions → NO | `php8` ≠ `php7` |
| **Numeric** | Different numbers → NO | `api1` ≠ `api2` |
| **Facet** | Different prefixes → NO | `type:*` ≠ `domain:*` |
| **Prefix** | Structured ≠ Plain | `type:refactor` ≠ `refactor` |

### Substring Boost

Tags that are substrings get a small boost if:
- Shorter word ≥ 4 characters
- Not in stop-words (api, ui, db, etc.)

Example: `"laravel"` ⊂ `"laravel framework"` → boost to 0.95

### Facet Model (Colon Tags)

Tags with colons (`prefix:value`) are treated as structured facets:

```
type:refactor     ← facet: "type", value: "refactor"
vendor:stripe     ← facet: "vendor", value: "stripe"
module:terminal   ← facet: "module", value: "terminal"
```

Rules:
- Same prefix can merge if similar: `type:refactor` ↔ `type:refactoring` ✅
- Different prefixes never merge: `type:*` ↔ `domain:*` ❌
- Structured never merges with plain: `type:*` ↔ `refactor` ❌

### Tag Variants (Alias Scent)

When tags are migrated, original variants are preserved:

```json
{
  "tags": ["auth"],
  "tag_variants": ["authentication", "auth-api", "login"]
}
```

Variants provide:
- Context for search ranking
- Explanation in UI ("Why auth? Because was login/authentication")
- Rerank signal for queries

## 📊 IDF Weights & Tag Classification

### IDF (Inverse Document Frequency)

Rare tags boost relevance more than common tags:

```
idf_weight = 1 / log(1 + frequency)
```

| Tag | Count | IDF Weight | Effect |
|-----|-------|------------|--------|
| `api` | 70% of tasks | 0.38 | Low signal |
| `vendor:stripe` | 3% of tasks | 1.44 | Strong signal |

### Tag Classification

Tags are classified by boost level:

| Level | Boost | Examples |
|-------|-------|----------|
| `high` | 1.5 | `vendor:*`, `module:*`, `service:*` |
| `medium` | 1.0 | Facet tags (`domain:*`, `type:*`), specific tags |
| `low` | 0.5 | General tags (`api`, `backend`, `test`) |
| `filter_only` | 0.1 | `status:*`, `priority:*` |

### Search Ranking

Final search score combines:
1. **Vector similarity** (cosine distance)
2. **IDF weight** (rare tags boost more)
3. **Tag classification** (high > medium > low > filter)
4. **Variant bonus** (tasks with tag_variants get small boost)

## 🔍 How Semantic Search Works

The server uses **sentence-transformers** to convert tasks into 384-dimensional vectors that capture semantic meaning:

### Example Searches

| Query | Finds Tasks About |
|-------|---------------------|
| "authentication" | Login, JWT, OAuth, user verification |
| "database optimization" | SQL queries, indexing, performance |
| "frontend components" | React, UI elements, styling |
| "API integration" | REST endpoints, webhooks, external services |

### Hierarchical Tasks

Create parent-child relationships:

```
# Create parent task
task_create(title="User Management", content="Complete user system")
# Returns: task_id = 100

# Create subtasks
task_create(title="User Registration", content="...", parent_id=100)
task_create(title="Email Verification", content="...", parent_id=100)
task_create(title="Password Reset", content="...", parent_id=100)
```

## 📊 Task Statistics

The `task_stats` tool provides comprehensive insights:

```json
{
  "total_tasks": 247,
  "by_status": {
    "pending": 120,
    "in_progress": 8,
    "completed": 80,
    "tested": 20,
    "validated": 10,
    "stopped": 9
  },
  "pending_count": 120,
  "in_progress_count": 8,
  "completed_count": 80,
  "tested_count": 20,
  "validated_count": 10,
  "stopped_count": 9,
  "with_subtasks": 15,
  "next_task_id": 45
}
```

### Statistics Fields Explained

- **total_tasks**: Total number of tasks in database
- **by_status**: Task count breakdown by status (pending, in_progress, completed, tested, validated, stopped)
- **pending_count**: Tasks not yet started
- **in_progress_count**: Tasks currently being worked on
- **completed_count**: Tasks finished (basic completion)
- **tested_count**: Tasks that have been tested
- **validated_count**: Tasks that have been validated
- **stopped_count**: Tasks that were stopped (can be resumed)
- **with_subtasks**: Number of parent tasks with subtasks
- **next_task_id**: ID of the next task to work on (smart selection)

## 🛡️ Security Features

### Input Validation
- Sanitizes all user input to prevent injection attacks
- Removes control characters and null bytes
- Enforces length limits on all content

### Path Security
- Validates and normalizes all file paths
- Prevents directory traversal attacks
- Blocks suspicious character patterns

### Resource Limits
- Limits bulk operations and individual task size
- Prevents database bloat
- Implements safe transaction handling

### SQL Safety
- Uses parameterized queries exclusively
- No dynamic SQL construction from user input
- SQLite WAL mode for safe concurrent access

## 🔧 Troubleshooting

### Common Issues

#### Server Not Starting
```bash
# Check if uv is installed
uv --version

# Test server manually
uv run main.py --working-dir ./test

# Check Python version
python --version  # Should be 3.10+
```

#### Claude Desktop Not Connecting
1. Verify absolute paths in configuration
2. Check Claude Desktop logs: `~/Library/Logs/Claude/`
3. Restart Claude Desktop after config changes
4. Test server manually before configuring Claude

#### Task Search Not Working
- Verify sentence-transformers model downloaded successfully
- Check database file permissions
- Try broader search terms
- Review task content for relevance

### Debug Mode

Run the server manually to see detailed logs:

```bash
uv run main.py --working-dir ./debug-test
```

## 🚀 Advanced Usage

### Task Organization Strategies

#### By Project Phase
Use tags to organize by development phase:
- `["phase-1", "mvp", "core-features"]`
- `["phase-2", "optimization", "performance"]`
- `["phase-3", "polish", "ux-improvements"]`

#### By Technology Stack
- `["frontend", "react", "typescript"]`
- `["backend", "python", "fastapi"]`
- `["devops", "docker", "kubernetes"]`

#### By Feature Domain
- `["authentication", "security", "jwt"]`
- `["payments", "stripe", "billing"]`
- `["analytics", "reporting", "dashboard"]`

### Integration with Development Workflow

#### Agile Sprint Planning
```
Create sprint backlog tasks with priorities
Track progress with task_start/task_finish
Use task_stats for sprint reports
```

#### Bug Tracking
```
Create bug tasks with "critical" priority
Add tags: ["bug", "production", "hotfix"]
Use comments for debugging notes
```

#### Feature Development
```
Create parent task for feature
Add subtasks for implementation steps
Track each subtask through lifecycle
```

## 📈 Performance Benchmarks

Based on testing with various dataset sizes:

| Task Count | Search Time | Storage Size | RAM Usage |
|------------|-------------|--------------|-----------|
| 1,000 | <50ms | ~5MB | ~100MB |
| 5,000 | <100ms | ~20MB | ~200MB |
| 10,000 | <200ms | ~40MB | ~300MB |

*Tested on MacBook Air M1 with sentence-transformers/all-MiniLM-L6-v2*

## 🧪 Test Coverage

```
tests/
├── test_task_store.py     # 60 tests - Task store operations
└── test_normalization.py  # 45 tests - Tag normalization

Total: 105 tests
```

Run tests:
```bash
uv run pytest tests/ -v
```

## 🔄 Backward Compatibility

New features are backward compatible:

| Feature | Migration |
|---------|-----------|
| `tag_variants` column | Auto-added via ALTER TABLE |
| `canonical_tags` table | Auto-created via CREATE TABLE IF NOT EXISTS |
| IDF reranking | Opt-in via `use_idf_rerank=True` |

Existing databases work without changes. New columns/tables added automatically on first run.

## 🤝 Contributing

This is a standalone MCP server designed for personal/team use. For improvements:

1. **Fork** the repository
2. **Modify** as needed for your use case
3. **Test** thoroughly with your specific requirements
4. **Share** improvements via pull requests

## 📄 License

This project is released under the MIT License.

## 🙏 Acknowledgments

- **sqlite-vec**: Alex Garcia's excellent SQLite vector extension
- **sentence-transformers**: Nils Reimers' semantic embedding library
- **FastMCP**: Anthropic's high-level MCP framework
- **Claude Desktop**: For providing the MCP integration platform

---

**Built for developers who want intelligent task management with semantic search capabilities.**