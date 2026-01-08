"""
CanonManager - Versioned fact database for story consistency.

Implements SPEC.md Section 7.2: Canon System
- Hard canon database with contradiction detection
- Versioned facts with branch support
- ChromaDB integration for semantic search
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


@dataclass
class CanonEntry:
    """A canonical fact in the story universe"""
    fact_id: str
    content: str
    category: str  # character, location, lore, timeline, relationship
    established_in: Optional[str] = None  # scene_id
    version: str = "main"
    supersedes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContradictionResult:
    """Result of a contradiction check"""
    has_contradiction: bool
    contradicting_facts: List[CanonEntry]
    similarity_scores: List[float]
    explanation: str = ""


class CanonManager:
    """
    Manages canonical facts for story consistency.

    Uses ChromaDB for semantic search to detect potential contradictions.
    Supports versioned facts for timeline branches.
    """

    COLLECTIONS = [
        "characters",
        "locations",
        "lore",
        "timeline",
        "relationships",
        "items"
    ]

    def __init__(self, storage_path: str = "./canon_db"):
        """
        Initialize Canon Manager.

        Args:
            storage_path: Directory for ChromaDB persistent storage
        """
        self.storage_path = storage_path
        self._client = None
        self._collections = {}
        self._facts = {}  # In-memory cache: fact_id -> CanonEntry

        if CHROMADB_AVAILABLE:
            self._init_chromadb()
        else:
            print("Warning: ChromaDB not available. Canon system running in memory-only mode.")

    def _init_chromadb(self):
        """Initialize ChromaDB client and collections"""
        os.makedirs(self.storage_path, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=self.storage_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collections for each category
        for collection_name in self.COLLECTIONS:
            self._collections[collection_name] = self._client.get_or_create_collection(
                name=f"canon_{collection_name}",
                metadata={"description": f"Canon facts for {collection_name}"}
            )

    def add_fact(
        self,
        content: str,
        category: str,
        established_in: str = None,
        version: str = "main",
        supersedes: str = None,
        metadata: Dict[str, Any] = None
    ) -> CanonEntry:
        """
        Add a new canonical fact.

        Args:
            content: The fact content (e.g., "Sarah has blue eyes")
            category: Category (character, location, lore, etc.)
            established_in: Scene ID where fact was first established
            version: Version/branch identifier (default "main")
            supersedes: ID of fact this replaces (for retcons)
            metadata: Additional metadata

        Returns:
            The created CanonEntry
        """
        # Generate fact ID
        fact_id = f"{category}_{len(self._facts) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        entry = CanonEntry(
            fact_id=fact_id,
            content=content,
            category=category,
            established_in=established_in,
            version=version,
            supersedes=supersedes,
            metadata=metadata or {}
        )

        # Store in memory
        self._facts[fact_id] = entry

        # Store in ChromaDB if available
        if CHROMADB_AVAILABLE and category in self._collections:
            self._collections[category].add(
                ids=[fact_id],
                documents=[content],
                metadatas=[{
                    "established_in": established_in or "",
                    "version": version,
                    "supersedes": supersedes or "",
                    "created_at": entry.created_at,
                    **entry.metadata
                }]
            )

        return entry

    def check_contradiction(
        self,
        proposed_content: str,
        category: str,
        similarity_threshold: float = 0.7,
        limit: int = 5
    ) -> ContradictionResult:
        """
        Check if proposed content contradicts established canon.

        Uses semantic search to find potentially contradicting facts.

        Args:
            proposed_content: The new content to check
            category: Category to search within
            similarity_threshold: Minimum similarity to flag as potential contradiction
            limit: Maximum number of results to return

        Returns:
            ContradictionResult with any potential contradictions
        """
        if not CHROMADB_AVAILABLE or category not in self._collections:
            # Fallback: simple keyword matching
            return self._check_contradiction_keyword(proposed_content, category)

        collection = self._collections[category]

        if collection.count() == 0:
            return ContradictionResult(
                has_contradiction=False,
                contradicting_facts=[],
                similarity_scores=[]
            )

        # Semantic search for similar facts
        results = collection.query(
            query_texts=[proposed_content],
            n_results=min(limit, collection.count())
        )

        contradicting_facts = []
        similarity_scores = []

        if results and results['ids'] and results['ids'][0]:
            for i, fact_id in enumerate(results['ids'][0]):
                # ChromaDB returns distances, convert to similarity
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - (distance / 2)  # Normalize to 0-1

                if similarity >= similarity_threshold:
                    if fact_id in self._facts:
                        contradicting_facts.append(self._facts[fact_id])
                        similarity_scores.append(similarity)

        return ContradictionResult(
            has_contradiction=len(contradicting_facts) > 0,
            contradicting_facts=contradicting_facts,
            similarity_scores=similarity_scores,
            explanation=self._generate_contradiction_explanation(
                proposed_content, contradicting_facts
            ) if contradicting_facts else ""
        )

    def _check_contradiction_keyword(
        self,
        proposed_content: str,
        category: str
    ) -> ContradictionResult:
        """Fallback keyword-based contradiction check"""
        proposed_words = set(proposed_content.lower().split())
        contradicting = []
        scores = []

        for fact_id, entry in self._facts.items():
            if entry.category != category:
                continue

            fact_words = set(entry.content.lower().split())
            overlap = len(proposed_words & fact_words)

            if overlap > 2:  # Arbitrary threshold
                similarity = overlap / max(len(proposed_words), len(fact_words))
                if similarity > 0.3:
                    contradicting.append(entry)
                    scores.append(similarity)

        return ContradictionResult(
            has_contradiction=len(contradicting) > 0,
            contradicting_facts=contradicting,
            similarity_scores=scores
        )

    def _generate_contradiction_explanation(
        self,
        proposed: str,
        existing: List[CanonEntry]
    ) -> str:
        """Generate human-readable explanation of potential contradiction"""
        if not existing:
            return ""

        lines = ["Potential contradiction detected:"]
        lines.append(f"\nProposed: {proposed}")
        lines.append("\nExisting canon:")

        for fact in existing:
            lines.append(f"  - {fact.content} (established in {fact.established_in or 'unknown'})")

        return "\n".join(lines)

    def get_facts_by_category(self, category: str, version: str = "main") -> List[CanonEntry]:
        """Get all facts in a category for a specific version"""
        return [
            entry for entry in self._facts.values()
            if entry.category == category and entry.version == version
        ]

    def get_fact(self, fact_id: str) -> Optional[CanonEntry]:
        """Get a specific fact by ID"""
        return self._facts.get(fact_id)

    def search_facts(self, query: str, category: str = None, limit: int = 10) -> List[CanonEntry]:
        """Search for facts using semantic search"""
        if not CHROMADB_AVAILABLE:
            # Keyword fallback
            results = []
            query_lower = query.lower()
            for entry in self._facts.values():
                if category and entry.category != category:
                    continue
                if query_lower in entry.content.lower():
                    results.append(entry)
            return results[:limit]

        # Search across all categories or specific one
        all_results = []
        collections_to_search = [category] if category else self.COLLECTIONS

        for cat in collections_to_search:
            if cat in self._collections and self._collections[cat].count() > 0:
                results = self._collections[cat].query(
                    query_texts=[query],
                    n_results=min(limit, self._collections[cat].count())
                )

                if results and results['ids'] and results['ids'][0]:
                    for fact_id in results['ids'][0]:
                        if fact_id in self._facts:
                            all_results.append(self._facts[fact_id])

        return all_results[:limit]

    def retcon_fact(self, old_fact_id: str, new_content: str) -> Optional[CanonEntry]:
        """
        Retcon (retroactively change) an existing fact.

        Creates a new fact that supersedes the old one.
        The old fact is preserved for history but marked as superseded.
        """
        old_fact = self.get_fact(old_fact_id)
        if not old_fact:
            return None

        # Create new fact that supersedes old one
        new_fact = self.add_fact(
            content=new_content,
            category=old_fact.category,
            version=old_fact.version,
            supersedes=old_fact_id,
            metadata={"retconned_from": old_fact_id}
        )

        return new_fact

    def export_canon(self, version: str = "main") -> Dict[str, List[Dict]]:
        """Export all canon facts as dictionary"""
        export = {cat: [] for cat in self.COLLECTIONS}

        for entry in self._facts.values():
            if entry.version == version:
                export[entry.category].append({
                    "fact_id": entry.fact_id,
                    "content": entry.content,
                    "established_in": entry.established_in,
                    "supersedes": entry.supersedes,
                    "created_at": entry.created_at
                })

        return export

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the canon database"""
        stats = {"total": len(self._facts)}
        for cat in self.COLLECTIONS:
            stats[cat] = len([f for f in self._facts.values() if f.category == cat])
        return stats
