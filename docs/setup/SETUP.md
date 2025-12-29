# Setup & Deployment Guide

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.9+ | Runtime environment |
| Ollama | Latest | Local LLM inference server |
| Git | Any | Version control |
| RAM | 8GB+ | Model loading (16GB recommended) |
| GPU | Optional | CUDA-compatible for acceleration |

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/troymroberts/AiBookWriter4.git
cd AiBookWriter4
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and Configure Ollama

#### Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download from [ollama.com](https://ollama.com/download)

#### Start Ollama Server

```bash
ollama serve
```

#### Pull Required Models

```bash
# Recommended models
ollama pull deepseek-r1:1.5b
ollama pull llama3:8b-instruct
ollama pull qwen2.5:1.5b
ollama pull deepseek-coder:1.3b
```

### 5. Verify Installation

```bash
# Check Ollama is running
ollama list

# Run test script
python ollama_langchain_test.py
```

## Configuration

### Main Configuration (`config.yaml`)

```yaml
model_list:
  - model_name: ollama/qwen2.5:1.5b
    litellm_params:
      base_url: http://localhost:11434

genre: literary_fiction
prompts_file: config/prompts.yaml
num_chapters: 4
```

### Configuration Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model_list` | list | - | Available LLM models and endpoints |
| `genre` | string | `literary_fiction` | Default genre selection |
| `prompts_file` | string | `config/prompts.yaml` | Path to prompts config |
| `num_chapters` | int | `4` | Default number of chapters |

### Environment Variables (`.env`)

Create a `.env` file for sensitive configuration:

```bash
# Optional: Override Ollama endpoint
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Set logging level
LOG_LEVEL=INFO
```

## Running the Application

### Web Interface (Streamlit)

```bash
streamlit run app.py
```

Access at: `http://localhost:8501`

#### Web UI Features:

1. **Project Setup Tab**
   - Select genre from 18 available options
   - Enter story idea/prompt
   - Set number of chapters (1-30)
   - Add additional instructions

2. **Agent Configuration Tab**
   - Select model for each agent
   - Adjust temperature (0.0-1.0)
   - Set max tokens (100-4000)
   - Configure top-p and context window

3. **Process Monitor Tab**
   - Real-time streaming output
   - View agent progress

4. **Output Tab**
   - Inspect final story arc
   - Review world settings
   - Examine chapter outlines

### Command Line Interface

```bash
python main.py
```

The CLI will:
1. Load configuration from `config.yaml`
2. Initialize Story Planner agent
3. Generate story arc
4. Save output to `output/story_arc.txt`

## Network Configuration

### Remote Ollama Server

If running Ollama on a different machine:

1. Update `config.yaml`:
```yaml
model_list:
  - model_name: ollama/qwen2.5:1.5b
    litellm_params:
      base_url: http://10.1.1.47:11434
```

2. Ensure Ollama is accessible:
```bash
# On Ollama server, bind to all interfaces
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

3. Check firewall allows port 11434

### Docker Deployment (Future)

```dockerfile
# Example Dockerfile (not included in repo)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

## Available Genres

The following genres are pre-configured in `config/genres/`:

| Genre | File | Description |
|-------|------|-------------|
| Literary Fiction | `literary_fiction.py` | Character-driven, thematic depth |
| Fantasy | `fantasy.py` | World-building, magic systems |
| Science Fiction | `science_fiction.py` | Tech-focused narratives |
| Historical Fiction | `historical_fiction.py` | Period accuracy |
| Romance | `romance.py` | Relationship-focused |
| Thriller | `thriller.py` | Suspense and tension |
| Mystery | `mystery.py` | Investigation plots |
| Young Adult | `young_adult.py` | Teen-focused themes |
| Non-Fiction | `non_fiction.py` | Factual content |
| Philosophy | `philosophy.py` | Conceptual exploration |
| Mysticism | `mysticism.py` | Spiritual themes |
| Consciousness Studies | `consciousness_studies.py` | Mind exploration |
| Comparative Religion | `comparative_religion.py` | Religious analysis |
| Esoteric Philosophy | `esoteric_philosophy.py` | Hidden knowledge |
| Chemistry Textbook | `chemistry_textbook.py` | Educational |
| CS Textbook | `computer_science_textbook.py` | Educational |
| Engineering Textbook | `engineering_textbook.py` | Educational |
| Math/Physics Textbook | `mathematics_physics_textbook.py` | Educational |

## Troubleshooting

### Ollama Connection Issues

**Error:** "Cannot connect to Ollama"

```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve

# Check port
curl http://localhost:11434/api/tags
```

### Model Not Found

**Error:** "Model not found"

```bash
# List available models
ollama list

# Pull missing model
ollama pull <model-name>
```

### Memory Issues

**Error:** "Out of memory"

1. Use smaller models (e.g., `qwen2.5:1.5b` instead of `llama3:70b`)
2. Reduce `max_tokens` in agent configuration
3. Adjust `MEMORY_LIMIT` in genre config
4. Close other applications

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Performance Tuning

### Model Selection Guide

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `qwen2.5:1.5b` | Small | Fast | Good | Quick drafts |
| `deepseek-r1:1.5b` | Small | Fast | Good | Story planning |
| `deepseek-coder:1.3b` | Small | Fast | Good | Technical content |
| `llama3:8b` | Medium | Moderate | Better | General writing |
| `llama3:70b` | Large | Slow | Best | Final prose |

### Recommended Configurations

**Fast Drafting:**
```yaml
temperature: 0.8
max_tokens: 2000
context_window: 4096
```

**Quality Writing:**
```yaml
temperature: 0.7
max_tokens: 4000
context_window: 8192
```

**Precision Mode:**
```yaml
temperature: 0.5
max_tokens: 3000
context_window: 16384
```

## Updating

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
```
