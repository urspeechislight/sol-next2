"""Pydantic DTOs for the domain/category taxonomy.

Domain := { id, label, label_ar, blurb, categories: [Category] }
Category := { slug, label, label_ar, count, volume_count, tradition }

``slug``/``label``/``label_ar`` are authored in ``data/taxonomy.json``;
``count`` (works), ``volume_count`` (physical volumes), and ``tradition`` are
overlaid from the live catalogue by the domains repository, so the numbers the
rail shows always equal the work-list totals.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.models._base import FrozenModel

Tradition = Literal["sunni", "shia", "shared"]


class Category(FrozenModel):
    """One category leaf under a domain in the IA taxonomy."""

    slug: str = Field(description="URL-safe identifier, e.g. 'shia-hadith-fiqh'.")
    label: str = Field(description="English label.")
    label_ar: str = Field(description="Arabic label.")
    count: int = Field(default=0, ge=0, description="Folded works in this category.")
    volume_count: int = Field(default=0, ge=0, description="Physical volumes in this category.")
    tradition: Tradition = Field(default="shared", description="Sunni, Shia, or shared/neutral.")


class Domain(FrozenModel):
    """One top-level domain of knowledge (e.g. Hadith, Fiqh, Theology)."""

    id: str = Field(description="Domain id, e.g. 'hadith'.")
    label: str = Field(description="English label.")
    label_ar: str = Field(description="Arabic label.")
    blurb: str = Field(description="One-sentence editorial summary of the domain.")
    categories: list[Category] = Field(description="Categories grouped under this domain.")
