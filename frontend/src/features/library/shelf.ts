// shelf.ts: SSOT for the Library's foundational shelf.
//
// Every "Foundational works" spotlight (each domain pane, each category pane)
// reads its policy from this one table: how many works stand on the shelf and
// which stems are pinned to the front. To change what a scope showcases, edit
// POLICY_OVERRIDES here, nothing else.

import type { Work } from '../../lib/types';
import { dedupeEditions } from './lib';

export interface ShelfPolicy {
  /** How many works stand on the shelf after dedup. */
  limit: number;
  /** Work stems pinned to the front of the shelf, in this order. */
  pinned: readonly string[];
}

const DEFAULT_POLICY: ShelfPolicy = { limit: 6, pinned: [] };

// Scope key (domain id or category slug) -> overrides.
const POLICY_OVERRIDES: Record<string, Partial<ShelfPolicy>> = {};

export function shelfPolicy(scope = ''): ShelfPolicy {
  return { ...DEFAULT_POLICY, ...POLICY_OVERRIDES[scope] };
}

function byDeath(a: Work, b: Work): number {
  return (
    (a.death_year_ah ?? Number.MAX_SAFE_INTEGER) - (b.death_year_ah ?? Number.MAX_SAFE_INTEGER)
  );
}

/** Order a fetched foundational shelf per policy: pinned stems first (in pin
    order), then the rest death-year ascending, edition-deduped, capped. */
export function shelfOrder(works: Work[], policy: ShelfPolicy): Work[] {
  const deduped = dedupeEditions(works);
  const byStem = new Map(deduped.map((w) => [w.stem, w]));
  const front = policy.pinned.map((stem) => byStem.get(stem)).filter((w): w is Work => Boolean(w));
  const pinnedSet = new Set(policy.pinned);
  const rest = deduped.filter((w) => !pinnedSet.has(w.stem)).sort(byDeath);
  return [...front, ...rest].slice(0, policy.limit);
}
