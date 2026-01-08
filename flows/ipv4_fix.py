"""
IPv4 Network Fix

This module patches Python's socket.getaddrinfo to use IPv4 only.
Import this module FIRST before any other imports that use network connections.

Usage:
    import flows.ipv4_fix  # Just importing applies the fix

    # Or explicitly call:
    from flows.ipv4_fix import ensure_ipv4
    ensure_ipv4()

Problem:
    Some environments have IPv6 addresses in DNS but no IPv6 connectivity.
    This causes "[Errno 97] Address family not supported by protocol" errors
    when httpx/requests tries to connect using IPv6.

Solution:
    Filter getaddrinfo results to only return IPv4 (AF_INET) addresses.
"""

import socket

_original_getaddrinfo = None
_ipv4_fix_applied = False


def _getaddrinfo_ipv4_only(*args, **kwargs):
    """Filter getaddrinfo to return only IPv4 addresses"""
    responses = _original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]


def ensure_ipv4():
    """Apply the IPv4-only fix if not already applied"""
    global _original_getaddrinfo, _ipv4_fix_applied

    if _ipv4_fix_applied:
        return

    _original_getaddrinfo = socket.getaddrinfo
    socket.getaddrinfo = _getaddrinfo_ipv4_only
    _ipv4_fix_applied = True


def restore_ipv6():
    """Restore original getaddrinfo behavior"""
    global _ipv4_fix_applied

    if _original_getaddrinfo and _ipv4_fix_applied:
        socket.getaddrinfo = _original_getaddrinfo
        _ipv4_fix_applied = False


# Auto-apply on import
ensure_ipv4()
