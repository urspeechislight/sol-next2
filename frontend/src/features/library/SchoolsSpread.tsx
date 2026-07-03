import { UnstyledButton } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getWorks } from '../../lib/api/client';
import { LIBRARY } from '../../lib/constants';
import type { Category, Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { countLabel } from '../../lib/utils';
import { Apparatus } from './Apparatus';
import { dedupeEditions } from './lib';
import { WorkRecord } from './WorkRecord';
import './SchoolsSpread.css';

export interface SchoolsSpreadProps {
  /** The domain's categories visible under the current lens. */
  categories: Category[];
  onPickCategory: (slug: string) => void;
  onOpen: (urn: string, page?: number) => void;
}

/** The domain's contents as walkable shelves, not a second index: each
    category is an apparatus-ruled section holding its leading works (rank
    tier, then death year, edition-deduped), which is exactly what the rail's
    bare names and counts cannot carry. The head states the category's true
    totals; the browse-all line is the step into the full category room. */
export function SchoolsSpread({ categories, onPickCategory, onOpen }: SchoolsSpreadProps) {
  return (
    <div className="spread">
      {categories.map((c) => (
        <SchoolSection key={c.slug} category={c} onPickCategory={onPickCategory} onOpen={onOpen} />
      ))}
    </div>
  );
}

interface SchoolSectionProps {
  category: Category;
  onPickCategory: (slug: string) => void;
  onOpen: (urn: string, page?: number) => void;
}

/** One category as a shelf section: rule, leading works, the step deeper.
    The fetch asks for sectionFetch rows so edition duplicates cannot starve
    the sectionSpread-row preview after dedupe. */
function SchoolSection({ category, onPickCategory, onOpen }: SchoolSectionProps) {
  const res = useAsync<Work[]>(
    () =>
      getWorks({
        category: category.slug,
        sort: 'canonical',
        limit: LIBRARY.sectionFetch,
      }).then((page) => dedupeEditions(page.items).slice(0, LIBRARY.sectionSpread)),
    [category.slug],
  );
  const browseLabel =
    category.count === 1 ? 'Browse the work' : `Browse all ${countLabel(category.count, 'work')}`;
  return (
    <section className="spread__school" aria-label={category.label}>
      <Apparatus
        marginalia={`${countLabel(category.count, 'work')} · ${countLabel(category.volume_count, 'vol')}`}
      >
        {category.label} · {category.label_ar}
      </Apparatus>
      <SectionBody works={res.data} loading={res.loading} error={res.error} onOpen={onOpen} />
      <UnstyledButton
        className="spread__all"
        onClick={() => onPickCategory(category.slug)}
        ariaLabel={`${browseLabel} in ${category.label}`}
      >
        {browseLabel} →
      </UnstyledButton>
    </section>
  );
}

interface SectionBodyProps {
  works: Work[] | null;
  loading: boolean;
  error: Error | null;
  onOpen: (urn: string, page?: number) => void;
}

/** The section's rows in their three honest states: fetching, failed (loud,
    per no-silent-fallback), or the leading works as catalog rows. */
function SectionBody({ works, loading, error, onOpen }: SectionBodyProps) {
  return (
    <DataView
      result={{ data: works, error, loading }}
      loadingLabel="Fetching the leading works"
      errorText="Could not load this category's works"
    >
      {(data) => (
        <div className="spread__rows">
          {data.map((w) => (
            <WorkRecord key={w.stem} work={w} onOpen={onOpen} />
          ))}
        </div>
      )}
    </DataView>
  );
}
