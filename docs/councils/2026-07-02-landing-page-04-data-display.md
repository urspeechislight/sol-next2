# Council submission — data display / content strategy lens (2026-07-02)

All claims verified against live payloads on 2026-07-02.

## Inventory

- Taxonomy (`/api/domains`): 7 domains, 39 categories, bilingual labels,
  blurbs, per-category counts. A complete blurbed sitemap in one call; the
  strongest landing-ready payload. One zero-count category (devotional /
  Manuscripts) must be hidden.
- Daily (`/api/daily`): richer than the page suggested: two cross-tradition
  tafsīr excerpts, a graded hadith with parallels, and an unused book pick
  carrying a written curatorial rationale and an `open_to` anchor. The
  highest-value unused field in the system.
- Continue reading: no API; localStorage plus `/api/books/{urn}` suffices.
- Search: real depth (a single fiqh category returned five-figure hits for a
  common term); the field earns body-level presence.
- Chronicles/Calendar: no endpoint existed; the cards rendered a hardcoded
  frontend table. Moved into the served contract or cut.
- Graph: no API; any landing teaser is a sentence plus a link, never a fake
  visualization.

## Display forms

Taxonomy as a typeset fihrist, not a treemap: a treemap turns a library into
an infographic. The verse as a hero blockquote, since a card equalizes and a
blockquote sanctifies. Corpus scale as one prose sentence with live sums,
never animated stat blocks. The book pick as an editorial shelf item quoting
its own rationale; no cover images exist anywhere in the API, so never mock
covers. Resume as a slim strip present only when a position exists.

## Data-quality risks found

- `/api/daily` was a static fixture dated 17 November 2024.
- Deep-link URNs in the daily payload were fabricated; most resolved to
  nothing and one collided with an unrelated real book.
- Count drift: the served catalog had resurrected the 588 purged Persian
  volumes after an index rebuild; whatever number the landing page speaks
  must come from the same live source the rail reads.
- `title_en` values are transliterations, not translations, and occasionally
  null: every work reference must render a bilingual lockup.
- `death_year_ce` is null corpus-wide: display AH years only.
