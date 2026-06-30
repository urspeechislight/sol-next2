"""Handler library.

Each module exports a single ``check(ctx) -> Decision`` callable. Handlers
must be deterministic, side-effect-free, and complete in well under 1s on a
typical file.
"""
