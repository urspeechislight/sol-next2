# Council submission — information architecture lens (2026-07-02)

## Diagnosis: the page has the wrong job

The landing page is a devotional digest sitting in front of a research
library. A first-time visitor arrives with librarian questions: What is this
collection? How large is it, and what does it cover? Is my tradition, author,
or book in here? Where do I start? The current page answers none of these.
It answers only "what should I read for ninety seconds today," which is a
returning-user ritual, not a front door.

Ranked failures:

1. Scale and scope are invisible. Nothing says how many works or volumes,
   and the domain taxonomy, the corpus's strongest orientation asset with
   bilingual labels, blurbs, and counts already served by `/api/domains`,
   appears nowhere. The library hides its own shelves.
2. Search is demoted to chrome. On a corpus of this size, search is a
   primary task. The 40% empty viewport below the cards is the symptom: the
   page ran out of things to say because its identity is wrong.
3. No re-entry path. A scholar working through a multi-volume work gets no
   "continue reading," so every visit restarts from zero.
4. Whole capabilities are unadvertised: rijāl data, canonical collections,
   and the graph never surface on the home page.

The daily content is good material in the wrong role: keep it as one module,
remove it as the identity.

## Nav

Browse · Qurʾān · Graph, plus the persistent header search with its scope
menu. No "Search" nav item: the visible field is the affordance. "Today"
content moves onto the landing page itself; it needs no nav slot because the
logo already leads there. Both `/` and the logo point to the landing page.

## Landing structure

Fold 1: orientation and entry: identity statement with live counts, search,
domain tiles deep-linking into Browse, and a conditional continue-reading
bar. Fold 2: today's reading, compressed: verse and hadith with their deep
links; chronicles and calendar collapse to one slim strip. Fold 3: ways
deeper: notable works, canonical collections, a graph teaser, and a footer
stating scope and provenance.

## References

- al-Maktaba al-Shamela: category grid with live book counts + prominent
  search; borrow counts-on-tiles.
- Chinese Text Project (ctext.org): taxonomy-as-homepage with parallel
  bilingual labels.
- Perseus / Scaife Viewer: state collection extent up front; two clicks to
  an actual text.
