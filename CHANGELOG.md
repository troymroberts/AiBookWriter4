# AiBookWriter4 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned (Per SPEC.md v2.0)
- Phase 1: Core Pipeline (Supervisor, StoryPlanner, Writer, Critic, Reviser, Continuity agents)
- Phase 2: World Building (CharacterCreator, LocationDesigner, LoreBuilder, Canon system)
- Phase 3: Quality Enhancement (PacingAnalyzer, DialogueCoach, SensoryEnricher)
- Phase 4: Advanced Features (Arc-based serialization, Research agent, Multi-page UI)

---

## [0.2.3-alpha] - 2026-01-08

### Added
- **Network Diagnostics Documentation** - New `docs/NETWORK_DIAGNOSTICS.md`
  - Comprehensive guide for diagnosing LXC container networking issues
  - MTU, TSO/GSO, IPv4/IPv6 diagnostic procedures
  - Troubleshooting steps for "Connection refused" errors
  - Proxmox/UniFi-specific considerations

### Changed
- **LLM Configuration** - Enhanced retry and timeout settings
  - `num_retries=3` for transient failure handling
  - `timeout=120.0` seconds for long-running LLM calls
  - Location: `flows/book_writer_flow.py:_get_llm()`

### Investigated
- **LXC Container Networking** - Extensive diagnostics performed
  - TSO/GSO offloading tested (not the root cause)
  - MTU tested at 1300 and 900 (not the root cause)
  - IPv4 fix working correctly
  - Issue appears to be intermittent LXC veth networking
  - See `docs/NETWORK_DIAGNOSTICS.md` for full analysis

### Recommended Free OpenRouter Models
Based on API query, best free models for long-form writing:

| Model | Context | Max Output | Notes |
|-------|---------|------------|-------|
| `nex-agi/deepseek-v3.1-nex-n1:free` | 131K | 163K | Highest output |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128K | 128K | Multimodal |
| `z-ai/glm-4.5-air:free` | 131K | 96K | Lightweight flagship |
| `xiaomi/mimo-v2-flash:free` | 262K | 65K | Best context (current default) |
| `tngtech/tng-r1t-chimera:free` | 163K | 65K | Creative storytelling |

---

## [0.2.2-alpha] - 2026-01-08

### Added
- **OpenRouter Support** - Full integration with OpenRouter cloud API
  - Model format: `openrouter/<provider>/<model>` (e.g., `openrouter/xiaomi/mimo-v2-flash:free`)
  - Set `OPENROUTER_API_KEY` environment variable to use
  - Free tier models available with high context/output limits
  - Location: `flows/book_writer_flow.py:_get_llm()`
- **IPv4 Network Fix** - New `flows/ipv4_fix.py` module
  - Automatically applied on import of `flows` module
  - Fixes "[Errno 97] Address family not supported by protocol" errors
  - Works around IPv6/IPv4 connectivity issues in some environments
- **Dynamic Memory Configuration** - `_should_use_memory()` helper
  - Automatically disables CrewAI memory for cloud providers
  - Prevents OpenAI embedding errors when using OpenRouter
  - Memory enabled for Ollama (local embeddings available)

### Changed
- **config.yaml** - Added OpenRouter configuration section
  - Recommended free models: `xiaomi/mimo-v2-flash:free` (262K context, 65K output)
- **BookState.llm_base_url** - Now Optional[str]
  - Can be None for cloud providers like OpenRouter

### Tested
- **OpenRouter + MiMo-V2-Flash** - Successfully generated 2,605-word chapter
  - Near 3,000 word target achieved
  - Excellent prose quality with vivid descriptions
  - Model: `openrouter/xiaomi/mimo-v2-flash:free`

---

## [0.2.1-alpha] - 2026-01-08

### Fixed
- **LiteLLM Ollama Configuration** - Added proper `litellm.OllamaConfig()` setup in `book_writer_flow.py`
  - Sets `num_predict` for max output tokens (maps to Ollama's token limit)
  - Sets `num_ctx=40000` to utilize model's full context window
  - Configured only when model starts with `ollama/` prefix
- **CrewAI Agent Output Length** - Added `use_system_prompt=False` to `scene_writer` agent
  - Prevents CrewAI's system prompts from being prioritized over task instructions
  - Improves long-form content generation with smaller models
  - Location: `agents_extended.py:create_scene_writer()`
- **Output Artifact Cleanup** - Added cleanup in `_write_chapter()` and `editorial_refinement()`
  - Removes leaked CrewAI prompt fragments ("Thought: I now can give a great answer", etc.)
  - Cleaner chapter content without internal prompting artifacts

### Improved
- **Chapter Word Count** - Output improved ~6x (from ~77 words to ~444 words)
  - Previous: CrewAI agents producing very short outputs
  - After fix: More substantial chapter content
  - Note: Full 3,000 word target may require larger model (4B+ parameters)

### Technical Details
- `litellm.OllamaConfig()` is a global configuration that LiteLLM applies to all Ollama calls
- `use_system_prompt=False` disables CrewAI's default system message separation
- Cleanup patterns remove: "Thought: I now can give a great answer", "Final Answer:", etc.

---

## [0.2.0-alpha] - 2026-01-08

### Added
- **IMPLEMENTATION_PLAN.md** - Detailed implementation plan leveraging new CrewAI features
  - Location: `docs/IMPLEMENTATION_PLAN.md`
- **CHANGELOG.md** - Project changelog for tracking changes and rollback capability
- **flows/** - New CrewAI Flows-based architecture
  - `flows/state.py` - BookState Pydantic model for workflow state
  - `flows/book_writer_flow.py` - Main Flow orchestrator with 5 phases
  - `flows/crews/` - Phase-specific crew configurations
- **canon/** - Versioned fact database for story consistency
  - `canon/canon_manager.py` - ChromaDB-based canon system

### Changed
- **requirements.txt** - Updated dependencies for latest CrewAI features:
  - `crewai>=1.8.0` (was >=1.7.0) - Adds Flows, HITL, Streaming, A2A
  - `crewai-tools>=0.17.0` (unchanged)
  - Added `chromadb>=0.5.0` for RAG/Canon system
- **app.py** - Complete rewrite using CrewAI Flows
  - Removed legacy workflow code (backed up to `legacy/app_legacy.py`)
  - Direct BookWriterFlow integration
  - Native async streaming support
  - HITL review gate UI
  - Clean, maintainable ~540 LOC (was ~1500 LOC)

### Fixed
- **BookWriterFlow state initialization** - Added `initial_state` parameter to properly pass configuration from UI to Flow
- **config.yaml Ollama IP** - Updated from 10.1.1.40 to 10.1.1.39

### Tested
- **End-to-end flow execution** - Successfully generated 1-chapter story:
  - All 5 phases completed: Foundation → World Building → Structure → Writing → Editorial
  - Story arc: 666 chars
  - Chapter content: 1,426 words
  - 100% progress reached
  - Model: `ollama/qwen3-0.6b-40k:latest`

### Architecture Decisions
Based on latest CrewAI release features:

| Feature | Purpose | SPEC.md Alignment |
|---------|---------|-------------------|
| **CrewAI Flows** | Supervisor orchestration with `@start`, `@listen`, `@router` | §2.2 Supervisor Pattern |
| **HITL** | User review gates with pause/resume | §7.1 Review Gates |
| **Streaming** | Real-time UI progress | §9.2 Dashboard Display |
| **A2A** | Agent-to-agent delegation | §5.5 Agent Invocation |
| **Memory** | ChromaDB-based RAG | §3.1 RAG System |

### New File Structure (Planned)
```
flows/
├── book_writer_flow.py      # Main Flow orchestrator
├── state.py                  # BookState Pydantic model
└── crews/                    # Phase-specific crews
    ├── foundation_crew.py
    ├── world_building_crew.py
    ├── structure_crew.py
    ├── writing_crew.py
    └── editorial_crew.py
canon/
├── canon_manager.py          # Canon CRUD operations
└── contradiction_checker.py  # Violation detection
```

### Codebase Assessment (from Explore agent)
- **Total Agents:** 23 (all pure CrewAI pattern - no LangChain mix!)
- **Agent Categories:** Core (8), Light Novel (4), Fantasy (4), Literary (3), Editorial (4)
- **Configuration:** 17 genre configs, YAML + Python dataclasses
- **Existing Features:** Two-pass entity generation, context-aware prompts, multi-provider LLM

### Implemented Components

#### flows/state.py - BookState Model
- Complete Pydantic model for workflow state management
- Tracks: project config, phases, characters, locations, lore, chapters
- Review gate support with `ReviewGateStatus` enum
- Progress calculation with `get_progress_percentage()`
- Helper methods: `get_character_by_name()`, `add_lore_entry()`

#### flows/book_writer_flow.py - Main Orchestrator
- CrewAI Flow implementation with `@start`, `@listen`, `@router` decorators
- 5-phase workflow: Foundation → World Building → Structure → Writing → Editorial
- Editorial loop with convergence detection (< 5% changes = converged)
- HITL review gates with `await_user_review()` and `resume_after_review()`
- Streaming support (`stream = True`) for real-time UI
- Export functionality with `export_manuscript()`

#### canon/canon_manager.py - Canon System
- Versioned fact database per SPEC.md §7.2
- ChromaDB integration for semantic search
- Contradiction detection with `check_contradiction()`
- Retcon support with version tracking
- Categories: characters, locations, lore, timeline, relationships, items

### Previous Issues Resolved
The CODE_REVIEW.md issues (mixed patterns, broken templates) appear to have been resolved in the current codebase:
- ✅ All agents now use pure CrewAI `Agent` class
- ✅ Factory pattern with `create_[agent_name]()` functions
- ✅ Python f-strings for prompts (no Jinja2 `{{}}` in production code)
- ✅ Flow orchestration implemented (BookWriterFlow)
- ✅ HITL review gates implemented
- ✅ Canon system implemented (CanonManager)

---

## [0.1.0-alpha] - 2025-12-29

### Initial State (Pre-Refactor)

**Status:** Non-Functional - Major architectural issues identified in CODE_REVIEW.md

### Current Components
- **Streamlit UI** (`app.py`) - Basic multi-page structure exists but calls non-existent methods
- **Agents (Mixed Patterns)**:
  - CrewAI-based: `Critic`, `Editor`, `Reviser`, `PlotAgent`, `RelationshipArchitect`, `CharacterCreator`, `OutlineCreator`
  - LangChain-based: `StoryPlanner`, `SettingBuilder`, `LoreBuilder`, `Writer`
- **Config System** - Genre configs (18 genres), YAML prompts, `config.yaml`
- **yWriter Integration** - Basic tools for reading/writing yWriter7 files
- **LLM Providers** - Support for Ollama, OpenAI, Anthropic, OpenRouter

### Known Issues (from CODE_REVIEW.md)
- Severely outdated dependencies (CrewAI 0.100.0 vs 1.7.2)
- Broken prompt template syntax (`{{}}` vs `{}`)
- Missing methods called by app.py (`OutlineCreator.run_information_gathering_task()`)
- Inconsistent agent initialization patterns
- CrewAI LLM API mismatches (template params on wrong class)
- Hardcoded IP addresses in defaults
- Genre config parameters not integrated into workflow

### Files Structure
```
AiBookWriter4/
├── app.py                 # Main Streamlit application
├── agents/                # Agent implementations (mixed patterns)
├── config/                # Configuration files
│   ├── genres/           # 18 genre configuration modules
│   └── prompts/          # YAML prompt templates
├── docs/                  # Documentation
│   └── CODE_REVIEW.md    # Detailed code review
├── knowledge/             # Knowledge base directory
├── legacy/                # Legacy LangChain code
├── output/                # Generated output directory
├── ywriter7/              # yWriter integration
├── llm_providers.py       # Multi-provider LLM support
├── workflow.py            # Workflow definitions
├── tasks_extended.py      # Extended task definitions
└── agents_extended.py     # Extended agent definitions
```

---

## Migration Roadmap (From SPEC.md v2.0)

### Phase 1: Core Pipeline
- [ ] Migrate all agents to pure CrewAI pattern
- [ ] Fix prompt template syntax (`{{}}` -> `{}`)
- [ ] Implement Supervisor agent orchestration
- [ ] Integrate genre parameters into prompts
- [ ] Implement RAG with ChromaDB
- [ ] Add Canon system for consistency
- [ ] Build single-page functional UI

### Phase 2: World Building
- [ ] CharacterCreator with voice profiles
- [ ] LocationDesigner with sensory details
- [ ] LoreBuilder with iterative expansion
- [ ] Canon system with versioned facts
- [ ] Dialogue indexing for character consistency

### Phase 3: Quality Enhancement
- [ ] PacingAnalyzer for tension curves
- [ ] DialogueCoach for subtext and voice
- [ ] SensoryEnricher for show-don't-tell
- [ ] Full editorial loop with convergence detection
- [ ] Dashboard UI with progress tracking

### Phase 4: Advanced Features
- [ ] Arc-based serialization for long novels
- [ ] Research agent for historical/non-fiction
- [ ] Multi-page Streamlit UI
- [ ] Checkpoint system for resume capability
- [ ] yWriter7 export validation

---

## Version History Summary

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 0.1.0-alpha | 2025-12-29 | Non-Functional | Initial codebase, needs refactor |
| 0.2.0-alpha | 2026-01-08 | Functional | CrewAI Flows architecture |
| 0.2.1-alpha | 2026-01-08 | Improved | LiteLLM/Ollama config fixes |
| 0.2.2-alpha | 2026-01-08 | Functional | OpenRouter cloud support |
| 0.2.3-alpha | 2026-01-08 | Documented | Network diagnostics guide |
| 1.0.0 | TBD | - | Phase 1 Complete |
| 2.0.0 | TBD | - | Full SPEC.md v2.0 Implementation |

---

## Contributing

When making changes:
1. Update this changelog with your changes under `[Unreleased]`
2. Use categories: Added, Changed, Deprecated, Removed, Fixed, Security
3. Include file references for significant changes
4. Document breaking changes clearly
