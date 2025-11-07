# Enhanced Workflow Usage Guide

## Quick Start

### First Time Run

```bash
# Run with defaults (10 chapters, science fiction)
python test_complete_workflow_v2.py

# Customize project
python test_complete_workflow_v2.py --project MyNovel --genre "fantasy" --chapters 15
```

### Resume After Failure

```bash
# Automatically resumes from last checkpoint
python test_complete_workflow_v2.py --project MyNovel --resume
```

### Check Status

```bash
# View detailed status
python test_complete_workflow_v2.py --project MyNovel --status
```

---

## Command Line Options

```
python test_complete_workflow_v2.py [OPTIONS]

Options:
  --project NAME        Project name (default: Ten_Chapter_Novel)
  --genre GENRE         Novel genre (default: science fiction)
  --chapters N          Number of chapters (default: 10)
  --resume              Resume from checkpoint
  --status              Show project status and exit
  -h, --help            Show help message
```

---

## Pause & Resume

### Method 1: Ctrl+C (Recommended)

Press `Ctrl+C` at any time during execution:
- Saves checkpoint automatically
- Shows resume command
- Exits gracefully

```
^C
⏸️  Received SIGINT. Saving checkpoint...
✅ Checkpoint saved successfully
📍 Resume with: python test_complete_workflow_v2.py --project MyNovel --resume
👋 Exiting gracefully...
```

### Method 2: Pause File (Remote/Automated)

Create a pause file to trigger pause at next checkpoint:

```bash
# Create pause file
python -m workflow.controller create MyNovel

# Workflow will pause at next checkpoint
# Resume normally with --resume
```

### Method 3: Error-Induced Pause

If workflow fails due to error:
- Checkpoint is automatically saved
- Resume with `--resume` flag
- Failed step will be retried

---

## Understanding Checkpoints

### What Gets Saved

Checkpoints save to: `output/{project_name}_workflow_checkpoint.json`

Contains:
- Completed workflow steps
- Current/failed step
- Scene-level progress (written/edited)
- Error history
- API usage statistics
- Provider usage metrics

### When Checkpoints Are Saved

- ✅ After each major workflow step completes
- ✅ After each scene is written
- ✅ After each scene is edited
- ✅ On Ctrl+C interrupt
- ✅ On error/exception
- ✅ On pause file detection

### Resume Behavior

When resuming:
- ✅ Skips completed steps
- ✅ Continues from exact scene where stopped
- ✅ Retries failed steps with backoff
- ✅ Uses same configuration
- ✅ Preserves error history

---

## Error Handling & Resilience

### Automatic Retries

Each step automatically retries on failure:
- **Default**: 3 retry attempts
- **Backoff**: Exponential (5s, 10s, 20s)
- **Validation**: Empty response detection
- **Recovery**: Provider fallback on persistent failures

### Provider Fallback

If primary provider fails, automatically tries alternatives:

```
groq fails → tries anthropic → tries gemini → tries openrouter
```

Fallback chains defined in `workflow/resilience.py`

### Empty Response Handling

Detects and handles empty/None responses from LLM:
- Validates response length (minimum 10 chars)
- Checks for error patterns
- Retries up to 3 times
- Logs detailed error information

### Per-Scene Isolation

Scene failures don't kill entire workflow:
- ✅ Failed scene marked as `[Scene writing failed: error]`
- ✅ Workflow continues with next scene
- ✅ Error logged for review
- ✅ Can manually retry individual scenes later

---

## Status Reports

### Viewing Status

```bash
python test_complete_workflow_v2.py --project MyNovel --status
```

### Status Output

```
================================================================================
📊 Workflow Status: MyNovel
================================================================================
Progress: 62.5%

Completed Steps:
  ✅ story_planning
  ✅ character_creation
  ✅ location_creation
  ✅ chapter_outlining
  ✅ scene_structuring

Current Step:
  ⏳ None

Next Step:
  ⏭️  prose_writing

Statistics:
  API Calls: 87
  Errors: 2
  Scenes Written: 12
  Scenes Edited: 0

Provider Usage:
  groq: 78 calls
  anthropic: 9 calls
================================================================================
```

---

## Common Scenarios

### Scenario 1: Network Interruption During Writing

**Problem**: Internet drops during scene writing

**What Happens**:
1. Current scene write fails
2. Retry with exponential backoff (3 attempts)
3. If all fail, checkpoint saves
4. Error logged with context

**Recovery**:
```bash
python test_complete_workflow_v2.py --project MyNovel --resume
# Skips completed scenes
# Retries failed scene
```

---

### Scenario 2: LLM Returns Empty Response

**Problem**: LLM API returns 200 OK but empty content

**What Happens**:
1. Empty response detected by validator
2. Automatic retry (up to 3 times)
3. If persistent, tries fallback provider
4. If all fail, checkpoint saves

**Recovery**:
```bash
# Auto-recovery happens internally
# If manual intervention needed:
python test_complete_workflow_v2.py --project MyNovel --resume
```

---

### Scenario 3: Rate Limit Hit

**Problem**: Too many requests to LLM provider

**What Happens**:
1. Rate limiter detects approaching limit
2. Pre-emptively waits before request
3. If rate limit hit anyway, exponential backoff
4. Automatic retry after backoff period

**No Manual Intervention Needed** - handled automatically

---

### Scenario 4: Need to Stop for the Night

**Problem**: Want to pause overnight

**Solution**:
```bash
# Press Ctrl+C
^C
⏸️  Received SIGINT. Saving checkpoint...
✅ Checkpoint saved

# Next morning
python test_complete_workflow_v2.py --project MyNovel --resume
```

---

### Scenario 5: Provider Completely Down

**Problem**: Groq API unavailable

**What Happens**:
1. Initial request fails
2. Retry with backoff (3 attempts)
3. Switch to fallback provider (Anthropic)
4. Continue with fallback
5. Logs provider switch

**Check Logs**:
```
❌ Provider groq failed: Connection error
🔧 Attempting to create LLM with provider: anthropic
✅ Successfully created LLM with anthropic
```

---

### Scenario 6: Want to Review Partial Novel

**Problem**: Workflow at 50%, want to see progress

**Check Status**:
```bash
python test_complete_workflow_v2.py --project MyNovel --status
```

**Open yWriter7 File**:
```bash
# File location
output/my_novel.yw7

# Open in yWriter7 or compatible editor
# Partially written scenes will be visible
```

---

## Advanced Usage

### Custom Checkpoint Location

Checkpoints save to `output/` by default. To change:

```python
from workflow import WorkflowState

state = WorkflowState.load("MyNovel", checkpoint_dir="custom/path")
state.save(checkpoint_dir="custom/path")
```

### Manual Scene Retry

If specific scenes failed:

1. Check status to see which scenes failed
2. Resume normally - failed scenes will be retried
3. Or manually edit `sceneContent` in yWriter7 file

### Switching Providers Mid-Workflow

Environment variables control provider:

```bash
# Start with Groq
export DEFAULT_LLM_PROVIDER=groq
python test_complete_workflow_v2.py --project MyNovel

# Pause (Ctrl+C)

# Switch to Anthropic
export DEFAULT_LLM_PROVIDER=anthropic
python test_complete_workflow_v2.py --project MyNovel --resume
```

### Monitoring Progress Programmatically

```python
from workflow import WorkflowState

state = WorkflowState.load("MyNovel")
if state:
    progress = state.get_progress_percentage()
    print(f"Progress: {progress}%")

    if state.failed_step:
        print(f"Failed at: {state.failed_step}")

    print(f"Scenes written: {len(state.scenes_written)}")
```

---

## Troubleshooting

### "No checkpoint found"

**Cause**: Project hasn't been run before or checkpoint deleted

**Solution**:
```bash
# Remove --resume flag and start fresh
python test_complete_workflow_v2.py --project MyNovel
```

---

### "Checkpoint corrupted"

**Cause**: JSON file corrupted or incomplete

**Solution**:
```bash
# Backup checkpoint
cp output/MyNovel_workflow_checkpoint.json output/MyNovel_backup.json

# Try manual fix or start fresh
python test_complete_workflow_v2.py --project MyNovel
```

---

### "All providers failed"

**Cause**: API keys missing or invalid for all providers

**Solution**:
```bash
# Check .env file
cat .env | grep API_KEY

# Ensure at least one provider has valid key
export GROQ_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
```

---

### "Scene writing very slow"

**Cause**: Rate limiting or slow provider

**Solution**:
1. Check rate limits in logs
2. Switch to faster provider
3. Reduce max_tokens if possible
4. Use smaller model

---

## Performance Tips

### Faster Execution

1. **Use faster models**:
   - Groq: `llama-3.1-8b-instant` (fastest)
   - Gemini: `gemini-2.0-flash-exp`
   - Anthropic: `claude-3-haiku-20240307`

2. **Reduce context**:
   - Lower `max_tokens` in agent configs
   - Shorter scene descriptions

3. **Parallel providers**:
   - Use different providers for different agents
   - Set via environment variables

### Cost Optimization

1. **Free tiers first**:
   - Groq (free): Use for most steps
   - Gemini (free): Backup
   - Anthropic (paid): Only for critical steps

2. **Checkpoint frequently**:
   - Avoid re-running expensive steps
   - Resume on failures

3. **Monitor usage**:
   ```bash
   python test_complete_workflow_v2.py --project MyNovel --status
   # Check "Provider Usage" section
   ```

---

## Files Created

### Output Directory

```
output/
├── my_novel.yw7                              # yWriter7 novel file
├── MyNovel_workflow_checkpoint.json          # Checkpoint state
└── MyNovel.pause                             # Pause trigger (optional)
```

### Checkpoint Structure

```json
{
  "project_name": "MyNovel",
  "completed_steps": ["story_planning", "character_creation"],
  "current_step": null,
  "failed_step": null,
  "scenes_written": ["sc1", "sc2", "sc3"],
  "scenes_edited": ["sc1", "sc2"],
  "total_api_calls": 42,
  "provider_usage": {
    "groq": 38,
    "anthropic": 4
  },
  "errors": [
    {
      "step": "prose_writing",
      "error": "Connection timeout",
      "timestamp": "2025-11-07T20:30:15"
    }
  ]
}
```

---

## Integration with Original Workflow

### Differences from test_complete_workflow.py

| Feature | Original | Enhanced (v2) |
|---------|----------|---------------|
| Checkpoints | ❌ No | ✅ Yes |
| Resume | ❌ No | ✅ Yes |
| Retry Logic | ❌ No | ✅ Yes (3x) |
| Provider Fallback | ❌ No | ✅ Yes |
| Empty Response Handling | ❌ No | ✅ Yes |
| Ctrl+C Handling | ❌ Kills | ✅ Saves |
| Per-Scene Isolation | ❌ No | ✅ Yes |
| Error Logging | ⚠️ Basic | ✅ Detailed |
| Status Command | ❌ No | ✅ Yes |

### Migration from Original

To migrate existing project:
1. Run original workflow to completion (or as far as possible)
2. Project saved in `output/project.yw7`
3. Enhanced workflow can continue from this file
4. Or start fresh with enhanced workflow

---

## Best Practices

### 1. Use Version Control

```bash
# Track checkpoints
git add output/*_workflow_checkpoint.json
git commit -m "Checkpoint at step 5"
```

### 2. Monitor Logs

```bash
# Save logs to file
python test_complete_workflow_v2.py 2>&1 | tee workflow.log
```

### 3. Test with Small Project First

```bash
# Test with 3 chapters first
python test_complete_workflow_v2.py --project TestNovel --chapters 3
```

### 4. Backup Before Resume

```bash
# Backup before resuming
cp output/MyNovel_workflow_checkpoint.json output/MyNovel_checkpoint_backup.json
cp output/my_novel.yw7 output/my_novel_backup.yw7
```

### 5. Check Status Regularly

```bash
# In another terminal
watch -n 30 "python test_complete_workflow_v2.py --project MyNovel --status"
```

---

## Support

### Getting Help

1. Check `RESILIENCE_DESIGN.md` for architecture
2. Check `ARCHITECTURE_QUICK_REF.md` for codebase reference
3. Review logs for error details
4. Check checkpoint JSON for state

### Reporting Issues

Include:
1. Command used
2. Checkpoint JSON (if exists)
3. Error logs
4. Steps to reproduce

---

*For more details, see:*
- `RESILIENCE_DESIGN.md` - Design specification
- `ARCHITECTURE_DETAILED.md` - Full architecture
- `IMPLEMENTATION_STATUS.md` - Current status
