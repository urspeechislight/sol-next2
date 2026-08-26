// variants.ts:status-map SSOT. Routes import these; never inline status maps.
import type { BadgeVariant } from './design-system';
import type { HadithGrade } from './types';

/** Map a hadith authenticity grade to a Badge variant. The one grade→tone path:
    ṣaḥīḥ is sound, ḥasan is fair, ḍaʿīf and mawḍūʿ are weak/fabricated. */
export function hadithBadge(grade: HadithGrade | null | undefined): BadgeVariant {
  switch (grade) {
    case 'sahih':
      return 'success';
    case 'hasan':
      return 'warning';
    case 'daif':
    case 'mawdu':
      return 'danger';
    default:
      return 'default';
  }
}

/** Map a narrator reliability grade to a Badge variant. */
export function reliabilityBadge(grade: string | null | undefined): BadgeVariant {
  const g = (grade ?? '').toLowerCase().trim();
  if (!g) return 'default';
  if (/(sahih|thiqa|thabt|hafiz|hujja|imam|trustworthy|reliable|strong|sound)/.test(g))
    return 'success';
  if (/(saduq|maqbul|hasan|acceptable|fair|truthful)/.test(g)) return 'warning';
  if (/(daif|matruk|majhul|kadhdhab|munkar|weak|rejected|liar|fabricat)/.test(g)) return 'danger';
  return 'default';
}

/** Reliability ranking over the served grade tiers (normalized_tier
    vocabulary): higher is more trustworthy. ṣaḥābī sits below the sound
    verdicts — it names a generation, not a critic's endorsement. */
const TIER_RANK: Record<string, number> = {
  thiqa: 7,
  saduq: 6,
  sahabi: 5,
  maqbul: 4,
  majhul: 3,
  daif: 2,
  matruk: 1,
};

/** The highest-ranked tier among a narrator's recorded grades ('' when none
    is in the known vocabulary). The card chip and the tarjama panel badge
    both read from here, so "top grade" can only mean one thing. */
export function topTier(tiers: readonly string[]): string {
  let best = '';
  let rank = 0;
  for (const tier of tiers) {
    const value = TIER_RANK[tier] ?? 0;
    if (value > rank) {
      best = tier;
      rank = value;
    }
  }
  return best;
}
