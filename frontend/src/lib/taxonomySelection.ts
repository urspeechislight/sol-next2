// taxonomySelection.ts: the one selection algebra for set-valued taxonomy
// filters. The canonical state is a flat Set of category slugs; a group's
// (domain's) checked / partial / empty state is DERIVED by comparing its slug
// list against the set, never stored. Every surface that multi-selects
// categories (the search map chips, the filter popover, future adopters)
// reads and writes this one model, so two views can never hold two truths.

export type GroupState = 'none' | 'partial' | 'all';

export interface ScopeGroup {
  id: string;
  label: string;
  /** The group's selectable slugs (e.g. a domain's MATCHING categories). */
  slugs: readonly string[];
}

export interface ScopeToken {
  kind: 'group' | 'category';
  id: string;
  label: string;
}

/** How much of the group's slug list the selection covers. */
export function groupState(slugs: readonly string[], selected: ReadonlySet<string>): GroupState {
  let hit = 0;
  for (const s of slugs) if (selected.has(s)) hit += 1;
  if (hit === 0) return 'none';
  return hit === slugs.length ? 'all' : 'partial';
}

/** Toggle one slug's membership. */
export function toggleOne(selected: ReadonlySet<string>, slug: string): Set<string> {
  const next = new Set(selected);
  if (next.has(slug)) next.delete(slug);
  else next.add(slug);
  return next;
}

/** Toggle a whole group: fully selected -> released, anything less -> all in. */
export function toggleGroup(selected: ReadonlySet<string>, slugs: readonly string[]): Set<string> {
  const next = new Set(selected);
  if (groupState(slugs, selected) === 'all') {
    for (const s of slugs) next.delete(s);
  } else {
    for (const s of slugs) next.add(s);
  }
  return next;
}

/** Collapse a selection into toolbar tokens: one token per FULLY selected
    group, then the loose categories no full group covers, in group order.
    labelOf resolves a category slug for the loose tokens. */
export function scopeTokens(
  groups: readonly ScopeGroup[],
  selected: ReadonlySet<string>,
  labelOf: (slug: string) => string,
): ScopeToken[] {
  const tokens: ScopeToken[] = [];
  const covered = new Set<string>();
  for (const g of groups) {
    if (g.slugs.length > 0 && groupState(g.slugs, selected) === 'all') {
      tokens.push({ kind: 'group', id: g.id, label: g.label });
      for (const s of g.slugs) covered.add(s);
    }
  }
  for (const g of groups) {
    for (const s of g.slugs) {
      if (selected.has(s) && !covered.has(s)) {
        tokens.push({ kind: 'category', id: s, label: labelOf(s) });
        covered.add(s);
      }
    }
  }
  for (const s of selected) {
    if (!covered.has(s)) tokens.push({ kind: 'category', id: s, label: labelOf(s) });
  }
  return tokens;
}

/** The wire form: the selection as a stable sorted category list. */
export function wireCategories(selected: ReadonlySet<string>): string[] {
  return [...selected].sort();
}
