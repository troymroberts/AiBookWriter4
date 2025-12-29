"""
YWriter7 Knowledge Source for CrewAI
Provides RAG access to yWriter7 project data for all agents.
"""

import os
from typing import Any, Optional, List, Dict
from pydantic import Field

from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

# Import yWriter7 models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ywriter7.yw.yw7_file import Yw7File


class YWriter7KnowledgeSource(BaseKnowledgeSource):
    """
    A knowledge source that reads yWriter7 project files and makes
    characters, locations, items, scenes, and chapters available for RAG.

    Attributes:
        file_path: Path to the .yw7 project file
        include_scene_content: Whether to include full scene prose (can be large)
        include_characters: Include character data
        include_locations: Include location data
        include_items: Include item data
        include_outlines: Include chapter/scene outlines
    """

    file_path: str = Field(..., description="Path to the .yw7 file")
    include_scene_content: bool = Field(default=False, description="Include full scene prose")
    include_characters: bool = Field(default=True, description="Include character data")
    include_locations: bool = Field(default=True, description="Include location data")
    include_items: bool = Field(default=True, description="Include item data")
    include_outlines: bool = Field(default=True, description="Include chapter/scene outlines")

    # Internal state
    _yw7_file: Optional[Yw7File] = None
    _raw_content: str = ""

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    def model_post_init(self, _: Any) -> None:
        """Post-initialization to validate and load content."""
        self.validate_content()

    def validate_content(self) -> None:
        """Validate that the yWriter7 file exists and is readable."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"yWriter7 file not found: {self.file_path}")

        if not self.file_path.lower().endswith('.yw7'):
            raise ValueError(f"File must be a .yw7 file: {self.file_path}")

        # Try to load the file
        try:
            self._yw7_file = Yw7File(self.file_path)
            self._yw7_file.read()
        except Exception as e:
            raise ValueError(f"Failed to read yWriter7 file: {e}")

        # Build the content string
        self._raw_content = self._build_content()

    def _build_content(self) -> str:
        """Build a searchable text representation of the yWriter7 project."""
        if not self._yw7_file:
            return ""

        novel = self._yw7_file.novel
        sections = []

        # Project metadata
        sections.append(self._format_project_metadata(novel))

        # Characters
        if self.include_characters:
            sections.append(self._format_characters(novel))

        # Locations
        if self.include_locations:
            sections.append(self._format_locations(novel))

        # Items
        if self.include_items:
            sections.append(self._format_items(novel))

        # Chapter and Scene outlines
        if self.include_outlines:
            sections.append(self._format_outlines(novel))

        # Full scene content (optional, can be very large)
        if self.include_scene_content:
            sections.append(self._format_scene_content(novel))

        return "\n\n".join(filter(None, sections))

    def _format_project_metadata(self, novel) -> str:
        """Format project-level metadata."""
        lines = ["=== PROJECT METADATA ==="]

        if novel.title:
            lines.append(f"Title: {novel.title}")
        if novel.authorName:
            lines.append(f"Author: {novel.authorName}")
        if novel.desc:
            lines.append(f"Description: {novel.desc}")
        if novel.wordTarget:
            lines.append(f"Word Target: {novel.wordTarget}")

        return "\n".join(lines)

    def _format_characters(self, novel) -> str:
        """Format all characters for searchability."""
        if not novel.characters:
            return ""

        lines = ["=== CHARACTERS ==="]

        for char_id in novel.srtCharacters:
            char = novel.characters.get(char_id)
            if not char:
                continue

            char_lines = [f"\n--- CHARACTER: {char.title or 'Unnamed'} (ID: {char_id}) ---"]

            if char.fullName:
                char_lines.append(f"Full Name: {char.fullName}")
            if char.isMajor:
                char_lines.append("Role: Major Character")
            else:
                char_lines.append("Role: Minor Character")
            if char.desc:
                char_lines.append(f"Description: {char.desc}")
            if char.bio:
                char_lines.append(f"Biography: {char.bio}")
            if char.goals:
                char_lines.append(f"Goals: {char.goals}")
            if char.notes:
                char_lines.append(f"Notes: {char.notes}")
            if hasattr(char, 'aka') and char.aka:
                char_lines.append(f"Also Known As: {char.aka}")
            if hasattr(char, 'tags') and char.tags:
                char_lines.append(f"Tags: {', '.join(char.tags)}")

            lines.extend(char_lines)

        return "\n".join(lines)

    def _format_locations(self, novel) -> str:
        """Format all locations for searchability."""
        if not novel.locations:
            return ""

        lines = ["=== LOCATIONS ==="]

        for loc_id in novel.srtLocations:
            loc = novel.locations.get(loc_id)
            if not loc:
                continue

            loc_lines = [f"\n--- LOCATION: {loc.title or 'Unnamed'} (ID: {loc_id}) ---"]

            if hasattr(loc, 'aka') and loc.aka:
                loc_lines.append(f"Also Known As: {loc.aka}")
            if loc.desc:
                loc_lines.append(f"Description: {loc.desc}")
            if hasattr(loc, 'tags') and loc.tags:
                loc_lines.append(f"Tags: {', '.join(loc.tags)}")

            lines.extend(loc_lines)

        return "\n".join(lines)

    def _format_items(self, novel) -> str:
        """Format all items for searchability."""
        if not novel.items:
            return ""

        lines = ["=== ITEMS ==="]

        for item_id in novel.srtItems:
            item = novel.items.get(item_id)
            if not item:
                continue

            item_lines = [f"\n--- ITEM: {item.title or 'Unnamed'} (ID: {item_id}) ---"]

            if hasattr(item, 'aka') and item.aka:
                item_lines.append(f"Also Known As: {item.aka}")
            if item.desc:
                item_lines.append(f"Description: {item.desc}")
            if hasattr(item, 'tags') and item.tags:
                item_lines.append(f"Tags: {', '.join(item.tags)}")

            lines.extend(item_lines)

        return "\n".join(lines)

    def _format_outlines(self, novel) -> str:
        """Format chapter and scene outlines."""
        if not novel.chapters:
            return ""

        lines = ["=== CHAPTER AND SCENE OUTLINES ==="]

        for ch_idx, ch_id in enumerate(novel.srtChapters, 1):
            chapter = novel.chapters.get(ch_id)
            if not chapter:
                continue

            ch_lines = [f"\n--- CHAPTER {ch_idx}: {chapter.title or 'Untitled'} (ID: {ch_id}) ---"]

            if chapter.desc:
                ch_lines.append(f"Chapter Summary: {chapter.desc}")

            # Scenes in this chapter
            if hasattr(chapter, 'srtScenes') and chapter.srtScenes:
                for sc_idx, sc_id in enumerate(chapter.srtScenes, 1):
                    scene = novel.scenes.get(sc_id)
                    if not scene:
                        continue

                    ch_lines.append(f"\n  Scene {sc_idx}: {scene.title or 'Untitled'} (ID: {sc_id})")

                    if scene.desc:
                        ch_lines.append(f"    Summary: {scene.desc}")

                    # Scene beats (goal, conflict, outcome)
                    if scene.goal:
                        ch_lines.append(f"    Goal: {scene.goal}")
                    if scene.conflict:
                        ch_lines.append(f"    Conflict: {scene.conflict}")
                    if scene.outcome:
                        ch_lines.append(f"    Outcome: {scene.outcome}")

                    # Characters in scene
                    if scene.characters:
                        char_names = []
                        for cid in scene.characters:
                            c = novel.characters.get(cid)
                            if c:
                                char_names.append(c.title or cid)
                        if char_names:
                            ch_lines.append(f"    Characters: {', '.join(char_names)}")

                    # Locations in scene
                    if scene.locations:
                        loc_names = []
                        for lid in scene.locations:
                            l = novel.locations.get(lid)
                            if l:
                                loc_names.append(l.title or lid)
                        if loc_names:
                            ch_lines.append(f"    Locations: {', '.join(loc_names)}")

                    # Scene status
                    if scene.status and scene.STATUS:
                        status_name = scene.STATUS[scene.status] if scene.status < len(scene.STATUS) else "Unknown"
                        ch_lines.append(f"    Status: {status_name}")

                    # Scene type
                    if scene.isReactionScene:
                        ch_lines.append("    Type: Reaction Scene")
                    else:
                        ch_lines.append("    Type: Action Scene")

            lines.extend(ch_lines)

        return "\n".join(lines)

    def _format_scene_content(self, novel) -> str:
        """Format full scene content (prose)."""
        if not novel.scenes:
            return ""

        lines = ["=== SCENE CONTENT ==="]

        for ch_idx, ch_id in enumerate(novel.srtChapters, 1):
            chapter = novel.chapters.get(ch_id)
            if not chapter:
                continue

            if hasattr(chapter, 'srtScenes') and chapter.srtScenes:
                for sc_idx, sc_id in enumerate(chapter.srtScenes, 1):
                    scene = novel.scenes.get(sc_id)
                    if not scene or not scene.sceneContent:
                        continue

                    lines.append(f"\n--- Chapter {ch_idx}, Scene {sc_idx}: {scene.title or 'Untitled'} ---")
                    lines.append(scene.sceneContent)

        return "\n".join(lines)

    def add(self) -> None:
        """Add yWriter7 content to knowledge source, chunk it, and save."""
        new_chunks = self._chunk_text(self._raw_content)
        self.chunks.extend(new_chunks)
        self._save_documents()

    async def aadd(self) -> None:
        """Add yWriter7 content asynchronously."""
        new_chunks = self._chunk_text(self._raw_content)
        self.chunks.extend(new_chunks)
        await self._asave_documents()

    # === Query helpers for direct access (non-RAG) ===

    def get_character(self, char_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific character by ID."""
        if not self._yw7_file:
            return None

        char = self._yw7_file.novel.characters.get(char_id)
        if not char:
            return None

        return {
            'id': char_id,
            'name': char.title,
            'full_name': char.fullName,
            'description': char.desc,
            'bio': char.bio,
            'goals': char.goals,
            'notes': char.notes,
            'is_major': char.isMajor,
        }

    def get_all_characters(self) -> List[Dict[str, Any]]:
        """Get all characters."""
        if not self._yw7_file:
            return []

        return [
            self.get_character(cid)
            for cid in self._yw7_file.novel.srtCharacters
            if self.get_character(cid)
        ]

    def get_location(self, loc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific location by ID."""
        if not self._yw7_file:
            return None

        loc = self._yw7_file.novel.locations.get(loc_id)
        if not loc:
            return None

        return {
            'id': loc_id,
            'name': loc.title,
            'description': loc.desc,
            'aka': getattr(loc, 'aka', None),
        }

    def get_all_locations(self) -> List[Dict[str, Any]]:
        """Get all locations."""
        if not self._yw7_file:
            return []

        return [
            self.get_location(lid)
            for lid in self._yw7_file.novel.srtLocations
            if self.get_location(lid)
        ]

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scene by ID."""
        if not self._yw7_file:
            return None

        scene = self._yw7_file.novel.scenes.get(scene_id)
        if not scene:
            return None

        return {
            'id': scene_id,
            'title': scene.title,
            'description': scene.desc,
            'content': scene.sceneContent,
            'goal': scene.goal,
            'conflict': scene.conflict,
            'outcome': scene.outcome,
            'characters': scene.characters or [],
            'locations': scene.locations or [],
            'items': scene.items or [],
            'status': scene.status,
            'word_count': scene.wordCount,
            'is_reaction': scene.isReactionScene,
            'is_subplot': scene.isSubPlot,
        }

    def get_chapter_scenes(self, chapter_id: str) -> List[Dict[str, Any]]:
        """Get all scenes in a chapter."""
        if not self._yw7_file:
            return []

        chapter = self._yw7_file.novel.chapters.get(chapter_id)
        if not chapter or not hasattr(chapter, 'srtScenes'):
            return []

        return [
            self.get_scene(sid)
            for sid in chapter.srtScenes
            if self.get_scene(sid)
        ]

    def get_character_appearances(self, char_id: str) -> List[str]:
        """Get list of scene IDs where a character appears."""
        if not self._yw7_file:
            return []

        appearances = []
        for sc_id, scene in self._yw7_file.novel.scenes.items():
            if scene.characters and char_id in scene.characters:
                appearances.append(sc_id)

        return appearances
