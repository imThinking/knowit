"""Deduplication algorithms using simhash

This module provides content deduplication functionality using the simhash algorithm.
It can detect near-duplicate content and suggest or perform merges.
"""

from typing import List, Tuple, Optional
from simhash import Simhash

from kv.services.database import db, Item


class DeduplicationEngine:
    """Engine for detecting and handling duplicate/similar content"""

    def __init__(self, threshold: float = 0.75):
        """
        Initialize the deduplication engine.

        Args:
            threshold: Similarity threshold (0-1). Higher = more strict matching.
        """
        self.threshold = threshold

    def compute_simhash(self, text: str) -> str:
        """
        Compute simhash for a piece of text.

        Args:
            text: The text to compute simhash for

        Returns:
            Simhash value as hex string
        """
        # Use simhash library with features
        simhash_value = Simhash(text)
        return format(simhash_value.value, "x")

    def compare_simhash(self, hash1: str, hash2: str) -> float:
        """
        Compare two simhash values and return similarity score.

        Args:
            hash1: First simhash value
            hash2: Second simhash value

        Returns:
            Similarity score between 0 and 1
        """
        # Convert hex strings to integers
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)

        # Compute Hamming distance using simhash library
        sim1 = Simhash(val1)
        sim2 = Simhash(val2)

        distance = sim1.distance(sim2)

        # Convert distance to similarity (assuming 64-bit hash)
        max_distance = 64
        similarity = 1 - (distance / max_distance)

        return similarity

    def find_duplicates(
        self, text: str, exclude_item_id: Optional[str] = None
    ) -> List[Tuple[Item, float]]:
        """
        Find items similar to the given text.

        Args:
            text: The text to compare against
            exclude_item_id: Optional item ID to exclude from comparison

        Returns:
            List of (item, similarity_score) tuples, sorted by similarity descending
        """
        # Compute simhash for the input text
        text_hash = self.compute_simhash(text)

        # Get all items from database
        items = db.get_items(status=None)  # Get all items regardless of status

        duplicates = []

        for item in items:
            # Skip the excluded item
            if exclude_item_id and item.id == exclude_item_id:
                continue

            # Skip items without simhash
            if not item.simhash:
                continue

            # Skip merged items
            if item.status == "merged":
                continue

            # Compare simhashes
            similarity = self.compare_simhash(text_hash, item.simhash)

            # Check if above threshold
            if similarity >= self.threshold:
                duplicates.append((item, similarity))

                # Cache the similarity in database
                db.save_similarity(item.id, text_hash, similarity, "simhash")

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x[1], reverse=True)

        return duplicates

    def check_item_duplicates(
        self, item_id: str
    ) -> List[Tuple[Item, float]]:
        """
        Find items similar to a given item.

        Args:
            item_id: The item to check for duplicates

        Returns:
            List of (item, similarity_score) tuples, sorted by similarity descending
        """
        item = db.get_item(item_id)

        if not item or not item.simhash:
            return []

        return self.find_duplicates(item.simhash, exclude_item_id=item_id)

    def should_merge(
        self, text: str, existing_item: Item, threshold: Optional[float] = None
    ) -> bool:
        """
        Determine if new content should be merged with an existing item.

        Args:
            text: The new content text
            existing_item: The existing item to compare against
            threshold: Optional custom threshold (uses default if not provided)

        Returns:
            True if the items should be merged
        """
        if threshold is None:
            threshold = self.threshold

        if not existing_item.simhash:
            return False

        text_hash = self.compute_simhash(text)
        similarity = self.compare_simhash(text_hash, existing_item.simhash)

        return similarity >= threshold

    def suggest_merge(self, item_id: str) -> Optional[str]:
        """
        Suggest an item to merge with, based on highest similarity.

        Args:
            item_id: The item to find a merge candidate for

        Returns:
            The ID of the most similar item, or None if no good match found
        """
        duplicates = self.check_item_duplicates(item_id)

        if not duplicates:
            return None

        # Return the most similar item
        best_match, _ = duplicates[0]

        return best_match.id

    def merge_items(
        self, source_id: str, target_id: str, keep_both: bool = False
    ) -> Item:
        """
        Merge two items by marking one as merged.

        Args:
            source_id: The item to mark as merged
            target_id: The item to merge into
            keep_both: If True, keep both items but link them; if False, mark source as merged

        Returns:
            The updated target item
        """
        source = db.get_item(source_id)
        target = db.get_item(target_id)

        if not source or not target:
            raise ValueError("Both source and target items must exist")

        if keep_both:
            # Add a note to the target about the merge
            if not target.content_markdown:
                target.content_markdown = target.content_text or ""

            note = f"\n\n---\n*Related content from: [{source.title}]({source.source_url})*"
            target.content_markdown += note
            db.update_item(target_id, content_markdown=target.content_markdown)
        else:
            # Mark source as merged
            db.update_item(source_id, status="merged", merged_into=target_id)

        return db.get_item(target_id)

    def batch_deduplicate(self, limit: int = 100) -> List[Tuple[str, str, float]]:
        """
        Run batch deduplication on recent items.

        Args:
            limit: Number of recent items to check

        Returns:
            List of (item_id_1, item_id_2, similarity) tuples for potential merges
        """
        # Get recent items that aren't merged
        recent_items = db.get_items(limit=limit)

        potential_merges = []

        for i, item1 in enumerate(recent_items):
            if not item1.simhash or item1.status == "merged":
                continue

            for item2 in recent_items[i + 1 :]:
                if not item2.simhash or item2.status == "merged":
                    continue

                similarity = self.compare_simhash(item1.simhash, item2.simhash)

                if similarity >= self.threshold:
                    potential_merges.append((item1.id, item2.id, similarity))

                    # Cache in database
                    db.save_similarity(item1.id, item2.id, similarity, "simhash")

        # Sort by similarity descending
        potential_merges.sort(key=lambda x: x[2], reverse=True)

        return potential_merges


# Global deduplication engine instance
dedup = DeduplicationEngine(threshold=0.75)
