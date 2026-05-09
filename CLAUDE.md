# Vector Task MCP Server

## Project Overview
MCP (Model Context Protocol) Server для управління задачами з використанням sqlite-vec для семантичного пошуку.

## Technology Stack
- **Python**: 3.11.8 (requires >= 3.10)
- **Package Manager**: `uv` (сучасний Python package manager)
- **Database**: SQLite 3.43.2 + sqlite-vec extension
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional vectors)
- **MCP Framework**: FastMCP >= 0.3.0

## Key Dependencies
- `mcp>=0.3.0` - Model Context Protocol framework
- `sqlite-vec>=0.1.6` - Vector search extension для SQLite
- `sentence-transformers>=2.2.2` - Embedding models

## Project Structure
- `main.py` - Entry point with uv script configuration
- `requirements.txt` - Python dependencies for pip/venv compatibility
- `pyproject.toml` - Modern Python project configuration
- `.python-version` - Python version specification (3.11)
- `claude-desktop-config.example.json` - Claude Desktop configuration template
- `src/models.py` - Data models and configuration
- `src/security.py` - Security validation and sanitization
- `src/task_store.py` - Vector task storage operations
- `tasks.db` - SQLite database for tasks

## How to Run

### Standalone
```bash
# Using uv (requires Python with SQLite extensions support)
uv run main.py --working-dir ./

# Alternative with conda Python (has SQLite extensions support)
~/miniconda3/envs/vector-mcp/bin/python main.py --working-dir ./
```

### Configuration Options

- `--working-dir` - Working directory for task database (required, default: current directory)
  - Specifies the project directory where the `memory/` subdirectory will be created
  - Database will be stored at `{working-dir}/memory/tasks.db`
  - Example: `--working-dir /path/to/project` → database at `/path/to/project/memory/tasks.db`

- `--task-folder` - Optional root directory for per-task folders (feature opt-in)
  - When set, every ROOT task gets its own folder named by its `code`
    (e.g. `{--task-folder}/FEAT-44/`) plus a generated `task.md` template.
  - Subtasks NEVER receive folders — only root tasks (`parent_id IS NULL`).
  - Status transitions rename/archive the folder automatically:
    `completed → -on-review`, `done → Archive/{code}-done`,
    `completed → in_progress` reverts the rename.
  - Filesystem failures NEVER block DB operations — the manager logs warnings
    and returns silently. DB state is the source of truth.
  - Read APIs: `task_get` returns `folder_path` + `folder_files` for root tasks;
    `task_folder_files(task_id|code)` returns the same listing on demand.
  - Example: `--task-folder /path/to/project/tasks` → root task `FEAT-12`
    gets `/path/to/project/tasks/FEAT-12/task.md`.

- `--timezone` - Optional IANA timezone for displayed timestamps (default: UTC)
  - Example: `--timezone Europe/Kyiv`

**⚠️ IMPORTANT for macOS Users:**
- Standard Python from python.org does NOT support SQLite loadable extensions
- Use conda/miniforge Python or compile Python with `--enable-loadable-sqlite-extensions`
- On Apple Silicon, ensure you're running native arm64 Python, not x86_64 through Rosetta

### Claude Desktop Integration
Використовуй `claude-desktop-config.example.json` як шаблон.

Конфігурація для Claude Desktop:
```json
{
  "mcpServers": {
    "vector-task": {
      "command": "uv",
      "args": [
        "run",
        "/absolute/path/to/main.py",
        "--working-dir",
        "/your/project/path"
      ]
    }
  }
}
```

**ВАЖЛИВО:**
- Використовуй абсолютні шляхи, не відносні!

## Database Architecture
- `task_metadata` - Метадані задач (title, content, status, priority, tags, timestamps)
- `task_vectors` - Векторна таблиця (vec0 virtual table)
- Індекси на status, priority, created_at, content_hash

## Task Management Features
- **Task Lifecycle**: draft → pending → in_progress → completed → tested → validated → done (or stopped/canceled at any point)
  - `done` may also be jumped to directly from `completed`, `tested`, or `validated`.
- **Statuses**: draft, pending, in_progress, completed, tested, validated, done, stopped, canceled
  - **draft**: Task draft (not ready for execution)
  - **pending**: Task ready but not started
  - **in_progress**: Currently being worked on
  - **completed**: Basic completion
  - **tested**: Completed and tested
  - **validated**: Completed, tested, and validated
  - **done**: Final / archived (terminal); reachable as a jump from completed/tested/validated
  - **stopped**: Paused/blocked
  - **canceled**: Task canceled (will not be done)
- **Priorities**: low, medium, high, critical
- **Hierarchical Tasks**: Parent-child task relationships
- **Smart Search**: Semantic search using vector embeddings
- **Tags**: Organize tasks with custom tags
- **Comments**: Add notes to tasks without changing content

## Available MCP Tools
- `task_create` - Create new task (accepts optional `code`)
- `task_create_bulk` - Create multiple tasks (each accepts optional `code`)
- `task_update` - Update task fields (status, priority, tags, comment with append, add_tag, remove_tag)
- `task_delete` / `task_delete_bulk` - Delete tasks
- `task_list` - List/search tasks with filters
- `task_get` - Get specific task by ID; for root tasks with `--task-folder` enabled, response also includes `folder_path` + `folder_files`
- `task_next` - Get next task to work on
- `task_stats` - Get task statistics (includes unique_tags)
- `task_folder_files` - List files in a root task's folder by `task_id` OR `code` (requires `--task-folder`)

## MCP Resources
- `project://info` - Read-only project metadata: working_dir, task_folder, task_folder_enabled, per-root-task folder summary

## Task Folder Feature

When `--task-folder` is set, the server materialises a folder per **ROOT** task. Subtasks never receive folders.

### Folder structure
- Initial: `{--task-folder}/{code}/` containing `task.md`
- After `completed`: `{--task-folder}/{code}-on-review/`
- After `done`: `{--task-folder}/{code}/Archive/{code}-done/` (folder moved into Archive subfolder of canonical container)
- Reverting `completed → in_progress`: folder renamed back to `{--task-folder}/{code}/`

### task.md template
Auto-generated on folder creation, contains: title (H1), Vector ID (= task_id), placeholders for Branch, Session ID, Description. Existing files are preserved on idempotent re-create; only the Vector ID section is appended when missing.

### Codes
- Auto-generated from primary type tag: `feature → FEAT-N`, `bugfix → FIX-N`, `refactor → REFACTOR-N`, etc.
- Custom codes accepted (e.g. `OLOM-460`, `JIRA-1234`) — must match `^[A-Z]+-\d+$`.
- Codes are unique per project (UNIQUE partial index on `code IS NOT NULL`).

### Resilience contract
Filesystem operations NEVER block DB transactions. Failures are logged with a warning and the DB state remains authoritative. Reads are best-effort — missing folders return empty file lists, not errors.

## Important Notes
- **sqlite-vec** працює як extension для SQLite, завантажується через `sqlite_vec.load(conn)`
- **uv** використовується замість venv - він керує ізольованим оточенням автоматично
- Векторний пошук використовує 384-вимірні embeddings
- База даних: `tasks.db` (location depends on `--working-dir`, see Configuration Options)

## Security Features
- Working directory validation
- Input sanitization
- Content hash для дедуплікації
- Resource limits для захисту від DoS
- Bulk operation limits (50 creates, 100 deletes max)

## Development Notes
- Проект налаштований як uv script з inline metadata (/// script ///)
- Не потрібно створювати venv вручну
- Всі залежності автоматично керуються через uv