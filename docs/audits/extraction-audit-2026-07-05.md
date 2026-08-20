# Extraction audit — Phase 3 `manuscript.db` (inspector at `:8767/#/extraction`)

**Date:** 2026-07-05 **Auditor session:** feature/wt-f799d5ce **Artifact
audited:** `sol-next2-wt/wt-9db19a37/data/manuscript.db` (the DB the `:8767`
inspector actually reads, via backend `:8002`) **Pipeline audited:**
`src/backend/pipeline/` in worktree `wt-9db19a37` (segment → extract), build
script `scripts/build_manuscript_index.py` **Books in the DB:** `iz32WsFJ_05`
(Bihar al-Anwar vol. 5, a _kalam_/theology volume — divine justice, jabr vs.
tafwid), `mEbWpeQ5_01`, `mEbWpeQ5_02` (Kanāsh volumes)

**Method:** direct SQL over the `span` / `entity` / `unit` tables; every span's
`patterns`, `metadata`, `hierarchy_path` inspected against source;
classification rules read from `config/sol.yaml` and
`pipeline/segment.py::route_behavior`; content completeness cross-checked
against the source corpus JSON
(`~/code/sol/data/books/shia-hadith-general/...v05...json`).

**Purpose:** identify and catalogue extraction issues only — what each is, why
it is an issue, and where it comes from. No fixes are applied here. Each entry
carries a stable `EX-NN` id for the later fix pass.

---

## Verified NON-issues (ruled out — do not re-audit)

These were suspected but disproven, recorded so nobody spends effort on them:

- **Page coverage is complete.** All 339 source pages of Bihar vol. 5 fall
  inside some span's `[page_start, page_end]` range; 0 source pages are blank.
  (An earlier count of "77 dropped pages" was an artifact of counting only span
  endpoints, not the interior pages of multi-page spans.)
- **Content is not truncated.** Total extracted span text is 492,250 chars vs.
  494,182 source chars after whitespace normalization — a 0.996 ratio. No silent
  body-text loss.

---

## Root mechanism (shared cause of EX-01…EX-05)

`route_behavior()` (`pipeline/segment.py`) assigns **exactly one** `behavior`
per print-paragraph span. Rules from `config/sol.yaml` are sorted by `priority`
descending and evaluated first-match-wins; a rule matches when its `requires`
are all present, one `any_of` is present, no `none_of` is present, and the genre
gate passes. A span carrying several signals at once — a numbered hadith that
quotes a verse and uses a juridical word inside the author's commentary, which
classical hadith commentary routinely is — collapses to the single
highest-priority rule that lacks a disqualifier. The behaviours are not mutually
exclusive in the source, but the schema forces exclusivity. Each entry below
names the specific rule and priority that wins.

Rule table as configured (priority desc, abbreviated):

```
95 SECTION_HEADING     requires HEADING_MARKER
92 SECTION_HEADING     requires SUBSECTION_MARKER            none_of (none)
90 QURAN_VERSE         requires QURAN_REF                    none_of ATTRIBUTION_STRONG, AN_CHAIN_INITIAL, BASMALA, MATN_BOUNDARY_HINT
85 AUTHOR_COMMENTARY   requires AUTHOR_COMMENTARY
80 HADITH_TRANSMISSION any_of ATTRIBUTION_STRONG_INITIAL, ISNAD_BACK_REF
78 HADITH_TRANSMISSION requires AN_CHAIN_INITIAL, GENEALOGY_CHAIN   none_of HEADING_MARKER
75 FIQH_RULING         requires FIQH_RULING                  none_of (none)   gate (none)
72 HADITH_TRANSMISSION requires NUMBERED_ENTRY, ATTRIBUTION, GENEALOGY_CHAIN  none_of HEADING_MARKER
60 NUMBERED_ENTRY      requires NUMBERED_ENTRY
 0 GENERAL_PROSE       (default)
```

---

## Catalogue

### EX-01 — HADITH_TRANSMISSION vs NUMBERED_ENTRY is a chain-shape artifact, not a content distinction

- **What:** The same structural unit — a numbered hadith
  (`N - source : … : matn`) — is labelled `HADITH_TRANSMISSION` when it carries
  a multi-name relay chain and `NUMBERED_ENTRY` when it does not, even though
  both are hadith.
- **Why it's an issue:** The label stops meaning "this is a hadith." A consumer
  that trusts `behavior = HADITH_TRANSMISSION` to find hadith will miss every
  direct-report hadith. The split is book-dependent, so cross-book queries are
  incoherent: Bihar vol. 5 = 390 HADITH / 130 NUMBERED_ENTRY, but the Kanāsh
  volumes = 1 and 8 HADITH against 259 and 360 NUMBERED_ENTRY, despite being the
  same genre of numbered isnad+matn entries.
- **Where it comes from:** All three `HADITH_TRANSMISSION` rules require an
  isnad-chain signature — `GENEALOGY_CHAIN` (the `بن`/`ابن` links) or a strong
  initial attribution within the first 5–20 chars (`AN_CHAIN_INITIAL`
  start_threshold=5, `ATTRIBUTION_STRONG_INITIAL` start_threshold=20). A hadith
  reported without a relayed chain — a direct question to an Imam, or "source :
  matn" — has no `GENEALOGY_CHAIN` and no early chain-opener, so it satisfies no
  HADITH rule and falls through to `NUMBERED_ENTRY` (priority 60).
  `pipeline/segment.py::route_behavior` + `config/sol.yaml` behavior rules.
- **Evidence:** 23 of 130 Bihar `NUMBERED_ENTRY` spans carry both an attribution
  and an Imam name (e.g. `s0021` "11 - وسئل الصادق ﵇ …", patterns =
  ATTRIBUTION×1 + SPEECH_VERB + NUMBERED_ENTRY, no GENEALOGY_CHAIN; `s0189`,
  `s0202`). Contrast `s0007` (HADITH, 4× ATTRIBUTION + GENEALOGY_CHAIN).
- **Severity:** High (systemic, cross-book).

### EX-02 — SECTION_HEADING absorbs numbered hadith that begin with the "\*" ornament

- **What:** A numbered hadith whose printed line starts with the `*` sub-section
  ornament is labelled `SECTION_HEADING` instead of a hadith.
- **Why it's an issue:** A full hadith (isnad + matn) is filed as a chapter
  heading; its narrators and text are misrepresented, and the isnad portion is
  severed from its matn (see EX-06). The span's own `hierarchy_path` says
  `hadith_12`, directly contradicting `behavior = SECTION_HEADING` — an internal
  inconsistency.
- **Where it comes from:** The priority-92 rule
  `SECTION_HEADING requires SUBSECTION_MARKER` has an **empty `none_of`**, so it
  fires on any paragraph beginning with `*` and outranks every HADITH rule
  (80/78/72). The reciprocal guard exists elsewhere — the HADITH prio-78/72
  rules carry `none_of HEADING_MARKER` — but the SUBSECTION_MARKER heading rule
  has no matching "not if it contains an isnad" disqualifier. `config/sol.yaml`
  behavior rules.
- **Evidence:** `iz32WsFJ_05_s0029` ("_ 19 - عيون أخبار الرضا (ع) : الدقاق ، عن
  … عن … بن …", patterns include SUBSECTION_MARKER at char 0 **and**
  ATTRIBUTION×3 + GENEALOGY_CHAIN×3, `metadata.isnad_end = 91`), `s0061` ("_
  39 - التوحيد : ابن الوليد ، عن الصفار …"). 2 of 54 Bihar SECTION_HEADING
  spans.
- **Severity:** Medium (low count, but each loses a whole hadith).

### EX-03 — QURAN_VERSE absorbs author commentary about verses

- **What:** Exegetical prose (Majlisi's `تفسير :` / `بيان :` / `أقول :`
  discussion) that quotes a verse is labelled `QURAN_VERSE`.
- **Why it's an issue:** Over half the `QURAN_VERSE` bucket is not verse text
  but commentary, so the label cannot be trusted to mean "Qurʾānic quotation."
  This directly threatens the citation-sidecar work: a naive "QURAN_VERSE span ⇒
  link to the Qurʾān reader" would mislink commentary paragraphs, and real
  verse-citation lists are conflated with prose about verses.
- **Where it comes from:** The priority-90 rule `QURAN_VERSE requires QURAN_REF`
  fires on the phrase `قوله تعالى` ("God's saying"), which every tafsīr
  contains, and it outranks `AUTHOR_COMMENTARY` (priority 85). Its `none_of`
  gate lists ATTRIBUTION_STRONG / AN_CHAIN_INITIAL / BASMALA /
  MATN_BOUNDARY_HINT but **not `AUTHOR_COMMENTARY`**, so a leading `تفسير :`
  does not disqualify it even though that pattern is detected.
  `config/sol.yaml`.
- **Evidence:** 29 of 55 Bihar `QURAN_VERSE` spans lead with a commentary marker
  — `s0006` ("تفسير : المبالغة في قوله تعالى …", patterns = QURAN_REF×2 +
  AUTHOR_COMMENTARY + FIQH_RULING + GENEALOGY_CHAIN), `s0015` ("بيان : …"),
  `s0046` ("أقول : قال الشيخ المفيد …"), `s0067`, `s0116`.
- **Severity:** High (majority of the bucket; interacts with verse-linking).

### EX-04 — FIQH_RULING misfires on theology and hadith via a polysemous lexicon

- **What:** Theological Q&A and numbered hadith are labelled `FIQH_RULING` in a
  volume that contains no jurisprudence.
- **Why it's an issue:** The genre label is simply wrong for this content (Bihar
  vol. 5 is _kalam_), and because the rule outranks `NUMBERED_ENTRY`/HADITH,
  numbered hadith that merely contain a juridical-looking verb are relabelled
  away from hadith.
- **Where it comes from:** The priority-75 rule
  `FIQH_RULING requires FIQH_RULING` has **no genre gate and no `none_of`**, and
  its trigger pattern is a small, highly polysemous verb set — `يكره`
  ("disliked" in fiqh, but "coerce/compel" in kalam), `يجب`/`فيجب` ("obligatory"
  vs "necessary"). Peer rules that could collide (RIJAL_ENTRY, BIOGRAPHY,
  HISTORICAL_NARRATIVE) are genre-gated; FIQH_RULING is not. `config/sol.yaml`.
- **Evidence:** All 16 Bihar FIQH_RULING spans are theology or hadith, e.g.
  `s0132` ("90 - فقه الرضا (ع) : … أجبر الله العباد …", FIQH_RULING pattern
  matched `يكره`×2 + NUMBERED_ENTRY), `s0288`/`s0322`/`s0323` (numbered
  `تفسير العياشي` hadith with isnad), `s0120` (kalam prose on God's power).
- **Severity:** Medium–High (whole label is spurious for kalam volumes).

### EX-05 — Single-label routing cannot represent multi-signal spans

- **What:** The structural cause behind EX-01…EX-04: `route_behavior` returns
  one label at the first predicate match, but hadith commentary legitimately
  carries numbered-entry + isnad + Qurʾān-ref + commentary + fiqh-lexicon
  signals simultaneously.
- **Why it's an issue:** Whichever rule sits highest and lacks a disqualifier
  wins, so behaviour is decided by priority-table accidents rather than by the
  span's dominant nature. Tuning one rule's `none_of` (EX-02/03/04) fixes
  symptoms; the exclusivity itself is the root.
- **Where it comes from:** `pipeline/segment.py::route_behavior` returns
  `tuple[str, bool]` (one `behavior_id`); the `span.behavior` column is scalar.
  No multi-label or confidence-ranked representation exists.
- **Evidence:** `s0006` carries QURAN_REF + AUTHOR_COMMENTARY + FIQH_RULING +
  GENEALOGY_CHAIN yet is stamped only `QURAN_VERSE`; `s0132` carries
  FIQH_RULING + NUMBERED_ENTRY + SPEECH_VERB yet is stamped only `FIQH_RULING`.
- **Severity:** High (design-level; parent of the above).

### EX-06 — Hadith fragmented: isnad and matn split into separate spans with different behaviours

- **What:** One hadith is emitted as two adjacent spans — the isnad paragraph
  (labelled SECTION_HEADING or HADITH) and its matn paragraph (labelled
  GENERAL_PROSE) — instead of one unit.
- **Why it's an issue:** The hadith is no longer a single addressable object;
  its behaviour is inconsistent across its own halves, and the matn loses the
  hadith label entirely.
- **Where it comes from:** Segmentation and classification operate on the print
  paragraph; each paragraph becomes one `Span` classified independently. The
  `sanad_matn` tracker records the shared `hierarchy_path` (both halves get
  `hadith_12`) but there is no post-pass that merges the isnad span with its
  matn span. `pipeline/segment.py` per-paragraph loop +
  `pipeline/trackers/sanad_matn.py`.
- **Evidence:** 20 candidate pairs in Bihar where an isnad-behaviour span is
  immediately followed by a same/next-page GENERAL_PROSE span, e.g.
  `s0029`(SECTION_HEADING isnad of hadith 12) → `s0030`(GENERAL_PROSE matn "جعفر
  الكوفي قال : سمعت …"); `s0161`→`s0162`; `s0163`→`s0164`.
- **Severity:** Medium.

### EX-07 — Narrator entities carry print line-breaks inside the name

- **What:** ~7% of narrator entity strings contain an embedded `\n` mid-name.
- **Why it's an issue:** The narrator name is corrupted for display, matching,
  and rijal linking (`صباح بن\nعبد الحميد` will not equal `صباح بن عبد الحميد`).
- **Where it comes from:** The source paragraph retains the print-column line
  break; the narrator extractor slices by character offset
  (`char_start`/`char_end`) without normalizing whitespace first, so the raw
  `\n` is included in `entity.text_ar`. Same raw-newline class as the reader
  mid-paragraph problem, surfacing here inside entity strings.
  `pipeline/name_extraction.py` / `build/narrator_link.py`.
- **Evidence:** 128 of 1815 Bihar entities, e.g. `صباح بن\nعبد الحميد`,
  `عمر بن محمد\nابن سيف`, `علي بن محمد بن\nسليمان`. Confirmed in
  `entity.provenance.context_after` too.
- **Severity:** Medium.

### EX-08 — Narrator boundary errors: dropped chain-head and over-captured direction/honorific

- **What:** (a) The first link of some isnads — a relational term such as `أبي`
  ("my father", = al-Saduq's teacher) — is not extracted; (b) a
  transmission-direction phrase plus a glued honorific is captured as if it were
  a narrator name.
- **Why it's an issue:** (a) under-captures the chain (a real narrator is
  missing); (b) produces non-name entities that pollute the narrator set and
  rijal linking.
- **Where it comes from:** The narrator walk keys on proper names after an
  `ATTRIBUTION` and skips leading relational terms, losing the chain head; and
  it stops at character offsets rather than token/name boundaries, so a leading
  `إلى` preposition and a trailing honorific (`﵇`) get absorbed.
  `pipeline/name_extraction.py` / `pipeline/extractors/isnad_boundary.py`.
- **Evidence:** (a) `s0007` "أمالي الصدوق : أبي ، عن سعد …" extracts سعد/ابن
  يزيد/ابن أبي عمير/صباح but not أبي. (b) `إلى الصادق ﵇`, `إلى علي بن الحسين ﵉`,
  `إلى عبد الصمد بن عبد الملك`, `عنه` — 4 in Bihar.
- **Severity:** Medium.

### EX-09 — Entity layer is isnad-narrators only; every person is force-labelled "narrator"

- **What:** 100% of entities are `entity_type = PERSON` with
  `role_in_context = narrator` (1838/1838 across all three books). No authors,
  no matn-speaker Imams, no place names, no cited book/source titles are
  extracted.
- **Why it's an issue:** (a) Coverage ceiling: the ~50%+ of a volume that is
  commentary and matn yields no entities, and cited sources (`أمالي الصدوق`,
  `التوحيد`, `علل الشرائع`) — high-value bibliographic links — are never
  captured. (b) The `role_in_context = narrator` label is a foregone constant,
  so it carries no discriminating information and mislabels by construction any
  non-narrator person that slips through (e.g. the over-captures in EX-08 are
  stamped "narrator").
- **Where it comes from:** Only the narrator extractor is wired into the entity
  registry (`provenance.extractor_id = narrator_extractor`, `phase 3`); role is
  hard-set, not inferred. `pipeline/extractors/` (only `mentions`/narrator path
  active) + `build/narrator_link.py`.
- **Severity:** Medium (coverage/precision ceiling; shapes what the graph can
  express).

### EX-10 — Footnote apparatus is never separated from the body

- **What:** `span.footnote_text` is empty for every span in all three books,
  while the editorial footnote markers `(N)` and their note bodies remain inline
  in `span.text_ar`.
- **Why it's an issue:** Footnote prose is mixed into the matn/commentary body,
  so the body text is polluted, footnote markers interrupt the reading flow, and
  the 0.996 completeness ratio counts footnote text as body (masking the fact
  that body and apparatus are not separated). Downstream the reader cannot
  render a proper footnote apparatus for these books.
- **Where it comes from:**
  `attach_footnote_text(paragraph_text, footnote_entries)` returns empty because
  `_collect_footnotes(layout.page_footnotes, …)` yields nothing for these source
  books — the segment layout stage is not detecting/splitting the printed
  footnote apparatus. `pipeline/segment.py::_collect_footnotes` /
  `attach_footnote_text`. (Distinct from the earlier corpus-level
  footnote-_shape_ normalization `«N» → (N)`, which unified marker glyphs in the
  source but was never meant to separate footnote bodies; separation is this
  unimplemented extraction step.)
- **Evidence:** `footnote_text` populated on 0/800, 0/586, 0/797 spans; inline
  `(N)` markers counted 701 / 2409 / 2417 across the three books (e.g. `s0052`
  "… ولو منع إبليس لعذره (1) ولم يلعنه").
- **Severity:** Medium–High (every footnoted page affected; affects reader +
  completeness accounting).

---

## Cross-book note

The Kanāsh volumes shift the whole distribution toward `NUMBERED_ENTRY`
(259/360) and away from `HADITH_TRANSMISSION` (1/8), confirming EX-01 is driven
by chain morphology rather than genre. `AUTHOR_COMMENTARY` collapses to 4/0
there (Bihar 121), and `POETRY`/`BIOGRAPHY` appear only in Kanāsh — so per-book
behaviour mixes are not comparable under the current labels, and any consumer
aggregating by `behavior` across books will get skewed counts.

## Downstream impact on sol-next2 (consumer side)

- **Citation sidecar / verse-linking:** EX-03 means `QURAN_VERSE` cannot gate
  verse links; the verse-verified `citations.db` path (which matches on text,
  not on `behavior`) is the correct source and should not be replaced by a
  `behavior`-driven shortcut.
- **Reader:** EX-06/EX-07/EX-10 (fragmented hadith, newline-corrupted names,
  un-separated footnotes) all surface in the reading view; EX-10 in particular
  blocks a clean footnote apparatus for these books.

---

# Re-audit — 2026-07-05, after commit `e82345e`

Commit `e82345e` ("fix(pipeline): four narrator-extraction defect classes")
rebuilt the DB (14.0 MB, Jul 5 06:07). It changed only the **entity**
extractors; the `behaviors:` rule table in `config/sol.yaml` was not touched, so
every behaviour-classification finding is byte-for-byte unchanged. Verified
against the same three-book DB.

| Issue                                       | Status                                        | Current measure                                                                                                                                                                                 |
| ------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| EX-01 NUMBERED_ENTRY reads as hadith        | **Outstanding**                               | 23 in Bihar; distribution identical                                                                                                                                                             |
| EX-02 SECTION_HEADING eats "\* N -" hadith  | **Outstanding**                               | 2 (`s0029`, `s0061`)                                                                                                                                                                            |
| EX-03 QURAN_VERSE eats commentary           | **Outstanding**                               | 29 of 55                                                                                                                                                                                        |
| EX-04 FIQH_RULING misfires in kalam         | **Outstanding**                               | 16                                                                                                                                                                                              |
| EX-05 single-label router (root of 01–04)   | **Outstanding**                               | design-level                                                                                                                                                                                    |
| EX-06 hadith split across spans             | **Outstanding**                               | 20 pairs                                                                                                                                                                                        |
| EX-07 newline inside narrator name          | **Outstanding**                               | 130 (116 narrator + 14 mention); now also breaks narrator_link matching                                                                                                                         |
| EX-08 chain-head / over-capture / honorific | **Fixed** (+ small residual)                  | head narrator now walked; citation head → 352 units carry `citation_head`; honorific-bearing names 0 (was many); kinship typed 103. Residual **EX-08b**: 23 connective-led over-captures        |
| EX-09 isnad-narrators only / role hard-set  | **Substantially fixed**                       | roles now narrator 2110 / mention 478 / relative_reference 103; matn persons captured. Residual: entity_type still PERSON-only (works ride as `citation_head`, acceptable; places/dates absent) |
| EX-10 footnote apparatus not separated      | **Outstanding** (now root-caused to one line) | `footnote_text` 0/800, 0/586, 0/797                                                                                                                                                             |

Validation of the EX-08 fix on the page-6 test hadith: `s0007` now emits
`أبي`@chain_position 0 (previously dropped), `s0008` emits head narrator
`السناني` with the ordinal+source citation head excluded from the chain, kinship
`عن أبيه` typed as `relative_reference` with the name (`محمد بن علي`) alone, and
matn persons (`أبو حنيفة`, `موسى بن جعفر`) as `mention`. The work is correct and
general.

**New residual — EX-08b (introduced by the narrator fix):** 23 Bihar entities
lead with a connective or are non-names. Two sub-classes: (a) 11 `mention`
entities keep a leading attribution particle, e.g. `عن ابن بطة`, `عن ابن محبوب`,
`عن ابن عيسى` — the new `person_mention_extractor` includes the preceding `عن`;
(b) 12 `narrator` entities are prepositional/bibliographic openers the head-walk
grabbed, e.g. `في الصحيح`, `من كتاب دلائل الحميري`, `من كلام له`, and the
pronoun `عنه` — the new head-narrator walk accepts a non-name head region.

---

# Fix plan for the outstanding issues

All fixes land in the pipeline that produces `manuscript.db`
(`src/backend/pipeline/`, `config/sol.yaml`,
`scripts/build_manuscript_index.py`), which lives on the extraction branch
(worktree `wt-9db19a37`), not this audit worktree. Each step: make the change,
rebuild the three-book DB, re-run the re-audit, confirm the target count drops
with no regression elsewhere, and lock it in
`tests/pipeline/test_extraction_quality.py`.

## P1 — EX-10 footnote wiring (one line, highest ROI)

- **Change:** `scripts/build_manuscript_index.py:54` builds
  `ManuscriptPage(page_number=row.page, page_name=str(row.page), text=row.content)`
  and drops the footnote. Add `footnote=row.footnote`.
- **Why it works:** `reader_repo.page_rows` already returns the separated
  footnote block (259/361/361 pages carry one; the reader renders them today),
  the `ManuscriptPage` model already has a `footnote` field, and `segment.py`
  already feeds `page.footnote` through `split_footnote_entries_to_dict` →
  `attach_footnote_text` → `span.footnote_text`. The only break is the omitted
  constructor argument.
- **Validate:** `footnote_text` populates on ~259 Bihar spans; note bodies leave
  the matn-facing unit text.
- **Risk:** low.

## P2 — EX-03 QURAN_VERSE disqualifier (one line, config)

- **Change:** in `config/sol.yaml`, add `AUTHOR_COMMENTARY` to the `none_of` of
  the priority-90 `QURAN_VERSE` rule.
- **Why it works:** `AUTHOR_COMMENTARY` has `start_threshold=20`, so it only
  counts when the paragraph opens with `تفسير :`/`بيان :`/`أقول :`. Such
  paragraphs then fail QURAN_VERSE and fall to `AUTHOR_COMMENTARY` (priority
  85); a real verse quotation that merely contains those words later is
  unaffected.
- **Validate:** commentary-led QURAN_VERSE → 0; AUTHOR_COMMENTARY rises ~29.
- **Risk:** low.

## P3 — EX-04 FIQH_RULING genre gate (config)

- **Change:** add a `genre_gate` to the priority-75 `FIQH_RULING` rule, listing
  the fiqh book categories (`independent-fiqh`, `hanafi-fiqh`, `hanbali-fiqh`,
  `maliki-fiqh`, `fiqh-terminology`), mirroring the gate
  `RIJAL_ENTRY`/`BIOGRAPHY`/`HISTORICAL_NARRATIVE` already carry.
- **Why it works:** the trigger lexicon (`يكره`/`يجب`) is polysemous; gating by
  book genre is the same pattern the config already uses for other
  context-dependent rules. In a kalam or hadith volume the rule is skipped and
  the span keeps its hadith/numbered label.
- **Validate:** FIQH_RULING in Bihar → 0; unchanged in a real fiqh book. First
  confirm the `book_type` value equals the category-folder name.
- **Risk:** low, pending the genre-list confirmation.

## P4 — EX-02 heading vs isnad (extend existing machinery, not a parallel gate)

- **Change:** `segment.py` already has `filter_heading_disqualifiers` /
  `filter_heading_shape` / `drop_heading_for_narrative`. Investigate why `s0029`
  ("\* 19 - … عن … بن …", a full isnad) survived them, and extend that machinery
  so a `SUBSECTION_MARKER` line carrying an isnad signature (`ATTRIBUTION` +
  `GENEALOGY_CHAIN`) or exceeding `narrative_heading_max_chars` is disqualified
  as a heading. Do not add a competing `none_of` if the disqualifier path is the
  canonical home.
- **Validate:** `s0029`, `s0061` → hadith; real short sub-section headings
  unchanged.
- **Risk:** medium (must not demote genuine headings). Depends before P7.

## P5 — EX-01 direct-report hadith (config, needs a labelled sample)

- **Change:** add a `HADITH_TRANSMISSION` rule for a numbered entry that reports
  directly from an Imam without a relay chain: `requires: [NUMBERED_ENTRY]`,
  `any_of: [ATTRIBUTION, SPEECH_VERB_TO_IMAM]`, `none_of: [HEADING_MARKER]`,
  `genre_gate:` the hadith-collection categories (`shia-hadith-general`,
  `sunni-hadith-*`). Sits above `NUMBERED_ENTRY` (60), below the chain-based
  HADITH rules.
- **Why it works:** the current HADITH rules all require `GENEALOGY_CHAIN`,
  which a direct question-to-Imam hadith lacks; a genre-gated
  numbered+attribution rule catches it without swallowing rijal/biography
  numbered entries (those are gated to narrator/biography genres).
- **Validate:** build a small labelled set of Bihar NUMBERED_ENTRY spans; the 23
  hadith reclassify, non-hadith numbered entries do not.
- **Risk:** higher; do after P2–P4 with the labelled check.

## P6 — EX-05 make the router's exclusivity honest (after P2–P5)

- **Change:** once the gates above are complete, add a diagnostic that flags any
  span where a second rule also matched at high priority (an ambiguity counter
  in `route_behavior`), logged per build. Only if the ambiguity rate stays high
  after P2–P5 escalate to a multi-label or scored `behavior` representation.
- **Why:** the single-label router is acceptable once its `none_of`/gates are
  complete; a redesign is justified only if measured ambiguity proves they
  cannot be. This targets the root without pre-emptive over-engineering.
- **Risk:** low (diagnostic first).

## P7 — EX-06 hadith cross-span merge (after P4/P5)

- **Change:** add a post-segmentation pass that merges consecutive spans sharing
  the same terminal hierarchy node (`hadith_N`) into one span, since the
  `sanad_matn` tracker already stamps both the isnad paragraph and its matn
  paragraph with the same `hadith_N`. Reconcile `page_start`/`page_end` and
  re-run atomicization on the merged span.
- **Why after P4/P5:** the isnad half must first be correctly labelled (P4) so
  the merge joins two hadith halves rather than cementing a heading.
- **Validate:** the 20 split pairs collapse; unit ISNAD/MATN split still
  correct.
- **Risk:** medium.

## P8 — EX-07 newline normalization in names (small)

- **Change:** in the name emitter (`pipeline/name_extraction.py`, the
  `clean_name_text` path that already cuts at honorifics), collapse internal
  whitespace with `patterns.WHITESPACE` before storing `entity.text`. Keep
  `char_start`/`char_end` pointing at the raw span, exactly as the honorific-cut
  names already diverge from the raw slice.
- **Validate:** newline-in-name → 0 across books; re-check `narrator_link` rate
  (expected to rise, since `صباح بن\nعبد الحميد`-style names will match the
  registry).
- **Risk:** low.

## P9 — EX-08b residual over-capture (small, precision)

- **Change:** (a) in `person_mention_extractor` (`extractors/mentions.py`),
  strip a leading attribution particle (`عن`/`و`/`فـ`) before emitting the
  mention; (b) in the head-narrator walk, reject a head candidate that opens
  with a preposition or is a bibliographic/pronoun phrase (`في الصحيح`,
  `من كتاب …`, `عنه`) — require a name shape (nasab/kunya/proper), not a
  prepositional phrase.
- **Validate:** connective-led entity count → ~0; the page-6 hadith unchanged.
- **Risk:** low–medium.

## Suggested order

P1, P2, P3 first (one-line, low-risk, independent). Then P8, P9 (entity
residuals, independent). Then P4 → P5 → P7 (the heading/hadith chain, ordered by
dependency). P6 last, as a diagnostic that decides whether the router needs a
deeper change. Rebuild and re-audit after each; each targets one measure and
must not move the others.

---

# Implemented — 2026-07-05, branch `feature/extraction-fixes`

P1, P2, P3, P8, and P9 are implemented, two commits stacked on the pipeline tip
(`feature/wt-9db19a37`):
`139a36e fix(build): carry page footnotes into the manuscript index` and
`e8cb2b1 fix(pipeline): gate verse/fiqh routing and clean narrator names`.
Validated by rebuilding the three-book `manuscript.db` and re-auditing;
`pnpm py:check` green and 408 pytest tests pass, including new regression tests
in `test_name_extraction.py` and `test_segment_routing.py`.

| Item         | Change                                                                                               | Result on the three-book rebuild                                                |
| ------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| P1 (EX-10)   | `build_manuscript_index.py` passes `footnote=row.footnote`                                           | `footnote_text` populated 330 / 345 / 293 spans (was 0 / 0 / 0)                 |
| P2 (EX-03)   | QURAN_VERSE `none_of` += `AUTHOR_COMMENTARY`                                                         | commentary-led QURAN_VERSE 29 → 0; AUTHOR_COMMENTARY 121 → 150                  |
| P3 (EX-04)   | FIQH_RULING genre-gated to fiqh categories                                                           | FIQH_RULING in Bihar 16 → 0, and 0 across all three books                       |
| —            | `route_behavior`: a content match declined only by a genre gate is clean GENERAL_PROSE, not unrouted | keeps the genre gate from tripping the segment failure budget on non-fiqh books |
| P8 (EX-07)   | `clean_name_text` collapses all whitespace, not only spaces                                          | newline-in-name 130 → 0                                                         |
| P9a (EX-08b) | `clean_name_text` strips a leading connective run                                                    | connective-led captures 23 → 0                                                  |
| P9b (EX-08b) | `has_non_name_leading_word` + config `non_name_leading_words` / new stopwords                        | bibliographic and pronoun captures (`كتاب X`, `في الصحيح`, `عنه`) → 0           |

Not moved, as expected (P4/P5/P6/P7 not in this batch): EX-01 (24), EX-02 (2),
EX-06 (~23).

**Not yet visible in the live inspector.** The `:8767` inspector serves
`wt-9db19a37/data/manuscript.db`, built before these fixes. It updates only
after `feature/extraction-fixes` merges onto the pipeline branch and that
worktree's DB is rebuilt.
