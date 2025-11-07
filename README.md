# AI Book Writer 4

An agentic AI book writing application that uses multiple specialized AI agents to collaboratively write books. Integrates with yWriter7 file format for professional novel writing workflows.

## 🚀 Features

- **Multi-Agent Collaboration**: Specialized AI agents work together to create compelling stories
  - Story Planner, Setting Builder, Outline Creator
  - Writer, Editor, Critic
  - Character Creator, Relationship Architect, Lore Builder

- **Multiple LLM Providers**: Flexible support for various AI providers
  - **Groq** - Fast & free API (llama-3.3-70b, mixtral-8x7b) **← Recommended for testing!**
  - **Ollama** - Run models locally (llama3, deepseek, qwen, etc.)
  - **Anthropic Claude** - Use Claude 3.5 Sonnet, Opus, or Haiku
  - **Google Gemini** - Access Gemini 2.0 Flash, 1.5 Pro, etc.

- **yWriter7 Integration**: Full read/write support for yWriter7 project files
  - Chapters, scenes, characters, locations, items
  - Project notes and metadata
  - Professional author workflow compatibility

- **Genre-Specific Configuration**: 18+ genre templates with customized parameters
  - Literary Fiction, Fantasy/Sci-Fi, Thriller/Mystery, Romance
  - Historical Fiction, Young Adult
  - Textbooks: Chemistry, Physics, Math, Computer Science, Engineering
  - Philosophy: Esoteric Philosophy, Mysticism, Consciousness Studies

- **Dual Interface**:
  - **CLI** - Command-line workflow for automation
  - **Streamlit UI** - Interactive web interface with real-time streaming

## 📋 Requirements

- Python 3.10 - 3.13
- **For Groq (Recommended)**: Free API key from https://console.groq.com/
- For local models: Ollama installed and running
- For Claude: Anthropic API key
- For Gemini: Google API key

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AiBookWriter4
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and configure your preferred LLM provider:

**For Groq (Recommended - Fast & Free!):**
```bash
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

**For Ollama (Local Models):**
```bash
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**For Anthropic Claude:**
```bash
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**For Google Gemini:**
```bash
DEFAULT_LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### 5. Install Ollama (Optional - for local models)

If using local models with Ollama:

1. Install Ollama from https://ollama.ai
2. Pull your preferred model:
   ```bash
   ollama pull llama3.2
   ollama pull deepseek-r1:1.5b
   ollama pull qwen2.5:1.5b
   ```

## 🎯 Quick Start

### Using the CLI

```bash
python main.py
```

### Using the Streamlit UI

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

## 📁 Project Structure

```
AiBookWriter4/
├── agents/              # AI agent definitions
│   ├── story_planner.py
│   ├── writer.py
│   ├── editor.py
│   └── ...
├── config/              # Configuration files
│   ├── genres/          # Genre-specific configs
│   ├── prompts/         # Agent prompt templates
│   ├── llm_config.py    # LLM provider configuration
│   └── config.yaml      # Application settings
├── tools/               # CrewAI tools for yWriter7
│   └── ywriter_tools.py
├── ywriter7/           # yWriter7 integration
│   ├── model/          # Data models
│   └── yw/             # File I/O
├── app.py              # Streamlit UI
├── main.py             # CLI interface
├── requirements.txt    # Python dependencies
├── .env                # Your configuration (not in git)
└── .env.example        # Example configuration
```

## ⚙️ Configuration

### Agent Configuration

Edit `config.yaml` to customize agent behavior:

```yaml
agents:
  story_planner:
    role: "Story Architect & Narrative Designer"
    goal: "Create compelling story arcs..."
    temperature: 0.7
    max_tokens: 4096
    # Optional: override provider for this agent
    # provider: "anthropic"
    # model: "claude-3-5-sonnet-20241022"
```

### Workflow Configuration

Define how agents collaborate in crews:

```yaml
workflows:
  story_planning:
    description: "Initial story development phase"
    process: "sequential"
    agents:
      - story_planner
      - setting_builder
      - outline_creator
```

### Genre Configuration

Genre templates are in `config/genres/`. Each genre has customized parameters:

```python
# config/genres/literary_fiction.py
CHARACTER_DEPTH = 0.9
CONFLICT_INTENSITY = 0.6
PACING_SPEED = 0.4
THEME_COMPLEXITY = 0.9
# ... and more
```

## 🔧 Advanced Usage

### Using Different Providers for Different Agents

You can mix providers - for example, use Claude for planning and local models for writing:

In `.env`:
```bash
DEFAULT_LLM_PROVIDER=ollama
AGENT_STORY_PLANNER_PROVIDER=anthropic
AGENT_WRITER_PROVIDER=ollama
```

### Agent-Specific Models

Configure different models for different agents in `.env`:

```bash
OLLAMA_MODEL_STORY_PLANNER=deepseek-r1:1.5b
OLLAMA_MODEL_WRITER=llama3:8b-instruct
OLLAMA_MODEL_EDITOR=qwen2.5:1.5b
```

## 📚 Usage Examples

### Example 1: Generate a Story Arc

```python
from config.llm_config import get_llm_config

# Initialize configuration
config = get_llm_config()

# Get agent config
story_planner_config = config.get_agent_config('story_planner')

# Create LLM for this agent
llm = config.create_llm('story_planner')

# Agent will use the configured provider (Ollama, Anthropic, or Gemini)
```

### Example 2: Create a yWriter7 Project

```python
from tools.ywriter_tools import WriteProjectNoteTool, CreateChapterTool

# Initialize tools
note_tool = WriteProjectNoteTool()
chapter_tool = CreateChapterTool()

# Write project note
note_tool._run(
    yw7_path="my_novel.yw7",
    title="Story Arc",
    content="Generated story arc content..."
)

# Create chapter
chapter_tool._run(
    yw7_path="my_novel.yw7",
    title="Chapter 1: The Beginning",
    description="Introduction to the protagonist..."
)
```

## 🐛 Troubleshooting

### Ollama Connection Issues

If you get connection errors with Ollama:

1. Make sure Ollama is running: `ollama serve`
2. Check the base URL in `.env` matches your Ollama server
3. Verify the model is downloaded: `ollama list`

### API Key Issues

For Anthropic or Gemini:

1. Verify your API key is correct in `.env`
2. Check you have credits/quota remaining
3. Ensure the model name is valid

### Import Errors

If you get import errors:

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## 🗺️ Roadmap

### Phase 1: ✅ Infrastructure (Complete)
- [x] Update to latest CrewAI
- [x] Multi-provider LLM support (Ollama, Anthropic, Gemini)
- [x] Unified configuration system

### Phase 2: 🚧 Agent Refactoring (In Progress)
- [ ] Convert agents to CrewAI Agent classes
- [ ] Define proper crews for workflows
- [ ] Implement agent collaboration
- [ ] Add memory/context sharing

### Phase 3: 📝 Future Enhancements
- [ ] Additional output formats (DOCX, PDF, Markdown)
- [ ] Enhanced UI with progress tracking
- [ ] Agent conversation visualization
- [ ] Advanced character relationship graphs
- [ ] Plot structure analysis tools

## 📄 License

[Add your license here]

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This project is in active development. Phase 1 (infrastructure) is complete. Phase 2 (agent refactoring) is next.
