"""Repository for the domain/category taxonomy.

The taxonomy structure (slugs, labels) is authored statically in
``_taxonomy.DOMAINS``; this overlays each category's real ``count`` (works),
``volume_count``, and ``tradition`` from the live catalogue so the rail numbers
always equal the work-list totals.
"""

from __future__ import annotations

from backend.models.domain import Category, Domain
from backend.repositories import _taxonomy
from backend.repositories import books as books_repo


def _overlay(category: Category, stats: dict[str, tuple[int, int]]) -> Category:
    """Replace a category's seeded count with real work/volume counts + tradition."""
    works_n, vols_n = stats.get(category.slug, (0, 0))
    return category.model_copy(
        update={
            "count": works_n,
            "volume_count": vols_n,
            "tradition": _taxonomy.tradition_of(category.slug),
        }
    )


def list_domains() -> list[Domain]:
    """Return all domains with their categories, counts + tradition overlaid from
    the live catalogue. Stable order."""
    stats = books_repo.category_stats()
    return [
        domain.model_copy(update={"categories": [_overlay(c, stats) for c in domain.categories]})
        for domain in _taxonomy.DOMAINS
    ]
