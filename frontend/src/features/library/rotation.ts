// rotation.ts — SSOT for the Library's landmark rotations.
//
// Every rotating "primary sources" hero (the library overview, each domain
// pane) reads its policy from this one table: how many works ride the
// rotation, how fast it advances, and which stems are pinned to the front.
// To change what a scope showcases, edit POLICY_OVERRIDES here — nothing else.

import type { Work } from '../../lib/types';
import { dedupeEditions } from './lib';

export interface RotationPolicy {
  /** How many landmark works ride the rotation after dedup. */
  limit: number;
  /** Auto-advance interval for the spotlight. */
  intervalMs: number;
  /** Work stems pinned to the front of the rotation, in this order. */
  pinned: readonly string[];
}

const DEFAULT_POLICY: RotationPolicy = { limit: 10, intervalMs: 9000, pinned: [] };

// Scope key (domain id or category slug) -> overrides. The whole-corpus
// rotation uses the empty key.
const POLICY_OVERRIDES: Record<string, Partial<RotationPolicy>> = {};

export function rotationPolicy(scope = ''): RotationPolicy {
  return { ...DEFAULT_POLICY, ...POLICY_OVERRIDES[scope] };
}

/** Order a fetched landmark shelf per policy: pinned stems first (in pin
    order), then the rest death-year ascending, edition-deduped, capped. */
export function rotationOrder(works: Work[], policy: RotationPolicy): Work[] {
  const deduped = dedupeEditions(works);
  const byStem = new Map(deduped.map((w) => [w.stem, w]));
  const front = policy.pinned.map((stem) => byStem.get(stem)).filter((w): w is Work => Boolean(w));
  const pinnedSet = new Set(policy.pinned);
  const rest = deduped
    .filter((w) => !pinnedSet.has(w.stem))
    .sort(
      (a, b) =>
        (a.death_year_ah ?? Number.MAX_SAFE_INTEGER) - (b.death_year_ah ?? Number.MAX_SAFE_INTEGER),
    );
  return [...front, ...rest].slice(0, policy.limit);
}
