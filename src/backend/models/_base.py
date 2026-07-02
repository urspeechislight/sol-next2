"""The shared pydantic base for every serving DTO.

One home for model config: every response model is immutable, declared once
here instead of 27 repeated ``model_config`` lines across the model files.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Immutable base for all response models."""

    model_config = ConfigDict(frozen=True)
