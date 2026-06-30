# Handoff — Home page revamp

**To:** the next agent, with no prior session memory.
**From:** the previous agent who ran the discovery + design phases.
**Date:** 2026-05-24.
**Status:** design committed; ready to build.

You are picking up a redesign of the Shia Online Library home page. Discovery, council critique, design consultation, and the user's ground-truth overrides are all done. **Your job is to execute the design spec below.** Do not redo the design work. Do not ask the user about font/color/layout choices — they're locked. Ask only about ambiguity in the *implementation*.

Read this entire document before writing any code.

---

## 1. The product in three sentences

**Shia Online Library** (codename `sol-next2`) — a knowledge-graph reader for classical Arabic manuscripts. 18,691 indexed books across 7 domains (Hadith, Qurʾan, Fiqh, Theology, Biography, Sciences, Devotional) and 39 categories. Currently Arabic-only; English translations are coming, which is why the chrome is **LTR**.

Repo: `/home/dev/code/sol-next2`. Branch: `feat/ux-quick-wins`. Git user: `urspeechislight`.

## 2. Tech stack — non-obvious bits

- **Frontend:** React + Babel **in the browser** via `<script type="text/babel">` tags. **No build step.** No bundler. No TS. Each `.jsx` file registers exports on `window.SOL_*` globals so siblings can import-by-window-name. Script load order in `index.html` matters — see line 90+ of `src/frontend/index.html`.
- **Static server:** something serves `src/frontend/` on `:8765`. Reload to see edits.
- **Backend:** FastAPI on `:8001`. Already running. Logs at `/tmp/sol-next2-uvicorn.log`. Restart command:
  ```bash
  kill $(ss -ltnp 2>/dev/null | grep :8001 | grep -oP 'pid=\K[0-9]+') 2>/dev/null; sleep 1
  SOL_BOOKS_DIR=/home/dev/code/sol-next/data/books \
    nohup uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001 --app-dir src \
    > /tmp/sol-next2-uvicorn.log 2>&1 & disown
  ```
- **Corpus path is env-only.** `SOL_BOOKS_DIR` lives in a gitignored `.env`. Don't hard-code paths to `/home/dev/code/sol-next/...` in source — the `external_refs` harness rule (ISO-001) will block you.
- **Backend changes:** routes register repo functions directly via `router.add_api_route(...)` where the repo function has the right signature. `models/reader.py::BookPage` (NOT `Page` — that name is owned by `models/pagination.py::Page[T]`). `ResourceNotFoundError` from `backend.core.errors` is raised by repos; `main.py` has one global exception handler that maps it to 404. Don't reintroduce per-route `HTTPException(404)` wrappers.

## 3. CRITICAL — Verify the harness fires before you trust it

There is a story you need to know.

`.claude/settings.json` invokes PreToolUse hooks. Until last session, it called them with bare `python3`, which on this machine resolves to a brew Python that has no PyYAML. The hook crashed at `import yaml` (exit 1). Claude Code treats hook exit-1 as a non-blocking error and **allows the tool call**. The harness was silently bypassed for an entire session.

**It's fixed now** — `.claude/settings.json` uses `uv run --quiet --project "$CLAUDE_PROJECT_DIR" python …`, and `lefthook.yml` uses `uv run --quiet python …`. But:

**Before you write a single line of code, run this canary:**

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"/home/dev/code/sol-next2/src/frontend/__canary.jsx","content":"const c = \"#ff0000\";"}}' \
  | uv run --quiet --project "$PWD" python "$PWD/.claude/hooks/pre_tool_use_write.py"
```

You should see `⛔ BLOCKED by no_raw_colors (DS-001)` and exit code 2. If it exits 1 with a `ModuleNotFoundError`, the harness is still broken — stop and tell the user.

If you want to test it through Claude Code's actual tool path, attempt to `Write` a JSX file containing `color: '#ff0000'`. The hook should reject it. If Claude Code lets it through, the session is broken.

**Harness invocations you'll use:**
- All 143 self-tests: `.venv/bin/python -m pytest .claude/tests -q`
- Lint specific files: `uv run --quiet python .claude/hooks/lint_staged.py <file...>`
- Full retroactive scan: `find src -type f \( -name "*.py" -o -name "*.jsx" -o -name "*.js" -o -name "*.css" -o -name "*.html" \) | xargs uv run --quiet python .claude/hooks/lint_staged.py`

## 4. Memory rules from this session — apply them

These are hard rules saved to user memory. Violating them is treated as a fireable offense by the user.

### 4a. NO META-NARRATION in UI or code

**Banned in user-facing UI text:**
- Mentions of design tokens, harness, SSOT/DRY, lint rules, "raw colors blocked", "prototype", "v0.1", "knowledge graph", references to past versions or sibling projects (e.g. "sol-next1").
- Footer/header taglines that describe internals instead of the product.

**Banned in code comments:**
- "Replaces the earlier X layout", "this was previously Y", "moved out of Z so it fits under cap".
- "The Bodleian redesign…", "Per emil rules…", "per minimalist-ui protocol…", "per the council verdict".
- ASCII diagrams of "old vs new" arrangements.
- Recaps of what just changed in this session.
- Section divider banners like `// ─── HEAD STRIP ───` are tolerated; multi-paragraph design narratives are not.

**Default is no comment.** Only add one when the WHY is non-obvious (hidden constraint, subtle invariant, workaround for a specific bug). If the comment would belong in a PR description, it doesn't belong in the code.

### 4b. NO bypass renames for SSOT/DRY violations

If the harness flags two functions/classes as duplicates: actually consolidate them. Don't rename one to dodge the rule. The exception is when the items genuinely represent different concepts that incidentally share a name (e.g. `Page[T]` envelope vs `BookPage` content) — then rename for *disambiguation* with explicit justification. The harness was fixed in the previous session: `function_duplication` and `class_duplication` will fire correctly now.

### 4c. Make the call

The user wants a senior engineer/designer, not a survey-taker. Pick the best modern default and proceed. Only ask the user about domain/brand specifics they alone can answer (e.g. "is the salawat string correct?" — yes, ask; "should we use Newsreader or Geist for body?" — no, decide).

## 5. Hard ground truths from the user (non-negotiable)

1. **LTR stays.** Don't make the home RTL-native. (The earlier llm-council recommended RTL unanimously; the user overruled.)
2. **Verse-of-the-Day AND Hadith-of-the-Day both stay** on the home, side-by-side. Currently static; rotation comes later.
3. **Preserve visual dynamic character.** Restraint applies to chrome, not editorial content. The user explicitly does not want a monastic empty page.
4. **Salawat needs smart placement** — not hero, not filler. (Spec below places it in a 64px eyebrow band at page top.)
5. **Tiles + Browse menu = redundancy.** Kill the tile grid. The header's Browse dropdown is the navigation.
6. **No autofocus** anywhere. The user has internalized emil's axiom 1.

## 6. The design spec (committed — do not negotiate)

This came out of an llm-council session followed by a minimalist-ui skill consultation. Council report at `docs/councils/2026-05-24-home-revamp-report.html`; full transcript at `docs/councils/2026-05-24-home-revamp-transcript.md`.

### 6a. Composition

Four visible blocks, top to bottom. Header (sticky, unchanged) and footer (already shipped editorial style) bracket them.

```
[ HEADER — sticky, already exists, do not touch except as noted in 6f ]

[1] EYEBROW BAND — ~64px, max-width container, 1px sepia rule below
    Left:  § BEFORE THE READING            (JetBrains Mono caps, color=accent)
    Right: اللهم صل على محمد وآل محمد         (Amiri italic 18px, dir=rtl)

[2] PRIMARY FRAME — max-w 720, vertical padding 96px (py-24)
    Centered editorial line above the field:
      "Eighteen thousand books. Search any line."   (Newsreader italic 24px, color=fg-2)

    SEARCH CARD (default state):
      A 56px-tall input with 1px border, 6px radius, NO shadow.
      Inside the field, left: small custom loupe SVG (16x16, 1.5px stroke).
      Placeholder: 'Search any line in any book — e.g. "Bukhari 1.1.2" or "في فضل العلم"'
      Right edge: <kbd>⌘K</kbd> hint (mono, 11px, 1px border, 4px radius, bg-2 fill).

    Below the field, three quiet suggestion buttons separated by · :
      "Bukhari 1.1.2"  ·  "Kashf al-Asrar"  ·  "في فضل العلم"
      Each is a real <button type="submit"> that submits the form with that q value.

    RESUME CARD (replaces search card when localStorage has last-read urn+page):
      Eyebrow: § CONTINUE READING (mono caps, accent)
      Book title (Newsreader italic 24px), chapter (Newsreader 17px, fg-2),
      "page N of M" (JetBrains Mono 12px, fg-3).
      CTA button: solid bg-fg1, text bg-0, slight 6px radius, no shadow.
        Label "Resume".
      Quiet link below: "or search any line" (Newsreader italic 14px, accent)

[3] DAILY PAIR — 12-col asymmetric bento, max-w 1100, py-20
    Section header:
      Eyebrow: § II · Today           (mono caps, accent, letter-spacing .12em)
      Title: The Daily Pair           (Newsreader 24px; "Daily Pair" italic accent)

    Two cards, asymmetric grid: grid-template-columns: 7fr 5fr; gap: 24px.
    Mobile (<880px): single column stack.

    Card structure (each):
      <article class="daily__card">
        <header>
          <span class="mono-eyebrow">§ Verse of the day</span>   <!-- or Hadith of the day -->
          <span class="mono-cite">Q 67:2</span>                  <!-- or al-Kāfī 1.1.2 -->
        </header>
        <p class="ar-display" lang="ar" dir="rtl">{Arabic}</p>
        <p class="en-body">{English translation, when available}</p>
        <a class="quiet-link" href="...">Read full sūrah →</a>
      </article>

    Card style:
      background: var(--bg-1)
      border: 1px solid var(--rule-1)
      border-radius: 8px
      padding: 32px
      NO box-shadow at rest.

    Hover (only when prefers-reduced-motion allows):
      transition: transform 200ms cubic-bezier(0.23,1,0.32,1), box-shadow 200ms;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px var(--shadow-1);   /* shadow-1 has 6% alpha; under 5% guidance is the spirit, 6% is the accepted bend */

    :active: transform: scale(0.99);

    Type inside:
      .mono-eyebrow: JetBrains Mono 500, 10px, letter-spacing .14em, uppercase, color var(--accent)
      .mono-cite:    JetBrains Mono 400, 11px, color var(--fg-3)
      .ar-display:   Amiri 700, clamp(20px, 2.2vw, 28px), line-height 1.7, color var(--fg-1)
      .en-body:      Newsreader italic 400, 17px, line-height 1.55, color var(--fg-2), margin-top: 16px
      .quiet-link:   Newsreader italic 14px, color var(--accent), no underline,
                     hover → var(--accent-strong)

    Scroll-entry (gated on prefers-reduced-motion):
      opacity:0 → 1, transform: translateY(12px) → 0,
      duration 280ms, easing cubic-bezier(0.23, 1, 0.32, 1),
      stagger: animation-delay: calc(var(--index, 0) * 80ms)
      NOTE: minimalist-ui protocol § 7 says 600ms; emil's axiom 1 caps at 300ms.
      We resolve toward emil. 280ms is correct.

[4] CHANGELOG STRIP — single line, mono, very quiet
    Indexed today · 03 new texts · Tatawwur al-Muṣṭalah · 336 pp · all changes →
    Color: var(--fg-3). Font: JetBrains Mono 500, 12px, letter-spacing .04em.
    The "all changes →" trailing link uses var(--accent).
    Background: transparent. 1px sepia rule above (--rule-1).
    Replaces the "now indexing" pill from the old hero.

[ FOOTER — already shipped, do not touch ]
```

### 6b. Salawat placement — locked

The salawat lives in block [1] as the page-opening editorial eyebrow band. It is not in the hero. It is not in the daily card. It is the spiritual prefix to engaging with the corpus, set once, no animation, never claims the visual hero. Move it nowhere else.

The Arabic string for now: `اللهم صل على محمد وآل محمد`. The mono caps caption to its left is `§ BEFORE THE READING`. Don't translate the salawat into the eyebrow caption — they live in separate languages on the same band.

### 6c. Type pairing — locked, all-serif

| Role | Family | Weight / style |
|---|---|---|
| Latin editorial display | Newsreader | 500–700, italic enabled, opsz axis |
| Latin body | Newsreader | 400–500 (same family — deliberate; see § 6c-note) |
| Arabic display | Amiri | 700, italic available |
| Arabic body | Amiri | 400 |
| UI labels / nav / small caps | Newsreader | `font-variant-caps: all-small-caps`, letter-spacing 0.06em |
| Metadata / mono / `<kbd>` | JetBrains Mono | 400–500 |

**6c-note: justified deviation from minimalist-ui protocol § 3.** That protocol wants a separate clean sans (SF Pro / Geist / Switzer) for body and UI. We are *all-serif* on purpose. This is a manuscript library; a Notion-register sans would break the book-not-dashboard voice the project depends on. Newsreader has the opsz axis specifically to do both editorial display and body. UI labels get the same face with small-caps + tracking, which is the editorial-UI tradition (NYT, LRB). JetBrains Mono carries metadata that would otherwise need a sans. The deviation is declared so it doesn't read as accidental.

Font imports already in `index.html`:
- Newsreader (`ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500;1,6..72,600`)
- JetBrains Mono (`wght@400;500;600`)
- Amiri (`ital,wght@0,400;0,700;1,400`)
- Vazirmatn, Scheherazade New, Noto Naskh Arabic, Reem Kufi — kept as user-selectable tweaks for the Arabic face; default is Amiri.

Token names already in `tokens.css`:
- `--font-display` → Newsreader
- `--font-sans` → Newsreader (same; serif body)
- `--font-arabic` → Amiri
- `--font-arabic-display` → Amiri
- `--font-mono` → JetBrains Mono
- `--font-arabic-ui` → Vazirmatn (kept available but not used in the new spec)

### 6d. Color palette — locked, both modes

Replace the current day/night blocks in `src/frontend/tokens.css` with these exact values. Hue band 50–80 for warm neutrals; hue 30–35 for the brick accent.

**LIGHT (Day) — applies to `:root, [data-theme='day']`:**

| Token | Value |
|---|---|
| `--color-bg-0` | `oklch(0.970 0.012 80)` |
| `--color-bg-1` | `oklch(0.945 0.013 75)` |
| `--color-bg-2` | `oklch(0.910 0.018 75)` |
| `--color-border-1` | `oklch(0.20 0.02 50 / 0.10)` |
| `--color-border-2` | `oklch(0.20 0.02 50 / 0.20)` |
| `--color-fg-1` | `oklch(0.20 0.02 50)` |
| `--color-fg-2` | `oklch(0.42 0.02 50)` |
| `--color-fg-3` | `oklch(0.58 0.015 60)` |
| `--accent-h` | `30` |
| `--color-accent` | `oklch(0.45 0.14 var(--accent-h))` |
| `--color-accent-strong` | `oklch(0.38 0.16 var(--accent-h))` |
| `--color-accent-soft` | `oklch(0.45 0.14 var(--accent-h) / 0.10)` |
| `--color-accent-border` | `oklch(0.45 0.14 var(--accent-h) / 0.32)` |
| `--color-success` | `oklch(0.45 0.13 145)` |
| `--color-warning` | `oklch(0.55 0.13 70)` |
| `--color-danger` | `oklch(0.48 0.16 25)` |
| `--color-info` | `oklch(0.45 0.10 220)` |
| `--color-marginalia` | `oklch(0.55 0.10 60)` |
| `--shadow-1` | `oklch(0.20 0.02 50 / 0.06)` |

**DARK (Night) — applies to `[data-theme='dark'], [data-theme='night']`:**

| Token | Value |
|---|---|
| `--color-bg-0` | `oklch(0.150 0.011 50)` |
| `--color-bg-1` | `oklch(0.190 0.012 50)` |
| `--color-bg-2` | `oklch(0.230 0.013 50)` |
| `--color-border-1` | `oklch(0.94 0.01 80 / 0.08)` |
| `--color-border-2` | `oklch(0.94 0.01 80 / 0.16)` |
| `--color-fg-1` | `oklch(0.94 0.010 80)` |
| `--color-fg-2` | `oklch(0.74 0.010 70)` |
| `--color-fg-3` | `oklch(0.55 0.015 65)` |
| `--accent-h` | `35` |
| `--color-accent` | `oklch(0.74 0.12 var(--accent-h))` |
| `--color-accent-strong` | `oklch(0.82 0.14 var(--accent-h))` |
| `--color-accent-soft` | `oklch(0.74 0.12 var(--accent-h) / 0.18)` |
| `--color-accent-border` | `oklch(0.74 0.12 var(--accent-h) / 0.42)` |
| `--color-success` | `oklch(0.72 0.13 145)` |
| `--color-warning` | `oklch(0.78 0.13 70)` |
| `--color-danger` | `oklch(0.70 0.16 25)` |
| `--color-info` | `oklch(0.72 0.10 220)` |
| `--color-marginalia` | `oklch(0.74 0.10 60)` |
| `--shadow-1` | `oklch(0 0 0 / 0.4)` |

`tokens.css` currently has many decorative-palette tokens (`--color-gold-*`, `--color-night-*`, `--color-parchment-*`, `--color-paper-*`, `--color-tint-white-*`, `--color-shadow-*`, `--color-domain-tint-*`). Most are leftovers from the original claude.ai/design export. **Audit them in light of this composition:** the new home only references `--color-bg-{0,1,2}`, `--color-border-{1,2}`, `--color-fg-{1,2,3}`, `--color-accent*`, `--shadow-1`, `--color-rule-sepia`, font tokens, and spacing tokens. Decorative tokens that no live file still consumes can come out — but the `screens-home-{hero,daily,instrument}.css` files (which are about to be replaced) still reference some of them, so do the deletion in the same commit you replace those CSS files.

### 6e. Daily-pair component spec

The HTML/CSS structure is in § 6a [3]. Implementation notes:

- The hadith side needs **a real hadith.** `data/daily.json` currently has only `verse` / `book` blocks. Add a `hadith` block to the JSON, extend `backend/models/daily.py::Daily` with the new field, extend `backend/repositories/daily.py::get_today` to return it, and extend the frontend `data.js`/`data-daily.js` fallback to mirror.
- The user said hadith content can match the existing verse for now (rotation is later) — but it must be a real hadith, not lorem. If you don't have one handy, use a short well-known one: e.g. `إنما الأعمال بالنيات` from al-Bukhārī / al-Kāfī. Cite it correctly.
- Each card's "Read full sūrah →" or "Read in context →" link must route to a real `/api/books/{urn}/pages/N`. If you can't resolve a real URN for the curated daily content, the link should disappear, not 404.

### 6f. Search component spec

The search input now lives in **two places sharing one form/handler:**
1. The slim inline input in the sticky header (already exists in `src/frontend/app-header.jsx`) — keep it, restyle it to match § 6a [2] visual treatment.
2. The large centered input in block [2] above the daily pair.

Behavior:

- **No autofocus** anywhere. Page load focuses nothing.
- `cmd+K` / `ctrl+K` from anywhere on the page focuses the inline header input. This is user-initiated, emil-compliant. Implement once at the AppRoot level with a `keydown` listener.
- Click on either field → focus (user-initiated).
- Three suggestion buttons below the centered field are real `<button type="submit">` elements; clicking submits the form with that `q` value.
- On submit, the front end pre-parses `q`:
  - If `q` matches `/^[A-Za-zāīūṣṭḍẓʾʿ؀-ۿ\- ]+\s+\d+(\.\d+){1,3}$/` (citation form like `Bukhari 1.1.2`), route to `/book/{slug}/{section}`.
  - Else, route to `/search?q=…`. (The /search route may not exist yet; if it doesn't, ship the form with that route as a TODO and link out to the library list as a soft fallback.)
- The field uses `var(--fg-1)` text on `var(--bg-1)` background, 1px `var(--border-2)` border, 6px radius, **no shadow**.
- On `:focus-within`: border becomes `var(--accent)`, plus a 3px outline of `var(--accent-soft)`. No box-shadow.

The `cmd+K` hint inside the input is a `<kbd>` element styled per minimalist-ui § 5: `1px solid var(--color-border-1); border-radius: 4px; background: var(--bg-2); font-family: var(--font-mono);`.

### 6g. Self-check the consultant already ran (don't repeat, but honor it)

The minimalist-ui consultant confirmed the spec is compliant on these axes — do not break any of them during implementation:

- No Inter/Roboto/Open Sans anywhere.
- No Lucide/Feather/Heroicons. The project ships custom SVG primitives in `src/frontend/primitives.jsx` (icon set). Use those.
- No heavy shadows. Max shadow alpha is 6% (`--shadow-1` in light mode).
- No gradients on primary surfaces. The header's `backdrop-filter: blur(8px)` is the permitted "subtle navbar blur" exception.
- No `rounded-full` on large containers. Cards 8px radius, CTA 6px, field 6px, kbd 4px. Pills are allowed on *small* status indicators only (e.g. the green `●online` chip in the header).
- No emojis.
- No AI copywriting clichés (elevate / seamless / unleash / next-gen / delve).
- All motion under 300ms, ease-out-strong `cubic-bezier(0.23, 1, 0.32, 1)`.
- No autofocus anywhere.
- `prefers-reduced-motion: reduce` → all transitions become `transition: none !important`.
- `:active` states use `scale(0.97)` for buttons, `scale(0.99)` for cards.
- Hover lifts use `translateY(-1px)` or `translateY(-2px)` max.
- Never animate from `scale(0)` — start from `0.95` or higher with opacity 0.

## 7. Ship order

Do these in order. Take screenshots after each step. Run the harness retroactively after each step (`uv run --quiet python .claude/hooks/lint_staged.py <files>`) and resolve any BLOCK before moving on.

1. **Tokens.** Update `src/frontend/tokens.css` with the committed palettes from § 6d. Audit and remove decorative tokens no live file consumes anymore. Verify `lint_staged.py tokens.css` is clean.

2. **Eyebrow band [1].** Create `src/frontend/screens-home-eyebrow.jsx` + `screens-home-eyebrow.css`. Link the CSS in `index.html` after `screens-home.css`. Add the script tag in the right order. Register `window.SOL_COMPS.HomeEyebrow`. Mount it as the first child of the home composition in `screens-home.jsx`.

3. **Primary frame [2].** Rewrite `src/frontend/screens-home-hero.{jsx,css}` to implement the search/resume card per § 6a [2] and § 6f. Wire `localStorage` reads for `sol:last-read-urn` and `sol:last-read-page`. Implement the citation-form pre-parser. Drop the corner ornaments, the "TRY: author=…" chip row, the salawat (moved to block [1]), and the "now indexing" pill (moves to block [4]).

4. **Daily pair [3].** Rewrite `src/frontend/screens-home-daily.{jsx,css}` (or replace the current `screens-home-instrument*.jsx` if that's where the verse lives — check which is loaded by the home). Implement the side-by-side bento. Add the hadith block to:
   - `data/daily.json` (real hadith content + cite)
   - `src/backend/models/daily.py::Daily` (new field)
   - `src/backend/repositories/daily.py::get_today` (return the new field)
   - `src/frontend/data.js`/`data-domains.js`/`data-daily.js` fallback (mirror the schema so the page still renders if `/api/daily` is down)
   Run the backend's pytest if any exists (`uv run --quiet python -m pytest src/backend -q` if there's a test dir).

5. **Changelog strip [4].** Build a tiny `src/frontend/screens-home-changelog.jsx` (or fold into the daily file if it's small enough). Static for now. Replace the old "now indexing" pill, which the previous step removed from the hero. Link to `/changelog` (route may not exist; ship as a TODO if so).

6. **Kill the cabinet.** Delete `src/frontend/screens-home-cabinet.jsx` and `src/frontend/screens-home-cabinet.css`. Remove their `<script>` and `<link>` tags from `index.html`. Remove `window.SOL_COMPS.DomainCabinet` references in `screens-home.jsx`. The header Browse dropdown stays as the sole navigation entry to domains.

7. **Verify.**
   - `find src -type f \( -name "*.py" -o -name "*.jsx" -o -name "*.js" -o -name "*.css" -o -name "*.html" \) | xargs uv run --quiet python .claude/hooks/lint_staged.py` — must exit 0.
   - `.venv/bin/python -m pytest .claude/tests -q` — must show 143/143 pass.
   - Backend restart per § 2 above; `curl -s http://localhost:8001/health` returns 200.
   - Screenshot the home; verify day mode renders correctly (cream paper, brick accent, all four blocks visible).
   - Flip to night mode via the tweaks panel; verify dark mode renders correctly (warm carbon canvas, glowing brick accent).
   - Verify keyboard `cmd+K` focuses the inline header search from anywhere.
   - Verify clicking a suggestion chip below the centered field actually submits.

## 8. What you should NOT do

- Don't redo the council / design consultation work. It's done. The output is committed.
- Don't add a sans-serif face. The all-serif decision is intentional (§ 6c).
- Don't make the page RTL. LTR is locked (§ 5.1).
- Don't reintroduce the Domain Cabinet tile grid (§ 5.5).
- Don't add ASCII before/after diagrams or "Bodleian redesign" prose to comments (§ 4a).
- Don't rename a duplicate to dodge the harness; consolidate (§ 4b).
- Don't trust the harness without running the canary (§ 3).
- Don't auto-focus the search field on page load. Use `cmd+K` (§ 6f).
- Don't add a placeholder rotator that cycles between example queries — use static suggestion chips (§ 6a [2], § 6f). Cycling violates emil's axiom 1.

## 9. Files you will likely touch

```
src/frontend/tokens.css                                      # palettes
src/frontend/index.html                                      # link/script tags
src/frontend/screens-home.jsx                                # composition
src/frontend/screens-home-eyebrow.{jsx,css}                  # NEW (block 1)
src/frontend/screens-home-hero.{jsx,css}                     # REWRITE (block 2)
src/frontend/screens-home-daily.{jsx,css}                    # REWRITE (block 3)
src/frontend/screens-home-changelog.{jsx,css}                # NEW (block 4)
src/frontend/screens-home-cabinet.{jsx,css}                  # DELETE
src/frontend/screens-home-instrument.{jsx,css}               # likely DELETE (verify it's no longer rendered)
src/frontend/screens-home-instrument-panels.jsx              # likely DELETE
src/frontend/app-header.jsx                                  # restyle inline search + add ⌘K handler
src/frontend/data.js                                         # daily.hadith fallback
src/frontend/data-domains.js                                 # no change expected

data/daily.json                                              # add hadith block

src/backend/models/daily.py                                  # add hadith field
src/backend/repositories/daily.py                            # extend get_today
```

## 10. Files you must NOT touch without good reason

```
.claude/**                # the harness — only the user changes rules
.env                      # operator's local env — gitignored
src/backend/main.py       # ResourceNotFoundError handler is correct; don't add per-route 404 wrappers
src/backend/api/*.py      # uses router.add_api_route + repo functions registered directly; don't re-wrap
src/backend/core/errors.py
docs/councils/*           # historical records, leave alone
```

## 11. How to know you're done

Definition of done:
- All seven ship-order steps complete.
- Harness retroactive scan exits 0 (only WARNs allowed, no BLOCKs).
- 143 harness self-tests pass.
- Day mode and night mode both render correctly; toggle works.
- `cmd+K` focuses the inline search from any scroll position.
- Three suggestion chips below the centered search each submit a real query.
- The four content blocks are visually distinct, no shared borders/halos crossing them.
- Backend smoke endpoints (`/health`, `/api/domains`, `/api/daily`, `/api/books?limit=2`) all return 200.
- A randomly chosen real book URN (e.g. fetched from `/api/books?limit=1`) returns 200 on detail/toc/page endpoints.
- A bogus URN returns 404 with the `{"detail":"No <kind> with identifier=…"}` envelope from the global handler.

When all of that is true, screenshot the home (day + night) and report back to the user.

## 12. Reference — emil's axioms verbatim

If you find yourself unsure during implementation, re-read these:

1. **Purpose-driven motion.** Animation only if it explains state or prevents jarring change. No animation on keyboard-initiated or 100/day actions. Every animation under 300ms. Use `cubic-bezier(0.23, 1, 0.32, 1)` for entering elements. Never animate from `scale(0)`.
2. **Restraint is the editorial voice.** Reading-room interface — Bodleian, not Awwwards. No GSAP scroll-pinning, kinetic typography, fullscreen video, hero scrolljacking.
3. **Unseen details compound.** Every interaction must feel correct: `:active scale(0.97)`, tap feedback under 160ms, hover lift ≤2px, `prefers-reduced-motion` respected.
4. **Editorial typography.** Newsreader + Amiri serif. Mono for metadata. Italic for editorial emphasis.
5. **Beauty as leverage** = restraint + craft, not novelty.

## 13. If you're blocked

- Harness issue → re-run the § 3 canary; if it doesn't BLOCK, stop and tell the user the hook is broken again.
- Schema ambiguity (e.g. what's the canonical shape of a hadith record?) → look at the existing `data/daily.json` `verse` block as the pattern, and `src/backend/models/daily.py` for the typed shape. Mirror the structure.
- Real data missing (e.g. the user wants a specific hadith of the day) → ask the user *that specific question* and proceed with a sensible default if they don't reply.
- Design ambiguity → re-read this document. The spec is meant to be unambiguous. If something is genuinely undefined, default toward restraint + minimalism + LTR + serif. Do not invent register.

— end of handoff —
