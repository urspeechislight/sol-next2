# Name-extraction audit against the combined people directory

Date: 2026-07-07. Read-only audit; no extraction change was made as part of it.

## The authoritative directory

`data/people.db` (table `people`, gitignored artifact like `registry.db`)
combines the two canonical upstream-pipeline corpora into one name-keyed lookup:

- **canonical rijal** — 169,468 deduplicated narrators (from `registry.db`,
  itself projected from the upstream `rijal/canonical.json`).
- **history persons** — 367,684 historical figures with their events (streamed
  from the upstream `history_corpus_v5.json`).

Records merge on `(normalize_arabic(full_name), death_year)`; a person present
in both sources is flagged `in_rijal` AND `in_history`.

| directory            | count   |
| -------------------- | ------- |
| total people         | 484,629 |
| in rijal only        | 118,388 |
| in history only      | 353,110 |
| in both              | 13,131  |
| with a death year    | 42,212  |
| with recorded events | 10,662  |

## Method

Every distinct extracted `PERSON` name in `manuscript.db` (the 7-book set:
Bukhārī, al-Kāfī, Ṭabaqāt ×2, al-Nasāʾī, al-Muʿjam, a history book) is folded
with `normalize_arabic` and matched against the directory in three tiers: exact
name, all-significant-tokens-in-one-directory-name (token subset), single-token
present. Anything unmatched is a suspect, split into a malformed shape (its
tokens are non-name words) vs a plausible name simply missing from the
directory.

## Result

|                                   | distinct          | occurrences        |
| --------------------------------- | ----------------- | ------------------ |
| extracted PERSON names            | 10,172            | 35,113             |
| **VALID (matched a real person)** | **7,760 (76.3%)** | **32,355 (92.1%)** |
| invalid / unmatched               | 2,412             | 2,758              |

Of the 2,412 unmatched distinct names:

- **Genuine garbage (malformed): 76.** Real extraction defects — a descriptor
  appended to a name (`عائشة زوج النبي`), a divine phrase (`قول الله ﷿`), or a
  matn fragment mis-captured as a name (`مرض رسول الله`, `دخل حديث بعضهم`,
  `بعض أهل المدائن`, `تلك الآية فأخبره بخلاف ...`). This is the residual to fix
  later.
- **Plausible but missing: 2,336.** Name-shaped, not in the directory. These are
  NOT extraction errors — they are real narrators the directory lacks
  (`هاشم بن القاسم الكناني` ×23, `عبد الوهاب بن عطاء العجلي` ×16,
  `خالد بن مخلد البجلي` ×14) and kunya forms that miss the directory's full-name
  keys because of the accusative/genitive (`أبا حمزة`, `أبا بصير`,
  `أبي أيوب الخزاز`). A handful are non-Arabic (`مؤمنان`, Persian).

## Reading of the numbers

The extraction produces overwhelmingly real narrator names: **92.1% of all name
occurrences resolve to a person in the authoritative directory**, and the
genuine malformed residue is 76 distinct names (0.7% of distinct, far less by
occurrence). Most of the unmatched bucket is directory coverage and name-form
normalization, not broken extraction:

1. **Directory recall.** Many valid narrators (with a nisba, e.g. `... الكناني`,
   `... العجلي`, `... البجلي`) are not reachable by exact/token match. Widening
   the directory (the raw rijal corpus adds 115K more entries) or relaxing the
   nisba in matching would recover them.
2. **Kunya normalization.** `أبا/أبي` (accusative/genitive of `أبو`) should fold
   to `أبو` before lookup so `أبا حمزة` matches `أبو حمزة`.
3. **Genuine garbage (76).** Descriptor/divine/matn absorptions — the same class
   the honorific-ligature normalization and the matn-transition crop already
   shrank; the remainder is appositive descriptors (`زوج النبي`, `أم المؤمنين`)
   and long matn sentences with an embedded name.

## Reproduce

```
# directory (needs the upstream corpus on the buildhost)
uv run --with ijson python scripts/build_people_directory.py \
  <upstream>/data/history_corpus_v5.json data/registry.db data/people.db
# audit
uv run python scripts/audit_names.py data/manuscript.db data/people.db data/name_audit.json
```

The full valid / malformed / plausible-missing lists are in the audit JSON
output.
