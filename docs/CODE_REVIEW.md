# AiBookWriter4 Code Review

**Date:** 2025-12-29
**Reviewer:** Claude Code
**Status:** Project Non-Functional - Major Issues Identified

---

## Executive Summary

The AiBookWriter4 project has significant architectural and implementation issues that prevent it from functioning. The codebase shows evidence of rapid prototyping without integration testing. Key problems include:

1. **Severely outdated dependencies** (CrewAI 0.100.0 vs current 1.7.2)
2. **Missing critical files** (tests reference non-existent `crew.py`)
3. **API mismatches** (app.py calls methods that don't exist)
4. **Broken template syntax** (Jinja2 `{{}}` vs LangChain `{}`)
5. **Inconsistent agent implementations** (mix of patterns, some incomplete)

---

## Critical Issues (Blockers)

### 1. Dependency Version Crisis

| Package | Current | Latest | Gap |
|---------|---------|--------|-----|
| `crewai` | 0.100.0 | 1.7.2 | **Major version change** |
| `langchain` | >=0.0.325 | 1.2.0 | **Major version change** |
| `langchain-ollama` | >=0.0.1 | 1.0.1 | **Major version change** |

**Impact:** The CrewAI API has changed significantly. The current code uses deprecated patterns that will not work with modern versions.

**Location:** `requirements.txt:1-4`

**Recommendation:** Lock to specific working versions or upgrade all code to latest APIs.

---

### 2. Missing `crew.py` Module

**Issue:** Tests import from a `crew` module that doesn't exist.

```python
# test/test_agent_communication.py:3
from crew import BookWritingCrew  # File does not exist!
```

**Impact:** All tests fail with `ModuleNotFoundError`.

**Location:** `test/test_agent_communication.py:3`

**Recommendation:** Either create `crew.py` with `BookWritingCrew` class or remove/rewrite tests.

---

### 3. Method Does Not Exist - `OutlineCreator.run_information_gathering_task()`

**Issue:** `app.py` calls a method that doesn't exist on `OutlineCreator`.

```python
# app.py:200-201
outline_stream = outline_creator.run_information_gathering_task(
    task_description=outline_task_description,
    project_notes_content=full_story_arc_output
)
```

But `OutlineCreator` extends `crewai.Agent` which has no such method:

```python
# agents/outline_creator.py:88
class OutlineCreator(Agent):  # CrewAI Agent - no run_information_gathering_task!
```

**Impact:** Application crashes when "Start Book Creation Process" is clicked.

**Location:** `app.py:200-201`, `agents/outline_creator.py:88`

**Recommendation:** Either:
- Add `run_information_gathering_task()` method to `OutlineCreator`
- Convert `OutlineCreator` to LangChain pattern like `SettingBuilder`
- Use CrewAI's `Task` and `Crew` execution pattern

---

### 4. Broken Prompt Template Syntax

**Issue:** YAML prompts use Jinja2 `{{variable}}` syntax, but LangChain's `ChatPromptTemplate` uses `{variable}`.

```yaml
# config/prompts/setting_builder.yaml:11
{{outline_context}}   # WRONG - Jinja2 syntax

# Should be:
{outline_context}     # Correct - LangChain syntax
```

**Affected Files:**
- `config/prompts/setting_builder.yaml` - `{{outline_context}}`, `{{task_description}}`
- `config/prompts/writer.yaml` - `{{outline_context}}`, `{{genre_config}}`, `{{genre_config.get(...)}}`
- `config/prompts/lore_builder.yaml` - `{{genre}}`, `{{story_arc}}`

**Impact:** Variables are not substituted; prompts contain literal `{{variable}}` text.

**Location:** `config/prompts/*.yaml`

**Recommendation:** Change all `{{var}}` to `{var}` in YAML prompt files.

---

### 5. Python Code in YAML Templates

**Issue:** Writer prompt tries to call Python methods inside YAML template:

```yaml
# config/prompts/writer.yaml:20
{{genre_config.get('MIN_WORDS_PER_CHAPTER', 1600)}}
```

**Impact:** This doesn't execute Python - it's passed as literal string.

**Location:** `config/prompts/writer.yaml:20`

**Recommendation:** Pass pre-computed values to template, or use a proper templating engine.

---

### 6. CrewAI LLM API Mismatch

**Issue:** Code passes `system_template`, `prompt_template`, `response_template` to `crewai.llm.LLM()`:

```python
# agents/critic.py:52-60
return LLM(
    base_url=config.llm_endpoint,
    model=config.llm_model,
    ...
    system_template=config.system_template,  # WRONG - belongs on Agent
    prompt_template=config.prompt_template,   # WRONG - belongs on Agent
    response_template=config.response_template,  # WRONG - belongs on Agent
)
```

Per current CrewAI docs, these parameters belong on the `Agent` class, not `LLM`.

**Affected Agents:**
- `agents/critic.py:52-60`
- `agents/plot_agent.py:49-59`
- `agents/relationship_architect.py:47-57`
- `agents/editor.py:52-62`
- `agents/reviser.py:49-59`
- `agents/outline_creator.py:126-138`

**Location:** All CrewAI-based agents

**Recommendation:** Move template parameters to `Agent.__init__()` calls.

---

### 7. CharacterCreator Has No LLM

**Issue:** `CharacterCreator` config defines `temperature` and `top_p` but never creates or uses an LLM:

```python
# agents/character_creator.py:24-61
class CharacterCreator(Agent):
    def __init__(self, config: CharacterCreatorConfig):
        super().__init__(
            role='Character Creator',
            ...
            # NO llm= parameter!
            tools=[]
        )
```

**Impact:** Agent will use default/global LLM settings or fail.

**Location:** `agents/character_creator.py:27-61`

**Recommendation:** Add `llm=self.create_llm(config)` pattern like other agents.

---

## High Priority Issues

### 8. f-strings with Brace Escaping Confusion

**Issue:** Some agent goals/backstories use f-strings with `{{}}`:

```python
# agents/critic.py:32
goal=f"""
    ... for a {{num_chapters}}-chapter story.
    ... {{genre_config.get('CRITIQUE_STYLE')}}.
"""
```

The `f""` prefix makes this an f-string, so `{{}}` becomes literal `{}` NOT variable substitution.

**Impact:** Goals contain literal `{num_chapters}` text instead of actual values.

**Affected Agents:** `critic.py`, `editor.py`, `reviser.py`, `plot_agent.py`, `outline_creator.py`

**Recommendation:** Either:
- Remove `f` prefix and use `.format()` later
- Pass variables properly at runtime
- Use CrewAI's task description for dynamic content

---

### 9. Inconsistent Agent Initialization Patterns

**Issue:** Three different patterns are used for agents:

**Pattern A - LangChain with Config Object:**
```python
# story_planner.py, setting_builder.py
def __init__(self, config: StoryPlannerConfig, prompts_dir, genre, num_chapters):
```

**Pattern B - LangChain with Direct Parameters:**
```python
# lore_builder.py, writer.py
def __init__(self, base_url, model, prompts_dir, genre, ...):
```

**Pattern C - CrewAI Agent:**
```python
# character_creator.py, critic.py, etc.
class Critic(Agent):
    def __init__(self, config: CriticConfig):
```

**Impact:** Confusing codebase, inconsistent behavior, maintenance nightmare.

**Recommendation:** Standardize on one pattern (recommend Pattern A with Config objects).

---

### 10. SettingBuilder Returns String, Not Stream

**Issue:** `app.py` expects streaming from `SettingBuilder`:

```python
# app.py:187-192
setting_stream = setting_builder.run_information_gathering_task(...)
for chunk in setting_stream:  # Expects iterator
```

But `SettingBuilder.run_information_gathering_task()` uses `chain.invoke()` which returns a string:

```python
# agents/setting_builder.py:77-84
def run_information_gathering_task(self, task_description, outline_context):
    chain = self.prompt | self.llm
    result = chain.invoke({...})  # Returns string, not iterator!
    return result
```

**Impact:** `for chunk in setting_stream` will iterate over characters, not meaningful chunks.

**Location:** `agents/setting_builder.py:77-84`

**Recommendation:** Use `chain.stream()` instead of `chain.invoke()` and `yield` chunks.

---

### 11. Hardcoded IP Addresses

**Issue:** Several files hardcode specific IP addresses:

```python
# Multiple agents
llm_endpoint: str = Field(default="http://10.1.1.47:11434", ...)

# outline_creator.py has different default
llm_endpoint: str = Field(default="http://localhost:11444", ...)  # Note: 11444 not 11434
```

**Affected Files:**
- `agents/critic.py:6`
- `agents/plot_agent.py:6`
- `agents/relationship_architect.py:6`
- `agents/editor.py:6`
- `agents/reviser.py:6`
- `agents/outline_creator.py:35` (wrong port!)

**Recommendation:** Use `http://localhost:11434` consistently or read from config/environment.

---

### 12. OutlineCreator Constructor Mismatch

**Issue:** `app.py` passes `streaming=True` to `OutlineCreator`:

```python
# app.py:168-169
outline_creator = OutlineCreator(
    config=outline_creator_config, streaming=True)
```

But `OutlineCreator.__init__` doesn't accept `streaming`:

```python
# agents/outline_creator.py:93
def __init__(self, config: OutlineCreatorConfig, tools: Optional[List[BaseTool]] = None):
```

**Impact:** `TypeError: __init__() got an unexpected keyword argument 'streaming'`

**Location:** `app.py:168-169`, `agents/outline_creator.py:93`

**Recommendation:** Either add `streaming` parameter to `OutlineCreator` or remove from `app.py`.

---

## Medium Priority Issues

### 13. Unused `context_window` in OutlineCreatorConfig

**Issue:** `OutlineCreatorConfig` in `app.py` sets `context_window` but the class doesn't have that field:

```python
# app.py:166
context_window=st.session_state.get("outline_creator_context", 8192)
```

**Location:** `app.py:166`

---

### 14. Redundant Assignment

```python
# agents/setting_builder.py:64
prompts_dir = prompts_dir  # Useless
```

---

### 15. Trailing Character in YAML

```yaml
# config/prompts/setting_builder.yaml:26
Be imaginative and descriptive to create truly compelling and believable settings.A
```

Note the trailing `A` at the end.

---

### 16. Missing Genre Config Integration

**Issue:** Genre configs (e.g., `literary_fiction.py`) define extensive parameters like:
- `CHARACTER_DEPTH = 0.9`
- `SHOW_DONT_TELL = 1.0`
- `NARRATIVE_STYLE = "third_person"`

But agents don't read or use these values. The `load_genre_config()` function in `main.py` is only called in a test block.

**Location:** `main.py:116-123`

**Recommendation:** Integrate genre config into the agent workflow.

---

### 17. `initial_prompt` Never Used

**Issue:** `app.py` collects `initial_prompt` from user but never passes it to agents:

```python
# app.py:236-240
initial_prompt = st.text_area(
    "Initial Story Idea/Prompt",
    value="A story about a solitary lighthouse keeper...",
)
```

This value is never stored in session state or passed to the workflow.

**Location:** `app.py:236-240`

---

### 18. Incomplete yWriter Tools

**Issue:** Some tools are imported but may not be fully implemented:

```python
# agents/outline_creator.py:21-28
from tools.ywriter_tools import (
    ReadProjectNotesTool,
    WriteProjectNoteTool,
    CreateChapterTool,
    ReadOutlineTool,
    ReadCharactersTool,
    ReadLocationsTool,
)
```

But `ReadItemsTool` is mentioned in docs but not in this import.

---

## Low Priority Issues

### 19. Debug Print Statements

Multiple debug prints left in production code:

```python
# main.py:51
print(f"DEBUG main.py: num_chapters_config from config.yaml: {num_chapters_config}")

# agents/story_planner.py:79
print(f"DEBUG agents/story_planner.py: StoryPlanner __init__ received num_chapters: {num_chapters}")
```

**Recommendation:** Remove or convert to proper logging.

---

### 20. Empty Directories

```
workflows/  # Empty
tasks/      # Empty
```

These suggest planned features that were never implemented.

---

### 21. Duplicate Config File

Two config files exist:
- `config.yaml` (root)
- `config/config.yaml`

May cause confusion about which is used.

---

## Recommendations Summary

### Immediate Actions (to make project run):

1. **Upgrade or lock dependencies** - Decide on CrewAI version strategy
2. **Fix prompt template syntax** - Change `{{var}}` to `{var}`
3. **Add missing method** - `OutlineCreator.run_information_gathering_task()`
4. **Fix streaming** - `SettingBuilder` should use `chain.stream()`
5. **Remove invalid kwargs** - `streaming=True` from `OutlineCreator` call
6. **Create or remove crew.py** - Fix test imports

### Short-term Improvements:

1. **Standardize agent patterns** - Pick one initialization style
2. **Move template params** - From `LLM()` to `Agent()` for CrewAI agents
3. **Add LLM to CharacterCreator** - Currently has no model
4. **Fix hardcoded IPs** - Use config/environment variables
5. **Integrate genre configs** - Actually use the 40+ parameters defined

### Long-term Refactoring:

1. **Decide on framework** - CrewAI OR LangChain, not both mixed
2. **Implement proper workflow** - Use CrewAI's `Crew` and `Task` pattern
3. **Add integration tests** - Test the full pipeline
4. **Add error handling** - Graceful failures with user feedback
5. **Implement missing features** - yWriter export, chapter writing, revision loop

---

## Files Requiring Changes

| Priority | File | Issues |
|----------|------|--------|
| Critical | `requirements.txt` | Outdated versions |
| Critical | `app.py` | Calls non-existent methods, invalid kwargs |
| Critical | `agents/outline_creator.py` | Missing method, invalid LLM params |
| Critical | `config/prompts/*.yaml` | Wrong template syntax |
| High | `agents/setting_builder.py` | Returns string not stream |
| High | `agents/character_creator.py` | No LLM configured |
| High | `agents/critic.py` | Template params on LLM, f-string issues |
| High | `agents/editor.py` | Template params on LLM, f-string issues |
| High | `agents/reviser.py` | Template params on LLM, f-string issues |
| High | `agents/plot_agent.py` | Template params on LLM, f-string issues |
| High | `agents/relationship_architect.py` | Template params on LLM |
| Medium | `test/test_agent_communication.py` | References missing crew.py |
| Medium | `main.py` | Debug prints, genre config not integrated |
| Low | `agents/story_planner.py` | Debug prints |

---

## Conclusion

The project requires significant refactoring before it can function. The core workflow (`app.py`) will crash immediately due to method/API mismatches. The recommended approach is:

1. First, fix the critical blockers to get basic functionality working
2. Then, standardize the architecture (choose CrewAI OR LangChain patterns)
3. Finally, implement the full pipeline with proper error handling

Estimated effort: **2-4 days** for basic functionality, **1-2 weeks** for production-ready state.
