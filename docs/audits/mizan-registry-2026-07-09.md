# Mizan al-I'tidal name registry — build and validation

Date: 2026-07-09. Branch: `feature/wt-ba4a09a4`.

## What this is

A standalone name registry for al-Dhahabi's _Mizan al-I'tidal fi Naqd al-Rijal_.
Every numbered narrator biography in the four volumes is segmented into its own
entry, and the opening name of each is decomposed into the five classical
onomastic components so that two narrators who share a lineage stay separable by
their kunya and nisba. Entry 576 is the motivating case: entries 576, 577, and
578 all read `أحمد بن محمد بن عيسى`, and only the trailing attribution tells
them apart (576 `أبو العباس / المصري / الحافظ, النحاس`, 577 `الواعظ`, 578
`السكوني`).

## Source and artifacts

- Source: `data/corpus.db`, book `ميزان الاعتدال`, volumes `Ww5X29dJ_01` through
  `Ww5X29dJ_04` (2,650 pages).
- Builder: `scripts/build_mizan_registry.py`, with segmentation and
  decomposition in `backend.build.mizan` and `backend.build.mizan_names`.
- Outputs: `data/mizan_registry.db` (table `entry`) and
  `data/mizan_registry.json` (decoded array).

Each row carries
`entry_no, volume, page, name, ism, nasab[], kunya, nisba[], laqab[], sigla[]`
plus a `snippet` for provenance. The `sigla` field holds the transmitter symbols
the edition prints in brackets (`[م ، د ، س]`), removed from the name and kept
separately.

## Segmentation

Entry numbers climb monotonically across the four volumes from 2 to 9945 and
reset nowhere. The raw text also carries footnote numbers, cross-reference
numbers, and year figures in the same `N -` shape, so a forward-tolerance filter
cascades into mass rejection after the first wide gap. The true chain is
recovered instead as the longest strictly-increasing subsequence of the matched
numbers, which locks onto the dense `+1` spine and drops the stray numbers
regardless of position.

Result: **9,875 entries** (volume 1: 2,564; volume 2: 2,734; volume 3: 2,695;
volume 4: 1,882). Of the numbers in [2, 9945], 69 are absent. Those 69 are
genuine skips in the edition's numbering (for example 61-64, 86-87, 173), not
extraction failures: no `N -` marker exists for them anywhere in the text.

## Decomposition

The parser walks name tokens from the entry start (ism, then each `بن`/`ابن`
ancestor, then a kunya, then definite-article attributions) and stops at the
first token that opens biography (a narration verb, a grading term, `مولى`,
`صاحب`, `نزيل`, a date). A `عبد`/`عبيد` head merges with a following article
word only (`عبد الله`), and a kunya is built recursively (`أبو عبد الله`), so a
biography word after `عبيد` is never absorbed. An attribution ending in the
nisba suffix (`ي`, `ية`, `اني`) or matching the place/tribe pattern is a nisba;
a known title, epithet, or profession (`الحافظ`, `الإمام`, `العطار`, `النحاس`)
is a laqab.

Field coverage across the 9,875 entries: ism 9,854; nasab 9,053; nisba 4,887;
kunya 1,374; laqab 1,270; sigla 3,688. No entry has an empty name.

## Validation against the local Arabic model

A 41-entry sample spread evenly across the whole book (every ~240th entry) was
decomposed independently by the domain-tuned local model `ask_ornith` and
compared field by field with the deterministic parser.

- Exact agreement on all five fields: ~34 of 41.
- Of the ~7 disagreements, the deterministic parser is correct in 3 (the model
  hallucinated a kunya from `عن أبي هريرة`, misfiled a nisba into the nasab
  chain, and pulled `طرطوس` in from `نزيل طرطوس`), the model is better in 3 (a
  bare-word nickname `كريزان`, a second nisba after `ثم`, and a leading
  connective `و`), and 1 is a nisba-versus-laqab judgement call where both
  readings are defensible (`الأسود`).

Deterministic field accuracy on the sample is therefore about 90 percent and on
par with the model. Two parser bugs the sample surfaced were fixed before this
report: a truncated `أبو عبد الله` kunya that leaked `الله` into laqab, and a
`عبيد` head that swallowed the following biography word.

## Known limitations

- **Nisba versus laqab is a judgement call for profession-epithets.** `الواعظ`
  is stored as a laqab under the scholarly reading; the model reads it as a
  nisba. Both fields are on every row, so disambiguation holds either way.
- **A relocation nisba after a sentence break is not captured.**
  `الأصبهاني . ثم البغدادي` yields only `الأصبهاني`; the parser does not cross a
  period to extend a name, because crossing sentence boundaries bleeds biography
  into the name more often than it recovers a second nisba. The no-period form
  `الأصبهاني ثم البغدادي` is captured.
- **A bare-word laqab or nickname without the article** (`كريزان`) is not
  captured, since a bare word after the name is biography far more often than a
  laqab.
- **A leading connective `و`** on a list-continuation sub-entry stays on the ism
  (`ومحمد`).
