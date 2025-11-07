# RAG Auto-Sync System

Automatic synchronization between yWriter7 files and the RAG (Retrieval-Augmented Generation) knowledge base.

## Overview

The RAG Auto-Sync system ensures that your story's knowledge base (characters, locations, plot events, etc.) is always up-to-date with your yWriter7 project files. Every time you make changes to your story, those changes are automatically reflected in the semantic search system used by AI agents.

## Features

- **Automatic Synchronization**: Changes to yWriter7 files are automatically synced to ChromaDB
- **Multiple Integration Methods**: Context managers, wrappers, and manual control
- **Configuration-Based**: Enable/disable via `config.yaml`
- **Transparent Integration**: Works seamlessly with existing code
- **Semantic Search**: Query story elements using natural language
- **Incremental Updates**: Only changed items are re-embedded

## Quick Start

### 1. Enable Auto-Sync in Configuration

Edit `config.yaml`:

```yaml
ywriter:
  auto_save: true
  backup_enabled: true
  output_format: "yw7"
  sync_to_rag: true  # Enable automatic RAG sync
```

### 2. Use Auto-Sync in Your Code

The simplest way is using the context manager:

```python
from rag.auto_sync import AutoSyncYw7File

# Automatic sync with context manager
with AutoSyncYw7File("my_story.yw7") as yw7_file:
    # Make changes
    yw7_file.novel.chapters[chapter_id].title = "New Title"
    yw7_file.novel.characters[char_id].desc = "Updated description"
    # Changes are automatically saved and synced when context exits
```

### 3. Query the Knowledge Base

```python
from rag.vector_store import VectorStoreManager

vector_store = VectorStoreManager()

# Search for characters semantically
results = vector_store.semantic_search(
    "characters",
    "brave warrior protagonist",
    n_results=5
)

for doc_id, doc, metadata, score in zip(
    results['ids'],
    results['documents'],
    results['metadatas'],
    results['distances']
):
    print(f"{metadata['name']}: {doc[:100]}...")
```

## Usage Methods

### Method 1: Context Manager (Recommended)

Best for most use cases - clean, automatic, and safe:

```python
from rag.auto_sync import AutoSyncYw7File

with AutoSyncYw7File("story.yw7") as yw7_file:
    # Read data
    print(yw7_file.novel.title)

    # Make changes
    yw7_file.novel.chapters[ch_id].desc = "Updated description"

    # Automatic save + sync on exit
```

**Pros:**
- Automatic resource management
- Exception-safe
- Clean syntax

**Cons:**
- Less control over when sync happens

### Method 2: Manual Control

Best when you need fine-grained control:

```python
from rag.auto_sync import AutoSyncYw7File

# Disable auto-sync
yw7_file = AutoSyncYw7File("story.yw7", auto_sync=False)
yw7_file.read()

# Make multiple changes
yw7_file.novel.chapters[ch1].title = "Chapter 1"
yw7_file.novel.chapters[ch2].title = "Chapter 2"

# Write to file (no sync yet)
yw7_file.write()

# Manually sync when ready
stats = yw7_file.sync_to_rag()
print(f"Synced {sum(stats.values())} items")
```

**Pros:**
- Full control over sync timing
- Can sync once for multiple changes
- Get sync statistics

**Cons:**
- More verbose
- Need to remember to sync

### Method 3: Batch Operations

Best for making many changes at once:

```python
from rag.auto_sync import RAGSyncContext

with RAGSyncContext("story.yw7") as ctx:
    yw7_file = ctx.yw7_file

    # Update many items
    for chapter_id in yw7_file.novel.srtChapters:
        chapter = yw7_file.novel.chapters[chapter_id]
        chapter.desc += "\n[Updated]"

    # Single sync for all changes on exit
```

**Pros:**
- Efficient for bulk operations
- Single sync for many changes
- Clear transaction boundary

**Cons:**
- Slightly more verbose than Method 1

### Method 4: Wrap Existing Code

Best for legacy code integration:

```python
from ywriter7.yw.yw7_file import Yw7File
from rag.auto_sync import enable_auto_sync

# Existing code using Yw7File
yw7_file = Yw7File("story.yw7")
yw7_file.read()

# Enable auto-sync on existing instance
enable_auto_sync(yw7_file)

# Now all writes will auto-sync
yw7_file.novel.chapters[ch_id].title = "New Title"
yw7_file.write()  # Automatically syncs!
```

**Pros:**
- Works with existing code
- No need to change class usage
- Drop-in enhancement

**Cons:**
- Monkey-patching (less clean)
- May surprise readers unfamiliar with wrapper

### Method 5: One-Shot Sync

Best for manual/administrative operations:

```python
from rag.auto_sync import sync_file_to_rag

# Sync existing file to RAG
stats = sync_file_to_rag("story.yw7")

print(f"Synced:")
print(f"  - {stats['characters']} characters")
print(f"  - {stats['locations']} locations")
print(f"  - {stats['plot_events']} plot events")
```

**Pros:**
- Simple for one-off operations
- Useful for initial population
- No file modifications

**Cons:**
- Manual operation only
- No automatic updates

## Integration with Existing Tools

All yWriter7 tools in `tools/ywriter_tools.py` automatically support auto-sync when enabled in `config.yaml`:

```python
from tools.ywriter_tools import WriteProjectNoteTool, CreateChapterTool

# These tools now automatically sync to RAG if sync_to_rag=true in config.yaml
write_note = WriteProjectNoteTool()
create_chapter = CreateChapterTool()

# Usage (automatic sync)
write_note._run(yw7_path="story.yw7", title="Note", content="Content")
create_chapter._run(yw7_path="story.yw7", title="Chapter 1")
```

The `load_yw7_file()` helper function automatically uses `AutoSyncYw7File` when configured.

## Configuration Reference

### config.yaml

```yaml
# RAG Configuration
rag:
  enabled: true                           # Enable RAG system
  vector_db_path: "knowledge_base"        # ChromaDB storage location
  embedding_model: "all-MiniLM-L6-v2"     # Sentence transformer model
  collection_prefix: "aibook"             # Prefix for collections
  chunk_size: 1000                        # Max characters per chunk
  chunk_overlap: 200                      # Overlap between chunks
  top_k: 5                                # Default search results
  similarity_threshold: 0.7               # Minimum similarity score
  auto_sync: true                         # Auto-sync on changes

  # Collections to maintain
  collections:
    - characters         # Character profiles
    - locations          # Location descriptions
    - items              # Item descriptions
    - plot_events        # Key plot events
    - relationships      # Character relationships
    - lore               # World-building lore

# yWriter7 Integration
ywriter:
  auto_save: true              # Auto-save after changes
  backup_enabled: true         # Create backups
  output_format: "yw7"         # Output format
  sync_to_rag: true            # Enable automatic RAG sync
```

## Architecture

### Components

1. **AutoSyncYw7File** (`rag/auto_sync.py`)
   - Extends `Yw7File` with automatic sync capability
   - Intercepts `write()` calls to trigger sync
   - Context manager support

2. **RAGSyncManager** (`rag/sync_manager.py`)
   - Handles bidirectional sync between yWriter7 and ChromaDB
   - Extracts and embeds story elements
   - Manages incremental updates

3. **VectorStoreManager** (`rag/vector_store.py`)
   - ChromaDB interface
   - Collection management
   - Semantic search operations

4. **RAG Tools** (`tools/rag_tools.py`)
   - CrewAI tools for agents to query knowledge base
   - Semantic character search
   - Plot event tracking
   - Continuity checking

### Data Flow

```
┌─────────────────┐
│  yWriter7 File  │
│   (story.yw7)   │
└────────┬────────┘
         │
         │ AutoSyncYw7File.write()
         ▼
┌─────────────────┐
│  RAGSyncManager │
│  - Extract data │
│  - Generate IDs │
└────────┬────────┘
         │
         │ sync_from_ywriter()
         ▼
┌─────────────────┐
│  VectorStore    │
│  (ChromaDB)     │
│  - Embeddings   │
│  - Collections  │
└────────┬────────┘
         │
         │ semantic_search()
         ▼
┌─────────────────┐
│   AI Agents     │
│  - MemoryKeeper │
│  - Writer       │
│  - Editor       │
└─────────────────┘
```

## Synced Collections

### 1. Characters

**Metadata:**
- `id`: Character ID from yWriter7
- `name`: Character name
- `type`: "character"

**Document:**
Combines character name, description, full name, notes, and bio into a searchable text.

**Usage:**
```python
results = vector_store.semantic_search("characters", "brave protagonist")
```

### 2. Locations

**Metadata:**
- `id`: Location ID
- `name`: Location name
- `type`: "location"

**Document:**
Combines location name, description, and AKA into searchable text.

**Usage:**
```python
results = vector_store.semantic_search("locations", "ancient castle fortress")
```

### 3. Items

**Metadata:**
- `id`: Item ID
- `name`: Item name
- `type`: "item"

**Document:**
Combines item name and description.

**Usage:**
```python
results = vector_store.semantic_search("items", "magical sword weapon")
```

### 4. Plot Events

**Metadata:**
- `id`: Scene ID
- `title`: Scene title
- `chapter_id`: Parent chapter ID
- `type`: "plot_event"

**Document:**
Scene title, description, and content combined.

**Usage:**
```python
results = vector_store.semantic_search("plot_events", "confrontation battle")
```

### 5. Relationships

**Metadata:**
- `id`: Relationship ID
- `character_ids`: List of character IDs
- `type`: "relationship"

**Document:**
Description of character relationships and dynamics.

**Usage:**
```python
results = vector_store.semantic_search("relationships", "friendship rivalry")
```

### 6. Lore

**Metadata:**
- `id`: Note ID
- `title`: Note title
- `type`: "lore"

**Document:**
World-building notes, mythology, history.

**Usage:**
```python
results = vector_store.semantic_search("lore", "ancient prophecy legend")
```

## Agent Integration

Agents have access to RAG tools for querying the knowledge base:

### Available RAG Tools

1. **SemanticCharacterSearchTool**
   - Search for characters by description
   - Example: "Find brave warriors"

2. **GetCharacterDetailsTool**
   - Get full details for a specific character
   - Example: "Get details for char_id_123"

3. **SemanticLocationSearchTool**
   - Search for locations by description
   - Example: "Find dark caves"

4. **SemanticPlotSearchTool**
   - Search plot events by description
   - Example: "Find battle scenes"

5. **FindRelationshipsTool**
   - Find relationships involving characters
   - Example: "Find relationships for protagonist"

6. **CheckContinuityTool**
   - Check for continuity issues
   - Example: "Verify character traits are consistent"

7. **GeneralKnowledgeSearchTool**
   - Search across all collections
   - Example: "Find anything about dragons"

### Agent Configuration

Agents with RAG tools (see `config.yaml` and agent files):

- **MemoryKeeper**: All 7 RAG tools (continuity tracking)
- **Writer**: 6 RAG tools (character/location/plot search)
- **Editor**: 6 RAG tools (continuity checking)
- **Critic**: 5 RAG tools (consistency analysis)
- **Character Creator**: 4 RAG tools (avoid duplicates)

## Troubleshooting

### Auto-sync not working

1. **Check configuration:**
   ```yaml
   ywriter:
     sync_to_rag: true  # Must be true
   ```

2. **Check RAG is enabled:**
   ```yaml
   rag:
     enabled: true  # Must be true
   ```

3. **Check logs:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Slow sync performance

1. **Reduce chunk size:**
   ```yaml
   rag:
     chunk_size: 500  # Smaller chunks
   ```

2. **Use batch operations:**
   ```python
   # Instead of multiple syncs
   with RAGSyncContext("story.yw7") as ctx:
       # Make all changes
   # Single sync at end
   ```

3. **Check embeddings model:**
   ```yaml
   rag:
     embedding_model: "all-MiniLM-L6-v2"  # Fast, lightweight
   ```

### Search not finding results

1. **Lower similarity threshold:**
   ```yaml
   rag:
     similarity_threshold: 0.5  # Lower = more results
   ```

2. **Increase result count:**
   ```python
   results = vector_store.semantic_search(
       "characters",
       "query",
       n_results=10  # More results
   )
   ```

3. **Check if data is synced:**
   ```python
   from rag.auto_sync import sync_file_to_rag
   stats = sync_file_to_rag("story.yw7")
   print(stats)  # Should show synced items
   ```

### ChromaDB errors

1. **Clear and rebuild:**
   ```bash
   rm -rf knowledge_base/
   python -c "from rag.auto_sync import sync_file_to_rag; sync_file_to_rag('story.yw7')"
   ```

2. **Check permissions:**
   ```bash
   ls -la knowledge_base/
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```

## Examples

See `examples/rag_auto_sync_demo.py` for comprehensive examples of all usage patterns.

Run the demo:

```bash
python examples/rag_auto_sync_demo.py
```

## Testing

Test the RAG integration:

```bash
# Run RAG integration tests
python test_rag_integration.py

# Run yWriter7 sync tests
python test_ywriter7_sync.py
```

## Performance Considerations

### Sync Frequency

- **High-frequency writes**: Use `auto_sync=False` and manual sync
- **Batch operations**: Use `RAGSyncContext` for multiple changes
- **Single changes**: Use `AutoSyncYw7File` with auto-sync

### Embedding Generation

- **First sync**: Slower (generates all embeddings)
- **Incremental sync**: Faster (only changed items)
- **Model size**: `all-MiniLM-L6-v2` is lightweight (80MB)

### Storage Requirements

- **ChromaDB**: ~10-50MB for typical novel
- **Embeddings**: 384 dimensions per item
- **Grows with**: Number of characters, locations, scenes

## Best Practices

1. **Enable auto-sync globally** via `config.yaml` for convenience
2. **Use context managers** for clean resource management
3. **Batch operations** when making many changes
4. **Monitor logs** during development to see sync operations
5. **Test semantic search** to verify data is synced correctly
6. **Back up vector DB** before major changes (`knowledge_base/`)

## Future Enhancements

Potential future features:

- [ ] Selective collection sync (only sync changed collections)
- [ ] Compression for large documents
- [ ] Multi-file project support
- [ ] Version tracking and rollback
- [ ] Sync conflict resolution
- [ ] Real-time sync notifications
- [ ] Performance metrics and profiling
- [ ] Export/import of knowledge base

## See Also

- [RAG System Documentation](YWRITER7_SYNC.md) - Original RAG implementation
- [Architecture Analysis](ARCHITECTURE_ANALYSIS.md) - System architecture
- [Quick Reference](QUICK_REFERENCE.md) - Command reference
- [Examples](examples/) - Code examples

## Support

For issues or questions:

1. Check logs with `logging.basicConfig(level=logging.DEBUG)`
2. Run tests: `python test_rag_integration.py`
3. Review examples: `examples/rag_auto_sync_demo.py`
4. Check configuration: `config.yaml`
