// variants.ts — status-map SSOT. Routes import these; never inline status maps.
import type { BadgeVariant } from "./design-system";

/** Map a narrator reliability grade to a Badge variant. */
export function reliabilityBadge(grade: string | null | undefined): BadgeVariant {
  const g = (grade ?? "").toLowerCase().trim();
  if (!g) return "default";
  if (/(sahih|thiqa|thabt|hafiz|hujja|imam|trustworthy|reliable|strong|sound)/.test(g)) return "success";
  if (/(saduq|maqbul|hasan|acceptable|fair|truthful)/.test(g)) return "warning";
  if (/(daif|matruk|majhul|kadhdhab|munkar|weak|rejected|liar|fabricat)/.test(g)) return "danger";
  return "default";
}

/** Map a canonical merge confidence (0..1, or null = unscored) to a Badge variant. */
export function confidenceBadge(confidence: number | null | undefined): BadgeVariant {
  if (confidence == null) return "default";
  if (confidence >= 0.85) return "success";
  if (confidence >= 0.6) return "warning";
  return "danger";
}

/** Human label for a confidence value (used alongside the badge). */
export function confidenceLabel(confidence: number | null | undefined): string {
  if (confidence == null) return "unscored";
  return `${Math.round(confidence * 100)}%`;
}
