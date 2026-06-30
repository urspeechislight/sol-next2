# Council Transcript — Home page revamp (first principles)

**Date:** 2026-05-24
**Question:** What should the home page of the Shia Online Library actually DO? Then derive structure. Foundation binding: Emil Kowalski's design philosophy.

---

## Framed question

Product: Shia Online Library (codename sol-next2) — knowledge-graph reader for classical Arabic manuscripts. Corpus: 18,691 indexed books across 7 domains and 39 categories. Tech: React+Babel static prototype + FastAPI backend.

Editorial design register: cream paper, carbon ink, brick accent, Newsreader (Latin) + Amiri (Arabic) serif typography. Day-mode default. No SaaS chrome.

Current home composition (reference, not constraint): Hero (Arabic salawat + search + "now indexing" pill) → Domain Cabinet (4×2 tile grid) → Daily Instrument → Curated-for-today → Footer.

**The actual question, from first principles:** What should the home page DO? Job-to-be-done first; structure second. The current home assumes one shape fits everyone — interrogate that. Discriminate among 6 audience candidates: (a) scholars looking up a specific text, (b) students browsing a domain, (c) casual daily readers, (d) researchers tracing isnad chains, (e) devotional users, (f) translators.

**Foundation (non-negotiable for all advisors):**
1. Purpose-driven motion < 300ms, ease-out-strong, never animate from scale(0).
2. Restraint as editorial voice — Bodleian, not Awwwards.
3. Unseen details compound — :active scale(0.97), tap < 160ms, hover lift ≤2px, prefers-reduced-motion respected.
4. Editorial typography — Newsreader + Amiri serif. Mono for metadata only.
5. Beauty as leverage = restraint + craft.

Each advisor: 150-300 words. Must self-flag axiom violations.

---

## Advisor responses

### The Contrarian

The fatal flaw: you are debating the *shape of a home page* before evidence that the home page is the actual entry point. It almost certainly isn't. An 18,691-book classical Arabic corpus gets discovered through Google, a friend's WhatsApp link to a specific hadith, a citation in a paper, or a deeplink from a sermon footnote. The home is the page real users see *least*. You are spending craft budget on a lobby nobody walks through.

Second flaw: the persona list is a wishlist disguised as research. You have no telemetry. Picking "who visits" by committee is how you get the current 4×2 tile grid — a compromise that serves no one. And "verse-of-the-day" on a *Shia* library? That's a devotional gesture imported from Christian-devotional UX patterns (Bible.com). Interrogate whether it belongs at all.

What the home should DO: **one job — get the user into a specific text in under 3 seconds, or admit they didn't know what they wanted and offer one honest path in.** The fallback is not 7 domains in a grid — it's the last book the user opened, then a single sentence: *"Or browse 18,691 books across 7 traditions."* One link. No cabinet.

Structure under emil's axioms:
- Salawat (small, top, set once).
- Search, autofocused, Arabic + Latin. The whole page is essentially this field.
- Below: *Continue reading: [last book, last page]* — or, for first visit, three hand-picked starting texts (not 7 domains, not 39 categories — *three*, chosen editorially).
- One quiet text link: *Browse the full library*.
- Footer.

Kill the Daily Instrument on the home (lives at `/daily` if it survives). Kill the Domain Cabinet — sitemap pretending to be a feature.

**Self-flag:** none. Removes motion, removes chrome, lets typography and a single input carry the page. The bravest move is the empty page. You won't make it.

---

### The First Principles Thinker

"Home page" is a web convention inherited from portals and SaaS. **A library doesn't have a home page. A library has an entrance, a catalog, and a reading desk.** The conflation of these three is the original sin of the current composition.

Strip the UI conventions: the user is either (a) **returning to a text they were reading**, (b) **looking up a known citation**, or (c) **arriving cold and needing to know what 18,691 books even contain**. Everything else is editorial garnish that pretends to solve discovery but actually defers it.

Discriminate ruthlessly: the load-bearing audience is **the returning reader and the citation-seeker**. Casual daily readers and devotional users are real but secondary — they don't need a homepage, they need a bookmark to a daily page.

What it should DO, in priority order:
1. **Resume.** Put the reader back inside the last text they touched, one keystroke.
2. **Locate.** A search field that accepts citations (`Bukhari 1.1.2`), titles, authors, and Arabic phrases — direct to the page, not a results gallery.

Everything else is *a room down the hall*, not the entrance.

Structure (~640px column on cream):
- Library name in Newsreader.
- Single search input (cmd-K focused on load), placeholder cycles between citation/title/Arabic phrase — no animation, just text swap on focus.
- *Continue: al-Kafi, vol. 1, p. 47* in italic Newsreader, one click resumes (only if returning).
- Three plain text links: *Browse · Today · Index*. No tiles. No grid. No hero.

Daily verse, cabinet, curated row → `/today`, `/browse`, `/curated`.

**Self-flag:** cycling placeholder text technically violates axiom 1 (motion without explaining state). Mitigation: swap only on focus event, no transition. If still uncomfortable, ship a static placeholder.

---

### The Expansionist

**The biggest opportunity nobody's naming: this is not a library home — it's the *front matter* of a living manuscript that 18,691 books deep-link into.**

Stop thinking of the home as a *destination*. Start thinking of it as a **citation surface**. Every scholar, student, translator, tafsir-tweeter quoting a passage needs a canonical URL with a beautiful preview. If the home is also the **default Open Graph card factory** for the entire Shia textual tradition, this becomes the substrate underneath every WhatsApp share, every Substack footnote, every Wikipedia citation, every X post for the next twenty years. That is infrastructure. That is the Stripe-for-classical-Arabic-scholarship outcome.

Adjacent upside: the **"now indexing" pill** is a public progress signal. Treat it as a living changelog and you've invented **Arxiv for the turath**.

What the home should DO: resolve identity in one breath. *"You are standing in front of 18,691 books. Here is the one sentence the tradition wants you to read today, and here is the search bar that will find any line in any of them."* Job-to-be-done is **orientation, not navigation.** Pick reader (c) the daily reader as the default surface — only audience who returns. Scholars deep-link past the home; serve them via citation cards, not tiles.

Structure (restraint *is* the leverage):
- **One** Arabic line, centered, Amiri, large. The salawat or daily ayah.
- **One** search field beneath it. Cmd-K bound.
- **One** quiet line: *"18,691 books. 7 domains. Indexing today: Bihar al-Anwar vol. 42."* — italic Newsreader, living changelog.
- Cabinet collapses to italic link *"Browse the cabinet →"*.
- Every book page = a perfect citation card.

**Self-flag:** none. Leverage is what was removed.

---

### The Outsider

I landed from a link. Arabic calligraphy I can't read, the word "salawat" (no idea), a "now indexing" pill (indexing what? is the site broken?), tiles labeled "Hadith, Fiqh, Isnad" I'd need to Google. "Knowledge-graph reader for classical Arabic manuscripts" tells me *what it technically is*, not *why I'd stay*. "Verse of the day with isnad and tafsir" assumes I already know what an isnad is. The whole frame says: *if you have to ask, you don't belong here*. That's an unforced error.

What the home must DO in 5 seconds: **prove there is something here worth reading, right now, in a language I understand.** Not orient me to the corpus. Not show me 7 domains. Give me one passage, beautifully set, with a one-line plain-English frame: *"This is a 9th-century narration about [X]. From [book], compiled by [person]."* If I read that passage and feel something, I'll click. If I don't, no taxonomy grid will save you.

Structure:
- Single passage, centered, large. Arabic + translation side by side. Source line in mono.
- One sentence of plain-English context above (italic Newsreader, no jargon).
- Search below, placeholder a real example query.
- Quiet second screen (scroll, no pinning): cabinet as a *table of contents*, not a hero.
- Footer explains what the library is and for whom.

**Self-flag:** plain-English gloss must stay editorial italic, not marketing copy. Fade-in tooltip glossing "isnad" must stay ≤200ms ease-out-strong, no scale-from-zero.

---

### The Executor

Smallest shippable change next week: kill the Domain Cabinet's click-to-expand tray, replace with a server-rendered flat list of domains with category counts inline, each row a real `<a href="/domain/hadith">`. One commit. No state, no animation, no JS. Books open faster, crawlers index it, screen readers parse it. Done by Wednesday.

Monday-morning new behavior: **resume reading.** Backend already serves `/api/books/{urn}/pages/N`; add `localStorage` for last-read URN + page, surface as the top block — *"Continue: Sahih al-Bukhari, page 47."* One click, back in the text. Beats hero salawat, daily verse, and domain tiles combined for anyone who has visited twice.

For first-time visitors that block is empty — fall through to the search bar. Two-state home.

Build-this-week structure:
```
[Search bar — autofocused on desktop, not mobile]
[Continue reading: <book>, p.<N>]   ← only if localStorage hit
[Daily verse — static, server-rendered, no carousel]
[Domains — flat <ul>, category counts inline]
[Footer]
```

No hero, no tray, no "open library" CTA — the whole page IS the library. Cut the "now indexing" pill — chrome about the product, not the corpus.

**Self-flag:** autofocusing search on desktop technically violates axiom 1 (shifts focus state without user input). Mitigation: only autofocus if `window.matchMedia('(pointer: fine)').matches` AND no `#hash` in URL AND viewport > 768px. Skip on mobile to avoid summoning the keyboard.

Primary user: scholars + students returning to a text. Casual/devotional users get the daily verse as a courtesy, not the centerpiece.

---

## Anonymization mapping (for the peer review round)

| Letter | Advisor |
|---|---|
| A | First Principles Thinker |
| B | Executor |
| C | Expansionist |
| D | Outsider |
| E | Contrarian |

---

## Peer reviews

### Reviewer 1
**Strongest: E.** Only response that interrogates the question itself — challenging the home-page premise, naming the persona list as wishlist without telemetry, calling out verse-of-the-day as imported Christian-devotional UX (a sharp specific observation nobody else made). Lands the bravest structural call: kill the cabinet, kill the daily instrument, three editorial picks not seven domains. A and B converge on similar conclusions but with less courage. C's "OG card factory" framing is the second-best insight.

**Biggest blind spot: D.** D earnestly redesigns for the cold first-timer without questioning whether that user matters — for a Shia turath corpus the cold-from-Google user almost always lands on a *book page*, not the home. D optimizes the least-trafficked surface for the least-load-bearing audience. Beautifully observed UX critique, wrong target.

**All five missed:** **right-to-left as a structural constraint.** Arabic is the primary content; a centered ~640px column and cmd-K Latin search ergonomics are LTR-default assumptions. The home's axis, search input direction, and citation format (`Bukhari 1.1.2` vs `البخاري ١.١.٢`) need an RTL-first answer. Restraint in the wrong reading direction is still wrong.

### Reviewer 2
**Strongest: E.** Only response that interrogates the *premise of the question* before answering it. Correctly identifies that home pages of deep-link corpora are vestigial, names the telemetry vacuum, flags "verse-of-the-day" as imported Christian-devotional UX — a critique no one else dared make on a Shia library. Its structural prescription is the most ruthless and the most defensible under emil's restraint axiom.

**Biggest blind spot: C.** C's "citation surface / OG card factory" insight is genuinely good but it conflates *the home page* with *every book page*. The compounding it describes happens at `/book/{urn}/page/{n}`, not `/`. So C's structural recommendation (Arabic line + search + cabinet link) doesn't actually deliver the 10× move it just pitched. The thesis and the artifact are misaligned.

**All five missed:** **the URL itself is the product.** None addressed canonical URN design, slug stability, redirect policy, or how citations survive a corpus re-index. For a knowledge graph that will be cited for decades, URL permanence dwarfs home-page composition. Also missed: RTL/bidi behavior of a cmd-K input mixing Arabic and Latin.

### Reviewer 3
**Strongest: E.** The only response that interrogates the question itself — challenging the home-page premise, the persona list, *and* the verse-of-the-day as imported Christian-devotional UX. That last point is genuinely sharp; nobody else noticed. Also lands on the bravest concrete structure (three editorially-chosen starting texts, not 7 domains).

**Biggest blind spot: B.** B is the most shippable but treats the question as a frontend ticket. It accepts every premise — domains, daily verse, cabinet — and just rearranges them server-side. Misses that "biggest opportunity" was the actual prompt. Also: localStorage-based resume silently fails across devices, where scholars actually work.

**All five missed:** the corpus is **Arabic-first, right-to-left**. Not one response addresses RTL as a structural force — direction of search input, citation format, where "Continue reading" anchors, mirrored layouts. Second miss: **auth and personalization**. "Continue reading" assumes identity none specified. Third: **the 18,691 number is the brand** — only C treats it as load-bearing copy.

### Reviewer 4
**Strongest: E.** Only response that interrogates the question itself — naming the cultural-specificity check on verse-of-the-day that others miss. "You're spending craft budget on a lobby nobody walks through" is the load-bearing insight.

**Biggest blind spot: D.** D optimizes for the cold first-timer arriving confused but offers no evidence that audience matters more than returning readers. Assumes the home must onboard outsiders, when E correctly notes outsiders rarely land on the home at all. D's "plain-English gloss" risks turning a scholarly corpus into a museum placard.

**All five missed:** **Arabic-first / RTL as the primary reading direction.** Every proposed structure (search bar, Continue block, cmd-K) is described in LTR Western-reading-order terms. The home's directionality is a load-bearing design decision — possibly the most editorial choice on the page. Also missed: offline / low-bandwidth realities for the actual global Shia readership (Iran, Iraq, Lebanon, Pakistan).

### Reviewer 5
**Strongest: E.** Only response that interrogates whether the question itself is well-posed. Names the silent assumption (that the home is the entry point) and refuses to design for it without telemetry. Calls out "verse-of-the-day" as imported Christian-devotional UX. Its prescription is the most editorially restrained: search + Continue + three editorial picks.

**Biggest blind spot: D.** D optimizes for the cold first-timer and ignores that the load-bearing user is the returning reader arriving via deeplink. Its "explain isnad" instinct turns the home into a tutorial — exactly the marketing-italic failure it self-flags. A library that apologizes for its vocabulary in the chrome stops being a library.

**All five missed:** **Arabic-first, RTL-native composition.** Every response prescribed structure in English reading order with Arabic as ornament (salawat at top, translation beside). For a Shia turath corpus, the home should likely be RTL by default with Latin as the secondary surface. None named language-of-entry detection or the politics of which script anchors the page.

---

## Chairman synthesis

### Where the council agrees

Four of five advisors (Contrarian, First Principles, Expansionist, Executor) converge on the same load-bearing user: **the returning reader arriving via deeplink or wanting to resume a specific text**. Only the Outsider dissents, and the peer reviewers unanimously flag that read as the weakest.

All five agree the current composition is doing too much. The Domain Cabinet, the click-to-expand tray, the hero CTA, the persona-flattering tile grid — sitemap furniture pretending to be features. The page is a lobby, not a reading desk.

Four of five agree on the same primitive: **a single search/command input as the page's center of gravity**, accepting citations, titles, authors, and Arabic phrases, routing directly to the page rather than a gallery.

Four of five agree the "verse-of-the-day" loses its claim to the home. The Contrarian names it as imported Christian-devotional UX; the others demote it to `/today` or a quiet secondary surface. Only the Outsider keeps a single beautiful passage central — and even there the cabinet moves off the hero.

All five agree the home should be radically smaller. The disagreements are about what occupies the silence.

### Where the council clashes

**Is the home a destination or a vestigial surface?** The Contrarian says vestigial — the bravest move is the empty page, because real users enter via deeplinks. The Expansionist inverts it — the home is infrastructure, the Open Graph card factory for the entire tradition. First Principles and Executor treat it as a small functional desk (Resume + Locate). The Outsider treats it as a first-impression onboarding moment. Reviewer 2 catches that the Expansionist's actual prescription doesn't deliver its own thesis — citation compounding happens at `/book/{urn}/page/{n}`, not at `/`.

**Who is the home for?** Four say returning readers and citation-seekers. The Outsider says the cold first-timer. Four reviewers independently rejected that framing — a Shia turath library that apologizes for its own vocabulary in the chrome stops being a library, and the cold-from-Google user almost never lands on `/` anyway.

**Resume reading: localStorage or auth?** The Executor proposes localStorage as the shippable path. Reviewer 3 correctly flags it as silently broken across devices, where scholars actually work. None of the advisors resolved the identity question.

### Blind spots the council caught

**Unanimous miss across all five reviewers: Arabic-first, RTL-native composition.** Every advisor described structure in English reading order with Arabic as ornament — salawat "at top," translation "beside," cmd-K input in Latin ergonomics, citations like `Bukhari 1.1.2` instead of `البخاري ١.١.٢`. For a Shia turath corpus serving Iran, Iraq, Lebanon, Pakistan, the home's directionality is probably the single most editorial decision on the page. No advisor named language-of-entry detection or which script anchors by default.

**URL permanence as the actual product** (Reviewer 2). For a knowledge graph that will be cited for decades, canonical URN design, slug stability, and redirect policy across re-indexes dwarf any home-page composition choice. No advisor named this.

**The telemetry vacuum** (Contrarian, amplified by all reviewers). The entire persona list is a wishlist. No advisor except the Contrarian refused to design on top of unverified personas.

**Offline / low-bandwidth realities** (Reviewer 4). None addressed it.

### The recommendation

Take the Contrarian's frame, First Principles' structural primitives, the Expansionist's one insight that survives review, and resolve the RTL miss the council made.

The home does **two things** in priority order: **Resume** and **Locate**. Nothing else earns the silence.

Compose it **RTL-native**. Arabic anchors the page; Latin is the secondary surface, swapped on language-of-entry detection. Salawat set once, small, top-of-page (right side in RTL). One search input, autofocused only on `pointer: fine` + viewport > 768px, accepting Arabic phrases, transliteration, and citations in both `البخاري ١.١.٢` and `Bukhari 1.1.2` form. Below: *Continue reading: [book, page]* if a session exists (server-side from a lightweight identity token, not localStorage — Reviewer 3 is right). First visit: three editorially-chosen starting texts, not seven domain tiles. One quiet text link: *Browse the full library*. Footer.

Kill the Domain Cabinet. Move the daily verse to `/daily`. Cut the "now indexing" pill from the home — keep it on `/changelog` as the Expansionist's "Arxiv for the turath" signal.

**Where the Expansionist's insight actually lives**: not on `/`, but on every `/book/{urn}/page/{n}` — perfect Open Graph cards, stable URNs, citation-grade preview. That is the compounding surface. Treat URL permanence as a first-class product decision before shipping anything else.

The Outsider's instinct to explain `isnad` belongs in a glossary on the book page, not in the home's chrome. A library does not apologize for its vocabulary.

### The one thing to do first

Before redesigning the home, **instrument the current site for one week** and answer one question: *what fraction of sessions begin on `/` versus on a deeplinked book page, and what's the language of the first interaction?* Every structural choice above — RTL default, Resume vs Locate priority, whether the home deserves craft budget at all — collapses into a guess until that data exists. The Contrarian's load-bearing insight was the telemetry vacuum. Fill it first.
