"""
Test CASES.md integrity: all categories must have description and content.

Run: pytest tests/test_cases_integrity.py -v

This test ensures:
1. All categories have non-empty description in <!-- description: ... -->
2. All categories have actual content (not empty when queried)
3. Category naming follows conventions
"""

import re
import pytest
from pathlib import Path


CASES_FILE = Path(__file__).parent.parent / "src" / "CASES.md"


def parse_categories_from_cases():
    """Parse all category headers with their descriptions from CASES.md"""
    content = CASES_FILE.read_text()
    
    # Pattern: ## Name Scenarios (optional) followed by optional <!-- description: ... -->
    pattern = r'^## (.+?)(?: Scenarios)?(?: \([A-Z]+\))?\n(?:<!-- description: (.+?) -->)?'
    matches = re.findall(pattern, content, re.MULTILINE)
    
    categories = []
    for name, description in matches:
        # Convert name to key: "Gates & Rules" -> "gates-rules"
        key = name.lower()
        key = re.sub(r'[&()]', '', key)
        key = re.sub(r'\s+', '-', key)
        key = re.sub(r'-+', '-', key).strip('-')
        
        categories.append({
            "name": name,
            "key": key,
            "description": description.strip() if description else ""
        })
    
    return categories


def get_expected_categories():
    """Expected categories based on cookbook API"""
    return [
        "essential-patterns",
        "task-decision", 
        "task-creation",
        "task-execution",
        "search-query",
        "tag-normalization",
        "hierarchy-decomposition",
        "status-time-tracking",
        "error-handling-recovery",
        "parallel-execution",
        "validation",
        "tag-intelligence",
        "debug-developer",
        "tag-selection",
        "statistics-reporting",
        "brainstorm-ideation",
        "multi-probe-search",
        "comment-context",
        "memory-integration",
        "gates-rules",
        "cookbook-usage",
        "garbage-collection-cleanup",
        "anti-pattern-examples",
        "technical-debt-management",
        "constitutional-learn-protocol",
        "self-improvement",
        "lightweight-lawyer-gate",
        "standard-search-patterns-quick-reference",
        "tag-taxonomy-quick-reference",
    ]


class TestCasesIntegrity:
    """Test suite for CASES.md integrity"""
    
    def test_cases_file_exists(self):
        """CASES.md must exist"""
        assert CASES_FILE.exists(), f"CASES.md not found at {CASES_FILE}"
    
    def test_all_categories_have_description(self):
        """All categories must have non-empty description"""
        categories = parse_categories_from_cases()
        
        missing_descriptions = []
        for cat in categories:
            if not cat["description"]:
                missing_descriptions.append(cat["key"])
        
        assert not missing_descriptions, (
            f"Categories missing description:\n"
            + "\n".join(f"  - {k}" for k in missing_descriptions)
            + "\n\nFix: Add <!-- description: Your description here --> after the ## header"
        )
    
    def test_expected_categories_exist(self):
        """All expected categories must be present in CASES.md"""
        categories = parse_categories_from_cases()
        found_keys = {cat["key"] for cat in categories}
        expected_keys = set(get_expected_categories())
        
        missing = expected_keys - found_keys
        extra = found_keys - expected_keys
        
        error_parts = []
        if missing:
            error_parts.append(f"Missing categories:\n" + "\n".join(f"  - {k}" for k in sorted(missing)))
        if extra:
            error_parts.append(f"Unexpected categories:\n" + "\n".join(f"  - {k}" for k in sorted(extra)))
        
        assert not missing and not extra, "\n\n".join(error_parts)
    
    def test_category_key_format(self):
        """Category keys must follow lowercase-with-dashes format"""
        categories = parse_categories_from_cases()
        
        invalid_keys = []
        for cat in categories:
            # Should be lowercase, dashes only, no double dashes
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', cat["key"]):
                invalid_keys.append(f"{cat['name']} -> {cat['key']}")
        
        assert not invalid_keys, (
            f"Invalid category key formats:\n"
            + "\n".join(f"  - {k}" for k in invalid_keys)
            + "\n\nKeys must be lowercase with single dashes: 'gates-rules', not 'Gates & Rules'"
        )
    
    def test_description_quality(self):
        """Descriptions should be meaningful (not too short, not placeholder)"""
        categories = parse_categories_from_cases()
        
        weak_descriptions = []
        for cat in categories:
            desc = cat["description"]
            # Check for placeholder-like descriptions
            if desc.lower() in ["", "todo", "tbd", "n/a", "none"]:
                weak_descriptions.append(f"{cat['key']}: '{desc}' (empty/placeholder)")
            elif len(desc) < 20:
                weak_descriptions.append(f"{cat['key']}: '{desc}' (too short, min 20 chars)")
        
        assert not weak_descriptions, (
            f"Weak descriptions found:\n"
            + "\n".join(f"  - {d}" for d in weak_descriptions)
            + "\n\nDescriptions should be informative and at least 20 characters"
        )
    
    def test_gates_rules_has_content(self):
        """gates-rules category must have 6 constitutional gates"""
        content = CASES_FILE.read_text()
        
        gates_match = re.search(
            r'^## Gates & Rules.*?(?=^## |\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        assert gates_match, "gates-rules section not found in CASES.md"
        
        gates_content = gates_match.group(0)
        
        required_gates = [
            "Gate 1: MCP-JSON-ONLY",
            "Gate 2: Lightweight Lawyer Gate",
            "Gate 3: Constitutional Learn Protocol",
            "Gate 4: Category Discipline Contract",
            "Gate 5: Cookbook-First Gate",
            "Gate 6: Failure Escalation Gate"
        ]
        
        missing_gates = []
        for gate in required_gates:
            if gate.lower() not in gates_content.lower():
                missing_gates.append(gate)
        
        assert not missing_gates, (
            f"gates-rules missing required gates:\n"
            + "\n".join(f"  - {g}" for g in missing_gates)
        )
        
        assert "[CRITICAL]" in gates_content, "gates-rules must contain CRITICAL priority rules"
        assert "[HIGH]" in gates_content, "gates-rules must contain HIGH priority rules"


# CLI helper to show current status
if __name__ == "__main__":
    print("=== CASES.md Integrity Check ===\n")
    
    categories = parse_categories_from_cases()
    expected = set(get_expected_categories())
    
    print("Categories with descriptions:\n")
    for cat in categories:
        status = "✓" if cat["description"] else "✗ MISSING"
        print(f"  {status} {cat['key']}")
        if cat["description"]:
            print(f"      {cat['description'][:60]}{'...' if len(cat['description']) > 60 else ''}")
    
    print(f"\nTotal: {len(categories)} categories")
    print(f"Missing descriptions: {sum(1 for c in categories if not c['description'])}")
    
    found_keys = {cat["key"] for cat in categories}
    missing = expected - found_keys
    if missing:
        print(f"\nMissing categories: {missing}")
