# Workflow Resilience & Pause/Resume Design

## Current State Analysis

### Error Points Identified

#### 1. **LLM Response Failures**
**Location**: Deep within CrewAI agent execution
**Error**: `ValueError: Invalid response from LLM call - None or empty`
**Cause**:
- API returns successful HTTP 200 but empty content
- Not caught by rate limiter (different from rate limit errors)
- CrewAI's internal validation catches it

**Current Handling**: None - workflow crashes

#### 2. **Network Errors**
**Location**: `config/rate_limiter.py` - LLM API calls
**Current Handling**:
- Exponential backoff with jitter
- Max 5 retries for network errors
- Works for: timeout, connection errors, 502, 503

**Gap**: Only applies to decorated functions, not CrewAI internal calls

#### 3. **Rate Limit Errors**
**Location**: LLM provider APIs
**Current Handling**:
- Pre-request throttling based on usage tracking
- Post-error exponential backoff
- Works well for rate limits

#### 4. **Workflow State Loss**
**Current**: No checkpointing between workflow steps
**Impact**: If Step 5 fails, Steps 1-4 must be re-run
**Cost**: Time + API credits wasted

#### 5. **CrewAI Internal Failures**
**Location**: `crewai/agents/crew_agent_executor.py`
**Types**:
- Agent execution errors
- Task parsing errors
- Tool execution errors

**Current Handling**: Bubbles up to workflow, crashes

---

## Proposed Solutions

### 1. **Workflow-Level Error Handling**

#### A. Step-Level Try/Catch
Wrap each workflow step with error handling:

```python
def run_step_with_retry(step_name, step_func, max_retries=3):
    """Run a workflow step with retry logic."""
    for attempt in range(max_retries):
        try:
            result = step_func()
            save_step_checkpoint(step_name, result)
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Step {step_name} failed (attempt {attempt+1}): {e}")
                wait_time = 2 ** attempt * 5  # 5s, 10s, 20s
                time.sleep(wait_time)
            else:
                logger.error(f"Step {step_name} failed after {max_retries} attempts")
                save_failure_state(step_name, e)
                raise
```

#### B. Provider Fallback Chain
If primary provider fails, try alternatives:

```python
PROVIDER_FALLBACK_CHAIN = {
    "groq": ["anthropic", "gemini", "openrouter"],
    "anthropic": ["groq", "gemini"],
    "gemini": ["groq", "anthropic"]
}

def create_llm_with_fallback(agent_name, preferred_provider):
    """Create LLM with fallback providers."""
    providers = [preferred_provider] + PROVIDER_FALLBACK_CHAIN.get(preferred_provider, [])

    for provider in providers:
        try:
            config.set_provider(provider)
            llm = config.create_llm(agent_name)
            logger.info(f"Using provider: {provider} for {agent_name}")
            return llm, provider
        except Exception as e:
            logger.warning(f"Provider {provider} failed: {e}")
            continue

    raise RuntimeError("All LLM providers failed")
```

#### C. Empty Response Detection & Retry
Add validation before CrewAI processing:

```python
def validate_and_retry_crew_kickoff(crew, max_retries=3):
    """Kickoff crew with validation and retry."""
    for attempt in range(max_retries):
        result = crew.kickoff()

        # Validate result
        if result and str(result).strip():
            return result

        logger.warning(f"Empty response from crew (attempt {attempt+1})")
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt * 3)  # 3s, 6s, 12s

    raise ValueError("Crew returned empty response after all retries")
```

---

### 2. **Enhanced Checkpoint System**

#### A. Workflow State Schema

```python
class WorkflowState:
    """Complete workflow state for pause/resume."""

    def __init__(self, project_name, project_path):
        self.project_name = project_name
        self.project_path = project_path

        # Step completion tracking
        self.completed_steps = []  # ['story_planning', 'character_creation', ...]
        self.current_step = None
        self.failed_step = None

        # Step-specific state
        self.story_arc = None
        self.characters_created = []
        self.locations_created = []
        self.chapters_outlined = []
        self.scenes_structured = []
        self.scenes_written = []
        self.scenes_edited = []

        # Metadata
        self.start_time = None
        self.last_checkpoint_time = None
        self.total_api_calls = 0
        self.provider_usage = {}  # {provider: call_count}

        # Error tracking
        self.errors = []  # [{step, error, timestamp, recovery_action}]

    def save(self):
        """Save to JSON checkpoint file."""
        checkpoint_path = f"{self.project_name}_workflow_checkpoint.json"
        data = {
            'project_name': self.project_name,
            'project_path': self.project_path,
            'completed_steps': self.completed_steps,
            'current_step': self.current_step,
            'failed_step': self.failed_step,
            # ... all state fields
        }
        with open(checkpoint_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Checkpoint saved: {checkpoint_path}")

    @classmethod
    def load(cls, project_name):
        """Load from checkpoint file."""
        checkpoint_path = f"{project_name}_workflow_checkpoint.json"
        if not os.path.exists(checkpoint_path):
            return None

        with open(checkpoint_path, 'r') as f:
            data = json.load(f)

        state = cls(data['project_name'], data['project_path'])
        state.completed_steps = data.get('completed_steps', [])
        # ... restore all fields
        logger.info(f"Checkpoint loaded: {checkpoint_path}")
        return state

    def can_skip_step(self, step_name):
        """Check if step can be skipped (already completed)."""
        return step_name in self.completed_steps

    def mark_step_complete(self, step_name, result_summary=None):
        """Mark a step as completed."""
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)
        self.current_step = None
        self.last_checkpoint_time = datetime.now()
        self.save()
```

#### B. Auto-Checkpoint After Each Step

```python
def run_workflow_with_checkpoints(project_name, genre, num_chapters, resume=True):
    """Run workflow with automatic checkpointing."""

    # Try to resume from checkpoint
    state = WorkflowState.load(project_name) if resume else None
    if not state:
        state = WorkflowState(project_name, f"output/{project_name.lower()}.yw7")
        state.start_time = datetime.now()

    # Step 1: Story Planning
    if not state.can_skip_step('story_planning'):
        state.current_step = 'story_planning'
        state.save()

        story_arc = run_step_with_retry(
            'story_planning',
            lambda: execute_story_planning(state.project_path, genre, num_chapters)
        )

        state.story_arc = story_arc[:500]
        state.mark_step_complete('story_planning')
    else:
        logger.info("⏭️  Skipping story_planning (already completed)")

    # Step 2: Character Creation
    if not state.can_skip_step('character_creation'):
        state.current_step = 'character_creation'
        state.save()

        # ... execute step
        state.mark_step_complete('character_creation')
    else:
        logger.info("⏭️  Skipping character_creation (already completed)")

    # ... continue for all 8 steps
```

---

### 3. **Graceful Degradation Strategies**

#### A. Per-Scene Failure Isolation
Don't let one scene failure kill the entire workflow:

```python
def write_all_scenes_with_isolation(writer, scenes, state):
    """Write scenes with per-scene error handling."""
    results = []

    for scene in scenes:
        try:
            if scene.id in state.scenes_written:
                logger.info(f"⏭️  Skipping {scene.title} (already written)")
                continue

            prose = write_scene_with_retry(writer, scene)
            scene.sceneContent = prose
            state.scenes_written.append(scene.id)
            state.save()  # Checkpoint after each scene
            results.append(('success', scene.id))

        except Exception as e:
            logger.error(f"Failed to write scene {scene.title}: {e}")
            scene.sceneContent = f"[Scene failed to generate: {e}]"
            state.errors.append({
                'step': 'writing',
                'scene_id': scene.id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            state.save()
            results.append(('failed', scene.id, str(e)))

    return results
```

#### B. Partial Success Reporting

```python
def generate_partial_success_report(state):
    """Generate report of partial workflow completion."""
    report = {
        'completed_steps': state.completed_steps,
        'failed_step': state.failed_step,
        'scenes_written': len(state.scenes_written),
        'scenes_failed': len([e for e in state.errors if e['step'] == 'writing']),
        'can_continue': state.failed_step not in ['story_planning', 'character_creation'],
        'next_actions': []
    }

    # Suggest next actions
    if state.failed_step == 'writing':
        report['next_actions'].append("Resume writing from last successful scene")

    if len(state.errors) > 3:
        report['next_actions'].append("Consider switching LLM provider")

    return report
```

---

### 4. **Interactive Resume/Pause**

#### A. Signal Handlers for Graceful Shutdown

```python
import signal

class WorkflowController:
    """Controls workflow execution with pause/resume."""

    def __init__(self, state):
        self.state = state
        self.paused = False
        self.should_stop = False

        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        logger.info("\n⏸️  Pause requested. Saving checkpoint...")
        self.paused = True
        self.state.save()
        logger.info("✅ Checkpoint saved. You can resume later with --resume")
        sys.exit(0)

    def check_pause_file(self):
        """Check for pause file (allows remote pausing)."""
        pause_file = f"{self.state.project_name}.pause"
        if os.path.exists(pause_file):
            logger.info("⏸️  Pause file detected. Saving checkpoint...")
            self.state.save()
            os.remove(pause_file)
            return True
        return False
```

#### B. CLI Resume Support

```python
# In main.py or test_complete_workflow.py
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--project', default='Ten_Chapter_Novel', help='Project name')
    parser.add_argument('--status', action='store_true', help='Show checkpoint status')
    args = parser.parse_args()

    if args.status:
        state = WorkflowState.load(args.project)
        if state:
            print(f"Project: {state.project_name}")
            print(f"Completed: {', '.join(state.completed_steps)}")
            print(f"Current: {state.current_step}")
            print(f"Failed: {state.failed_step}")
        else:
            print("No checkpoint found")
        return

    # Run workflow
    run_workflow_with_checkpoints(
        project_name=args.project,
        genre='science fiction',
        num_chapters=10,
        resume=args.resume
    )
```

---

## Implementation Priority

### Phase 1: Critical Resilience (Week 1)
1. ✅ Wrap each workflow step with try/except
2. ✅ Add WorkflowState class with save/load
3. ✅ Implement checkpoint after each major step
4. ✅ Add step-level retry logic (3 attempts)

### Phase 2: Enhanced Recovery (Week 2)
5. ✅ Per-scene error isolation
6. ✅ Empty response detection & retry
7. ✅ Provider fallback chain
8. ✅ Partial success reporting

### Phase 3: User Control (Week 3)
9. ✅ CLI arguments for --resume, --status
10. ✅ Signal handlers for graceful Ctrl+C
11. ✅ Pause file monitoring
12. ✅ Resume from any step

### Phase 4: Observability (Week 4)
13. Enhanced logging with structured output
14. Progress bar for long operations
15. Estimated time remaining
16. Cost tracking per provider

---

## File Structure After Implementation

```
AiBookWriter4/
├── workflow/
│   ├── __init__.py
│   ├── state.py              # WorkflowState class
│   ├── controller.py         # WorkflowController (pause/resume)
│   ├── resilience.py         # Error handling utilities
│   └── runner.py             # Enhanced workflow runner
├── output/
│   ├── ten_chapter_novel.yw7
│   ├── Ten_Chapter_Novel_workflow_checkpoint.json
│   └── Ten_Chapter_Novel.pause  (optional, for remote pause)
└── test_complete_workflow_v2.py  # Enhanced workflow script
```

---

## Example Usage

### First Run (Normal)
```bash
python test_complete_workflow_v2.py --project MyNovel
# Runs all 8 steps, saves checkpoints after each
```

### Resume After Failure
```bash
python test_complete_workflow_v2.py --project MyNovel --resume
# Skips completed steps, resumes from failure point
```

### Check Status
```bash
python test_complete_workflow_v2.py --project MyNovel --status
# Shows: completed steps, current step, errors
```

### Pause During Execution
```bash
# Option 1: Ctrl+C (gracefully saves checkpoint)
# Option 2: Create pause file
touch output/MyNovel.pause
# Workflow detects it at next checkpoint and pauses
```

---

## Benefits

1. **Resilience**: Workflow survives LLM failures, network issues, empty responses
2. **Cost Savings**: Don't re-run completed steps = fewer API calls
3. **User Control**: Pause/resume at will
4. **Transparency**: Clear status reporting
5. **Flexibility**: Switch providers mid-workflow if needed
6. **Debugging**: Error log with context for each failure
7. **Partial Results**: Even failed workflows produce partial novels

---

## Testing Strategy

1. **Simulated Failures**: Inject errors at each step to test recovery
2. **Provider Switching**: Test fallback chain with unavailable providers
3. **Resume Tests**: Start workflow, kill it, resume multiple times
4. **Empty Response Handling**: Mock empty LLM responses
5. **Long-Running**: Test with 50+ chapter novel
6. **Concurrent**: Multiple workflows running simultaneously

---

## Backward Compatibility

- New workflow runner is separate file (`test_complete_workflow_v2.py`)
- Original workflow still works as-is
- Opt-in via `--resume` flag
- No changes to core agents, tools, or yWriter7 integration
