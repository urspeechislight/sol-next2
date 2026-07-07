# Rijal validation against source material — pass 1 (Sunni)

Date: 2026-07-07. Read-only; no source or canonical data was modified.

## What was done

For each canonical narrator, every one of its source entries (via `entry_ids`
into the upstream `rijal/corpus.jsonl`) is pulled and cross-checked. Per person
we aggregate, from the actual rijal books:

- **identity** — consensus kunya, nisba, birth/death year (with the count of
  sources that agree), tradition;
- **reliability** — every evaluator's grade (`ابن حجر: ثقة حافظ`,
  `البخاري: لين`, …);
- **teachers / students** — the upstream lists are noisy (matn fragments mixed
  in), so each name is filtered against the authoritative directory: a teacher
  that matches a real canonical person is kept, a fragment is dropped;
- **position vis-à-vis ahlulbayt** — the `stance` field (`pro_ahlulbayt`, …);
- **places** — birth/death/activity locations;
- **historical events** — with the person's role;
- **biography snippet** and **which rijal books** each fact came from.

Two blind-spot guards, as required: (1) after the kunya/nisba are known, the
corpus is searched by the person's distinctive name tokens AND by kunya+nisba,
so a mention listed under the kunya or a partial name is still found; (2)
disambiguation — persons sharing a name are separated by death-year clusters,
and the canonical record with the strongest attestation is validated.

## Result — 1,409 well-attested Sunni narrators (>= 15 source entries)

### A clean, correct profile

**جابر بن يزيد الجعفي** — kunya `أبو عبد الله`, nisba `الجعفي`, **death 128
(canonical and sources agree)**, place Kūfa, stance **pro_ahlulbayt**, bio "عدة
من أصحاب الباقر ﵇". Reliability captures the real cross-tradition debate: Ibn
Ḥajar `صدوق`, al-Bukhārī `لين`, al-ʿIjlī `ضعيف`, al-Nasāʾī `متروك`.
Cross-referenced across 27 rijal books.

**سفيان بن عيينة** — kunya `أبو محمد` (17 sources), nisba `الهلالي`, birth 107,
Kūfan→Meccan; graded `حجة`/`ثقة حافظ` by Ibn Saʿd and Ibn Ḥajar; 19 real
teachers recovered (al-Zuhrī, ʿAmr b. Dīnār, Zayd b. Aslam…). Across 23 books.

## Findings (canonical data quality — recorded, not fixed)

1. **Death-year conflicts: 478 / 1,409.** Some are genuine canonical errors
   (Sufyān b. ʿUyayna: canonical d.191 vs source-consensus d.198). Others are
   source-extraction truncation of the century digit (a `172` read as `72`,
   `117` as `17`). Both are recorded per person in the profile output.
2. **Over-merging on shared kunya.** A high-entry record can conflate many
   different people who share a kunya — e.g. a "سميع أبو صالح" record with five
   different home cities and an impossible birth 388 / death 67, whose bio says
   al-Dāraqutnī declared him a liar. Such records fail the internal-consistency
   check (multiple death years, multiple nisbas/places).
3. **Fragmentation of major figures.** Imām Mālik b. Anas is scattered (under
   `يحيى بن مالك`, the book title `الموطأ ... مالك`, an obscure 1-entry
   `مالك بن انس`), with no single consolidated record — the canonical dedup
   missed him.
4. **Upstream teacher/student noise is recoverable.** Filtering the raw lists
   against the directory reliably separates real transmitters from matn
   fragments.

## Output & reproduce

One JSON profile per narrator (identity, reliability, teachers, students,
places, stance, events, bio, source books, and the canonical-vs-source
death-year flag) is written by the batch validator; the single-person validator
prints the same for a named narrator with the full disambiguation and
cross-reference trace.

## Next passes

- **Shia rijal** — same tool with `tradition=shia`; the `stance`/ahlulbayt field
  is richer there (al-Kashshī, al-Najāshī, Ibn Dāwūd, al-Ṭūsī).
- **History books** — validate the history persons' events/dates against the
  history corpus and link them to the same canonical people.
- **Data-quality follow-ups** (separate from this read-only audit): re-dedup the
  over-merged kunya records, normalize truncated death years, and consolidate
  the fragmented major narrators.
