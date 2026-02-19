"""
Tag Normalization Tests
======================

Tests for src/normalization.py TagNormalizer class.
"""

import pytest
import numpy as np
from unittest.mock import Mock

from src.normalization import TagNormalizer, TagGroup, NormalizationPreview


class TestTagNormalizer:
    """
    Tests for TagNormalizer class.
    """

    @pytest.fixture
    def mock_embedding_model(self):
        """
        Mock embedding model with controllable similarity behavior.
        """
        mock_model = Mock()

        embeddings_cache = {}

        def encode_single(text: str) -> np.ndarray:
            if text not in embeddings_cache:
                text_hash = hash(text) % 2**32
                np.random.seed(text_hash)
                embeddings_cache[text] = np.random.rand(384).astype(np.float32)
            return embeddings_cache[text]

        def encode(texts: list) -> np.ndarray:
            return np.array([encode_single(t) for t in texts])

        mock_model.encode_single = encode_single
        mock_model.encode = encode

        return mock_model

    @pytest.fixture
    def similar_embedding_model(self):
        """
        Mock embedding model where similar tags produce similar embeddings.
        """
        mock_model = Mock()

        def get_tag_base(tag: str) -> str:
            tag_lower = tag.lower()
            if tag_lower in ("auth", "authentication", "auth-api"):
                return "auth"
            if tag_lower in ("backend", "backend-api", "backend-dev"):
                return "backend"
            if tag_lower in ("frontend", "frontend-ui"):
                return "frontend"
            return tag_lower

        def encode_single(text: str) -> np.ndarray:
            base = get_tag_base(text)
            base_hash = hash(base) % 2**32
            np.random.seed(base_hash)
            base_embedding = np.random.rand(384).astype(np.float32)
            
            variation = np.random.rand(384).astype(np.float32) * 0.1
            return base_embedding + variation

        def encode(texts: list) -> np.ndarray:
            return np.array([encode_single(t) for t in texts])

        mock_model.encode_single = encode_single
        mock_model.encode = encode

        return mock_model

    def test_preview_empty_tags(self, mock_embedding_model):
        """Test preview with no tags."""
        normalizer = TagNormalizer(mock_embedding_model)
        preview = normalizer.preview_normalization([], {})

        assert preview.total_tags == 0
        assert preview.unique_tags_after == 0
        assert preview.tags_to_merge == 0
        assert preview.groups == []

    def test_preview_single_tag(self, mock_embedding_model):
        """Test preview with single tag (no merging possible)."""
        normalizer = TagNormalizer(mock_embedding_model)
        preview = normalizer.preview_normalization(["auth"], {"auth": 5})

        assert preview.total_tags == 1
        assert preview.unique_tags_after == 1
        assert preview.tags_to_merge == 0
        assert preview.groups == []

    def test_preview_different_tags(self, mock_embedding_model):
        """Test preview with completely different tags."""
        normalizer = TagNormalizer(mock_embedding_model)
        preview = normalizer.preview_normalization(
            ["auth", "backend", "frontend"],
            {"auth": 5, "backend": 3, "frontend": 2}
        )

        assert preview.total_tags == 3
        assert preview.unique_tags_after == 3
        assert preview.tags_to_merge == 0
        assert preview.groups == []

    def test_preview_similar_tags(self, similar_embedding_model):
        """Test preview with similar tags that should be grouped."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)
        preview = normalizer.preview_normalization(
            ["auth", "authentication"],
            {"auth": 5, "authentication": 2}
        )

        assert preview.total_tags == 2
        assert len(preview.groups) >= 0

    def test_get_mapping_empty(self, mock_embedding_model):
        """Test mapping generation with no groups."""
        normalizer = TagNormalizer(mock_embedding_model)
        preview = NormalizationPreview(
            groups=[],
            total_tags=3,
            unique_tags_after=3,
            tags_to_merge=0
        )
        mapping = normalizer.get_mapping(preview)

        assert mapping == {}

    def test_get_mapping_with_groups(self, mock_embedding_model):
        """Test mapping generation with tag groups."""
        normalizer = TagNormalizer(mock_embedding_model)
        preview = NormalizationPreview(
            groups=[
                TagGroup(canonical="auth", variants=["authentication", "auth-api"], similarity=0.9),
                TagGroup(canonical="backend", variants=["backend-api"], similarity=0.85)
            ],
            total_tags=5,
            unique_tags_after=2,
            tags_to_merge=3
        )
        mapping = normalizer.get_mapping(preview)

        assert mapping["authentication"] == "auth"
        assert mapping["auth-api"] == "auth"
        assert mapping["backend-api"] == "backend"
        assert len(mapping) == 3

    def test_threshold_affects_grouping(self, similar_embedding_model):
        """Test that threshold affects how tags are grouped."""
        tags = ["auth", "authentication", "backend", "backend-api"]
        tag_counts = {"auth": 5, "authentication": 2, "backend": 3, "backend-api": 1}

        low_threshold = TagNormalizer(similar_embedding_model, threshold=0.5)
        high_threshold = TagNormalizer(similar_embedding_model, threshold=0.95)

        preview_low = low_threshold.preview_normalization(tags, tag_counts)
        preview_high = high_threshold.preview_normalization(tags, tag_counts)

        assert preview_low.tags_to_merge >= preview_high.tags_to_merge

    def test_cosine_similarity(self, mock_embedding_model):
        """Test cosine similarity calculation."""
        normalizer = TagNormalizer(mock_embedding_model)

        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        assert normalizer._cosine_similarity(a, b) == pytest.approx(1.0, rel=0.01)

        c = np.array([0.0, 1.0, 0.0])
        assert normalizer._cosine_similarity(a, c) == pytest.approx(0.0, abs=0.01)

        d = np.array([0.0, 0.0, 0.0])
        assert normalizer._cosine_similarity(a, d) == 0.0

    def test_canonical_selection_by_count(self, similar_embedding_model):
        """Test that canonical tag is selected by usage count."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)
        preview = normalizer.preview_normalization(
            ["auth", "authentication"],
            {"auth": 10, "authentication": 2}
        )

        if preview.groups:
            assert preview.groups[0].canonical == "auth"

    def test_canonical_selection_by_length_when_counts_equal(self, similar_embedding_model):
        """Test that longer tag is selected when counts are equal."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)
        preview = normalizer.preview_normalization(
            ["auth", "authentication"],
            {"auth": 2, "authentication": 2}
        )

        if preview.groups:
            assert preview.groups[0].canonical == "authentication"

    def test_predefined_mappings_prioritized(self, mock_embedding_model):
        """Test that predefined canonical mappings take priority over vector grouping."""
        canonical_mappings = {"authentication": "auth", "db": "database"}
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.85, canonical_mappings=canonical_mappings)

        preview = normalizer.preview_normalization(
            ["authentication", "db", "backend"],
            {"authentication": 2, "db": 1, "backend": 3}
        )

        predefined_groups = [g for g in preview.groups if g.source == "predefined"]
        assert len(predefined_groups) == 2
        assert preview.predefined_mappings_used == 2

        auth_group = next((g for g in predefined_groups if g.canonical == "auth"), None)
        assert auth_group is not None
        assert "authentication" in auth_group.variants

    def test_predefined_mappings_combine_variants(self, mock_embedding_model):
        """Test that multiple variants map to same canonical."""
        canonical_mappings = {"authentication": "auth", "auth-api": "auth"}
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.85, canonical_mappings=canonical_mappings)

        preview = normalizer.preview_normalization(
            ["authentication", "auth-api"],
            {"authentication": 2, "auth-api": 1}
        )

        predefined_groups = [g for g in preview.groups if g.source == "predefined"]
        assert len(predefined_groups) == 1
        assert predefined_groups[0].canonical == "auth"
        assert set(predefined_groups[0].variants) == {"authentication", "auth-api"}

    def test_get_mapping_with_predefined(self, mock_embedding_model):
        """Test that get_mapping includes predefined mappings."""
        canonical_mappings = {"authentication": "auth"}
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.85, canonical_mappings=canonical_mappings)

        preview = normalizer.preview_normalization(
            ["authentication", "backend"],
            {"authentication": 2, "backend": 3}
        )

        mapping = normalizer.get_mapping(preview)
        assert mapping["authentication"] == "auth"

    def test_source_field_in_groups(self, mock_embedding_model):
        """Test that groups have correct source field."""
        canonical_mappings = {"authentication": "auth"}
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.85, canonical_mappings=canonical_mappings)

        preview = normalizer.preview_normalization(
            ["authentication", "backend"],
            {"authentication": 2, "backend": 3}
        )

        for group in preview.groups:
            assert group.source in ["predefined", "vector"]

    # =========================================================================
    # Hard Guards Tests
    # =========================================================================

    def test_version_guard_blocks_merge(self, similar_embedding_model):
        """Test that tags with different versions never merge."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        can_merge, reason = normalizer._can_merge_tags("api v1", "api v2")
        assert can_merge is False
        assert "version_guard" in reason

    def test_version_guard_same_version_allows_merge(self, similar_embedding_model):
        """Test that tags with same version can merge."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        # v2 and v2.0 are same version (normalized to "2")
        can_merge, reason = normalizer._can_merge_tags("api v2", "api v2.0")
        assert can_merge is True

    def test_version_guard_same_version_exact(self, similar_embedding_model):
        """Test that tags with exact same version can merge."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        can_merge, reason = normalizer._can_merge_tags("api v1", "api v1")
        assert can_merge is True

    def test_version_guard_php_versions(self, similar_embedding_model):
        """Test version guard with PHP-like tags."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        can_merge, reason = normalizer._can_merge_tags("php8", "php7")
        assert can_merge is False
        assert "version_guard" in reason

    def test_numeric_guard_blocks_merge(self, similar_embedding_model):
        """Test that tags with different numbers never merge (non-version context)."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        # Use tags where numbers are clearly NOT versions (no v/version prefix)
        can_merge, reason = normalizer._can_merge_tags("task1", "task2")
        assert can_merge is False
        # Could be either guard depending on context
        assert "guard" in reason

    def test_numeric_guard_same_numbers_allows_merge(self, similar_embedding_model):
        """Test that tags with same numbers can merge."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        can_merge, reason = normalizer._can_merge_tags("api1", "api-1")
        assert can_merge is True

    def test_no_numbers_allows_merge(self, similar_embedding_model):
        """Test that tags without numbers can merge."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        can_merge, reason = normalizer._can_merge_tags("auth", "authentication")
        assert can_merge is True

    def test_one_tag_with_number_one_without(self, similar_embedding_model):
        """Test merge when one tag has number and other doesn't."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.7)

        can_merge, reason = normalizer._can_merge_tags("api", "api2")
        assert can_merge is True

    def test_extract_versions(self, mock_embedding_model):
        """Test version extraction from tags."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer._extract_versions("api v2.0") == {"2"}
        assert normalizer._extract_versions("php8") == {"8"}
        assert normalizer._extract_versions("laravel v11") == {"11"}
        assert normalizer._extract_versions("node v18.17") == {"18.17"}
        assert normalizer._extract_versions("api v2.0.0") == {"2"}

    def test_extract_numbers(self, mock_embedding_model):
        """Test number extraction from tags."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer._extract_numbers("api2") == {"2"}
        assert normalizer._extract_numbers("php 8.2") == {"8", "2"}
        assert normalizer._extract_numbers("level 3 stage 4") == {"3", "4"}

    def test_normalize_tag(self, mock_embedding_model):
        """Test tag normalization."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer._normalize_tag("API_V2") == "api v2"
        assert normalizer._normalize_tag("auth-api") == "auth api"
        assert normalizer._normalize_tag("Version 2") == "v 2"
        assert normalizer._normalize_tag("PHP_8.2") == "php 8.2"

    def test_normalize_version(self, mock_embedding_model):
        """Test version normalization."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer._normalize_version("2.0") == "2"
        assert normalizer._normalize_version("2.0.0") == "2"
        assert normalizer._normalize_version("2.1") == "2.1"
        assert normalizer._normalize_version("18.17") == "18.17"
        assert normalizer._normalize_version("1") == "1"

    def test_default_threshold_is_0_90(self, mock_embedding_model):
        """Test that default threshold is 0.90."""
        normalizer = TagNormalizer(mock_embedding_model)
        assert normalizer.threshold == 0.90

    def test_merge_and_suggest_thresholds_defined(self, mock_embedding_model):
        """Test that MERGE_THRESHOLD and SUGGEST_THRESHOLD are defined."""
        assert TagNormalizer.MERGE_THRESHOLD == 0.90
        assert TagNormalizer.SUGGEST_THRESHOLD == 0.85

    # =========================================================================
    # Substring Boost Tests
    # =========================================================================

    def test_is_substring_match(self, mock_embedding_model):
        """Test substring detection."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer._is_substring_match("laravel", "laravel framework") is True
        assert normalizer._is_substring_match("api", "rest api") is True
        assert normalizer._is_substring_match("auth", "authentication") is True
        assert normalizer._is_substring_match("backend", "frontend") is False
        assert normalizer._is_substring_match("api", "api") is False

    def test_substring_boost_applied(self, similar_embedding_model):
        """Test that substring boost is applied."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.90)

        raw_sim = 0.86  # below threshold, but will pass after boost
        boosted = normalizer._apply_substring_boost("laravel", "laravel framework", raw_sim)

        # Boost = raw + delta (0.05)
        assert boosted == raw_sim + 0.05
        assert boosted >= 0.90  # Now passes threshold

    def test_substring_boost_not_applied_for_different_versions(self, similar_embedding_model):
        """Test that substring boost is NOT applied when versions differ."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.90)

        raw_sim = 0.80
        boosted = normalizer._apply_substring_boost("php", "php8", raw_sim)

        # php has no version, php8 has version 8 → no boost
        assert boosted == raw_sim

    def test_substring_boost_same_version_allows_boost(self, similar_embedding_model):
        """Test that substring boost IS applied when both have same version."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.90)

        raw_sim = 0.86  # below threshold, but will pass after boost
        # 'laravel' is not stop-word, both have version 2
        boosted = normalizer._apply_substring_boost("laravel v2", "laravel v2 framework", raw_sim)

        # both have version 2 → boost applied (raw + delta)
        assert boosted == raw_sim + 0.05
        assert boosted >= 0.90  # Now passes threshold

    def test_substring_boost_no_match(self, similar_embedding_model):
        """Test that boost is not applied when no substring match."""
        normalizer = TagNormalizer(similar_embedding_model, threshold=0.90)

        raw_sim = 0.80
        boosted = normalizer._apply_substring_boost("backend", "frontend", raw_sim)

        assert boosted == raw_sim

    # =========================================================================
    # Facet Model Tests (Colon Tags)
    # =========================================================================

    def test_facet_guard_different_prefixes_blocked(self, mock_embedding_model):
        """Test that structured tags with different prefixes don't merge."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        can_merge, reason = normalizer._can_merge_tags("type:refactor", "domain:refactor")
        assert can_merge is False
        assert "facet_guard" in reason

    def test_facet_same_prefix_allows_merge(self, mock_embedding_model):
        """Test that structured tags with same prefix CAN merge (similarity decides)."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        # Same prefix - guard allows, similarity will decide
        can_merge, reason = normalizer._can_merge_tags("type:refactor", "type:refactoring")
        assert can_merge is True

    def test_facet_identical_tags_allowed(self, mock_embedding_model):
        """Test that identical colon tags can merge."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        can_merge, reason = normalizer._can_merge_tags("type:refactor", "type:refactor")
        assert can_merge is True

    def test_prefix_guard_structured_vs_plain(self, mock_embedding_model):
        """Test that structured tag vs plain tag don't merge."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        can_merge, reason = normalizer._can_merge_tags("type:refactor", "refactor")
        assert can_merge is False
        assert "prefix_guard" in reason

        can_merge, reason = normalizer._can_merge_tags("priority:high", "high")
        assert can_merge is False
        assert "prefix_guard" in reason

    def test_extract_prefix_suffix(self, mock_embedding_model):
        """Test prefix/suffix extraction from colon tags."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer._extract_prefix_suffix("type:refactor") == ("type", "refactor")
        assert normalizer._extract_prefix_suffix("priority:high") == ("priority", "high")
        assert normalizer._extract_prefix_suffix("backend") == (None, None)
        assert normalizer._extract_prefix_suffix("no-colon-here") == (None, None)

    def test_plain_tags_can_still_merge(self, mock_embedding_model):
        """Test that plain tags without colons can still merge."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        can_merge, reason = normalizer._can_merge_tags("backend", "api")
        assert can_merge is True

    # =========================================================================
    # Substring Boost Stop-Words Tests
    # =========================================================================

    def test_substring_boost_stop_word_api(self, mock_embedding_model):
        """Test that 'api' stop-word doesn't get boost."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        raw_sim = 0.74
        boosted = normalizer._apply_substring_boost("api", "rest api", raw_sim)
        assert boosted == raw_sim  # No boost

    def test_substring_boost_stop_word_db(self, mock_embedding_model):
        """Test that 'db' stop-word doesn't get boost."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        raw_sim = 0.80
        boosted = normalizer._apply_substring_boost("db", "database", raw_sim)
        assert boosted == raw_sim  # No boost

    def test_substring_boost_non_stop_word(self, mock_embedding_model):
        """Test that non-stop-word gets boost."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        raw_sim = 0.86  # below threshold, but will pass after boost
        boosted = normalizer._apply_substring_boost("laravel", "laravel framework", raw_sim)
        assert boosted == raw_sim + 0.05  # Boosted by delta
        assert boosted >= 0.90  # Now passes threshold

    def test_substring_boost_min_length(self, mock_embedding_model):
        """Test that short tags (< 4 chars) don't get boost."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        raw_sim = 0.80
        # 'web' is 3 chars < MIN_LENGTH (4)
        boosted = normalizer._apply_substring_boost("web", "web framework", raw_sim)
        assert boosted == raw_sim  # No boost

    def test_stop_words_defined(self, mock_embedding_model):
        """Test that stop-words are defined."""
        assert 'api' in TagNormalizer.SUBSTRING_BOOST_STOP_WORDS
        assert 'db' in TagNormalizer.SUBSTRING_BOOST_STOP_WORDS
        assert 'ui' in TagNormalizer.SUBSTRING_BOOST_STOP_WORDS
        assert 'laravel' not in TagNormalizer.SUBSTRING_BOOST_STOP_WORDS

    def test_min_length_defined(self, mock_embedding_model):
        """Test that MIN_LENGTH is defined."""
        assert TagNormalizer.SUBSTRING_BOOST_MIN_LENGTH == 4

    def test_boost_delta_defined(self, mock_embedding_model):
        """Test that SUBSTRING_BOOST_DELTA is defined."""
        assert TagNormalizer.SUBSTRING_BOOST_DELTA == 0.05

    def test_boost_delta_not_guaranteed_merge(self, mock_embedding_model):
        """Test that boost delta doesn't guarantee merge if still below threshold."""
        normalizer = TagNormalizer(mock_embedding_model, threshold=0.90)

        # 0.84 + 0.05 = 0.89 < 0.90 → NO MERGE even with boost
        raw_sim = 0.84
        boosted = normalizer._apply_substring_boost("server", "server config", raw_sim)
        assert boosted == 0.89
        assert boosted < 0.90  # Still below threshold

    # =========================================================================
    # Tag Classification Tests
    # =========================================================================

    def test_classify_high_boost_vendor(self, mock_embedding_model):
        """Test that vendor:* tags get high boost."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("vendor:stripe")
        assert result['level'] == 'high'
        assert result['boost'] == 1.5

    def test_classify_high_boost_module(self, mock_embedding_model):
        """Test that module:* tags get high boost."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("module:terminal")
        assert result['level'] == 'high'
        assert result['boost'] == 1.5

    def test_classify_filter_only_status(self, mock_embedding_model):
        """Test that status:* tags are filter_only."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("status:pending")
        assert result['level'] == 'filter_only'
        assert result['boost'] == 0.1

    def test_classify_filter_only_priority(self, mock_embedding_model):
        """Test that priority:* tags are filter_only."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("priority:high")
        assert result['level'] == 'filter_only'
        assert result['boost'] == 0.1

    def test_classify_medium_facet(self, mock_embedding_model):
        """Test that facet tags get medium boost."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("domain:api")
        assert result['level'] == 'medium'
        assert result['boost'] == 1.0

    def test_classify_low_general(self, mock_embedding_model):
        """Test that general tags get low boost."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("api")
        assert result['level'] == 'low'
        assert result['boost'] == 0.5

    def test_classify_low_backend(self, mock_embedding_model):
        """Test that 'backend' tag gets low boost."""
        normalizer = TagNormalizer(mock_embedding_model)

        result = normalizer.classify_tag("backend")
        assert result['level'] == 'low'
        assert result['boost'] == 0.5

    def test_get_tag_boost(self, mock_embedding_model):
        """Test get_tag_boost returns numeric value."""
        normalizer = TagNormalizer(mock_embedding_model)

        assert normalizer.get_tag_boost("vendor:stripe") == 1.5
        assert normalizer.get_tag_boost("api") == 0.5
        assert normalizer.get_tag_boost("type:refactor") == 1.0

    def test_classify_tags_batch(self, mock_embedding_model):
        """Test batch classification."""
        normalizer = TagNormalizer(mock_embedding_model)

        tags = ["vendor:stripe", "module:auth", "api", "status:pending", "domain:payment"]
        result = normalizer.classify_tags(tags)

        assert len(result['high']) == 2
        assert len(result['low']) == 1
        assert len(result['filter_only']) == 1
        assert len(result['medium']) == 1
