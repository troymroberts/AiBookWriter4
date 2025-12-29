"""
World Knowledge Source for CrewAI
Specialized knowledge source for locations, items, factions, and lore.
"""

from typing import Any, Optional, List, Dict
from pydantic import Field

from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource


class WorldKnowledgeSource(BaseKnowledgeSource):
    """
    A knowledge source for world-building elements.
    Covers locations, items, factions, magic systems, and lore.
    """

    locations: List[Dict[str, Any]] = Field(default_factory=list)
    items: List[Dict[str, Any]] = Field(default_factory=list)
    factions: List[Dict[str, Any]] = Field(default_factory=list)
    magic_system: Optional[Dict[str, Any]] = Field(default=None)
    lore: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

    collection_name: str | None = Field(default="world")

    def model_post_init(self, _: Any) -> None:
        """Post-initialization."""
        self.validate_content()

    def validate_content(self) -> None:
        """Validate world data structure."""
        for loc in self.locations:
            if not isinstance(loc, dict):
                raise ValueError("Each location must be a dictionary")
        for item in self.items:
            if not isinstance(item, dict):
                raise ValueError("Each item must be a dictionary")

    def add(self) -> None:
        """Add world content to knowledge source."""
        content = self._build_world_content()
        new_chunks = self._chunk_text(content)
        self.chunks.extend(new_chunks)
        self._save_documents()

    async def aadd(self) -> None:
        """Add world content asynchronously."""
        content = self._build_world_content()
        new_chunks = self._chunk_text(content)
        self.chunks.extend(new_chunks)
        await self._asave_documents()

    def _build_world_content(self) -> str:
        """Build searchable text from world data."""
        sections = []

        # Locations
        if self.locations:
            sections.append(self._format_locations())

        # Items
        if self.items:
            sections.append(self._format_items())

        # Factions
        if self.factions:
            sections.append(self._format_factions())

        # Magic System
        if self.magic_system:
            sections.append(self._format_magic_system())

        # Lore
        if self.lore:
            sections.append(self._format_lore())

        # Timeline
        if self.timeline:
            sections.append(self._format_timeline())

        return "\n\n".join(sections)

    def _format_locations(self) -> str:
        """Format locations for searchability."""
        lines = ["=== LOCATIONS ==="]

        for loc in self.locations:
            loc_lines = [f"\n--- LOCATION: {loc.get('name', 'Unknown')} ---"]

            if loc.get('type'):
                loc_lines.append(f"Type: {loc['type']}")
            if loc.get('region'):
                loc_lines.append(f"Region: {loc['region']}")
            if loc.get('description'):
                loc_lines.append(f"Description: {loc['description']}")

            # Sensory details
            if loc.get('sights'):
                loc_lines.append(f"Sights: {loc['sights']}")
            if loc.get('sounds'):
                loc_lines.append(f"Sounds: {loc['sounds']}")
            if loc.get('smells'):
                loc_lines.append(f"Smells: {loc['smells']}")
            if loc.get('atmosphere'):
                loc_lines.append(f"Atmosphere: {loc['atmosphere']}")

            # Significance
            if loc.get('significance'):
                loc_lines.append(f"Story Significance: {loc['significance']}")
            if loc.get('history'):
                loc_lines.append(f"History: {loc['history']}")

            # Connected locations
            if loc.get('connections'):
                loc_lines.append(f"Connected To: {', '.join(loc['connections'])}")

            lines.extend(loc_lines)

        return "\n".join(lines)

    def _format_items(self) -> str:
        """Format items for searchability."""
        lines = ["=== ITEMS ==="]

        for item in self.items:
            item_lines = [f"\n--- ITEM: {item.get('name', 'Unknown')} ---"]

            if item.get('type'):
                item_lines.append(f"Type: {item['type']}")
            if item.get('description'):
                item_lines.append(f"Description: {item['description']}")
            if item.get('properties'):
                item_lines.append(f"Properties: {item['properties']}")
            if item.get('significance'):
                item_lines.append(f"Story Significance: {item['significance']}")
            if item.get('owner'):
                item_lines.append(f"Owner: {item['owner']}")
            if item.get('location'):
                item_lines.append(f"Location: {item['location']}")
            if item.get('history'):
                item_lines.append(f"History: {item['history']}")

            # For magical items
            if item.get('powers'):
                item_lines.append(f"Powers: {item['powers']}")
            if item.get('limitations'):
                item_lines.append(f"Limitations: {item['limitations']}")

            lines.extend(item_lines)

        return "\n".join(lines)

    def _format_factions(self) -> str:
        """Format factions for searchability."""
        lines = ["=== FACTIONS ==="]

        for faction in self.factions:
            f_lines = [f"\n--- FACTION: {faction.get('name', 'Unknown')} ---"]

            if faction.get('type'):
                f_lines.append(f"Type: {faction['type']}")
            if faction.get('ideology'):
                f_lines.append(f"Ideology: {faction['ideology']}")
            if faction.get('goals'):
                f_lines.append(f"Goals: {faction['goals']}")
            if faction.get('leadership'):
                f_lines.append(f"Leadership: {faction['leadership']}")
            if faction.get('members'):
                f_lines.append(f"Notable Members: {', '.join(faction['members'])}")
            if faction.get('headquarters'):
                f_lines.append(f"Headquarters: {faction['headquarters']}")
            if faction.get('resources'):
                f_lines.append(f"Resources: {faction['resources']}")
            if faction.get('history'):
                f_lines.append(f"History: {faction['history']}")

            # Relationships with other factions
            if faction.get('allies'):
                f_lines.append(f"Allies: {', '.join(faction['allies'])}")
            if faction.get('enemies'):
                f_lines.append(f"Enemies: {', '.join(faction['enemies'])}")

            lines.extend(f_lines)

        return "\n".join(lines)

    def _format_magic_system(self) -> str:
        """Format magic/power system for searchability."""
        if not self.magic_system:
            return ""

        lines = ["=== MAGIC/POWER SYSTEM ==="]
        ms = self.magic_system

        if ms.get('name'):
            lines.append(f"System Name: {ms['name']}")
        if ms.get('description'):
            lines.append(f"Description: {ms['description']}")
        if ms.get('source'):
            lines.append(f"Source of Power: {ms['source']}")
        if ms.get('rules'):
            lines.append(f"Fundamental Rules: {ms['rules']}")
        if ms.get('limitations'):
            lines.append(f"Limitations: {ms['limitations']}")
        if ms.get('costs'):
            lines.append(f"Costs: {ms['costs']}")

        # Abilities/skills
        if ms.get('abilities'):
            lines.append("\nAbilities/Skills:")
            for ability in ms['abilities']:
                if isinstance(ability, dict):
                    lines.append(f"  - {ability.get('name', 'Unknown')}: {ability.get('description', '')}")
                else:
                    lines.append(f"  - {ability}")

        # Ranks/levels
        if ms.get('ranks'):
            lines.append("\nPower Ranks:")
            for rank in ms['ranks']:
                if isinstance(rank, dict):
                    lines.append(f"  - {rank.get('name', 'Unknown')}: {rank.get('description', '')}")
                else:
                    lines.append(f"  - {rank}")

        return "\n".join(lines)

    def _format_lore(self) -> str:
        """Format lore entries for searchability."""
        lines = ["=== LORE ==="]

        for entry in self.lore:
            lore_lines = [f"\n--- {entry.get('title', 'Untitled')} ---"]

            if entry.get('category'):
                lore_lines.append(f"Category: {entry['category']}")
            if entry.get('content'):
                lore_lines.append(entry['content'])
            if entry.get('related_to'):
                lore_lines.append(f"Related To: {', '.join(entry['related_to'])}")

            lines.extend(lore_lines)

        return "\n".join(lines)

    def _format_timeline(self) -> str:
        """Format timeline for searchability."""
        lines = ["=== TIMELINE ==="]

        # Sort by date if possible
        sorted_events = sorted(
            self.timeline,
            key=lambda x: x.get('order', 0)
        )

        for event in sorted_events:
            event_lines = []

            date_str = event.get('date', event.get('era', 'Unknown time'))
            event_lines.append(f"\n[{date_str}] {event.get('title', 'Untitled Event')}")

            if event.get('description'):
                event_lines.append(f"  {event['description']}")
            if event.get('significance'):
                event_lines.append(f"  Significance: {event['significance']}")
            if event.get('characters_involved'):
                event_lines.append(f"  Characters: {', '.join(event['characters_involved'])}")

            lines.extend(event_lines)

        return "\n".join(lines)

    # === Helper methods ===

    def add_location(self, location: Dict[str, Any]) -> None:
        """Add a location to the world."""
        self.locations.append(location)

    def add_item(self, item: Dict[str, Any]) -> None:
        """Add an item to the world."""
        self.items.append(item)

    def add_faction(self, faction: Dict[str, Any]) -> None:
        """Add a faction to the world."""
        self.factions.append(faction)

    def add_lore_entry(self, entry: Dict[str, Any]) -> None:
        """Add a lore entry."""
        self.lore.append(entry)

    def add_timeline_event(self, event: Dict[str, Any]) -> None:
        """Add a timeline event."""
        self.timeline.append(event)

    def get_location_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a location by name."""
        name_lower = name.lower()
        for loc in self.locations:
            if loc.get('name', '').lower() == name_lower:
                return loc
        return None

    def get_faction_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a faction by name."""
        name_lower = name.lower()
        for faction in self.factions:
            if faction.get('name', '').lower() == name_lower:
                return faction
        return None
