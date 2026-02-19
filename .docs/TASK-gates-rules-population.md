# TASK: Populate Gates & Rules Category

## Status: COMPLETED

### Issue 1: Header Format (FIXED)

The header `## Gates & Rules Scenarios` was changed to `## Gates Rules Scenarios` (no `&`).

**Reason:** The `&` symbol breaks regex parsing in category detection.

**Consistency:** Same fix applied to both MCPs:
- `vector-task-mcp/src/CASES.md` → `## Gates Rules Scenarios`
- `vector-memory-mcp/src/CASES_AGENTS.md` → `## Gates Rules Scenarios`

Regex in test updated to handle format: `r'^## Gates.*?Rules.*?(?=^## |\Z)'`

### Issue 2: Description (FIXED)

```markdown
## Gates Rules Scenarios
<!-- description: Critical gates and constitutional rules. WHEN to enforce, not HOW to implement. -->
```

### Issue 3: 6 Constitutional Gates Added (FIXED)

All 6 gates added to `src/CASES.md`:

1. **Gate 1: MCP-JSON-ONLY** [CRITICAL]
2. **Gate 2: Lightweight Lawyer Gate** [HIGH]
3. **Gate 3: Constitutional Learn Protocol** [CRITICAL]
4. **Gate 4: Category Discipline Contract** [HIGH]
5. **Gate 5: Cookbook-First Gate** [HIGH]
6. **Gate 6: Failure Escalation Gate** [HIGH]

### Tests Passing

```
tests/test_cases_integrity.py::TestCasesIntegrity::test_gates_rules_has_content PASSED
```

### Files Updated

- `src/CASES.md` - Added Six Constitutional Gates section
- `tests/test_cases_integrity.py` - Updated regex, added 6 gates check
- `.docs/brain-integration-guide.md` - Added Section F: Six Constitutional Gates
- `.docs/common/vector-task-brain-integration-guide.md` - Added Section F
- `.docs/common/vector-memory-brain-integration-guide.md` - Added Section F

### Cross-Project Consistency

Same changes applied to `vector-memory-mcp`:
- `src/CASES_AGENTS.md` - Added Six Constitutional Gates
- `tests/test_cases_integrity.py` - Created (identical test)
- `.docs/brain-integration-guide.md` - Added Section F
