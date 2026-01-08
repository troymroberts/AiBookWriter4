# Canon System Module
# Versioned fact database for story consistency

"""
This module implements the Canon system from SPEC.md Section 7.2:
- Hard canon database with contradiction detection
- Versioned facts with branch support
- Integration with Continuity Agent

Canon Entry Structure:
- fact_id: unique identifier
- content: "Sarah has blue eyes"
- established_in: scene_id where first mentioned
- version: branch identifier
- supersedes: previous fact_id (if retconned)
"""

from .canon_manager import CanonManager

__all__ = ["CanonManager"]
