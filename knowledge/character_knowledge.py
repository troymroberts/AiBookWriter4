"""
Character Knowledge Source for CrewAI
Specialized knowledge source focused on character data for voice consistency.
"""

from typing import Any, Optional, List, Dict
from pydantic import Field

from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource


class CharacterKnowledgeSource(BaseKnowledgeSource):
    """
    A knowledge source specifically for character information.
    Optimized for dialogue and voice consistency checks.

    This can be populated from:
    - yWriter7 character data
    - Direct character definitions
    - Generated character profiles
    """

    characters: List[Dict[str, Any]] = Field(default_factory=list)
    collection_name: str | None = Field(default="characters")

    def model_post_init(self, _: Any) -> None:
        """Post-initialization to validate content."""
        self.validate_content()

    def validate_content(self) -> None:
        """Validate character data structure."""
        for char in self.characters:
            if not isinstance(char, dict):
                raise ValueError("Each character must be a dictionary")
            if 'name' not in char:
                raise ValueError("Each character must have a 'name' field")

    def add(self) -> None:
        """Add character content to knowledge source."""
        content = self._build_character_content()
        new_chunks = self._chunk_text(content)
        self.chunks.extend(new_chunks)
        self._save_documents()

    async def aadd(self) -> None:
        """Add character content asynchronously."""
        content = self._build_character_content()
        new_chunks = self._chunk_text(content)
        self.chunks.extend(new_chunks)
        await self._asave_documents()

    def _build_character_content(self) -> str:
        """Build searchable text from character data."""
        sections = []

        for char in self.characters:
            lines = [f"=== CHARACTER: {char.get('name', 'Unknown')} ==="]

            # Basic info
            if char.get('full_name'):
                lines.append(f"Full Name: {char['full_name']}")
            if char.get('role'):
                lines.append(f"Role: {char['role']}")
            if char.get('age'):
                lines.append(f"Age: {char['age']}")

            # Physical description
            if char.get('appearance'):
                lines.append(f"Appearance: {char['appearance']}")

            # Personality and voice (critical for consistency)
            if char.get('personality'):
                lines.append(f"Personality: {char['personality']}")
            if char.get('speech_patterns'):
                lines.append(f"Speech Patterns: {char['speech_patterns']}")
            if char.get('vocabulary_level'):
                lines.append(f"Vocabulary Level: {char['vocabulary_level']}")
            if char.get('catchphrases'):
                lines.append(f"Catchphrases: {char['catchphrases']}")
            if char.get('dialect'):
                lines.append(f"Dialect/Accent: {char['dialect']}")

            # Background
            if char.get('backstory'):
                lines.append(f"Backstory: {char['backstory']}")
            if char.get('motivation'):
                lines.append(f"Motivation: {char['motivation']}")
            if char.get('goals'):
                lines.append(f"Goals: {char['goals']}")
            if char.get('fears'):
                lines.append(f"Fears: {char['fears']}")
            if char.get('secrets'):
                lines.append(f"Secrets: {char['secrets']}")

            # Arc
            if char.get('arc_start'):
                lines.append(f"Arc Start: {char['arc_start']}")
            if char.get('arc_end'):
                lines.append(f"Arc End: {char['arc_end']}")
            if char.get('arc_transformation'):
                lines.append(f"Transformation: {char['arc_transformation']}")

            # Relationships
            if char.get('relationships'):
                lines.append("Relationships:")
                for rel in char['relationships']:
                    if isinstance(rel, dict):
                        lines.append(f"  - {rel.get('character', 'Unknown')}: {rel.get('type', 'Unknown')}")
                    else:
                        lines.append(f"  - {rel}")

            # Power/abilities (for fantasy/LN)
            if char.get('abilities'):
                lines.append(f"Abilities: {char['abilities']}")
            if char.get('power_level'):
                lines.append(f"Power Level: {char['power_level']}")

            # Faction (for fantasy)
            if char.get('faction'):
                lines.append(f"Faction: {char['faction']}")

            sections.append("\n".join(lines))

        return "\n\n".join(sections)

    def add_character(self, character: Dict[str, Any]) -> None:
        """Add a single character to the knowledge source."""
        if 'name' not in character:
            raise ValueError("Character must have a 'name' field")
        self.characters.append(character)

    def get_character_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a character by name (case-insensitive)."""
        name_lower = name.lower()
        for char in self.characters:
            if char.get('name', '').lower() == name_lower:
                return char
            if char.get('full_name', '').lower() == name_lower:
                return char
        return None

    def get_character_voice_profile(self, name: str) -> Optional[Dict[str, str]]:
        """Get just the voice-related attributes for dialogue writing."""
        char = self.get_character_by_name(name)
        if not char:
            return None

        return {
            'name': char.get('name'),
            'personality': char.get('personality', ''),
            'speech_patterns': char.get('speech_patterns', ''),
            'vocabulary_level': char.get('vocabulary_level', ''),
            'catchphrases': char.get('catchphrases', ''),
            'dialect': char.get('dialect', ''),
            'education': char.get('education', ''),
            'emotional_state': char.get('emotional_state', ''),
        }

    def get_relationship(self, char1_name: str, char2_name: str) -> Optional[str]:
        """Get the relationship between two characters."""
        char1 = self.get_character_by_name(char1_name)
        if not char1 or 'relationships' not in char1:
            return None

        for rel in char1['relationships']:
            if isinstance(rel, dict):
                if rel.get('character', '').lower() == char2_name.lower():
                    return rel.get('type')
            elif char2_name.lower() in rel.lower():
                return rel

        return None
