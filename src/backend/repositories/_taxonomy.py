"""Static taxonomy loader + derived lookups: 7 domains x 39 categories.

The structure (slugs, labels) is authored in ``data/taxonomy.json``; per-category
work/volume counts are overlaid from the live catalogue by the domains repo. The
Sunni / Shia / shared TRADITION of a category is derived here, once, from its
slug, so client and server never diverge on the sectarian axis.

Fiqh madhabs whose slug carries no ``sunni-`` / ``shia-`` prefix are mapped to
a fixed tradition explicitly in ``_SUNNI_MADHABS`` / ``_SHIA_MADHABS``.
``DOMAIN_OF`` maps each category slug to its domain id and ``_CATEGORIES_IN``
maps each domain id to its category slugs, both derived once from ``DOMAINS``.
"""

from __future__ import annotations

from typing import get_args

from backend.models.domain import Domain, Tradition
from backend.repositories._data_loader import load_json

_SUNNI_MADHABS: frozenset[str] = frozenset(
    {"hanafi-fiqh", "maliki-fiqh", "shafii-fiqh", "hanbali-fiqh", "zahiri-fiqh"}
)
_SHIA_MADHABS: frozenset[str] = frozenset({"zaidi-fiqh"})


def tradition_of(slug: str) -> Tradition:
    """Sunni / Shia / shared for a category slug. The sunni-/shia- prefix decides
    the sectarian pairs; the madhab maps cover the prefix-less fiqh schools;
    everything non-sectarian (Qurʾanic sciences, language, biography, ...) is
    shared and stays visible under any tradition lens."""
    if slug.startswith("sunni-") or slug in _SUNNI_MADHABS:
        return "sunni"
    if slug.startswith("shia-") or slug in _SHIA_MADHABS:
        return "shia"
    return "shared"


def _load() -> tuple[Domain, ...]:
    """Parse data/taxonomy.json into typed Domain models."""
    raw = load_json("taxonomy.json")
    return tuple(Domain.model_validate(entry) for entry in raw)


DOMAINS: tuple[Domain, ...] = _load()

DOMAIN_OF: dict[str, str] = {c.slug: d.id for d in DOMAINS for c in d.categories}
_CATEGORIES_IN: dict[str, tuple[str, ...]] = {
    d.id: tuple(c.slug for c in d.categories) for d in DOMAINS
}


def categories_in(domain_id: str) -> tuple[str, ...]:
    """Category slugs grouped under a domain id (empty tuple if unknown)."""
    return _CATEGORIES_IN.get(domain_id, ())


_VALID_TRADITIONS: frozenset[str] = frozenset(get_args(Tradition))


def is_known_domain(domain_id: str) -> bool:
    """True if ``domain_id`` is a real domain in the taxonomy. Lets the API reject
    an unknown ``?domain=`` with 422 instead of silently returning an empty list."""
    return domain_id in _CATEGORIES_IN


def is_known_category(slug: str) -> bool:
    """True if ``slug`` is a real category in the taxonomy. Lets the API reject an
    unknown ``?category=`` with 422 instead of silently filtering to an empty list."""
    return slug in DOMAIN_OF


def is_known_tradition(tradition: str) -> bool:
    """True if ``tradition`` is one of the taxonomy's Tradition values (sunni, shia,
    shared), derived from the Literal so the two stacks can't drift. Lets the API
    reject an unknown ``?tradition=`` with 422."""
    return tradition in _VALID_TRADITIONS
