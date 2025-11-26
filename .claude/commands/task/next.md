---
name: task:next
description: "Get next task to execute (in_progress or highest priority pending)"
---

<command>
<meta>
<id>task:next</id>
<description>Get next task to execute (in_progress or highest priority pending)</description>
</meta>
<purpose>Smart selection of next task to work on. Returns currently in_progress task or highest priority pending task. Shows task details, parent hierarchy, and related vector memory insights. Simple utility command for task workflow.</purpose>
<purpose>The next task selection specialist uses MCP to identify the next task to work on. Includes task details, parent hierarchy, and related vector memory insights.</purpose>
<guidelines>
<guideline id="workflow-step1">
<text>STEP 1 - Get Next Task via MCP</text>
<example>
<phase name="action">mcp__vector-task__task_next('{}')</phase>
<phase name="store">STORE-AS($NEXT_TASK = 'task object or null')</phase>
</example>
</guideline>
<guideline id="workflow-step2">
<text>STEP 2 - Handle No Tasks Available</text>
<example>
<phase name="check">IF(STORE-GET($NEXT_TASK) is null or empty) → THEN → [Display: "No pending tasks available." → Suggest: "Use /task:init to initialize project tasks" → Suggest: "Use /task:create {description} to add a new task" → SKIP(No task to display)] → END-IF</phase>
</example>
</guideline>
<guideline id="workflow-step3">
<text>STEP 3 - Display Task Details</text>
<example>
<phase name="display-1">Task ID: {id}</phase>
<phase name="display-2">Status: {status} (in_progress or pending)</phase>
<phase name="display-3">Title: {title}</phase>
<phase name="display-4">Priority: {priority}</phase>
<phase name="display-5">Tags: {tags}</phase>
<phase name="display-6">Content: {content}</phase>
</example>
</guideline>
<guideline id="workflow-step4">
<text>STEP 4 - Show Parent Hierarchy (if parent_id exists)</text>
<example>
<phase name="check">IF(STORE-GET($NEXT_TASK).parent_id is not null) → THEN → [mcp__vector-task__task_get('{task_id: STORE-GET($NEXT_TASK).parent_id}') → STORE-AS($PARENT_TASK = 'parent task object') → Display: "Parent Task: {parent.title} (ID: {parent.id})"] → ELSE → [SKIP(No parent task)] → END-IF</phase>
</example>
</guideline>
<guideline id="workflow-step5">
<text>STEP 5 - Search Vector Memory for Related Insights</text>
<example>
<phase name="search">mcp__vector-memory__search_memories('{query: "STORE-GET($NEXT_TASK).title", limit: 3}')</phase>
<phase name="display">IF(memories found) → THEN → [Display: "Related Insights:" followed by memory summaries] → ELSE → [SKIP(No related insights)] → END-IF</phase>
</example>
</guideline>
<guideline id="workflow-step6">
<text>STEP 6 - Suggest Next Actions</text>
<example>
<phase name="suggest-1">IF(STORE-GET($NEXT_TASK).status is pending) → THEN → [Suggest: "Start working? Use /do:async or /do:sync to execute this task"] → END-IF</phase>
<phase name="suggest-2">IF(STORE-GET($NEXT_TASK).status is in_progress) → THEN → [Suggest: "Continue working on this task. Use /do:async or /do:sync"] → END-IF</phase>
<phase name="suggest-3">Suggest: "Use /task:decompose {id} if task needs breakdown"</phase>
</example>
</guideline>
<guideline id="output-format">
<text>Display format for task details</text>
<example key="header">## Next Task</example>
<example key="meta">ID: {id} | Status: {status} | Priority: {priority}</example>
<example key="title">Title: {title}</example>
<example key="tags">Tags: {tags joined}</example>
<example key="content">Content: {content}</example>
<example key="parent">Parent: {parent.title} (optional)</example>
<example key="insights">Related Insights: {memories} (optional)</example>
<example key="cta">Ready to execute? Use /do:async or /do:sync</example>
</guideline>
</guidelines>
</command>