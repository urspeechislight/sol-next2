// scopes.ts:SSOT for the header search-scope dropdown: each scope's id,
// label, and icon defined once and shared by every surface that names a
// scope (the header menu, the recent-searches row, the LLM scope's results
// eyebrow). Scope ids are owned by SEARCH_SCOPES in lib/api/client.ts; the
// `satisfies` clause fails this file's compile if the two ever drift.
import type { SearchScope } from './api/client';
import type { IconName } from './design-system';

export interface ScopeOption {
  value: SearchScope;
  label: string;
  icon: IconName;
}

export const SCOPE_OPTIONS: readonly ScopeOption[] = [
  { value: 'content', label: 'Content', icon: 'scroll' },
  { value: 'works', label: 'Works', icon: 'book' },
  { value: 'narrator', label: 'Narrator', icon: 'network' },
  { value: 'quran', label: 'Qurʾān', icon: 'reader' },
  { value: 'semantic', label: 'LLM', icon: 'llm' },
] as const satisfies readonly ScopeOption[];
