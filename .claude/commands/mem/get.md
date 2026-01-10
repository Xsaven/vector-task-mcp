---
name: "mem:get"
description: "Get specific memory by ID"
---

<command>
<meta>
<id>mem:get</id>
<description>Get specific memory by ID</description>
</meta>
<purpose>Retrieves and displays full content of a specific memory by ID from $ARGUMENTS. Shows all metadata, full content, and suggested actions.</purpose>
<purpose>Retrieves and displays full content of a specific memory by ID.</purpose>
<guidelines>

# Role
Memory retrieval utility that fetches and displays full content of a specific memory by ID.

# Workflow step1
STEP 1 - Parse Arguments for Memory ID
## Examples
- format-1: /mem:get 15 → get memory by ID
- format-2: /mem:get id=15 → explicit parameter
- validate: IF(STORE-GET($RAW_INPUT) is empty or not a number) → THEN → [Display: "Error: Memory ID required" → Display: "Usage: /mem:get {id}" → SKIP(No ID provided)] → END-IF

# Input
STORE-AS($RAW_INPUT = '$ARGUMENTS')
STORE-AS($MEMORY_ID = '{numeric ID extracted from $RAW_INPUT}')

# Workflow step2
STEP 2 - Fetch Memory by ID
## Examples
- fetch: mcp__vector-memory__get_by_memory_id('{memory_id: STORE-GET($MEMORY_ID)}')
- store: STORE-AS($MEMORY = 'memory object or null')

# Workflow step3
STEP 3 - Handle Memory Not Found
## Examples
- check: IF(STORE-GET($MEMORY) is null) → THEN → [Display: "Memory #{id} not found." → Suggest: "Use /mem:list to see available memories" → Suggest: "Use /mem:search to find by content"] → END-IF

# Workflow step4
STEP 4 - Display Full Memory Content
## Examples
- header: Display: "--- Memory #{id} ---"
- meta: Display: "Category: {category}" → Display: "Tags: {tags}" → Display: "Created: {created_at}" → Display: "Updated: {updated_at}" → Display: "Access count: {access_count}"
- divider: Display: "---"
- content: Display: "{full_content}"
- divider-end: Display: "---"
- actions: Display: "Actions:" → Display: "  /mem:cleanup id={id} → delete this memory" → Display: "  /mem:search \\"{first_words}\\" → find similar"

# Output format
Memory display format
## Examples
- --- Memory #15 ---
- Category: code-solution
- Tags: php, laravel, auth
- Created: 2025-11-20 14:30:00
- Access count: 5
- ---
- {full memory content here}
- Actions:
-   /mem:cleanup id=15 → delete
-   /mem:search "keywords" → find similar

# Usage examples
Command usage patterns
## Examples
- /mem:get 15 → get memory #15
- /mem:get id=15 → explicit parameter

# Error messages
Error handling messages
## Examples
- Error: Memory ID required
- Memory #15 not found.
- Use /mem:list to see available memories

</guidelines>
</command>