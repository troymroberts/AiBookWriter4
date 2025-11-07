"""
RAG Sync Manager for bidirectional synchronization between yWriter7 and ChromaDB.

Handles:
- Syncing yWriter7 data to vector database
- Updating yWriter7 from vector database
- Automatic sync on file changes
- Incremental updates
"""

from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import json

from .vector_store import VectorStoreManager
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.item import Item
from ywriter7.model.scene import Scene

logger = logging.getLogger(__name__)


class RAGSyncManager:
    """
    Manages bidirectional synchronization between yWriter7 and RAG vector database.

    Features:
    - Sync characters, locations, items, scenes to vector DB
    - Track changes and perform incremental updates
    - Generate embeddings for semantic search
    - Maintain consistency between file and DB
    """

    def __init__(self, vector_store: VectorStoreManager):
        """
        Initialize the sync manager.

        Args:
            vector_store: VectorStoreManager instance
        """
        self.vector_store = vector_store
        logger.info("RAGSyncManager initialized")

    def sync_from_ywriter(self, yw7_path: str) -> Dict[str, int]:
        """
        Sync all data from a yWriter7 file to the vector database.

        Args:
            yw7_path: Path to the .yw7 file

        Returns:
            Dictionary with sync statistics (counts per collection)
        """
        logger.info(f"Starting sync from yWriter7: {yw7_path}")

        try:
            # Load yWriter7 file
            yw7_file = Yw7File(yw7_path)
            yw7_file.read()
            novel = yw7_file.novel

            stats = {
                'characters': 0,
                'locations': 0,
                'items': 0,
                'plot_events': 0,
                'relationships': 0
            }

            # Sync characters
            stats['characters'] = self._sync_characters(novel)

            # Sync locations
            stats['locations'] = self._sync_locations(novel)

            # Sync items
            stats['items'] = self._sync_items(novel)

            # Sync scenes (as plot events)
            stats['plot_events'] = self._sync_scenes(novel)

            # Extract and sync relationships
            stats['relationships'] = self._sync_relationships(novel)

            logger.info(f"Sync completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to sync from yWriter7: {e}")
            raise

    def _sync_characters(self, novel: Novel) -> int:
        """Sync all characters to vector database."""
        count = 0

        for char_id, character in novel.characters.items():
            # Build comprehensive character document
            content = self._build_character_document(character)

            # Metadata for filtering
            metadata = {
                'type': 'character',
                'char_id': char_id,
                'title': character.title or '',
                'is_major': str(character.isMajor),
                'full_name': character.fullName or '',
            }

            # Add to vector store
            success = self.vector_store.add_document(
                collection_name='characters',
                document_id=f"char_{char_id}",
                content=content,
                metadata=metadata
            )

            if success:
                count += 1

        logger.debug(f"Synced {count} characters")
        return count

    def _build_character_document(self, character: Character) -> str:
        """Build a comprehensive text document for character embedding."""
        parts = []

        # Name
        if character.title:
            parts.append(f"Name: {character.title}")
        if character.fullName:
            parts.append(f"Full Name: {character.fullName}")
        if character.aka:
            parts.append(f"Also Known As: {character.aka}")

        # Description and bio
        if character.desc:
            parts.append(f"Description: {character.desc}")
        if character.bio:
            parts.append(f"Biography: {character.bio}")
        if character.goals:
            parts.append(f"Goals: {character.goals}")

        # Character type
        char_type = "Major Character" if character.isMajor else "Minor Character"
        parts.append(f"Character Type: {char_type}")

        # Notes
        if character.notes:
            parts.append(f"Notes: {character.notes}")

        return "\n\n".join(parts)

    def _sync_locations(self, novel: Novel) -> int:
        """Sync all locations to vector database."""
        count = 0

        for loc_id, location in novel.locations.items():
            # Build location document
            content = self._build_location_document(location)

            # Metadata
            metadata = {
                'type': 'location',
                'loc_id': loc_id,
                'title': location.title or '',
            }

            # Add to vector store
            success = self.vector_store.add_document(
                collection_name='locations',
                document_id=f"loc_{loc_id}",
                content=content,
                metadata=metadata
            )

            if success:
                count += 1

        logger.debug(f"Synced {count} locations")
        return count

    def _build_location_document(self, location: Location) -> str:
        """Build a comprehensive text document for location embedding."""
        parts = []

        if location.title:
            parts.append(f"Location: {location.title}")

        if location.desc:
            parts.append(f"Description: {location.desc}")

        return "\n\n".join(parts)

    def _sync_items(self, novel: Novel) -> int:
        """Sync all items to vector database."""
        count = 0

        for item_id, item in novel.items.items():
            # Build item document
            content = self._build_item_document(item)

            # Metadata
            metadata = {
                'type': 'item',
                'item_id': item_id,
                'title': item.title or '',
            }

            # Add to vector store
            success = self.vector_store.add_document(
                collection_name='items',
                document_id=f"item_{item_id}",
                content=content,
                metadata=metadata
            )

            if success:
                count += 1

        logger.debug(f"Synced {count} items")
        return count

    def _build_item_document(self, item: Item) -> str:
        """Build a comprehensive text document for item embedding."""
        parts = []

        if item.title:
            parts.append(f"Item: {item.title}")

        if item.desc:
            parts.append(f"Description: {item.desc}")

        return "\n\n".join(parts)

    def _sync_scenes(self, novel: Novel) -> int:
        """Sync all scenes as plot events to vector database."""
        count = 0

        for scene_id, scene in novel.scenes.items():
            # Build scene/plot event document
            content = self._build_scene_document(scene, novel)

            # Find chapter for this scene
            chapter_title = self._find_chapter_for_scene(novel, scene_id)

            # Metadata
            metadata = {
                'type': 'plot_event',
                'scene_id': scene_id,
                'title': scene.title or '',
                'chapter': chapter_title or 'Unknown',
                'word_count': str(scene.wordCount),
            }

            # Add to vector store
            success = self.vector_store.add_document(
                collection_name='plot_events',
                document_id=f"scene_{scene_id}",
                content=content,
                metadata=metadata
            )

            if success:
                count += 1

        logger.debug(f"Synced {count} scenes as plot events")
        return count

    def _build_scene_document(self, scene: Scene, novel: Novel) -> str:
        """Build a comprehensive text document for scene embedding."""
        parts = []

        if scene.title:
            parts.append(f"Scene: {scene.title}")

        if scene.desc:
            parts.append(f"Description: {scene.desc}")

        # Add character information
        if scene.characters:
            char_names = []
            for char_id in scene.characters:
                if char_id in novel.characters:
                    char_names.append(novel.characters[char_id].title)
            if char_names:
                parts.append(f"Characters Present: {', '.join(char_names)}")

        # Add location information
        if scene.locations:
            loc_names = []
            for loc_id in scene.locations:
                if loc_id in novel.locations:
                    loc_names.append(novel.locations[loc_id].title)
            if loc_names:
                parts.append(f"Locations: {', '.join(loc_names)}")

        # Add scene content (if available and not too long)
        if scene.sceneContent:
            # Truncate if too long
            max_content_length = 2000
            content = scene.sceneContent
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            parts.append(f"Content: {content}")

        return "\n\n".join(parts)

    def _find_chapter_for_scene(self, novel: Novel, scene_id: str) -> Optional[str]:
        """Find which chapter contains a scene."""
        for chapter_id, chapter in novel.chapters.items():
            if scene_id in chapter.srtScenes:
                return chapter.title
        return None

    def _sync_relationships(self, novel: Novel) -> int:
        """
        Extract and sync character relationships from character bios and notes.

        This is a simple implementation that creates relationship documents
        based on character mentions in other characters' bios.
        """
        count = 0

        for char_id, character in novel.characters.items():
            # Look for other characters mentioned in this character's bio/notes
            relationships = self._extract_relationships(character, novel)

            for rel_id, rel_text in enumerate(relationships):
                doc_id = f"rel_{char_id}_{rel_id}"

                metadata = {
                    'type': 'relationship',
                    'char_id': char_id,
                    'character_name': character.title or '',
                }

                success = self.vector_store.add_document(
                    collection_name='relationships',
                    document_id=doc_id,
                    content=rel_text,
                    metadata=metadata
                )

                if success:
                    count += 1

        logger.debug(f"Synced {count} relationship records")
        return count

    def _extract_relationships(self, character: Character, novel: Novel) -> List[str]:
        """
        Extract relationship information from character bio/notes.

        This is a simple implementation. Could be enhanced with NLP.
        """
        relationships = []

        # Combine all text about the character
        text_parts = []
        if character.bio:
            text_parts.append(character.bio)
        if character.notes:
            text_parts.append(character.notes)
        if character.goals:
            text_parts.append(character.goals)

        combined_text = " ".join(text_parts)

        # Look for other character names mentioned
        for other_id, other_char in novel.characters.items():
            if other_id == character.title:  # Skip self
                continue

            if other_char.title and other_char.title in combined_text:
                # Found a relationship mention
                rel_text = (
                    f"{character.title}'s relationship with {other_char.title}: "
                    f"Mentioned in context: {combined_text}"
                )
                relationships.append(rel_text)

        return relationships

    def update_character(
        self,
        char_id: str,
        character: Character
    ) -> bool:
        """
        Update a specific character in the vector database.

        Args:
            char_id: Character ID
            character: Character object

        Returns:
            True if successful
        """
        content = self._build_character_document(character)

        metadata = {
            'type': 'character',
            'char_id': char_id,
            'title': character.title or '',
            'is_major': str(character.isMajor),
            'full_name': character.fullName or '',
        }

        return self.vector_store.update_document(
            collection_name='characters',
            document_id=f"char_{char_id}",
            content=content,
            metadata=metadata
        )

    def update_location(
        self,
        loc_id: str,
        location: Location
    ) -> bool:
        """Update a specific location in the vector database."""
        content = self._build_location_document(location)

        metadata = {
            'type': 'location',
            'loc_id': loc_id,
            'title': location.title or '',
        }

        return self.vector_store.update_document(
            collection_name='locations',
            document_id=f"loc_{loc_id}",
            content=content,
            metadata=metadata
        )

    def update_scene(
        self,
        scene_id: str,
        scene: Scene,
        novel: Novel
    ) -> bool:
        """Update a specific scene in the vector database."""
        content = self._build_scene_document(scene, novel)

        chapter_title = self._find_chapter_for_scene(novel, scene_id)

        metadata = {
            'type': 'plot_event',
            'scene_id': scene_id,
            'title': scene.title or '',
            'chapter': chapter_title or 'Unknown',
            'word_count': str(scene.wordCount),
        }

        return self.vector_store.update_document(
            collection_name='plot_events',
            document_id=f"scene_{scene_id}",
            content=content,
            metadata=metadata
        )

    def delete_character(self, char_id: str) -> bool:
        """Delete a character from the vector database."""
        return self.vector_store.delete_document(
            collection_name='characters',
            document_id=f"char_{char_id}"
        )

    def delete_location(self, loc_id: str) -> bool:
        """Delete a location from the vector database."""
        return self.vector_store.delete_document(
            collection_name='locations',
            document_id=f"loc_{loc_id}"
        )

    def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene from the vector database."""
        return self.vector_store.delete_document(
            collection_name='plot_events',
            document_id=f"scene_{scene_id}"
        )

    def get_sync_stats(self, yw7_path: str) -> Dict[str, Any]:
        """
        Get statistics comparing yWriter7 file and vector database.

        Args:
            yw7_path: Path to .yw7 file

        Returns:
            Dictionary with comparison statistics
        """
        try:
            # Load yWriter7 file
            yw7_file = Yw7File(yw7_path)
            yw7_file.read()
            novel = yw7_file.novel

            # Get vector DB stats
            db_stats = self.vector_store.get_stats()

            return {
                'ywriter': {
                    'characters': len(novel.characters),
                    'locations': len(novel.locations),
                    'items': len(novel.items),
                    'scenes': len(novel.scenes),
                },
                'vector_db': db_stats,
                'in_sync': self._check_sync_status(novel, db_stats)
            }

        except Exception as e:
            logger.error(f"Failed to get sync stats: {e}")
            return {}

    def _check_sync_status(self, novel: Novel, db_stats: Dict[str, int]) -> bool:
        """Check if yWriter7 and vector DB are in sync."""
        return (
            len(novel.characters) == db_stats.get('characters', 0) and
            len(novel.locations) == db_stats.get('locations', 0) and
            len(novel.items) == db_stats.get('items', 0) and
            len(novel.scenes) == db_stats.get('plot_events', 0)
        )
