"""
RAG (Retrieval-Augmented Generation) Tools for CrewAI agents.

These tools provide semantic search capabilities for story knowledge:
- Character queries
- Location queries
- Plot event queries
- Relationship queries
- Continuity checking
"""

import json
from typing import Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import logging

from rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


# Singleton vector store instance
_vector_store = None


def get_vector_store() -> VectorStoreManager:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store


# ============================================================================
# Character Query Tools
# ============================================================================

class SemanticCharacterSearchInput(BaseModel):
    query: str = Field(..., description="Natural language query about characters (e.g., 'tell me about the protagonist' or 'who is the villain?')")
    top_k: int = Field(default=3, description="Number of results to return")


class SemanticCharacterSearchTool(BaseTool):
    name: str = "Semantic Character Search"
    description: str = (
        "Search for characters using natural language queries. "
        "Use this to find characters by description, role, personality, or relationships. "
        "Examples: 'the main protagonist', 'characters who are enemies', 'noble knights'"
    )
    args_schema: type[BaseModel] = SemanticCharacterSearchInput

    def _run(self, query: str, top_k: int = 3, **kwargs) -> str:
        """Search for characters semantically."""
        try:
            vector_store = get_vector_store()

            results = vector_store.semantic_search(
                collection_name='characters',
                query=query,
                n_results=top_k
            )

            if not results['ids']:
                return f"No characters found matching: {query}"

            # Format results
            character_results = []
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                content = results['documents'][i]
                distance = results['distances'][i]

                char_info = {
                    'name': metadata.get('title', 'Unknown'),
                    'type': 'Major' if metadata.get('is_major') == 'True' else 'Minor',
                    'relevance_score': round(1 - distance, 3),  # Convert distance to similarity
                    'details': content[:300] + "..." if len(content) > 300 else content
                }
                character_results.append(json.dumps(char_info, indent=2))

            return "\n\n---\n\n".join(character_results)

        except Exception as e:
            logger.error(f"Character search failed: {e}")
            return f"Error searching characters: {e}"


class GetCharacterDetailsInput(BaseModel):
    character_name: str = Field(..., description="The name of the character to look up")


class GetCharacterDetailsTool(BaseTool):
    name: str = "Get Character Details"
    description: str = (
        "Get detailed information about a specific character by name. "
        "Use this when you know the character's name and need their full profile."
    )
    args_schema: type[BaseModel] = GetCharacterDetailsInput

    def _run(self, character_name: str, **kwargs) -> str:
        """Get details for a specific character."""
        try:
            vector_store = get_vector_store()

            # Search by exact name match first
            results = vector_store.semantic_search(
                collection_name='characters',
                query=character_name,
                n_results=1
            )

            if not results['ids']:
                return f"Character not found: {character_name}"

            # Return the most relevant result
            content = results['documents'][0]
            metadata = results['metadatas'][0]

            return f"Character: {metadata.get('title')}\n\n{content}"

        except Exception as e:
            logger.error(f"Failed to get character details: {e}")
            return f"Error retrieving character: {e}"


# ============================================================================
# Location Query Tools
# ============================================================================

class SemanticLocationSearchInput(BaseModel):
    query: str = Field(..., description="Natural language query about locations (e.g., 'dark forest', 'royal palace')")
    top_k: int = Field(default=3, description="Number of results to return")


class SemanticLocationSearchTool(BaseTool):
    name: str = "Semantic Location Search"
    description: str = (
        "Search for locations using natural language descriptions. "
        "Use this to find settings by atmosphere, type, or characteristics. "
        "Examples: 'spooky mansion', 'busy marketplace', 'remote hideout'"
    )
    args_schema: type[BaseModel] = SemanticLocationSearchInput

    def _run(self, query: str, top_k: int = 3, **kwargs) -> str:
        """Search for locations semantically."""
        try:
            vector_store = get_vector_store()

            results = vector_store.semantic_search(
                collection_name='locations',
                query=query,
                n_results=top_k
            )

            if not results['ids']:
                return f"No locations found matching: {query}"

            # Format results
            location_results = []
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                content = results['documents'][i]
                distance = results['distances'][i]

                loc_info = {
                    'name': metadata.get('title', 'Unknown'),
                    'relevance_score': round(1 - distance, 3),
                    'description': content[:300] + "..." if len(content) > 300 else content
                }
                location_results.append(json.dumps(loc_info, indent=2))

            return "\n\n---\n\n".join(location_results)

        except Exception as e:
            logger.error(f"Location search failed: {e}")
            return f"Error searching locations: {e}"


# ============================================================================
# Plot Event Query Tools
# ============================================================================

class SemanticPlotSearchInput(BaseModel):
    query: str = Field(..., description="Natural language query about plot events or scenes (e.g., 'battle scene', 'romantic moment')")
    top_k: int = Field(default=5, description="Number of results to return")


class SemanticPlotSearchTool(BaseTool):
    name: str = "Semantic Plot Search"
    description: str = (
        "Search for plot events and scenes using natural language. "
        "Use this to find relevant story moments, track plot progression, or check what happened. "
        "Examples: 'when they first met', 'the betrayal scene', 'action sequences'"
    )
    args_schema: type[BaseModel] = SemanticPlotSearchInput

    def _run(self, query: str, top_k: int = 5, **kwargs) -> str:
        """Search for plot events semantically."""
        try:
            vector_store = get_vector_store()

            results = vector_store.semantic_search(
                collection_name='plot_events',
                query=query,
                n_results=top_k
            )

            if not results['ids']:
                return f"No plot events found matching: {query}"

            # Format results
            plot_results = []
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                content = results['documents'][i]
                distance = results['distances'][i]

                plot_info = {
                    'scene': metadata.get('title', 'Unknown'),
                    'chapter': metadata.get('chapter', 'Unknown'),
                    'word_count': metadata.get('word_count', '0'),
                    'relevance_score': round(1 - distance, 3),
                    'summary': content[:400] + "..." if len(content) > 400 else content
                }
                plot_results.append(json.dumps(plot_info, indent=2))

            return "\n\n---\n\n".join(plot_results)

        except Exception as e:
            logger.error(f"Plot search failed: {e}")
            return f"Error searching plot events: {e}"


# ============================================================================
# Relationship Query Tools
# ============================================================================

class FindRelationshipsInput(BaseModel):
    character_name: str = Field(..., description="Name of the character to find relationships for")
    top_k: int = Field(default=5, description="Number of relationships to return")


class FindRelationshipsTool(BaseTool):
    name: str = "Find Character Relationships"
    description: str = (
        "Find relationships involving a specific character. "
        "Use this to understand character dynamics, connections, and social networks."
    )
    args_schema: type[BaseModel] = FindRelationshipsInput

    def _run(self, character_name: str, top_k: int = 5, **kwargs) -> str:
        """Find relationships for a character."""
        try:
            vector_store = get_vector_store()

            # Search for relationships mentioning this character
            results = vector_store.semantic_search(
                collection_name='relationships',
                query=f"relationships involving {character_name}",
                n_results=top_k
            )

            if not results['ids']:
                return f"No relationships found for character: {character_name}"

            # Format results
            rel_results = []
            for i, doc_id in enumerate(results['ids']):
                content = results['documents'][i]
                metadata = results['metadatas'][i]

                rel_info = {
                    'character': metadata.get('character_name', 'Unknown'),
                    'relationship': content[:300] + "..." if len(content) > 300 else content
                }
                rel_results.append(json.dumps(rel_info, indent=2))

            return "\n\n---\n\n".join(rel_results)

        except Exception as e:
            logger.error(f"Relationship search failed: {e}")
            return f"Error searching relationships: {e}"


# ============================================================================
# Continuity Checking Tools
# ============================================================================

class CheckContinuityInput(BaseModel):
    query: str = Field(..., description="What to check for continuity (e.g., 'has Alice been to the castle before?', 'what color are Bob's eyes?')")


class CheckContinuityTool(BaseTool):
    name: str = "Check Story Continuity"
    description: str = (
        "Check story continuity by searching across all knowledge. "
        "Use this to verify facts, check for contradictions, and maintain consistency. "
        "Examples: 'what happened in chapter 3?', 'has this character met before?', 'what was established about this location?'"
    )
    args_schema: type[BaseModel] = CheckContinuityInput

    def _run(self, query: str, **kwargs) -> str:
        """Check continuity across all story elements."""
        try:
            vector_store = get_vector_store()

            # Search across all collections
            all_results = []

            # Search characters
            char_results = vector_store.semantic_search(
                collection_name='characters',
                query=query,
                n_results=2
            )
            if char_results['ids']:
                all_results.append(("Characters", char_results))

            # Search locations
            loc_results = vector_store.semantic_search(
                collection_name='locations',
                query=query,
                n_results=2
            )
            if loc_results['ids']:
                all_results.append(("Locations", loc_results))

            # Search plot events
            plot_results = vector_store.semantic_search(
                collection_name='plot_events',
                query=query,
                n_results=3
            )
            if plot_results['ids']:
                all_results.append(("Plot Events", plot_results))

            if not all_results:
                return f"No relevant information found for continuity check: {query}"

            # Format combined results
            output_parts = [f"Continuity Check: {query}\n"]

            for category, results in all_results:
                output_parts.append(f"\n{category}:")
                for i, doc_id in enumerate(results['ids']):
                    content = results['documents'][i]
                    metadata = results['metadatas'][i]
                    title = metadata.get('title', metadata.get('scene', 'Unknown'))

                    snippet = content[:200] + "..." if len(content) > 200 else content
                    output_parts.append(f"  - {title}: {snippet}")

            return "\n".join(output_parts)

        except Exception as e:
            logger.error(f"Continuity check failed: {e}")
            return f"Error checking continuity: {e}"


# ============================================================================
# General Knowledge Search
# ============================================================================

class GeneralKnowledgeSearchInput(BaseModel):
    query: str = Field(..., description="General question about the story")
    top_k: int = Field(default=5, description="Number of total results to return")


class GeneralKnowledgeSearchTool(BaseTool):
    name: str = "General Story Knowledge Search"
    description: str = (
        "Search across all story knowledge (characters, locations, plot, relationships). "
        "Use this for general questions about the story that might span multiple elements. "
        "Examples: 'what is the main conflict?', 'tell me about the world', 'summarize the story so far'"
    )
    args_schema: type[BaseModel] = GeneralKnowledgeSearchInput

    def _run(self, query: str, top_k: int = 5, **kwargs) -> str:
        """Search across all collections."""
        try:
            vector_store = get_vector_store()

            # Distribute search across collections
            results_per_collection = max(1, top_k // 3)

            all_results = []

            # Search each collection
            for collection in ['characters', 'locations', 'plot_events']:
                results = vector_store.semantic_search(
                    collection_name=collection,
                    query=query,
                    n_results=results_per_collection
                )

                for i, doc_id in enumerate(results['ids']):
                    all_results.append({
                        'collection': collection,
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i],
                        'distance': results['distances'][i]
                    })

            if not all_results:
                return f"No information found for query: {query}"

            # Sort by distance (most relevant first)
            all_results.sort(key=lambda x: x['distance'])

            # Format output
            output_parts = []
            for result in all_results[:top_k]:
                collection = result['collection'].replace('_', ' ').title()
                title = result['metadata'].get('title', result['metadata'].get('scene', 'Unknown'))
                content = result['content']

                snippet = content[:300] + "..." if len(content) > 300 else content
                output_parts.append(f"[{collection}] {title}:\n{snippet}")

            return "\n\n---\n\n".join(output_parts)

        except Exception as e:
            logger.error(f"General knowledge search failed: {e}")
            return f"Error searching story knowledge: {e}"
