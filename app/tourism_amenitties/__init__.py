"""Top-level package for tourism amenitties.

Expose lightweight helpers used by the application package (kept minimal
to avoid circular imports during app startup).
"""
from .registry import redis_configure

__all__ = ["redis_configure"]
