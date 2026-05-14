"""Tests for deduplication algorithm"""

import pytest

from kv.algorithms.dedup import dedup, DeduplicationEngine


class TestSimhash:
    """Test simhash computation"""

    def test_simhash_computation(self):
        """Test that simhash can be computed for text"""
        text1 = "This is a test article about Python programming"
        text2 = "This is a test article about Python coding"
        text3 = "Completely different content about cooking"

        # Compute hashes
        hash1 = dedup.compute_simhash(text1)
        hash2 = dedup.compute_simhash(text2)
        hash3 = dedup.compute_simhash(text3)

        assert hash1 is not None
        assert hash2 is not None
        assert hash3 is not None
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        assert isinstance(hash3, str)

    def test_simhash_similarity(self):
        """Test simhash similarity calculation"""
        text1 = "This is a test article about Python programming"
        text2 = "This is a test article about Python coding"

        hash1 = dedup.compute_simhash(text1)
        hash2 = dedup.compute_simhash(text2)

        # Compare hashes using the engine's method
        similarity = dedup.compare_simhash(hash1, hash2)

        # Similar texts should have high similarity
        assert similarity > 0.7


class TestDedupLogic:
    """Test deduplication logic"""

    def test_exact_duplicates(self):
        """Test detection of exact duplicates"""
        text = "This is a test article"
        hash1 = dedup.compute_simhash(text)
        hash2 = dedup.compute_simhash(text)

        # Exact duplicates should have 1.0 similarity
        similarity = dedup.compare_simhash(hash1, hash2)
        assert similarity == 1.0

    def test_similar_content(self):
        """Test detection of similar content"""
        text1 = "Python is a great programming language"
        text2 = "Python is an excellent programming language"

        hash1 = dedup.compute_simhash(text1)
        hash2 = dedup.compute_simhash(text2)

        similarity = dedup.compare_simhash(hash1, hash2)

        # Should be similar but not identical
        assert 0.7 <= similarity < 1.0

    def test_different_content(self):
        """Test that different content has low similarity"""
        text1 = "Python programming tutorial"
        text2 = "Baking chocolate chip cookies"

        hash1 = dedup.compute_simhash(text1)
        hash2 = dedup.compute_simhash(text2)

        similarity = dedup.compare_simhash(hash1, hash2)

        # Should have low similarity
        assert similarity < 0.7


class TestDeduplicationEngine:
    """Test DeduplicationEngine class"""

    def test_custom_threshold(self):
        """Test creating engine with custom threshold"""
        engine = DeduplicationEngine(threshold=0.9)
        assert engine.threshold == 0.9

    def test_should_merge(self):
        """Test should_merge logic"""
        engine = DeduplicationEngine(threshold=0.75)

        # Create mock item with simhash
        from kv.core.database import Item
        from datetime import datetime

        item = Item()
        item.id = "test-1"
        item.title = "Test"
        item.simhash = engine.compute_simhash("Python programming tutorial")
        item.status = "inbox"

        # Very similar text should merge
        assert engine.should_merge("Python programming tutorial", item) is True

        # Different text should not merge
        assert engine.should_merge("Baking cookies recipe", item) is False
