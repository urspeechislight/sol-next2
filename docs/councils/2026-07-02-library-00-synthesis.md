# Library council — synthesis (2026-07-02)

Four reviewers (catalog IA, editorial continuity, data feasibility, browsing
journey) examined the Library screen after the owner asked for: a hero that
shows the highlighted books plural, no "Begin here" anywhere, clearer
era/author/volumes browsing (the volumes view was "a dump"), and visual
continuity with the new landing folio.

## Converged diagnosis

1. Closed accordions destroyed scent: a 941-work category read as 15 shut
   drawers. "By volumes" was a sort masquerading as a view. Author grouping
   by prolificness surfaced modern institutional authors over the classics
   (top 5 authors hold 8-13% of big scopes).
2. The 600-work client cap made counts WRONG: five categories and every
   domain exceed it; in shia-fiqh-8th-century seven of nine century counts
   were wrong and 124 of 325 authors vanished. Full fetches measure cheap
   (2,278 works in 0.55s).
3. `sort=` on /api/works was silently ignored (fail-loud violation).
4. The one-at-a-time carousel hid its own collection; the card grids broke
   the landing's open-composition + fihrist-row language.
5. Canonical tier is binary (207 primary_reference / 9,075 secondary), rich
   enough for domain shelves (8-47 each) but empty in 11 of 39 categories.

## Adopted design

- "Foundational works · أمهات الكتب": a static shelf of up to six works
  visible at once on a gold shelf line, hairline book edges, category chips
  in domain rooms (the shelf doubles as a map), opening at the first TOC
  entry. Hidden when a scope has no primary references; never padded from
  the secondary tier. Dropped at CORPUS level after live inspection showed
  the upstream canonical_status field mis-ranks there (Galen as a primary
  reference with a year-1 death date, while al-Kāfī carries no rank).
- "Begin here" deleted; the canonical claim became an inline gold ✻ mark
  and a Foundational filter chip.
- One honest list with combinable facets: era chips with true counts
  (Undated first-class), author filter, Foundational toggle, explicit sort
  (era / title / author / largest). Era sort renders open century sections
  headed by apparatus rules; load-more pages of 100 with a persistent
  "Showing X of Y" line. The 600 cap removed; scopes page to their total.
- Compact one-line work rows (EN voice, dotted leader, mono margin, AR
  spine); domain cards and category cards became IndexRow contents rows,
  a design-system component now shared with the landing's fihrist band.
- Backend: /api/works honors sort= (death_year_ah undated-last, title_ar,
  volume_count) and 422s unknown values.

## Data flags for upstream

canonical_status quality (classical canon unranked, outliers ranked);
death_year 1 artifacts on ancient translated authors; 336 title+author
pairs split across stems (fold misses) visible as repeated rows in century
sections.
