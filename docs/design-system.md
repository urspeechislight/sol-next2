<!-- GENERATED from .claude/policies/quality.yaml and the handler DOC anchors by .claude/lib/gen_standards_docs.py. Do not edit by hand; run `pnpm docs:standards`. -->

# Design System

Enforced by the harness; see the named handler under `.claude/lib/handlers/` for
the exact check.

<a id="hard-rules"></a>

## Hard Rules

- **DS-001** (`no_raw_colors`, block) — Raw color literals (#hex, rgb, oklch...)
  only in tokens.css. _Single source of truth for color. Theme retuning must be
  one edit._
- **DS-002** (`no_inline_styles`, block) — No inline style props in React .tsx
  and .jsx files. _Inline styles bypass the design system and twMerge._
- **DS-003** (`primitive_usage`, block) — Routes must use design-system
  primitives, not raw HTML elements. _Raw <button>/<input> drift from the rest
  of the app._
- **DS-004** (`variants_only`, block) — Status → palette maps live only in
  variants.ts. _Vocabulary spread across files breaks rebrandability._
- **DS-005** (`no_arbitrary_values`, block) — Tailwind arbitrary values for the
  spacing / sizing / type scales (text-[14px], p-[7px], w-[200px]) are blocked;
  only values that resolve to a token (bg-[var(--color-x)]) pass. _no_raw_colors
  covers color; this closes the same SSOT hole for the spacing and type scales._
