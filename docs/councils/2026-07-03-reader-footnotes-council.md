# Council transcript: reader footnote rendering (2026-07-03)

## Original question

The reader is processing content but not footnotes. The predecessor pipeline project renders footnotes as superscripts with a different-colored floating font and numbers in the reader, and a smaller block with lighter colors at the bottom of the reader. Build something similar but intelligently designed for this project, comparing what exists in the predecessor and building from the ground up.

## Framed question

A React + FastAPI reader for classical Arabic manuscripts must add footnote support end-to-end: API shape, marker-rendering treatment, apparatus behavior across language modes, interaction design. The project bans silent fallbacks and holds that a wrong rendering is worse than none.

Corpus evidence (measured, 407-file / 180,435-row sample):
- 46% of page rows carry a separate `footnote` field formatted "(1) text\n(2) text"; ~9k of 83k are free-form unnumbered blocks; guillemet-form entries rare (432).
- Body markers: guillemet «N» dominates (47,791 pages); paren (N) on 8,639 pages; Western digits only.
- 32% of footnote pages have NO in-text marker.
- False-positive risks: (1984)-style years in body; huge "entry numbers" like (20856) in fields.
- ~1% of pages duplicate entry text inline in content.

Proposed design put to the council: backend parses entries once and serves BookPage.footnotes list of {marker, text}; frontend tokenizes text_ar with a valid-numbers guard; gold superscript Arabic-Indic digits replacing printed glyphs; apparatus block in all language modes; click-to-scroll linking; no popovers in v1.

## Advisor responses

### The Contrarian

Two parts of this design break the project's own rule that a wrong rendering is worse than none.

First, re-typesetting markers into Arabic-Indic superscripts while discarding the printed « » and ( ) glyphs is an editorial rewrite of the witness. Your own evidence says the corpus prints Western digits only; the reader would display digits the edition never printed, and the guillemet-versus-paren distinction, which is edition evidence, vanishes. Preserve the printed form and style it. Do not beautify it into something false.

Second, the valid-numbers guard is aimed at the wrong failure. It correctly rejects (1984), but it does nothing about in-set collisions: on a page whose apparatus contains entry 1, every body «1» or (1) becomes a marker, including hadith numbers, verse references, and quoted counts. Low numbers are exactly what the guard admits and exactly the commonest false positives. The design also has no answer for duplicate occurrences of the same N, yet the entry-to-marker backlink assumes the first occurrence is the right one with zero supporting measurement.

On the API: marker: null conflates "genuinely unnumbered note" with "parser failed to split," inside a frozen DTO, with the raw field withheld from the client. That is a silent fallback baked into an unamendable contract. Serve the raw footnote string alongside parsed entries, or add an explicit parse-status field, so a parser bug is detectable rather than invisible.

Unspecified and likely to break in practice: whether the tokenizer runs inside structured hadith unit text at all, and how the marker segmenter composes with the existing Highlight mark segmenter when a search hit overlaps a marker span.

On (c): show the apparatus in EN mode; hiding served scholarly data is itself a fallback.

### The First Principles Thinker

Strip the framing: you are not "adding footnotes." You are preserving a print edition's critical apparatus whose body-linkage is unreliable by construction. The evidence proves the fundamental unit is the page-level note block, not the numbered entry: 32% of footnote pages have no marker at all, and ~9k fields have no numbered entries. The design's primitive, list of {marker, text} with nullable marker, matches that reality, so (a) is right. One addition: the server parser is now the single point of truth, so it must fail loudly per page. A field it cannot parse should surface as an explicit unparsed state, never a best-effort mangled entry.

(b) Ask what the glyphs actually are. They are not manuscript witness; they are the digitizer's typesetting of the editor's marker. The number is the semantics, the delimiter is typography. Converting to a superscript Arabic-Indic digit loses nothing scholarly. The real consequence to accept openly: unmatched «N» stays raw in the body while matched N becomes superscript, so the same construct renders two ways across pages. Under fail-loud rules that is correct, but document it as intended.

(c) is the wrong question. The apparatus annotates the Arabic text, so the rule is: apparatus renders wherever text_ar renders. EN-only mode is a placeholder today; deciding its apparatus behavior is designing for a mode that does not exist. State the binding rule and stop.

(e) The design misses its own strongest evidence: the ~1% pages where entry text is duplicated inside content defeat the valid-numbers guard completely, because those line-start (N) tokens match the served entry set exactly. That produces wrong markers in body text, which your contract says is worse than none. Exclude line-start paren matches from tokenization. That is one condition, and it closes the only proven false-positive class the guard cannot.

### The Expansionist

Everyone is treating this as a rendering feature. The evidence says you are actually building the corpus's first structured annotation layer, and the design should be shaped to cash that in.

(a) The API shape is right, but undervalued. list of {marker, text} over 83,176 rows is a queryable scholarly apparatus: variant readings, editorial judgments, source attributions. The moment the canonical parser exists, footnote text belongs in the FTS index and in the /search concordance you already built. That is a second search corpus arriving for free; plan the ingest hook now so the parser runs once, not twice.

(b) Drop the glyphs, convert to Arabic-Indic, and notice what the tokenizer buys you: a composable marker-token segmenter that already stacks with the Highlight segmenter. The same machinery later recognizes Qurʾān citations, hadith numbers, and cross-references. Build it as a token-type pipeline, not a footnote-only regex, and every future annotation type is a config entry.

(c) Show the apparatus in EN mode, and go further: {marker, text} extends additively to text_en without breaking the frozen DTO. Footnotes are the cheapest, highest-value translation target in the corpus because entries are short and self-contained.

(d) Give every entry a stable fragment id derived from page plus marker, not a DOM-order index. That turns marker-entry linking into shareable deep links, and scholars cite apparatus constantly. A citation URL per footnote is a distribution channel.

(e) The 26,892 marker-less pages and the ~9k free-form blocks are not edge cases; they are unnumbered editorial commentary, exactly the material your daily-picks and almanac surfaces could rotate through. The design is correct. The miss is scoping it as a reader feature when the parser output is a dataset.

### The Outsider

You wrote "wrong rendering is worse than none" and then proposed rewriting what the page shows. Your own evidence says the corpus uses Western digits, and the dominant printed marker is «1». The design drops those glyphs and displays Arabic-Indic superscripts instead. To a reader checking the app against a physical edition, the marker on screen no longer matches the marker in the book. That is a silent transformation of source data in a project that bans silent anything. Preserve the printed form, or serve both the raw marker string and a normalized number in the DTO so the display choice is reversible and inspectable. On question (b): preserve.

Second thing an outsider notices: 32% of footnote pages have no in-text marker at all. That is not an edge case, it is a third of your inventory. The whole interaction design, click marker, scroll, pulse, is built for the 68%. Design the standalone-apparatus page first. And on those pages, do not render the entry numbers in gold clickable styling that does nothing when clicked. A control that looks interactive and is inert reads as a bug.

On (c): yes, show the apparatus in EN mode, hiding data would be your forbidden fallback. But an unlabeled block of Arabic under English text will look like a rendering error to a non-Arabic reader. The label must say, in English, that these are the original edition's notes, untranslated. Also, "small uppercase label" assumes a script that has uppercase. Arabic does not. State what the label says in each mode.

On (a): shape is fine, add the raw marker string. On (d): define what clicking does when the counterpart is absent or duplicated, because "(1)" can plausibly occur twice.

### The Executor

Ship order, Monday morning: promote the existing tested splitter into one shared module the serving path imports, freeze the DTO, regenerate types with pnpm types:gen, then build the apparatus component before touching marker tokenization. The 26,892 markerless pages mean the apparatus alone delivers value to 100% of footnote pages; markers only add value on the subset. Do not invert that order.

(a) The DTO is right precisely because it is presentation-free: marker plus text, null for unnumbered. Nothing about superscripts or digit scripts is frozen, so the expensive-to-reverse surface stays small. One addition: make marker a string, not int, so the frozen model survives future "1a" or Arabic-letter markers without a breaking regen.

(b) Convert to Arabic-Indic. Since text_ar ships raw, this is a frontend-only, fully reversible decision. Not worth debating; change it in one component later if scholars object.

(c) Yes, all modes. EN is a placeholder today, so hiding the apparatus there is extra conditional code for zero benefit.

(d) Scroll plus pulse is one afternoon. Popovers mean portal positioning, RTL edge handling, focus management: correctly cut.

Two real gaps. First, the valid-numbers guard is only as good as the parser: a field line "(20856) ..." makes 20856 a served entry number, and the guard then superscripts a matching hadith number in the body. Add a sequential-plausibility check in the parser, entries starting near 1 and roughly contiguous, with loud logging on rejects per the no-fallback contract. Second, the hidden integration cost is composing the marker tokenizer with the existing Highlight segmenter; two independent splitters over the same string will conflict on overlapping ranges. Design one segmentation pass with two token types, and write vitest fixtures from the 407-file sample before writing the component.

## Peer reviews

Anonymization mapping: A=Executor, B=Outsider, C=First Principles, D=Contrarian, E=Expansionist.

All five reviewers independently ranked D (the Contrarian) strongest, citing the marker-null conflation as a contract-level silent fallback and the in-set collision critique as the sharpest tokenizer analysis. All five named E (the Expansionist) as the biggest blind spot: zero correctness engagement, scope expansion on an unvalidated parser, and a fragment-id proposal undefined for the markerless third of the inventory.

Collective misses the reviews surfaced:
- Cross-page note continuation: a marker on page N can reference an entry printed on page N+1; a per-page footnotes list cannot represent that, and the rate is measurable but unmeasured.
- The 32% markerless figure is itself unvalidated: it may be a marker-regex artifact rather than real absence.
- Bidi and accessibility of an interactive control inside RTL text: digit-run ordering, tap-target size, keyboard focus, screen-reader semantics.
- Injected superscripts would contaminate copy-paste text and search snippets derived from text_ar.
- Every guard proposal was argued, not measured: a corpus-wide tokenizer dry run must report residual collision rates before the guard is frozen.

## Chairman's verdict

### Where the council agrees

The API primitive is correct: a list of {marker, text} with nullable marker matches the corpus, where the page-level note block is the fundamental unit. Marker must be a string, not an int. The apparatus must render in EN-only mode; hiding served scholarly data is the forbidden fallback. The valid-numbers guard as designed is unsound: three advisors found three independent holes (in-set collisions on low numbers, the ~1% duplicated-entry pages, entry-set poisoning by reference-numbered lines). Build the apparatus before the markers: it delivers value on 100% of footnote pages, markers only on the 68% subset. The marker tokenizer and the Highlight segmenter must be one segmentation pass with two token types.

### Where the council clashes

Question (b) split two against three. The Contrarian and Outsider: dropping printed « » and ( ) glyphs and showing Arabic-Indic digits the edition never printed is an editorial rewrite of the witness. First Principles, Executor, Expansionist: the glyphs are digitizer typesetting, the number is the semantics, and the choice is a reversible one-component decision. The camps disagree about the preservation target: printed page as witness versus semantic content as witness.

A quieter clash on (c): First Principles says stating the binding rule (apparatus renders wherever text_ar renders) settles it; the Outsider insists the EN-mode label copy must be specified now because an unlabeled Arabic block under English text reads as a rendering error.

The Expansionist's dataset framing (FTS indexing, deep links, translation targets) was rejected unanimously by peer review, except one fragment: structure the parser as an importable module so a future ingest hook runs the same code.

### The recommendation

(a) Keep the primitive, amend before freezing: marker is a string; add a page-level parse state with explicit values (numbered, freeform, failed); on failure ship the raw field with an empty entries list so a parser bug is a visible state, never a mangled best effort. Do not freeze until the dry run measures cross-page continuation.

(b) Preserve the printed form; wrap, do not replace. The tokenizer wraps the existing «1» or (1) characters in a styled span (gold, slightly raised, clickable) and never substitutes characters. This closes the copy-paste blind spot, keeps the guillemet-versus-paren distinction visible, and cannot be wrong under the contract. Arabic-Indic superscripts may later ship as an explicit user preference, never a silent default.

(c) Bind the apparatus to text_ar, not to language mode. In EN mode the label states in English that these are the printed edition's notes in Arabic, untranslated. In Arabic modes the label is Arabic, with no uppercase assumption.

(d) Scroll plus pulse. On markerless pages, entry numbers render plain: no gold, no cursor affordance. Duplicate N: backlink jumps to first occurrence (dry run measures whether cycling is needed). Entries with no matched body occurrence get no backlink. Markers are keyboard-focusable, activate on Enter, meet minimum tap-target size, carry doc-noteref / doc-endnotes roles.

(e) Layered guard replacing the single valid-numbers check: sequential-plausibility in the parser with loud logging, line-start paren exclusion in the tokenizer, entry-set membership as the final filter, frozen only after the dry run reports residual collision rates. One segmentation pass shared with Highlight, vitest fixtures from the corpus sample. Parser as one shared importable module.

### The one thing to do first

Run the parser and tokenizer over all 83k footnote page rows as a headless dry run emitting one report: parse-state counts; per-page marker match and miss counts; collision proxies (matched markers exceeding entry count, line-start matches, four-plus-digit matches); duplicate-N rate; re-measurement of the 32% markerless figure; cross-page continuation candidates. Every unresolved judgment is settled by that report rather than by argument.
