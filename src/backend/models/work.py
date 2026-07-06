"""Pydantic DTO for a volume-folded work.

The catalogue stores one :class:`~backend.models.book.Book` row per physical
volume; a multi-volume work therefore appears as many rows sharing a URN stem
(``VdFfCzwY_01``, ``VdFfCzwY_02`` -> stem ``VdFfCzwY``). A ``Work`` is those
rows folded into one entry: the shared bibliographic fields come from
:class:`~backend.models.book.BibRecord`: so the Library lists works, not volumes.
"""

from __future__ import annotations

from pydantic import Field, computed_field

from backend.models.book import CANONICAL_TIERS, BibRecord


class Work(BibRecord):
    """One work, folded across the volumes that share its URN stem. ``page_count``
    is summed across the folded volumes."""

    stem: str = Field(description="URN stem shared by the work's volumes; the work key.")
    volume_count: int = Field(ge=1, description="Number of volumes folded into this work.")
    volumes: list[str] = Field(description="Member volume URNs, ordered by volume number.")
    first_urn: str = Field(description="URN of the first volume; opening the work opens this.")

    @computed_field(
        description=(
            "Editorial-rank tier derived from `canonical`, 0 = most authoritative; "
            "null when unranked. Served so client-side ordering and server-side "
            "`sort=canonical` paging share one tier table instead of each owning a copy."
        )
    )
    @property
    def canonical_tier(self) -> int | None:
        """The work's tier in ``CANONICAL_TIERS``, or None when unranked."""
        return None if self.canonical is None else CANONICAL_TIERS[self.canonical]
