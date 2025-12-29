# AiBookWriter4 Documentation

## Overview

AiBookWriter4 is a multi-agent AI system for automated novel and book generation. It uses a pipeline of specialized AI agents powered by local LLMs (via Ollama) to create story arcs, world settings, chapter outlines, and prose.

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture/ARCHITECTURE.md) | System design, data flow, and component overview |
| [Setup Guide](setup/SETUP.md) | Installation, configuration, and deployment |
| [Agents API](api/AGENTS.md) | Agent classes, configuration, and usage |
| [Tools API](api/TOOLS.md) | CrewAI tools for yWriter integration |
| [yWriter7 Integration](ywriter7/YWRITER7.md) | yWriter 7 file format and library reference |

## Features

- **Multi-Agent Pipeline**: Specialized agents for each phase of book creation
- **Local LLM Support**: Uses Ollama for privacy and cost-effective inference
- **18 Genre Configurations**: Pre-configured settings for various genres
- **Streaming Output**: Real-time content generation display
- **yWriter 7 Integration**: Export to professional writing software
- **Web UI & CLI**: Streamlit interface and command-line access

## Technology Stack

| Component | Technology |
|-----------|------------|
| Agent Frameworks | CrewAI, LangChain |
| LLM Provider | Ollama (local) |
| Web Interface | Streamlit |
| Configuration | PyYAML, Pydantic |
| Project Export | yWriter 7 (.yw7) |

## Getting Started

### Prerequisites

- Python 3.9+
- Ollama installed and running
- 8GB+ RAM (16GB recommended)

### Quick Start

```bash
# Clone repository
git clone https://github.com/troymroberts/AiBookWriter4.git
cd AiBookWriter4

# Install dependencies
pip install -r requirements.txt

# Pull required models
ollama pull qwen2.5:1.5b

# Run web interface
streamlit run app.py
```

For detailed setup instructions, see [Setup Guide](setup/SETUP.md).

## Project Structure

```
AiBookWriter4/
├── docs/               # Documentation (you are here)
│   ├── architecture/   # System architecture docs
│   ├── setup/          # Setup and deployment guides
│   ├── api/            # API reference documentation
│   └── ywriter7/       # yWriter integration docs
├── agents/             # AI agent implementations
├── config/
│   ├── genres/         # Genre configuration files
│   └── prompts/        # Agent prompt templates
├── tools/              # CrewAI tools
├── ywriter7/           # Embedded yWriter library
├── test/               # Unit and integration tests
├── output/             # Generated content
├── app.py              # Streamlit web UI
├── main.py             # CLI entry point
├── config.yaml         # Main configuration
└── requirements.txt    # Python dependencies
```

## Agent Pipeline

```
User Input → Story Planner → Setting Builder → Outline Creator → Writer
                                                                    ↓
                                              ← Reviser ← Critic ←─┘
```

| Agent | Purpose |
|-------|---------|
| Story Planner | Creates high-level story arcs |
| Setting Builder | Develops world settings and locations |
| Outline Creator | Generates chapter-by-chapter outlines |
| Writer | Produces prose for each chapter |
| Critic | Provides quality feedback |
| Reviser | Refines and polishes content |

## Configuration

### Main Config (`config.yaml`)

```yaml
model_list:
  - model_name: ollama/qwen2.5:1.5b
    litellm_params:
      base_url: http://localhost:11434

genre: literary_fiction
num_chapters: 4
```

### Genre Configs

18 pre-configured genres in `config/genres/`:
- Literary Fiction, Fantasy, Science Fiction
- Historical Fiction, Romance, Thriller, Mystery
- Young Adult, Non-Fiction, Philosophy
- And more...

Each genre configures 40+ parameters controlling narrative style, pacing, and thematic elements.

## Supported Models

| Model | Size | Recommended For |
|-------|------|-----------------|
| `qwen2.5:1.5b` | 1.5B | Fast drafts |
| `deepseek-r1:1.5b` | 1.5B | Story planning |
| `llama3:8b` | 8B | General writing |
| `llama3:70b` | 70B | High-quality prose |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

See repository LICENSE file.

## Support

- GitHub Issues: [AiBookWriter4 Issues](https://github.com/troymroberts/AiBookWriter4/issues)
