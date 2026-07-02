// narrators.ts:narrator-name linkage. Reading units carry no narrator IDs, so
// we join reading text to the rijāl/canonical registries BY NAME, using the
// name fold from lib/arabic.ts (normalizeName):
//   1. buildNarratorIndex:token-keyed lookup over NarratorRecord[].
//   2. annotateText:split a string into plain + narrator segments (longest,
//      non-overlapping, >=2-token match for precision).
// Pure functions only; no DOM, no fetch.

import { normalizeName } from './arabic';
import type { CanonicalEntry, NarratorRecord, RijalEntry } from './types';

const STOP = new Set(['بن', 'ابن', 'بنت', 'عن', 'ابي', 'ابو', 'ال', 'عبد', 'حدثنا', 'اخبرنا']);

function tokens(name: string): string[] {
  return normalizeName(name).split(' ').filter(Boolean);
}

export interface NarratorIndex {
  byFirstToken: Map<string, { toks: string[]; record: NarratorRecord }[]>;
  size: number;
}

/** Build a token-keyed index. Names of >=2 tokens only (single tokens are too
    ambiguous to link safely). Longer names are tried first at match time. */
export function buildNarratorIndex(records: NarratorRecord[]): NarratorIndex {
  const byFirstToken = new Map<string, { toks: string[]; record: NarratorRecord }[]>();
  let size = 0;
  for (const record of records) {
    const toks = tokens(record.full_name);
    if (toks.length < 2) continue;
    const key = toks[0];
    const bucket = byFirstToken.get(key) ?? [];
    bucket.push({ toks, record });
    byFirstToken.set(key, bucket);
    size += 1;
  }
  // longest names first within each bucket
  for (const bucket of byFirstToken.values()) bucket.sort((a, b) => b.toks.length - a.toks.length);
  return { byFirstToken, size };
}

export type TextSegment =
  | { type: 'text'; value: string }
  | { type: 'narrator'; value: string; record: NarratorRecord };

/** Split text into plain + narrator segments, preserving original spacing. */
export function annotateText(text: string, index: NarratorIndex | null): TextSegment[] {
  if (!text) return [];
  if (!index || index.size === 0) return [{ type: 'text', value: text }];

  const parts = text.split(/(\s+)/); // words at even indices, whitespace between
  const isWord = (p: string) => p.length > 0 && !/^\s+$/.test(p);
  const segs: TextSegment[] = [];
  let buffer = '';
  let i = 0;

  while (i < parts.length) {
    const part = parts[i];
    if (!isWord(part)) {
      buffer += part;
      i += 1;
      continue;
    }

    const match = matchAt(parts, i, index);
    if (match) {
      if (buffer) {
        segs.push({ type: 'text', value: buffer });
        buffer = '';
      }
      segs.push({
        type: 'narrator',
        value: parts.slice(i, match.endIndex + 1).join(''),
        record: match.record,
      });
      i = match.endIndex + 1;
    } else {
      buffer += part;
      i += 1;
    }
  }
  if (buffer) segs.push({ type: 'text', value: buffer });
  return segs;
}

interface Match {
  endIndex: number;
  record: NarratorRecord;
}

function matchAt(parts: string[], start: number, index: NarratorIndex): Match | null {
  const firstNorm = normalizeName(parts[start]);
  const candidates = index.byFirstToken.get(firstNorm);
  if (!candidates) return null;

  for (const { toks, record } of candidates) {
    let pi = start;
    let ti = 0;
    let lastWordIndex = start;
    while (ti < toks.length && pi < parts.length) {
      const part = parts[pi];
      if (!part || /^\s+$/.test(part)) {
        pi += 1;
        continue;
      }
      const norm = normalizeName(part);
      if (norm === toks[ti]) {
        lastWordIndex = pi;
        pi += 1;
        ti += 1;
        continue;
      }
      // allow a connective (bn/ibn/an...) in the text that the name omits
      if (STOP.has(norm) && ti > 0) {
        pi += 1;
        continue;
      }
      break;
    }
    if (ti === toks.length) return { endIndex: lastWordIndex, record };
  }
  return null;
}

// ---- record mappers (RijalEntry / CanonicalEntry -> NarratorRecord) ----
export function rijalToRecord(e: RijalEntry): NarratorRecord {
  return {
    id: e.id,
    full_name: e.full_name,
    kunya: e.kunya,
    nisba: e.nisba,
    tradition: e.tradition,
    birth_year: e.birth_year,
    death_year: e.death_year,
    teacher_count: e.teacher_count,
    student_count: e.student_count,
    reliability_term: e.reliability_term,
    reliability_grade: e.reliability_grade,
    evaluator: e.evaluator,
    source_label: e.source_label,
    origin: 'rijal',
  };
}

export function canonicalToRecord(e: CanonicalEntry): NarratorRecord {
  return {
    id: e.canonical_id,
    full_name: e.full_name,
    kunya: e.kunya,
    nisba: e.nisba,
    tradition: e.tradition,
    birth_year: String(e.birth_year ?? ''),
    death_year: String(e.death_year ?? ''),
    teacher_count: e.teacher_count,
    student_count: e.student_count,
    merge_confidence: e.merge_confidence,
    origin: 'canonical',
  };
}

