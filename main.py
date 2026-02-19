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
from pathlib import Path
from typing import Any, List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.fastmcp import FastMCP

# Import our modules
from src.models import Config
from src.security import validate_working_dir, SecurityError, validate_task_list_params, validate_tags, validate_task_stats_params
from src.task_store import TaskStore
from src.normalization import TagNormalizer


def get_working_dir() -> Path:
    """Get working directory from command line arguments"""
    if "--working-dir" in sys.argv:
        idx = sys.argv.index("--working-dir")
        if idx + 1 < len(sys.argv):
            return validate_working_dir(sys.argv[idx + 1])
    # Default to current directory
    return validate_working_dir(".")


def get_timezone() -> str | None:
    """Get timezone from command line arguments.

    Returns:
        Timezone string (e.g., 'Europe/Kyiv') or None for UTC default.

    Raises:
        SystemExit: If invalid timezone name provided.
    """
    if "--timezone" in sys.argv:
        idx = sys.argv.index("--timezone")
        if idx + 1 < len(sys.argv):
            tz_str = sys.argv[idx + 1]
            try:
                ZoneInfo(tz_str)  # Validate timezone exists
                return tz_str
            except ZoneInfoNotFoundError:
                print(f"Error: Invalid timezone '{tz_str}'. Use IANA timezone names (e.g., 'Europe/Kyiv', 'America/New_York').", file=sys.stderr)
                sys.exit(1)
    return None


def create_server() -> FastMCP:
    """Create and configure the MCP server"""

    # Initialize task store (database and embedding model are lazy-loaded on first use)
    try:
        working_dir = get_working_dir()
        timezone = get_timezone()
        memory_dir = working_dir / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        task_db_path = memory_dir / "tasks.db"
        task_store = TaskStore(task_db_path, timezone=timezone)
        print(f"Task database path: {task_db_path} (lazy initialization)", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize task store: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create FastMCP server
    mcp = FastMCP(
        Config.SERVER_NAME,
        instructions="""Hierarchical task manager with vector search.

Status propagation:
- child→pending ⟹ parent→pending (immediate, even if parent was completed)
- ALL children→finished ⟹ parent→completed (auto, recursive up)

Example: Parent[completed] + Child1[completed] + Child2[completed].
Validation fails → Child2→pending ⟹ Parent→pending.
Fix → Child2→completed ⟹ all finished ⟹ Parent→completed again.

NEVER update parent task status. System propagates automatically. Only update YOUR assigned task."""
    )
    
    # ===============================================================================
    # TASK MANAGEMENT TOOLS
    # ===============================================================================

    @mcp.tool()
    async def task_create(
        title: str,
        content: str,
        parent_id: int = None,
        comment: str = None,
        priority: str = None,
        estimate: float | None = None,
        order: int | None = None,
        tags: list[str] = None,
        parallel: bool = False
    ) -> dict[str, Any]:
        """
        Create new task with vector embedding for semantic search.

        Args:
            title: Task title (max 200 chars)
            content: Task description/details (max 10K chars)
            parent_id: Optional parent task ID for subtasks
            comment: Optional comment/note for the task
            priority: Optional task priority (low, medium, high, critical, default: medium)
            estimate: Optional time estimate in hours
            order: Optional task order/position (auto-assigned if not provided)
            tags: Optional list of tags for organization (max 10)
            parallel: Whether task can be executed in parallel with siblings (default: False)
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

            # Get embedding model asynchronously (lazy loading)
            model = await task_store.get_embedding_model_async()

            result = task_store.create_task(
                title=title,
                content=content,
                parent_id=parent_id,
                comment=comment,
                priority=priority,
                tags=tags,
                estimate=estimate,
                order=order,
                parallel=parallel,
                embedding_model=model
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
                "error": "Task creation failed",
                "message": str(e)
            }

    @mcp.tool()
    async def task_create_bulk(tasks: list[dict]) -> dict[str, Any]:
        """
        Create multiple tasks in bulk with vector embeddings.

        Args:
            tasks: List of task objects with fields:
                - title (required): Task title (max 200 chars)
                - content (required): Task description (max 10K chars)
                - parent_id (optional): Parent task ID for subtasks
                - comment (optional): Comment/note for the task
                - priority (optional): Task priority (low, medium, high, critical)
                - estimate (optional): Time estimate in hours
                - order (optional): Task order/position (auto-assigned if not provided)
                - tags (optional): List of tags for organization (max 10)
                - parallel (optional): Whether task can be executed in parallel with siblings (default: False)

        Example:
            tasks = [
                {"title": "Task 1", "content": "Description", "parent_id": None, "comment": "Note", "priority": "high", "estimate": 3.5, "order": 1, "tags": ["backend", "api"], "parallel": True},
                {"title": "Task 2", "content": "Description", "parent_id": 1, "comment": None, "estimate": 2.0, "order": 2, "tags": ["frontend"], "parallel": True}
            ]
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

            # Get embedding model asynchronously (lazy loading)
            model = await task_store.get_embedding_model_async()

            result = task_store.create_tasks_bulk(tasks, embedding_model=model)
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
    async def task_update(
        task_id: int,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
        parent_id: int | None = None,
        comment: str | None = None,
        start_at: str | None = None,
        finish_at: str | None = None,
        priority: str | None = None,
        estimate: float | None = None,
        order: int | None = None,
        tags: list[str] | None = None,
        append_comment: bool = True,
        add_tag: str | None = None,
        remove_tag: str | None = None,
        parallel: bool | None = None
    ) -> dict[str, Any]:
        """
        Update task fields by ID.

        Status propagation: child→pending ⟹ parent→pending; ALL children→finished ⟹ parent→completed.

        Args:
            task_id: Task ID to update
            title: Optional new title
            content: Optional new content
            status: Optional new status (draft, pending, in_progress, completed, tested, validated, stopped, canceled)
            parent_id: Optional new parent task ID
            comment: Optional comment to add or replace
            start_at: Optional start timestamp (ISO 8601 format)
            finish_at: Optional finish timestamp (ISO 8601 format)
            priority: Optional new priority (low, medium, high, critical)
            estimate: Optional time estimate in hours
            order: Optional new order/position (triggers sibling reordering)
            tags: Optional list of tags to replace existing tags
            append_comment: Append comment to existing with \\n\\n separator (default True). Set False to replace entirely
            add_tag: Optional single tag to add (validates duplicates and 10-tag limit)
            remove_tag: Optional single tag to remove (case-insensitive, silent if not found)
            parallel: Optional flag for parallel execution with siblings
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

            if not isinstance(task_id, int) or task_id < 1:
                return {
                    "success": False,
                    "error": "Invalid parameter",
                    "message": "task_id must be a positive integer"
                }

            # Handle comment append logic
            if comment is not None and append_comment:
                existing = task_store.get_task_by_id(task_id)
                if existing and existing.comment:
                    comment = existing.comment + "\n\n" + comment

            # Build kwargs from provided parameters
            kwargs = {}

            # Handle add_tag - append single tag with validation
            if add_tag is not None:
                try:
                    sanitized_tags = validate_tags([add_tag])
                    sanitized_tag = sanitized_tags[0]
                except SecurityError as e:
                    return {"success": False, "error": f"Invalid tag: {e}"}

                existing = task_store.get_task_by_id(task_id)
                if not existing:
                    return {"success": False, "error": f"Task {task_id} not found"}

                current_tags = existing.tags or []

                if sanitized_tag in current_tags:
                    return {"success": False, "error": f"Tag '{sanitized_tag}' already exists on task"}

                if len(current_tags) >= 10:
                    return {"success": False, "error": "Maximum 10 tags per task"}

                kwargs["tags"] = current_tags + [sanitized_tag]

            # Handle remove_tag - remove single tag with case-insensitive match
            if remove_tag is not None:
                tag_normalized = remove_tag.lower().strip()
                if tag_normalized:
                    existing = task_store.get_task_by_id(task_id)
                    if existing and existing.tags:
                        updated_tags = [t for t in existing.tags if t != tag_normalized]
                        if len(updated_tags) != len(existing.tags):
                            kwargs["tags"] = updated_tags

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
            if estimate is not None:
                kwargs['estimate'] = estimate
            if order is not None:
                kwargs['order'] = order
            if tags is not None:
                kwargs['tags'] = tags
            if parallel is not None:
                kwargs['parallel'] = parallel

            # Only load embedding model if title, content, or tags are changing
            embedding_model = None
            if title is not None or content is not None or tags is not None or add_tag is not None or remove_tag is not None:
                embedding_model = await task_store.get_embedding_model_async()

            result = task_store.update_task(task_id, embedding_model=embedding_model, **kwargs)
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
    async def task_delete(task_id: int) -> dict[str, Any]:
        """
        Delete task by ID (permanent, cannot be undone).

        Args:
            task_id: Task ID to delete
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

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
    async def task_delete_bulk(task_ids: list[int]) -> dict[str, Any]:
        """
        Delete multiple tasks by IDs (permanent, cannot be undone).

        Args:
            task_ids: List of task IDs to delete
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

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
    async def task_list(
        query: str = None,
        limit: int = 10,
        offset: int = 0,
        status: str = None,
        parent_id: int = None,
        tags: list[str] = None,
        ids: list[int] = None
    ) -> dict[str, Any]:
        """
        List tasks with optional filters and vector semantic search.

        Args:
            query: Optional semantic search query for title/content
            limit: Max results (1-50, default 10)
            offset: Starting position for pagination (default 0)
            status: Optional status filter (draft, pending, in_progress, completed, tested, validated, stopped, canceled)
            parent_id: Optional parent task ID filter (for subtasks)
            tags: Optional list of tags to filter by (matches tasks containing ANY of the specified tags)
            ids: Optional list of task IDs to filter by (AND logic with other filters, max 50)
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

            # Validate parameters
            limit, offset, status, parent_id, validated_tags, validated_ids = validate_task_list_params(
                limit=limit,
                offset=offset,
                status=status,
                parent_id=parent_id,
                tags=tags,
                ids=ids
            )

            # Only load embedding model if query is provided (semantic search)
            embedding_model = None
            if query:
                embedding_model = await task_store.get_embedding_model_async()

            # Search tasks
            tasks, total = task_store.search_tasks(
                query=query,
                limit=limit,
                offset=offset,
                status=status,
                parent_id=parent_id,
                tags=validated_tags,
                ids=validated_ids,
                embedding_model=embedding_model
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
    async def task_next() -> dict[str, Any]:
        """
        Get next task to work on (smart selection).

        Returns in_progress task if any exists, otherwise returns
        next pending task after last finished task.

        Task status lifecycle:
        - draft: Task draft (not ready for execution)
        - pending: Task not yet started
        - in_progress: Currently being worked on
        - completed: Task finished (basic completion)
        - tested: Task completed and tested
        - validated: Task completed, tested and validated
        - stopped: Task paused/blocked
        - canceled: Task canceled (will not be done)
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

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
    async def task_get(task_id: int) -> dict[str, Any]:
        """
        Get task by ID.

        Args:
            task_id: Task ID to retrieve
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

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

            # Check for subtasks
            subtask_ids = task_store.get_subtask_ids(task_id)

            response = {
                "success": True,
                "task": task.to_dict(),
                "message": "Task retrieved successfully"
            }

            # Add subtask info if task has children
            if subtask_ids:
                response["subtask_ids"] = subtask_ids
                next_child = task_store.get_next_child(task_id)
                if next_child:
                    response["next_child"] = next_child.to_dict()

            return response

        except Exception as e:
            return {
                "success": False,
                "error": "Retrieval failed",
                "message": str(e)
            }

    @mcp.tool()
    async def task_stats(
        created_after: str = None,
        created_before: str = None,
        start_after: str = None,
        start_before: str = None,
        finish_after: str = None,
        finish_before: str = None,
        status: str = None,
        priority: str = None,
        tags: list[str] = None,
        parent_id: int = None
    ) -> dict[str, Any]:
        """
        Get task statistics (total, completed, tested, validated, pending, in_progress, stopped, next_task_id, etc.).

        Returns comprehensive task statistics including:
        - Total tasks count
        - Count by status (draft, pending, in_progress, completed, tested, validated, stopped, canceled)
        - Tasks with subtasks count
        - Next task ID (from smart selection logic)
        - Unique tags across all tasks

        Args:
            created_after: Filter tasks created after this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            created_before: Filter tasks created before this date (ISO 8601 format)
            start_after: Filter tasks started after this date (ISO 8601 format)
            start_before: Filter tasks started before this date (ISO 8601 format)
            finish_after: Filter tasks finished after this date (ISO 8601 format)
            finish_before: Filter tasks finished before this date (ISO 8601 format)
            status: Filter by task status (draft, pending, in_progress, completed, tested, validated, stopped, canceled)
            priority: Filter by priority (low, medium, high, critical)
            tags: Filter by tags (OR logic - matches tasks with ANY specified tag)
            parent_id: Filter for subtasks of specific parent (use 0 for root tasks only)
        """
        try:
            # Ensure database is initialized (lazy loading)
            await task_store._ensure_db_initialized_async()

            # Validate filter parameters
            (
                validated_created_after, validated_created_before,
                validated_start_after, validated_start_before,
                validated_finish_after, validated_finish_before,
                validated_status, validated_priority,
                validated_tags, validated_parent_id
            ) = validate_task_stats_params(
                created_after=created_after,
                created_before=created_before,
                start_after=start_after,
                start_before=start_before,
                finish_after=finish_after,
                finish_before=finish_before,
                status=status,
                priority=priority,
                tags=tags,
                parent_id=parent_id
            )

            # Get stats from TaskStore with filters
            stats = task_store.get_stats(
                created_after=validated_created_after,
                created_before=validated_created_before,
                start_after=validated_start_after,
                start_before=validated_start_before,
                finish_after=validated_finish_after,
                finish_before=validated_finish_before,
                status=validated_status,
                priority=validated_priority,
                tags=validated_tags,
                parent_id=validated_parent_id
            )

            # Get next task ID
            next_task = task_store.get_next_task()
            next_task_id = next_task.id if next_task else None

            # Get unique tags
            unique_tags = task_store.get_all_tags()

            # Build response with stats
            result = stats.to_dict()
            result["success"] = True
            result["next_task_id"] = next_task_id
            result["unique_tags"] = unique_tags

            # Build message based on whether filters are applied
            filters_applied = any([
                validated_created_after, validated_created_before,
                validated_start_after, validated_start_before,
                validated_finish_after, validated_finish_before,
                validated_status, validated_priority,
                validated_tags, validated_parent_id is not None
            ])

            if filters_applied:
                result["message"] = f"Filtered statistics for {result['total_tasks']} tasks, {len(unique_tags)} unique tags"
            else:
                result["message"] = f"Statistics for {result['total_tasks']} tasks, {len(unique_tags)} unique tags"

            return result

        except ValueError as e:
            return {
                "success": False,
                "error": "Validation failed",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to get statistics",
                "message": str(e)
            }

    # ===============================================================================
    # TAG FREQUENCIES / IDF WEIGHTS
    # ===============================================================================

    @mcp.tool()
    async def tag_frequencies() -> dict[str, Any]:
        """
        Get tag frequencies with IDF weights for search ranking.

        IDF (Inverse Document Frequency) weight formula:
            idf_weight = 1 / log(1 + freq)

        - Rare tags (low frequency) → higher weight → stronger signal
        - Common tags (high frequency) → lower weight → weaker signal

        Returns:
            Dict with tag frequencies, counts, and IDF weights
        """
        try:
            await task_store._ensure_db_initialized_async()

            frequencies = task_store.get_tag_frequencies()

            sorted_tags = sorted(frequencies.items(), key=lambda x: x[1]["count"], reverse=True)

            return {
                "success": True,
                "tags": dict(sorted_tags),
                "total_unique_tags": len(frequencies),
                "message": f"Retrieved {len(frequencies)} tags with frequencies and IDF weights"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to get tag frequencies",
                "message": str(e)
            }

    @mcp.tool()
    async def tag_weights() -> dict[str, Any]:
        """
        Get IDF weights for all tags (simplified for ranking).

        Use for search ranking: multiply tag match by idf_weight.
        Rare tags boost relevance more than common tags.

        Returns:
            Dict mapping tag -> idf_weight
        """
        try:
            await task_store._ensure_db_initialized_async()

            weights = task_store.get_tag_weights()

            sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)

            return {
                "success": True,
                "weights": dict(sorted_weights),
                "total_tags": len(weights),
                "message": f"Retrieved IDF weights for {len(weights)} tags"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to get tag weights",
                "message": str(e)
            }

    @mcp.tool()
    async def tag_classify(tag: str) -> dict[str, Any]:
        """
        Classify a tag by boost level for search ranking.

        Boost levels:
        - high (1.5): Specific tags like vendor:*, module:*, service:*
        - medium (1.0): Facet tags (domain:*, type:*) and specific tags
        - low (0.5): General/common tags (api, backend, test)
        - filter_only (0.1): Filter-only tags (status:*, priority:*)

        Args:
            tag: Tag string to classify

        Returns:
            Dict with level, boost, and reason
        """
        try:
            from src.normalization import TagNormalizer

            normalizer = TagNormalizer(None)
            classification = normalizer.classify_tag(tag)

            return {
                "success": True,
                "tag": tag,
                "level": classification['level'],
                "boost": classification['boost'],
                "reason": classification['reason']
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to classify tag",
                "message": str(e)
            }

    @mcp.tool()
    async def tags_classify_batch(tags: List[str]) -> dict[str, Any]:
        """
        Classify multiple tags by boost level.

        Args:
            tags: List of tag strings

        Returns:
            Dict with tags grouped by boost level
        """
        try:
            from src.normalization import TagNormalizer

            normalizer = TagNormalizer(None)
            classified = normalizer.classify_tags(tags)

            return {
                "success": True,
                "high": classified['high'],
                "medium": classified['medium'],
                "low": classified['low'],
                "filter_only": classified['filter_only'],
                "total_tags": len(tags),
                "message": f"Classified {len(tags)} tags"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to classify tags",
                "message": str(e)
            }

    @mcp.tool()
    async def search_explain(query: str, limit: int = 5) -> dict[str, Any]:
        """
        Search with ranking explanation.

        Shows how IDF weights, tag classification, and tag_variants
        affect search ranking.

        Args:
            query: Search query
            limit: Max results (default 5)

        Returns:
            Dict with results and ranking explanation
        """
        try:
            await task_store._ensure_db_initialized_async()

            model = await task_store.get_embedding_model_async()

            tasks, total = task_store.search_tasks(
                query=query,
                limit=limit,
                embedding_model=model,
                use_idf_rerank=True
            )

            from src.normalization import TagNormalizer
            normalizer = TagNormalizer(None)
            tag_weights = task_store.get_tag_weights()

            explained = []
            for i, task in enumerate(tasks):
                explanation = {
                    "rank": i + 1,
                    "task_id": task.id,
                    "title": task.title,
                    "tags": task.tags,
                    "tag_variants": task.tag_variants,
                    "tag_classifications": [],
                    "variant_boost": len(task.tag_variants) * 0.02 if task.tag_variants else 0
                }

                for tag in task.tags:
                    classification = normalizer.classify_tag(tag)
                    idf = tag_weights.get(tag, 0)
                    explanation["tag_classifications"].append({
                        "tag": tag,
                        "level": classification['level'],
                        "boost": classification['boost'],
                        "idf_weight": round(idf, 3)
                    })

                explained.append(explanation)

            return {
                "success": True,
                "query": query,
                "results": explained,
                "total_matching": total,
                "message": f"Found {total} results, showing top {len(explained)} with ranking explanation"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to search",
                "message": str(e)
            }

    # ===============================================================================
    # TAG NORMALIZATION TOOLS
    # ===============================================================================

    @mcp.tool()
    async def tag_normalize_preview(threshold: float = 0.90, require_predefined: bool = False) -> dict[str, Any]:
        """
        Preview tag normalization suggestions using vector similarity.

        Analyzes all tags and groups semantically similar ones, suggesting canonical forms.
        Does NOT modify any data - use tag_normalize_apply to execute changes.

        Predefined canonical mappings (from canonical_tag_add) take priority over vector grouping.

        Hard Guards (block merging regardless of similarity):
        - Version guard: tags with different versions never merge (v1 vs v2, php8 vs php7)
        - Numeric guard: tags with different numbers never merge (api1 vs api2)

        Substring Boost:
        - If one tag is substring of another AND both have same version context → auto-merge
        - Example: "laravel" ⊂ "laravel framework" → merge (0.8959 boosted to 0.91)

        Drift Prevention:
        - Set require_predefined=True to ONLY see predefined mappings (canonical freeze)

        Args:
            threshold: Similarity threshold for grouping (0.0-1.0, default: 0.90)
                       0.90 = strict merge (recommended for auto-merge)
                       0.85 = suggest only (more aggressive grouping)
            require_predefined: If True, ONLY show predefined canonical mappings (drift prevention)

        Returns:
            Dict with:
                - groups: List of tag groups with canonical form and variants
                - total_tags: Current total unique tags
                - unique_tags_after: Unique tags after normalization
                - tags_to_merge: Number of tags that would be merged
                - predefined_mappings_used: Number of predefined mappings applied
        """
        try:
            await task_store._ensure_db_initialized_async()

            model = await task_store.get_embedding_model_async()

            canonical_mappings = task_store.get_canonical_mappings()

            normalizer = TagNormalizer(model, threshold=threshold, canonical_mappings=canonical_mappings)

            tag_counts = task_store.get_all_tags_with_counts()

            if not tag_counts:
                return {
                    "success": True,
                    "groups": [],
                    "total_tags": 0,
                    "unique_tags_after": 0,
                    "tags_to_merge": 0,
                    "predefined_mappings": len(canonical_mappings),
                    "message": "No tags found in database"
                }

            all_tags = list(tag_counts.keys())
            preview = normalizer.preview_normalization(all_tags, tag_counts)

            if require_predefined:
                preview.groups = [g for g in preview.groups if g.source == "predefined"]
                preview.tags_to_merge = sum(len(g.variants) for g in preview.groups)
                preview.unique_tags_after = preview.total_tags - preview.tags_to_merge

            groups_data = []
            for group in preview.groups:
                groups_data.append({
                    "canonical": group.canonical,
                    "variants": group.variants,
                    "similarity": group.similarity,
                    "source": group.source,
                    "canonical_count": tag_counts.get(group.canonical, 0),
                    "total_count": tag_counts.get(group.canonical, 0) + sum(tag_counts.get(v, 0) for v in group.variants)
                })

            return {
                "success": True,
                "groups": groups_data,
                "total_tags": preview.total_tags,
                "unique_tags_after": preview.unique_tags_after,
                "tags_to_merge": preview.tags_to_merge,
                "predefined_mappings_used": preview.predefined_mappings_used,
                "require_predefined": require_predefined,
                "threshold": threshold,
                "message": f"Found {len(groups_data)} tag groups ({preview.predefined_mappings_used} predefined). {preview.tags_to_merge} tags can be merged (reducing from {preview.total_tags} to {preview.unique_tags_after} unique tags)" + (" (require_predefined=True)" if require_predefined else "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to preview normalization",
                "message": str(e)
            }

    @mcp.tool()
    async def tag_normalize_apply(threshold: float = 0.90, dry_run: bool = False, require_predefined: bool = False) -> dict[str, Any]:
        """
        Apply tag normalization using vector similarity.

        Merges semantically similar tags into canonical forms. Use tag_normalize_preview first
        to see what changes will be made.

        Predefined canonical mappings (from canonical_tag_add) take priority over vector grouping.

        Hard Guards (block merging regardless of similarity):
        - Version guard: tags with different versions never merge (v1 vs v2, php8 vs php7)
        - Numeric guard: tags with different numbers never merge (api1 vs api2)

        Substring Boost:
        - If one tag is substring of another AND both have same version context → auto-merge
        - Example: "laravel" ⊂ "laravel framework" → merge (0.8959 boosted to 0.91)

        Drift Prevention:
        - Set require_predefined=True to ONLY apply predefined mappings (canonical freeze)
        - Vector-based grouping will be ignored

        Selection of canonical tag (for vector-grouped tags):
            1. Most frequently used tag in group
            2. Longest tag (if counts equal)

        Args:
            threshold: Similarity threshold for grouping (0.0-1.0, default: 0.90)
                       0.90 = strict merge (recommended for auto-merge)
                       0.85 = suggest only (more aggressive grouping)
            dry_run: If True, preview changes without applying
            require_predefined: If True, ONLY use predefined canonical mappings (drift prevention)

        Returns:
            Dict with:
                - success: True if completed
                - tasks_updated: Number of tasks modified
                - tags_replaced: Number of individual tag replacements
                - mapping: Dict of old_tag -> new_tag
        """
        try:
            await task_store._ensure_db_initialized_async()

            model = await task_store.get_embedding_model_async()

            canonical_mappings = task_store.get_canonical_mappings()

            normalizer = TagNormalizer(model, threshold=threshold, canonical_mappings=canonical_mappings)

            tag_counts = task_store.get_all_tags_with_counts()

            if not tag_counts:
                return {
                    "success": True,
                    "tasks_updated": 0,
                    "tags_replaced": 0,
                    "mapping": {},
                    "dry_run": dry_run,
                    "predefined_mappings_used": 0,
                    "message": "No tags found in database"
                }

            all_tags = list(tag_counts.keys())
            preview = normalizer.preview_normalization(all_tags, tag_counts)

            if require_predefined:
                vector_groups = [g for g in preview.groups if g.source == "vector"]
                if vector_groups:
                    preview.groups = [g for g in preview.groups if g.source == "predefined"]
                    preview.tags_to_merge = sum(len(g.variants) for g in preview.groups)
                    preview.unique_tags_after = preview.total_tags - preview.tags_to_merge

            if preview.tags_to_merge == 0:
                return {
                    "success": True,
                    "tasks_updated": 0,
                    "tags_replaced": 0,
                    "mapping": {},
                    "dry_run": dry_run,
                    "require_predefined": require_predefined,
                    "predefined_mappings_used": preview.predefined_mappings_used,
                    "message": "No tags to merge." + (" (require_predefined=True, only predefined mappings allowed)" if require_predefined else "")
                }

            mapping = normalizer.get_mapping(preview)

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "require_predefined": require_predefined,
                    "tasks_updated": 0,
                    "tags_replaced": preview.tags_to_merge,
                    "mapping": mapping,
                    "predefined_mappings_used": preview.predefined_mappings_used,
                    "message": f"DRY RUN: Would merge {preview.tags_to_merge} tags ({preview.predefined_mappings_used} from predefined mappings)" + (" (require_predefined=True)" if require_predefined else "")
                }

            result = task_store.migrate_tags(mapping, embedding_model=model)

            result["dry_run"] = False
            result["require_predefined"] = require_predefined
            result["threshold"] = threshold
            result["unique_tags_before"] = preview.total_tags
            result["unique_tags_after"] = preview.unique_tags_after
            result["predefined_mappings_used"] = preview.predefined_mappings_used

            return result

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to apply normalization",
                "message": str(e)
            }

    @mcp.tool()
    async def canonical_tag_add(canonical_tag: str, variant_tag: str) -> dict[str, Any]:
        """
        Add a canonical tag mapping for tag normalization.

        When tag_normalize_apply is called, variant_tag will be replaced with canonical_tag.

        Args:
            canonical_tag: The canonical (preferred) tag form
            variant_tag: A variant tag to map to the canonical form

        Returns:
            Dict with success status and mapping info
        """
        try:
            await task_store._ensure_db_initialized_async()

            result = task_store.add_canonical_mapping(canonical_tag, variant_tag)
            return result

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to add canonical mapping",
                "message": str(e)
            }

    @mcp.tool()
    async def canonical_tag_remove(variant_tag: str) -> dict[str, Any]:
        """
        Remove a canonical tag mapping.

        Args:
            variant_tag: The variant tag to remove from mappings

        Returns:
            Dict with success status
        """
        try:
            await task_store._ensure_db_initialized_async()

            result = task_store.remove_canonical_mapping(variant_tag)
            return result

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to remove canonical mapping",
                "message": str(e)
            }

    @mcp.tool()
    async def canonical_tag_list() -> dict[str, Any]:
        """
        List all canonical tag mappings.

        Returns:
            Dict with list of canonical tags and their variants
        """
        try:
            await task_store._ensure_db_initialized_async()

            canonical_tags = task_store.get_all_canonical_tags()

            return {
                "success": True,
                "canonical_tags": canonical_tags,
                "total_mappings": sum(len(ct["variants"]) for ct in canonical_tags),
                "total_canonicals": len(canonical_tags),
                "message": f"Found {len(canonical_tags)} canonical tags with {sum(len(ct['variants']) for ct in canonical_tags)} variant mappings"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to list canonical tags",
                "message": str(e)
            }

    @mcp.tool()
    async def tag_similarity(tag1: str, tag2: str) -> dict[str, Any]:
        """
        Calculate semantic similarity between two tags using embeddings.

        Args:
            tag1: First tag
            tag2: Second tag

        Returns:
            Dict with similarity score (0.0 to 1.0)
        """
        try:
            await task_store._ensure_db_initialized_async()

            model = await task_store.get_embedding_model_async()

            similarity = model.similarity(tag1, tag2)

            return {
                "success": True,
                "tag1": tag1,
                "tag2": tag2,
                "similarity": round(similarity, 4),
                "message": f"Similarity between '{tag1}' and '{tag2}': {similarity:.4f}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to calculate similarity",
                "message": str(e)
            }

    @mcp.tool()
    async def get_canonical_tags() -> dict[str, Any]:
        """
        Get all canonical tags (semantic tag clusters).

        Canonical tags are the normalized form of semantically similar tags.
        Returns list of canonical tags from predefined mappings only.
        """
        try:
            await task_store._ensure_db_initialized_async()

            canonical_tags = task_store.get_all_canonical_tags()

            tags_list = [ct["canonical_tag"] for ct in canonical_tags]

            return {
                "success": True,
                "tags": tags_list,
                "count": len(tags_list),
                "message": f"Retrieved {len(tags_list)} canonical tags"
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Failed to retrieve canonical tags",
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
