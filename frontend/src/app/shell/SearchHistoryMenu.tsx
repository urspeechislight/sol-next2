import { Icon, Text, UnstyledButton } from '../../lib/design-system';
import type { IconName, MenuOption } from '../../lib/design-system';
import type { SearchScope } from '../../lib/api/client';
import { clearSearchHistory, removeSearch, useSearchHistory } from '../../lib/searchHistory';
import './SearchHistoryMenu.css';

export interface SearchHistoryMenuProps {
  open: boolean;
  /** Scope -> icon lookup, the same list the header's scope Menu renders
      (single definition in Header.tsx), so a row's icon always matches the
      one the scope switcher shows for that scope. */
  scopes: MenuOption[];
  onPick: (query: string, scope: SearchScope) => void;
}

/** The header search field's recent-searches dropdown: shown while the field
    is focused and empty (Header.tsx owns that state and the outside-click
    dismissal), backed by the reactive localStorage history in
    lib/searchHistory so it reflects every past search without prop drilling.
    Picking a row re-runs that exact query+scope; each row can be dismissed on
    its own, or the whole list cleared. */
export function SearchHistoryMenu({ open, scopes, onPick }: SearchHistoryMenuProps) {
  const entries = useSearchHistory();
  if (!open || entries.length === 0) return null;
  const iconFor = (scope: SearchScope): IconName | undefined =>
    scopes.find((s) => s.value === scope)?.icon;

  return (
    <div className="search-history" role="listbox" aria-label="Recent searches">
      <ul className="search-history__list">
        {entries.map((e) => (
          <li key={`${e.scope}:${e.query}`} className="search-history__item">
            <UnstyledButton
              className="search-history__row"
              ariaLabel={`Search again for "${e.query}"`}
              onClick={() => onPick(e.query, e.scope)}
            >
              <Icon name={iconFor(e.scope) ?? 'search'} size="sm" className="search-history__icon" />
              <span className="search-history__query">{e.query}</span>
            </UnstyledButton>
            <UnstyledButton
              className="search-history__remove"
              ariaLabel={`Remove "${e.query}" from recent searches`}
              onClick={() => removeSearch(e.query, e.scope)}
            >
              <Icon name="close" size="sm" />
            </UnstyledButton>
          </li>
        ))}
      </ul>
      <footer className="search-history__foot">
        <UnstyledButton
          className="search-history__clear"
          ariaLabel="Clear all recent searches"
          onClick={clearSearchHistory}
        >
          <Text size="xs" tone="muted">
            Clear recent searches
          </Text>
        </UnstyledButton>
      </footer>
    </div>
  );
}
