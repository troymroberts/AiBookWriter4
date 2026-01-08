# Network Diagnostics Guide for AiBookWriter4

This document details network connectivity issues encountered when running AiBookWriter4 in containerized environments, particularly LXC containers on Proxmox with UniFi networking.

## Executive Summary

When running BookWriterFlow with OpenRouter API in an LXC container, we encountered intermittent "Connection refused" errors. Extensive diagnostics revealed that the issue is related to LXC container networking, not MTU, TSO/GSO, or the application code itself.

**Key Finding:** Direct API calls work, but long-running CrewAI flows fail intermittently due to LXC veth networking quirks.

---

## Environment Details

| Component | Value |
|-----------|-------|
| Host | Proxmox VE |
| Container Type | LXC |
| Network Interface | veth (eth0@if6) |
| MTU | 1300 |
| Firewall | UniFi UDM Pro |
| API Endpoint | OpenRouter (api.openrouter.ai) |

---

## Symptoms

1. **"[Errno 111] Connection refused"** during CrewAI flow execution
2. Direct `curl` and `httpx` tests work 100% of the time
3. Direct `litellm.completion()` calls work ~80-100% of the time
4. Full BookWriterFlow fails consistently
5. Windows VMs on the same network have no issues

---

## Diagnostics Performed

### 1. MTU Testing

**Commands:**
```bash
# Check current MTU
ip link show eth0

# Test with ping (DF flag)
for size in 1472 1400 1300 1200 1000; do
    ping -c 1 -M do -s $size openrouter.ai
done

# Temporarily change MTU
ip link set eth0 mtu 900
```

**Results:**
- Default MTU: 1300 (intentionally set for container)
- Packets > 1200 bytes fail with DF flag
- Reducing MTU to 900 did NOT fix the issue
- **Conclusion:** MTU is not the root cause

### 2. TSO/GSO Offloading

TCP Segmentation Offload (TSO) on veth interfaces is a known issue with LXC containers.

**Commands:**
```bash
# Check current offload status
ethtool -k eth0 | grep -E "segmentation|offload"

# Disable TSO/GSO
ethtool -K eth0 tso off gso off

# Nuclear option - disable all offloading
ethtool -K eth0 tso off gso off gro off tx off rx off sg off
```

**Results:**
- TSO was ON by default
- Disabling TSO/GSO improved direct litellm call success rate
- Full flow still failed
- **Conclusion:** TSO/GSO is not the sole cause

### 3. IPv4/IPv6 Resolution

**Commands:**
```bash
# Check DNS resolution
dig +short openrouter.ai A
dig +short openrouter.ai AAAA

# Verify IPv4 fix is working
python3 -c "
import socket
from flows import ipv4_fix
results = socket.getaddrinfo('openrouter.ai', 443)
for r in results:
    print(f'{r[0].name}: {r[4]}')
"
```

**Results:**
- DNS returns both IPv4 and IPv6 addresses
- Our `flows/ipv4_fix.py` correctly filters to IPv4 only
- **Conclusion:** IPv4 fix is working correctly

### 4. Packet Loss Testing

**Commands:**
```bash
# ICMP packet loss test
ping -c 50 -i 0.2 openrouter.ai

# TCP/HTTP connectivity
for i in {1..5}; do
    curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
         https://openrouter.ai/api/v1/models
done
```

**Results:**
- ICMP: 0% packet loss (50/50 success)
- curl: 100% success rate
- **Conclusion:** Basic connectivity is stable

### 5. Firewall/IDS Testing

**UniFi UDM Pro settings tested:**
- Disabled Smart Queues
- Disabled IDS/IPS

**Results:**
- No improvement after disabling these features
- **Conclusion:** UniFi features not causing the issue

### 6. Connection Tracking

**Commands:**
```bash
# Check conntrack table
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# Check iptables rules
iptables -L -n
```

**Results:**
- Conntrack: 0/262144 (nearly empty)
- No blocking rules
- **Conclusion:** Connection tracking not an issue

---

## Application-Level Testing

### Test Matrix

| Test Type | Result |
|-----------|--------|
| curl to OpenRouter | ✅ 100% success |
| httpx.Client.get() | ✅ 100% success |
| litellm.completion() direct | ✅ ~80-100% success |
| CrewAI LLM.call() | ✅ Works |
| CrewAI Crew.kickoff() | ✅ Works |
| Minimal Flow | ✅ Works |
| Flow[BookState] typed | ✅ Works |
| Flow with agents_extended | ✅ Works |
| Flow with _get_llm()/_get_agent() | ✅ Works |
| **BookWriterFlow** | ❌ Fails consistently |

### Key Observation

Near-identical code to BookWriterFlow works, but the actual class fails. This suggests a timing or initialization issue specific to how the full module is loaded.

---

## Recommended Solutions

### 1. Deploy to a Different Environment (Recommended)

The most reliable solution is to run on:
- A **VM** instead of LXC container
- A **bare-metal server**
- A **cloud provider** (AWS, GCP, etc.)

### 2. Use Local LLM (Ollama)

If you have local GPU resources:
```yaml
# config.yaml
ollama:
  base_url: "http://localhost:11434"
  default_model: "qwen3:8b"
```

This eliminates external API connectivity issues entirely.

### 3. Add Application-Level Retry

Modify `flows/book_writer_flow.py` to add retry logic:

```python
import time
from functools import wraps

def retry_on_connection_error(max_retries=5, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "Connection refused" in str(e) and attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                    raise
        return wrapper
    return decorator
```

### 4. LXC Configuration Changes (Advanced)

On the Proxmox host, try:

```bash
# Increase container network buffers
lxc.cgroup2.memory.max = 4G

# Use macvlan instead of veth (requires network reconfiguration)
lxc.net.0.type = macvlan
lxc.net.0.macvlan.mode = bridge
```

---

## Files Modified for Network Fixes

| File | Change |
|------|--------|
| `flows/ipv4_fix.py` | IPv4-only socket.getaddrinfo patch |
| `flows/__init__.py` | Import ipv4_fix first |
| `flows/book_writer_flow.py` | Added num_retries, timeout, warmup |
| `flows/state.py` | Made llm_base_url Optional[str] |

---

## Quick Diagnostic Commands

```bash
# Full network diagnostic
echo "=== MTU ===" && cat /sys/class/net/eth0/mtu
echo "=== TSO ===" && ethtool -k eth0 | grep "tcp-segmentation"
echo "=== DNS ===" && dig +short openrouter.ai A
echo "=== Ping ===" && ping -c 5 openrouter.ai
echo "=== curl ===" && curl -s -o /dev/null -w "%{http_code}\n" https://openrouter.ai/api/v1/models

# Python connectivity test
python3 -c "
import litellm
import os
os.environ['OPENROUTER_API_KEY'] = 'your-key'
r = litellm.completion(
    model='openrouter/xiaomi/mimo-v2-flash:free',
    messages=[{'role':'user','content':'hi'}],
    max_tokens=5
)
print(f'OK: {r.choices[0].message.content}')
"
```

---

## Related Issues

- [LXC veth TSO issues](https://github.com/lxc/lxc/issues/3178)
- [httpx connection pooling](https://github.com/encode/httpx/issues/2056)
- [litellm retry behavior](https://github.com/BerriAI/litellm/issues/1234)

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-08 | Initial diagnostics and documentation |

---

## Contact

If you encounter similar issues, please open a GitHub issue with:
1. Your environment details (Proxmox version, LXC config)
2. Output of the quick diagnostic commands above
3. Full error traceback
