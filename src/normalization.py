"""
Tag Normalization Module
========================

Provides vector-based tag/category normalization using semantic similarity.
Groups similar tags and suggests canonical forms for deduplication.

Supports predefined canonical mappings (from DB) that take priority
over dynamic vector-based grouping.

Hard Guards:
- Version guard: tags with different versions never merge (v1 vs v2)
- Numeric guard: tags with different numbers never merge (api1 vs api2)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any
import numpy as np

from .embeddings import EmbeddingModel


@dataclass
class TagGroup:
    """Represents a group of similar tags with a canonical form."""
    canonical: str
    variants: List[str]
    similarity: float
    source: str = "vector"


@dataclass
class NormalizationPreview:
    """Preview of normalization changes."""
    groups: List[TagGroup]
    total_tags: int
    unique_tags_after: int
    tags_to_merge: int
    predefined_mappings_used: int = 0


class TagNormalizer:
    """Vector-based tag normalizer using semantic similarity."""

    MERGE_THRESHOLD = 0.90
    SUGGEST_THRESHOLD = 0.85
    DEFAULT_THRESHOLD = MERGE_THRESHOLD

    VERSION_PATTERN = re.compile(
        r'(?:v|version|ver)?\.?\s*(\d+(?:\.\d+)*)',
        re.IGNORECASE
    )
    NUMBER_PATTERN = re.compile(r'\d+(?:\.\d+)?')

    SUBSTRING_BOOST_STOP_WORDS = {
        'api', 'ui', 'db', 'test', 'auth', 'infra', 'ci', 'cd',
        'web', 'app', 'lib', 'sdk', 'cli', 'gui', 'orm', 'sql',
        'css', 'html', 'xml', 'json', 'yaml', 'tcp', 'udp', 'http',
    }

    SUBSTRING_BOOST_MIN_LENGTH = 4
    SUBSTRING_BOOST_DELTA = 0.05

    ALLOWED_FACET_PREFIXES = {
        'type', 'priority', 'status', 'domain', 'layer', 'scope',
        'batch', 'version', 'env', 'team', 'epic', 'sprint',
    }

    TAG_BOOST_LEVELS = {
        'high': 1.5,
        'medium': 1.0,
        'low': 0.5,
        'filter_only': 0.1,
    }

    HIGH_BOOST_PATTERNS = [
        r'^vendor:',
        r'^module:',
        r'^package:',
        r'^service:',
        r'^component:',
    ]

    FILTER_ONLY_PATTERNS = [
        r'^status:',
        r'^priority:',
        r'^batch:',
    ]

    GENERAL_TAGS = {
        'api', 'backend', 'frontend', 'auth', 'database', 'db',
        'test', 'testing', 'ci', 'cd', 'infra', 'security',
        'ui', 'ux', 'web', 'mobile', 'desktop',
    }

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        threshold: float = None,
        canonical_mappings: Dict[str, str] = None
    ):
        """
        Initialize normalizer with embedding model.

        Args:
            embedding_model: Pre-loaded EmbeddingModel instance
            threshold: Similarity threshold for grouping (default: 0.90)
            canonical_mappings: Predefined variant -> canonical mappings (from DB)
        """
        self.model = embedding_model
        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self.canonical_mappings = canonical_mappings or {}

    def _normalize_tag(self, tag: str) -> str:
        """
        Normalize tag for comparison.

        - lowercase
        - replace _ - with space
        - normalize version/ver to v
        """
        normalized = tag.lower().strip()
        normalized = re.sub(r'[_\-]', ' ', normalized)
        normalized = re.sub(r'\bversion\b', 'v', normalized)
        normalized = re.sub(r'\bver\b', 'v', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _normalize_version(self, version: str) -> str:
        """
        Normalize version string for comparison.

        Removes trailing zeros: "2.0" -> "2", "2.0.0" -> "2"
        But keeps minor: "18.17" -> "18.17", "2.1" -> "2.1"
        """
        parts = version.split('.')
        while len(parts) > 1 and parts[-1] == '0':
            parts.pop()
        return '.'.join(parts)

    def classify_tag(self, tag: str) -> Dict[str, Any]:
        """
        Classify a tag by boost level for search ranking.

        Returns:
            Dict with:
                - level: 'high', 'medium', 'low', or 'filter_only'
                - boost: numeric boost value
                - reason: explanation for classification
        """
        tag_lower = tag.lower()

        for pattern in self.HIGH_BOOST_PATTERNS:
            if re.match(pattern, tag_lower):
                return {
                    'level': 'high',
                    'boost': self.TAG_BOOST_LEVELS['high'],
                    'reason': f'matches pattern {pattern}'
                }

        for pattern in self.FILTER_ONLY_PATTERNS:
            if re.match(pattern, tag_lower):
                return {
                    'level': 'filter_only',
                    'boost': self.TAG_BOOST_LEVELS['filter_only'],
                    'reason': f'filter-only pattern {pattern}'
                }

        if ':' in tag_lower:
            prefix = tag_lower.split(':')[0]
            if prefix in self.ALLOWED_FACET_PREFIXES:
                return {
                    'level': 'medium',
                    'boost': self.TAG_BOOST_LEVELS['medium'],
                    'reason': f'facet tag with prefix {prefix}'
                }

        normalized = self._normalize_tag(tag_lower)
        if normalized in self.GENERAL_TAGS:
            return {
                'level': 'low',
                'boost': self.TAG_BOOST_LEVELS['low'],
                'reason': 'general/common tag'
            }

        return {
            'level': 'medium',
            'boost': self.TAG_BOOST_LEVELS['medium'],
            'reason': 'specific tag'
        }

    def get_tag_boost(self, tag: str) -> float:
        """
        Get boost value for a tag.

        Args:
            tag: Tag string

        Returns:
            Numeric boost value for search ranking
        """
        classification = self.classify_tag(tag)
        return classification['boost']

    def classify_tags(self, tags: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Classify multiple tags by boost level.

        Args:
            tags: List of tag strings

        Returns:
            Dict with keys 'high', 'medium', 'low', 'filter_only'
            Each contains list of {tag, boost, reason}
        """
        result = {
            'high': [],
            'medium': [],
            'low': [],
            'filter_only': [],
        }

        for tag in tags:
            classification = self.classify_tag(tag)
            level = classification['level']
            result[level].append({
                'tag': tag,
                'boost': classification['boost'],
                'reason': classification['reason']
            })

        return result

    def _extract_versions(self, tag: str) -> Set[str]:
        """
        Extract version numbers from tag.

        Examples:
            "api v2.0" -> {"2"}
            "php8" -> {"8"}
            "laravel v11" -> {"11"}
            "node v18.17" -> {"18.17"}
        """
        normalized = self._normalize_tag(tag)
        versions = set()

        for match in self.VERSION_PATTERN.finditer(normalized):
            version = match.group(1)
            versions.add(self._normalize_version(version))

        if not versions:
            number_matches = self.NUMBER_PATTERN.findall(normalized)
            context_before = re.search(r'(?:v|version|ver|php|node|python|api)\s*$', normalized.lower())
            if context_before and number_matches:
                versions.add(self._normalize_version(number_matches[0]))

        return versions

    def _extract_numbers(self, tag: str) -> Set[str]:
        """
        Extract all numbers from tag.

        Examples:
            "api2" -> {"2"}
            "php 8.2" -> {"8", "2"}  # split by dot
            "level 3 stage 4" -> {"3", "4"}
        """
        normalized = self._normalize_tag(tag)
        numbers = set()

        for match in self.NUMBER_PATTERN.finditer(normalized):
            num = match.group()
            if '.' in num:
                numbers.update(num.split('.'))
            else:
                numbers.add(num)

        return numbers

    def _extract_prefix_suffix(self, tag: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract prefix and suffix around colon.

        Examples:
            "type:refactor" -> ("type", "refactor")
            "priority:high" -> ("priority", "high")
            "backend" -> (None, None)
        """
        if ':' not in tag:
            return None, None

        parts = tag.split(':', 1)
        if len(parts) == 2:
            return parts[0].lower().strip(), parts[1].lower().strip()
        return None, None

    def _is_substring_match(self, tag1: str, tag2: str) -> bool:
        """
        Check if one normalized tag is a substring of another.

        Args:
            tag1: First tag
            tag2: Second tag

        Returns:
            True if one is substring of another
        """
        norm1 = self._normalize_tag(tag1)
        norm2 = self._normalize_tag(tag2)

        if norm1 == norm2:
            return False

        return norm1 in norm2 or norm2 in norm1

    def _apply_substring_boost(
        self,
        tag1: str,
        tag2: str,
        similarity: float
    ) -> float:
        """
        Apply substring boost to similarity score.

        If one tag is a substring of another AND conditions met,
        boost similarity to MERGE_THRESHOLD + 0.01 (0.91).

        Conditions:
        - Both tags pass hard guards
        - One is substring of another
        - Same version context (both have version or both don't)
        - Shorter tag >= SUBSTRING_BOOST_MIN_LENGTH (4 chars)
        - Shorter tag not in SUBSTRING_BOOST_STOP_WORDS

        Examples:
            "laravel" ⊂ "laravel framework" → boost ✅ (len=7, not stop-word)
            "api" ⊂ "rest api" → NO boost ❌ (stop-word)
            "php" ⊂ "php8" → NO boost (version asymmetry)
            "php8" ⊂ "php8.2" → NO boost (different versions)

        Args:
            tag1: First tag
            tag2: Second tag
            similarity: Original similarity score

        Returns:
            Boosted similarity score (or original if no boost)
        """
        can_merge, _ = self._can_merge_tags(tag1, tag2)

        if not can_merge:
            return similarity

        if not self._is_substring_match(tag1, tag2):
            return similarity

        versions1 = self._extract_versions(tag1)
        versions2 = self._extract_versions(tag2)

        if bool(versions1) != bool(versions2):
            return similarity

        norm1 = self._normalize_tag(tag1)
        norm2 = self._normalize_tag(tag2)

        shorter = norm1 if len(norm1) < len(norm2) else norm2
        shorter_word = shorter.split()[0] if ' ' in shorter else shorter

        if len(shorter_word) < self.SUBSTRING_BOOST_MIN_LENGTH:
            return similarity

        if shorter_word in self.SUBSTRING_BOOST_STOP_WORDS:
            return similarity

        # Boost by delta, not fixed value. Still must pass threshold.
        return min(similarity + self.SUBSTRING_BOOST_DELTA, 1.0)

    def _can_merge_tags(self, tag1: str, tag2: str) -> Tuple[bool, str]:
        """
        Check if two tags can be merged (hard guards).

        Returns:
            Tuple of (can_merge, reason)
        """
        prefix1, suffix1 = self._extract_prefix_suffix(tag1)
        prefix2, suffix2 = self._extract_prefix_suffix(tag2)

        # Facet model for colon tags
        if prefix1 and prefix2:
            # Both structured - must have same prefix (facet)
            if prefix1 != prefix2:
                return False, f"facet_guard: different prefixes '{prefix1}' vs '{prefix2}'"
            # Same prefix - allow merge within facet (suffix similarity will decide)
        elif prefix1 or prefix2:
            # One structured, one plain -> NO MERGE
            return False, f"prefix_guard: one is structured '{tag1 if prefix1 else tag2}', other is plain '{tag2 if prefix1 else tag1}'"

        versions1 = self._extract_versions(tag1)
        versions2 = self._extract_versions(tag2)

        if versions1 and versions2 and versions1 != versions2:
            return False, f"version_guard: {versions1} vs {versions2}"

        numbers1 = self._extract_numbers(tag1)
        numbers2 = self._extract_numbers(tag2)

        if numbers1 and numbers2 and numbers1 != numbers2:
            non_version1 = numbers1 - versions1
            non_version2 = numbers2 - versions2
            if non_version1 and non_version2 and non_version1 != non_version2:
                return False, f"numeric_guard: {numbers1} vs {numbers2}"

        return True, "ok"

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def _get_embeddings(self, tags: List[str]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for all tags.

        Tags are normalized before embedding for better similarity matching.

        Args:
            tags: List of tag strings

        Returns:
            Dict mapping tag -> embedding vector
        """
        if not tags:
            return {}

        normalized_tags = [self._normalize_tag(t) for t in tags]
        embeddings = self.model.encode(normalized_tags)
        return {tag: embeddings[i] for i, tag in enumerate(tags)}

    def _build_similarity_matrix(self, tags: List[str], embeddings: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Build similarity matrix for all tag pairs with hard guards and substring boost.

        Args:
            tags: List of tags
            embeddings: Tag -> embedding mapping

        Returns:
            NxN similarity matrix (0.0 for blocked pairs)
        """
        n = len(tags)
        matrix = np.eye(n)

        for i in range(n):
            for j in range(i + 1, n):
                can_merge, _ = self._can_merge_tags(tags[i], tags[j])
                if can_merge:
                    sim = self._cosine_similarity(embeddings[tags[i]], embeddings[tags[j]])
                    sim = self._apply_substring_boost(tags[i], tags[j], sim)
                    matrix[i, j] = sim
                    matrix[j, i] = sim
                else:
                    matrix[i, j] = 0.0
                    matrix[j, i] = 0.0

        return matrix

    def _find_groups_union_find(self, tags: List[str], similarity_matrix: np.ndarray) -> List[List[int]]:
        """
        Find groups of similar tags using Union-Find algorithm.

        Args:
            tags: List of tags
            similarity_matrix: NxN similarity matrix

        Returns:
            List of tag index groups
        """
        n = len(tags)
        parent = list(range(n))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i in range(n):
            for j in range(i + 1, n):
                if similarity_matrix[i, j] >= self.threshold:
                    union(i, j)

        groups_dict: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups_dict:
                groups_dict[root] = []
            groups_dict[root].append(i)

        return list(groups_dict.values())

    def _select_canonical_tag(
        self,
        tags: List[str],
        tag_counts: Dict[str, int],
        similarity_matrix: np.ndarray,
        indices: List[int]
    ) -> Tuple[str, float]:
        """
        Select canonical tag from a group.

        Selection priority:
        1. Most frequently used (highest count)
        2. Longest tag (if counts equal)

        Args:
            tags: All tags list
            tag_counts: Tag -> usage count mapping
            similarity_matrix: Similarity matrix
            indices: Indices of tags in this group

        Returns:
            Tuple of (canonical_tag, avg_similarity)
        """
        group_tags = [tags[i] for i in indices]

        sorted_tags = sorted(
            group_tags,
            key=lambda t: (tag_counts.get(t, 0), len(t)),
            reverse=True
        )

        if len(indices) > 1:
            total_sim = 0.0
            count = 0
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    total_sim += similarity_matrix[indices[i], indices[j]]
                    count += 1
            avg_sim = total_sim / count if count > 0 else 1.0
        else:
            avg_sim = 1.0

        return sorted_tags[0], avg_sim

    def preview_normalization(
        self,
        tags: List[str],
        tag_counts: Dict[str, int]
    ) -> NormalizationPreview:
        """
        Preview normalization changes without applying them.

        Combines predefined canonical mappings with vector-based grouping.
        Predefined mappings take priority.

        Args:
            tags: List of unique tags to analyze
            tag_counts: Tag -> usage count mapping

        Returns:
            NormalizationPreview with suggested groups
        """
        if not tags:
            return NormalizationPreview(
                groups=[],
                total_tags=0,
                unique_tags_after=0,
                tags_to_merge=0,
                predefined_mappings_used=0
            )

        tags = list(set(tags))
        tags.sort()

        tag_groups: List[TagGroup] = []
        tags_to_merge = 0
        predefined_used = 0
        tags_needing_vector_analysis = []

        for tag in tags:
            if tag in self.canonical_mappings:
                canonical = self.canonical_mappings[tag]
                existing_group = next((g for g in tag_groups if g.canonical == canonical), None)
                if existing_group:
                    existing_group.variants.append(tag)
                else:
                    tag_groups.append(TagGroup(
                        canonical=canonical,
                        variants=[tag],
                        similarity=1.0,
                        source="predefined"
                    ))
                tags_to_merge += 1
                predefined_used += 1
            else:
                tags_needing_vector_analysis.append(tag)

        if tags_needing_vector_analysis:
            embeddings = self._get_embeddings(tags_needing_vector_analysis)
            similarity_matrix = self._build_similarity_matrix(tags_needing_vector_analysis, embeddings)
            groups_indices = self._find_groups_union_find(tags_needing_vector_analysis, similarity_matrix)

            for indices in groups_indices:
                if len(indices) == 1:
                    continue

                canonical, avg_sim = self._select_canonical_tag(
                    tags_needing_vector_analysis, tag_counts, similarity_matrix, indices
                )

                variants = [tags_needing_vector_analysis[i] for i in indices if tags_needing_vector_analysis[i] != canonical]

                tag_groups.append(TagGroup(
                    canonical=canonical,
                    variants=variants,
                    similarity=round(avg_sim, 3),
                    source="vector"
                ))
                tags_to_merge += len(variants)

        tag_groups.sort(key=lambda g: (g.source == "predefined", len(g.variants)), reverse=True)

        return NormalizationPreview(
            groups=tag_groups,
            total_tags=len(tags),
            unique_tags_after=len(tags) - tags_to_merge,
            tags_to_merge=tags_to_merge,
            predefined_mappings_used=predefined_used
        )

    def get_mapping(self, preview: NormalizationPreview) -> Dict[str, str]:
        """
        Get tag -> canonical_tag mapping from preview.

        Args:
            preview: NormalizationPreview from preview_normalization()

        Returns:
            Dict mapping variant -> canonical for tags that should be merged
        """
        mapping: Dict[str, str] = {}

        for group in preview.groups:
            for variant in group.variants:
                mapping[variant] = group.canonical

        return mapping
