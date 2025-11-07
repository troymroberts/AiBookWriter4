# Rate Limiting System

## Overview

The AI Book Writer includes a comprehensive rate limiting system that automatically manages API rate limits for all LLM providers (Groq, Anthropic, OpenAI, Gemini, etc.).

**Key Features:**
- ✅ Automatic rate limit detection and enforcement
- ✅ Exponential backoff with jitter on errors
- ✅ Per-minute AND per-day limit tracking
- ✅ Multi-provider support
- ✅ Reads rate limit headers from provider responses (Groq)
- ✅ Transparent - works with all existing code
- ✅ Zero configuration required

---

## How It Works

### Automatic Installation

Rate limiting is **automatically enabled** when you import the config module:

```python
from config import get_llm_config  # Rate limiting installed automatically!
```

All LLM calls throughout the application will now respect rate limits.

### What Gets Tracked

The system tracks:
- **TPM** (Tokens Per Minute) - Token usage in rolling 60-second window
- **RPM** (Requests Per Minute) - Request count in rolling 60-second window
- **TPD** (Tokens Per Day) - Token usage in rolling 24-hour window
- **RPD** (Requests Per Day) - Request count in rolling 24-hour window

### Provider Support

#### Groq (Full Support)
- Tracks all limits (TPM, RPM, TPD, RPD)
- Reads actual limits from response headers
- Auto-updates tracking based on real API responses

**Configured Models:**
```python
"llama-3.3-70b-versatile":   TPM: 12K,  RPM: 30,  TPD: 100K,  RPD: 1K
"llama-3.1-8b-instant":      TPM: 6K,   RPM: 30,  TPD: 500K,  RPD: 14.4K
"llama-4-scout-17b-16e":     TPM: 30K,  RPM: 30,  TPD: 500K,  RPD: 1K
```

#### Anthropic (Tier 1 Limits)
```python
"claude-3-5-sonnet-20241022": TPM: 40K, RPM: 50
"claude-3-haiku-20240307":    TPM: 50K, RPM: 50
```

#### OpenAI (Free Tier)
```python
"gpt-4":          TPM: 10K, RPM: 3
"gpt-3.5-turbo":  TPM: 60K, RPM: 3
```

#### Gemini
```python
"gemini-pro": TPM: 32K, RPM: 2
```

#### Ollama (Local)
- **No rate limiting applied** (local models have no API limits)

---

## Current Groq Rate Limits (Free Tier)

Source: https://console.groq.com/docs/rate-limits (as of 2025-11-07)

| Model | RPM | RPD | TPM | TPD |
|-------|-----|-----|-----|-----|
| llama-3.3-70b-versatile | 30 | 1K | 12K | 100K |
| llama-3.1-8b-instant | 30 | 14.4K | 6K | 500K |
| llama-4-scout-17b-16e | 30 | 1K | 30K | 500K |
| llama-4-maverick-17b-128e | 30 | 1K | 6K | 500K |
| whisper-large-v3 | 20 | 2K | - | - |

---

## Behavior

### Proactive Waiting

Before making an API call, the system checks if the request would exceed limits. If it would, the system **automatically waits** until the limit window resets:

```
[INFO] Rate limit approaching for groq/llama-3.3-70b-versatile. Waiting 12.3s...
```

### Exponential Backoff

If a rate limit error occurs anyway (race condition, network timing, etc.), the system uses **exponential backoff**:

```
Attempt 1: Wait 2s
Attempt 2: Wait 4s
Attempt 3: Wait 8s
Attempt 4: Wait 16s
Attempt 5: Wait 32s
```

### Jitter

Random jitter (±20%) is added to wait times to prevent the "thundering herd" problem when multiple requests hit limits simultaneously.

---

## Usage Examples

### Basic Usage (Automatic)

Rate limiting is automatic - just use your code normally:

```python
from agents.story_planner import StoryPlanner, StoryPlannerConfig

# Rate limiting happens automatically!
planner = StoryPlanner(config=StoryPlannerConfig())
result = planner.run("Create a story about space exploration")
```

### Check Current Usage

```python
from config import get_rate_limiter

limiter = get_rate_limiter()
usage = limiter._get_current_usage("groq", "llama-3.3-70b-versatile")

print(f"Tokens used (minute): {usage['tokens_minute']} / 12000")
print(f"Requests made (minute): {usage['requests_minute']} / 30")
print(f"Tokens used (day): {usage['tokens_day']} / 100000")
print(f"Requests made (day): {usage['requests_day']} / 1000")
```

### Update Rate Limits

If you upgrade to a paid tier or need to adjust limits:

```python
from config import update_rate_limits

# Update for Groq Pro tier (hypothetical)
update_rate_limits(
    provider="groq",
    model="llama-3.3-70b-versatile",
    tpm=60000,  # 60K TPM on pro tier
    rpm=100     # 100 RPM on pro tier
)
```

### Disable Rate Limiting (Testing)

```python
from config.llm_wrapper import uninstall_rate_limiting

# Temporarily disable for testing
uninstall_rate_limiting()

# ... run tests ...

# Re-enable
from config.llm_wrapper import install_rate_limiting
install_rate_limiting()
```

---

## Error Handling

### Rate Limit Errors (429)

Automatically retried with exponential backoff (up to 5 attempts by default):

```
[WARNING] Rate limit hit for groq/llama-3.3-70b-versatile. Backing off for 2.1s (multiplier: 2.0x)
[INFO] Retry 1/5 after 2.1s
```

### Network Errors (503, Connection Timeout)

Automatically retried with simple exponential backoff:

```
[WARNING] Network error for groq/llama-3.3-70b-versatile. Retrying in 2.3s... (1/5)
```

### SSL/TLS Errors

Retried once (these are usually not transient):

```
[ERROR] SSL/TLS error for groq/llama-3.3-70b-versatile: CERTIFICATE_VERIFY_FAILED
[INFO] Retrying once in case of transient SSL issue...
```

---

## Configuration

### Environment Variables

No configuration needed! The system uses smart defaults.

However, you can override:

```bash
# Use different default provider
export DEFAULT_LLM_PROVIDER=groq

# Agent-specific provider override
export AGENT_STORY_PLANNER_PROVIDER=anthropic
```

### Code Configuration

Update `config/rate_limiter.py` to add new models or adjust limits:

```python
RATE_LIMITS = {
    "groq": {
        "your-custom-model": {
            "tpm": 10000,
            "rpm": 50,
            "tpd": 1000000,
            "rpd": 5000,
        },
    },
}
```

---

## Monitoring

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

You'll see detailed rate limiting decisions:

```
[DEBUG] Making rate-limited call to groq/llama-3.3-70b-versatile (estimated 2500 tokens)
[DEBUG] Would exceed TPM limit (10500 + 2500 > 12000). Wait: 15.2s
[INFO] Rate limit approaching for groq/llama-3.3-70b-versatile. Waiting 15.4s...
[DEBUG] Successful call to groq/llama-3.3-70b-versatile (used 2134 tokens)
[DEBUG] Updated rate limits from headers for groq/llama-3.3-70b-versatile: TPM=12000, RPD=1000
```

---

## Advantages Over Manual Rate Limiting

| Feature | Manual Approach | Our System |
|---------|----------------|------------|
| **Setup** | Write custom retry logic per call | Automatic, zero config |
| **Tracking** | Track usage manually | Automatic token/request tracking |
| **Multi-provider** | Separate logic per provider | Unified system |
| **Headers** | Ignore provider headers | Reads and uses real limits |
| **Daily limits** | Often forgotten | Tracked automatically |
| **Jitter** | Easy to forget | Built-in |
| **Transparency** | Modifies call sites | Works with existing code |

---

## Technical Details

### Architecture

```
Application Code
    ↓
LiteLLM completion() [wrapped]
    ↓
rate_limited_completion() [llm_wrapper.py]
    ↓
RateLimiter [rate_limiter.py]
    ├─ Check current usage
    ├─ Calculate wait time if needed
    ├─ Wait with jitter
    ├─ Make API call
    ├─ Extract token usage from response
    ├─ Update rate limiter from headers
    └─ Record usage for future calculations
```

### Token Estimation

For proactive rate limiting, the system estimates token count:

```python
# Rough estimation: 1 token ≈ 4 characters (conservative)
input_tokens = sum(len(msg["content"]) for msg in messages) // 4
estimated_total = input_tokens + max_tokens
```

After the response, actual token usage (from API) replaces the estimate.

### Window Tracking

Uses rolling windows:
- **Minute window**: Entries expire 60 seconds after creation
- **Day window**: Entries expire 24 hours after creation

Cleanup happens before each usage check to keep memory bounded.

---

## Testing

The system includes comprehensive tests:

```bash
# Run rate limiter tests
pytest tests/test_rate_limiter.py

# Test with actual API (will hit real rate limits)
python test_workflow_reduced.py
```

---

## Troubleshooting

### "Still hitting rate limits"

- Check if multiple processes are running (rate limiter is per-process)
- Verify model name matches configuration exactly
- Enable debug logging to see what's happening

### "Waiting too long"

- System is being conservative - you're close to daily limits
- Check usage: `limiter._get_current_usage(provider, model)`
- Consider using a smaller model or spreading work over time

### "Not working with my custom provider"

- Add your provider to `RATE_LIMITS` in `config/rate_limiter.py`
- Or use `update_rate_limits()` programmatically

---

## Future Enhancements

Potential improvements:
- [ ] Persistent rate limit tracking across sessions (Redis/database)
- [ ] Multi-process coordination (shared rate limiter)
- [ ] Web dashboard showing current usage
- [ ] Alert when approaching daily limits
- [ ] Cost tracking alongside rate limits
- [ ] Support for more provider-specific headers (OpenAI, Anthropic)

---

## Summary

The rate limiting system provides **production-ready** rate limit management with:

✅ **Zero configuration** - Works out of the box
✅ **Intelligent** - Reads provider headers, tracks actual usage
✅ **Robust** - Exponential backoff, jitter, comprehensive error handling
✅ **Transparent** - No code changes needed
✅ **Multi-provider** - Groq, Anthropic, OpenAI, Gemini, Ollama

Just import and use your agents normally - rate limiting happens automatically! 🎉
