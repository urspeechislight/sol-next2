# Landing page council — synthesis (2026-07-02)

Four parallel reviewers (information architecture, editorial craft, reader
journey, data display) examined the landing page after the owner reported it
"lacking heavily" and constrained the nav: no "Today" menu item, Browse first.

## Converged diagnosis

1. Wrong job: a devotional digest in front of a research library. The page
   never answered "what is this, how large, how serious, where do I start."
2. Four equal cards, zero hierarchy: the banned identical-card-grid in mild
   disguise. The verse, the product's most sacred content, was one quadrant.
3. All middle: no opening statement, no close; 40% of the viewport trailed
   off as bare ground.
4. The Arabic never reached display scale; the English word "Today's" got
   the display moment. Voice hierarchy inverted.
5. Scale and taxonomy invisible; rijāl, canonical registries, and the graph
   unadvertised; no re-entry path; search only in chrome.
6. Ornament too timid to register.

## Data findings (verified against the live API during the council)

- `/api/daily` was a frozen fixture dated 17 November 2024; the rotation key
  was dead data; the Hijri date was computed client-side over a stale payload.
- 7 of 8 rotation URNs (and every daily deep link) were fabricated
  identifiers that resolved to nothing; one collided with an unrelated book.
- Chronicles/Calendar cards had no API; their tables were hardcoded frontend
  placeholder data.
- The June 30 index rebuild resurrected all 588 volumes of the Persian
  purge because the ingest had no exclusion mechanism.

## Adopted plan

A manuscript folio: illuminated ʿunwān + basmala masthead with live counts,
conditional resume strip, the verse as matn with hadith + book-of-the-day in
the hāshiya margin, a one-line almanac, the fihrist of domains as a contents
band linking into Browse, and a colophon close. Color strategy Committed:
gold graduates from accent to structure. One orchestrated load under 1.2s.
Nav: Browse · Qurʾān · Graph; the logo and `/` carry the landing.

Stage 1 (data preflight) preceded all visuals: catalog exclusion manifest +
rebuild, pooled date-rotated daily.json with corpus-verified URNs and page
anchors, scripture text composed from the Qurʾān repository at serve time,
and the almanac moved into the served data contract (`/api/almanac`).
