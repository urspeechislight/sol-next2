"""ID generation — the only place ``uuid``/``ulid``/``secrets`` may be called.

Centralizing here lets us swap UUID4 for ULID in one place when ordering
matters, and makes ID-format conventions (prefixed, ``user_abc123``, etc.)
inspectable in one file.
"""

from __future__ import annotations

import uuid


def new_request_id() -> str:
    """Generate a fresh request-correlation id."""
    return uuid.uuid4().hex


def new_resource_id() -> str:
    """Generate a fresh opaque resource id."""
    return uuid.uuid4().hex
