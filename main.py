#!/usr/bin/env -S uv run --script
# -*- coding: utf-8 -*-
# /// script
# dependencies = [
#     "mcp>=0.3.0",
#     "sqlite-vec>=0.1.6",
#     "sentence-transformers>=2.2.2"
# ]
# requires-python = ">=3.8"
# ///

"""
Vector Task MCP Server - Main Entry Point
==========================================

A secure, vector-based task management server using sqlite-vec for semantic search.
Stores and retrieves tasks with vector embeddings for intelligent task retrieval.

Usage:
    python main.py --working-dir /path/to/project

Task database stored in: {working_dir}/memory/tasks.db
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.fastmcp import FastMCP

# Import our modules
from src.models import Config
from src.security import validate_working_dir, SecurityError, validate_task_list_params
from src.task_store import TaskStore


def get_working_dir() -> Path:
    """Get working directory from command line arguments"""
    if "--working-dir" in sys.argv:
        idx = sys.argv.index("--working-dir")
        if idx + 1 < len(sys.argv):
            return validate_working_dir(sys.argv[idx + 1])
    # Default to current directory
    return validate_working_dir(".")


def create_server() -> FastMCP:
    """Create and configure the MCP server"""

    # Initialize task store
    try:
        working_dir = get_working_dir()
        memory_dir = working_dir / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        task_db_path = memory_dir / "tasks.db"
        task_store = TaskStore(task_db_path)
        print(f"Task database initialized: {task_db_path}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize task store: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create FastMCP server
    mcp = FastMCP(Config.SERVER_NAME)
    
    # ===============================================================================
    # TASK MANAGEMENT TOOLS
    # ===============================================================================

    @mcp.tool()
    def task_create(
        title: str,
        content: str,
        parent_id: int = None,
        comment: str = None,
        priority: str = None,
        tags: list[str] = None
    ) -> dict[str, Any]:
        """
        Create new task with vector embedding for semantic search.

        Args:
            title: Task title (max 200 chars)
            content: Task description/details (max 10K chars)
            parent_id: Optional parent task ID for subtasks
            comment: Optional comment/note for the task
            priority: Optional task priority (low, medium, high, critical, default: medium)
            tags: Optional list of tags for organization (max 10)
        """
        try:
            result = task_store.create_task(title, content, parent_id, comment, priority, tags)
            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Task creation failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_create_bulk(tasks: list[dict]) -> dict[str, Any]:
        """
        Create multiple tasks in bulk with vector embeddings.

        Args:
            tasks: List of task objects with fields:
                - title (required): Task title (max 200 chars)
                - content (required): Task description (max 10K chars)
                - parent_id (optional): Parent task ID for subtasks
                - comment (optional): Comment/note for the task
                - tags (optional): List of tags for organization (max 10)

        Example:
            tasks = [
                {"title": "Task 1", "content": "Description", "parent_id": None, "comment": "Note", "tags": ["backend", "api"]},
                {"title": "Task 2", "content": "Description", "parent_id": 1, "comment": None, "tags": ["frontend"]}
            ]
        """
        try:
            result = task_store.create_tasks_bulk(tasks)
            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Bulk task creation failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_update(
        task_id: int,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
        parent_id: int | None = None,
        comment: str | None = None,
        start_at: str | None = None,
        finish_at: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Update task fields by ID.

        Args:
            task_id: Task ID to update
            title: Optional new title
            content: Optional new content
            status: Optional new status (pending, in_progress, completed, stopped)
            parent_id: Optional new parent task ID
            comment: Optional comment to add or replace
            start_at: Optional start timestamp (ISO 8601 format)
            finish_at: Optional finish timestamp (ISO 8601 format)
            priority: Optional new priority (low, medium, high, critical)
            tags: Optional list of tags to replace existing tags
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            # Build kwargs from provided parameters
            kwargs = {}
            if title is not None:
                kwargs['title'] = title
            if content is not None:
                kwargs['content'] = content
            if status is not None:
                kwargs['status'] = status
            if parent_id is not None:
                kwargs['parent_id'] = parent_id
            if comment is not None:
                kwargs['comment'] = comment
            if start_at is not None:
                kwargs['start_at'] = start_at
            if finish_at is not None:
                kwargs['finish_at'] = finish_at
            if priority is not None:
                kwargs['priority'] = priority
            if tags is not None:
                kwargs['tags'] = tags

            result = task_store.update_task(task_id, **kwargs)
            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Task update failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_delete(task_id: int) -> dict[str, Any]:
        """
        Delete task by ID (permanent, cannot be undone).

        Args:
            task_id: Task ID to delete
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            deleted = task_store.delete_task(task_id)

            if not deleted:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Task with ID {task_id} not found"
                }

            return {
                "success": True,
                "task_id": task_id,
                "message": "Task deleted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Deletion failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_delete_bulk(task_ids: list[int]) -> dict[str, Any]:
        """
        Delete multiple tasks by IDs (permanent, cannot be undone).

        Args:
            task_ids: List of task IDs to delete
        """
        try:
            result = task_store.delete_tasks_bulk(task_ids)
            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Bulk deletion failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_last() -> dict[str, Any]:
        """Get last created task."""
        try:
            task = task_store.get_last_task()

            if task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": "No tasks found in database"
                }

            return {
                "success": True,
                "task": task.to_dict(),
                "message": "Last task retrieved successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Retrieval failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_start(task_id: int) -> dict[str, Any]:
        """
        Start task (set status to in_progress, record start time).

        Args:
            task_id: Task ID to start
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            # Fetch current task to validate status transition
            current_task = task_store.get_task_by_id(task_id)
            if current_task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Task {task_id} not found"
                }

            # Validate status transition
            if current_task.status == "completed":
                raise SecurityError("Cannot start completed task. Task already finished.")

            if current_task.status == "in_progress":
                raise SecurityError("Task already in progress")

            # Only pending and stopped tasks can be started
            result = task_store.update_task(
                task_id,
                status="in_progress",
                start_at=datetime.now(timezone.utc).isoformat(),
                finish_at=None
            )

            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to start task",
                "message": str(e)
            }

    @mcp.tool()
    def task_stop(task_id: int) -> dict[str, Any]:
        """
        Stop task (set status to stopped).

        Args:
            task_id: Task ID to stop
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            result = task_store.update_task(task_id, status="stopped")

            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to stop task",
                "message": str(e)
            }

    @mcp.tool()
    def task_finish(task_id: int) -> dict[str, Any]:
        """
        Finish task (set status to completed, record finish time).

        Args:
            task_id: Task ID to finish
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            result = task_store.update_task(
                task_id,
                status="completed",
                finish_at=datetime.now(timezone.utc).isoformat()
            )

            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to finish task",
                "message": str(e)
            }

    @mcp.tool()
    def task_resume(task_id: int) -> dict[str, Any]:
        """
        Resume stopped task (set status back to in_progress).

        Args:
            task_id: Task ID to resume
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            result = task_store.update_task(task_id, status="in_progress", finish_at=None)

            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to resume task",
                "message": str(e)
            }

    @mcp.tool()
    def task_list(
        query: str = None,
        limit: int = 10,
        offset: int = 0,
        status: str = None,
        parent_id: int = None,
        tags: list[str] = None
    ) -> dict[str, Any]:
        """
        List tasks with optional filters and vector semantic search.

        Args:
            query: Optional semantic search query for title/content
            limit: Max results (1-50, default 10)
            offset: Starting position for pagination (default 0)
            status: Optional status filter (pending, in_progress, completed, stopped)
            parent_id: Optional parent task ID filter (for subtasks)
            tags: Optional list of tags to filter by (matches tasks containing ANY of the specified tags)
        """
        try:
            # Validate parameters
            limit, offset, status, parent_id, validated_tags = validate_task_list_params(
                limit=limit,
                offset=offset,
                status=status,
                parent_id=parent_id,
                tags=tags
            )

            # Search tasks
            tasks, total = task_store.search_tasks(
                query=query,
                limit=limit,
                offset=offset,
                status=status,
                parent_id=parent_id,
                tags=validated_tags
            )

            if not tasks:
                return {
                    "success": True,
                    "tasks": [],
                    "total": total,
                    "count": 0,
                    "message": "No tasks found matching filters"
                }

            # Convert Task objects to dictionaries
            task_dicts = [task.to_dict() for task in tasks]

            return {
                "success": True,
                "query": query,
                "tasks": task_dicts,
                "total": total,
                "count": len(task_dicts),
                "message": f"Retrieved {len(task_dicts)} of {total} tasks"
            }

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Task list failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_next() -> dict[str, Any]:
        """
        Get next task to work on (smart selection).

        Returns in_progress task if any exists, otherwise returns
        next pending task after last completed task.
        """
        try:
            task = task_store.get_next_task()

            if task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": "No pending or in-progress tasks found"
                }

            return {
                "success": True,
                "task": task.to_dict(),
                "message": f"Next task: {task.status}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to get next task",
                "message": str(e)
            }

    @mcp.tool()
    def task_get(task_id: int) -> dict[str, Any]:
        """
        Get task by ID.

        Args:
            task_id: Task ID to retrieve
        """
        try:
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            task = task_store.get_task_by_id(task_id)

            if task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Task with ID {task_id} not found"
                }

            return {
                "success": True,
                "task": task.to_dict(),
                "message": "Task retrieved successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Retrieval failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_stats() -> dict[str, Any]:
        """
        Get task statistics (total, completed, pending, in_progress, stopped, next_task_id, etc.).

        Returns comprehensive task statistics including:
        - Total tasks count
        - Count by status (pending, in_progress, completed, stopped)
        - Tasks with subtasks count
        - Next task ID (from smart selection logic)
        """
        try:
            # Get stats from TaskStore
            stats = task_store.get_stats()

            # Get next task ID
            next_task = task_store.get_next_task()
            next_task_id = next_task.id if next_task else None

            # Build response with stats
            result = stats.to_dict()
            result["success"] = True
            result["next_task_id"] = next_task_id
            result["message"] = f"Statistics for {result['total_tasks']} tasks"

            return result

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to get statistics",
                "message": str(e)
            }

    @mcp.tool()
    def task_comment(task_id: int, comment: str, append: bool = True) -> dict[str, Any]:
        """
        Add or replace task comment.

        Args:
            task_id: Task ID to update
            comment: Comment text to add or set
            append: If True, append to existing comment with \\n\\n separator. If False, replace entirely.
        """
        try:
            # Parameter validation
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            if not isinstance(comment, str) or not comment.strip():
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "comment cannot be empty"
                }

            # Fetch existing task
            existing_task = task_store.get_task_by_id(task_id)

            if existing_task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Task with ID {task_id} not found"
                }

            # Build new comment
            if append and existing_task.comment:
                new_comment = existing_task.comment + "\n\n" + comment
            else:
                new_comment = comment

            # Update task
            result = task_store.update_task(task_id, comment=new_comment)
            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Comment update failed",
                "message": str(e)
            }

    @mcp.tool()
    def task_add_tag(task_id: int, tag: str) -> dict[str, Any]:
        """
        Add a single tag to a task (appends to existing tags).

        Args:
            task_id: Task ID to update
            tag: Tag to add (will be sanitized and lowercased)
        """
        try:
            # Validate task_id
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            # Validate tag
            if not isinstance(tag, str) or not tag.strip():
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "tag cannot be empty"
                }

            # Get existing task
            task = task_store.get_task_by_id(task_id)

            if task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Task with ID {task_id} not found"
                }

            # Get current tags and add new tag
            current_tags = task.tags if task.tags else []

            # Sanitize and normalize new tag
            from src.security import validate_tags
            validated_tags = validate_tags([tag])

            if not validated_tags:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "message": "Tag validation failed (must be alphanumeric + hyphens/underscores)"
                }

            new_tag = validated_tags[0]

            # Check if tag already exists
            if new_tag in current_tags:
                return {
                    "success": False,
                    "error": "Already exists",
                    "message": f"Tag '{new_tag}' already exists on task {task_id}"
                }

            # Check max tags limit
            if len(current_tags) >= 10:
                return {
                    "success": False,
                    "error": "Limit exceeded",
                    "message": "Task already has maximum of 10 tags"
                }

            # Add tag
            updated_tags = current_tags + [new_tag]
            result = task_store.update_task(task_id, tags=updated_tags)

            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to add tag",
                "message": str(e)
            }

    @mcp.tool()
    def task_remove_tag(task_id: int, tag: str) -> dict[str, Any]:
        """
        Remove a single tag from a task.

        Args:
            task_id: Task ID to update
            tag: Tag to remove (case-insensitive match)
        """
        try:
            # Validate task_id
            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            # Validate tag
            if not isinstance(tag, str) or not tag.strip():
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "tag cannot be empty"
                }

            # Get existing task
            task = task_store.get_task_by_id(task_id)

            if task is None:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Task with ID {task_id} not found"
                }

            # Get current tags
            current_tags = task.tags if task.tags else []

            # Normalize tag for comparison (lowercase)
            tag_normalized = tag.lower().strip()

            # Check if tag exists
            if tag_normalized not in current_tags:
                return {
                    "success": False,
                    "error": "Not found",
                    "message": f"Tag '{tag_normalized}' not found on task {task_id}"
                }

            # Remove tag
            updated_tags = [t for t in current_tags if t != tag_normalized]
            result = task_store.update_task(task_id, tags=updated_tags)

            return result

        except SecurityError as e:
            return {
                "success": False,
                "error": "Security validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to remove tag",
                "message": str(e)
            }

    @mcp.tool()
    def task_get_all_tags() -> dict[str, Any]:
        """
        Get all unique tags across all tasks.

        Returns sorted list of unique tags from the task database.
        """
        try:
            tags = task_store.get_all_tags()

            return {
                "success": True,
                "tags": tags,
                "count": len(tags),
                "message": f"Retrieved {len(tags)} unique tags"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to retrieve tags",
                "message": str(e)
            }

    return mcp


def main():
    """Main entry point"""
    print(f"Starting {Config.SERVER_NAME} v{Config.SERVER_VERSION}", file=sys.stderr)

    try:
        # Get working directory and config
        working_dir = get_working_dir()
        memory_dir = working_dir / "memory"
        task_db_path = memory_dir / "tasks.db"

        print(f"Working directory: {working_dir}", file=sys.stderr)
        print(f"Task database: {task_db_path}", file=sys.stderr)
        print(f"Embedding model: {Config.EMBEDDING_MODEL}", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        
        # Create and run server
        server = create_server()
        print("Server ready for connections...", file=sys.stderr)
        server.run()
        
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server failed to start: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
