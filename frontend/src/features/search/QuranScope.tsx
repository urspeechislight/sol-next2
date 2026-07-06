import { Badge, SourceRecord, Spinner, Stack, Text } from '../../lib/design-system';
import { getVerse, searchQuran } from '../../lib/api/client';
import type { SearchScope } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { parseVerseRef } from '../../lib/surahs';
import type { Ayah, Page } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { ContentScope } from './ContentScope';
import { ResultsFrame } from './ResultsFrame';
import './SearchResults.css';

/** A Qurʾān verse as the shared two-zone SourceRecord, identical in shape to a
    content or book hit: the reference + translation on the English spine, the
    pointed verse with its bare (matched) form on the Arabic body. Selecting it
    searches that verse's reference to surface the passages that quote it. */
function VerseRecord({
  verse,
  query,
  onOpen,
}: {
  verse: Ayah;
  query?: string;
  onOpen: () => void;
}) {
  return (
    <SourceRecord
      section={`Qurʾān ${verse.surah}:${verse.ayah}`}
      titleAr={verse.text_ar}
      titleEn={verse.text_en}
      author={null}
      badges={<Badge>{`ayah ${verse.ayah} / ${verse.verse_count}`}</Badge>}
      snippet={verse.text_plain}
      query={query}
      onOpen={onOpen}
    />
  );
}

interface VersePanelProps {
  surah: number;
  ayah: number;
  onSearch: (q: string, scope: SearchScope) => void;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

function VersePanel({ surah, ayah, onSearch, onOpenReader }: VersePanelProps) {
  const res = useAsync<Ayah>(() => getVerse(surah, ayah), [surah, ayah]);
  return (
    <Stack gap="md">
      {res.loading ? <Spinner label="Loading verse" /> : null}
      {res.error ? (
        <Text as="p" size="sm" tone="muted">
          No verse at {surah}:{ayah}. Check the surah and ayah numbers.
        </Text>
      ) : null}
      {res.data ? (
        <>
          <div className="ds-records">
            <VerseRecord verse={res.data} onOpen={() => onSearch(`${surah}:${ayah}`, 'quran')} />
          </div>
          <ContentScope q={res.data.text_ar} initialMode="broad" onOpenReader={onOpenReader} />
        </>
      ) : null}
    </Stack>
  );
}

function QuranTermResults({
  q,
  onSearch,
}: {
  q: string;
  onSearch: (q: string, scope: SearchScope) => void;
}) {
  const res = useAsync<Page<Ayah>>(() => searchQuran(q, { limit: PAGE.defaultLimit }), [q]);
  return (
    <ResultsFrame
      filters={{ total: res.data?.total ?? 0 }}
      loading={res.loading}
      loadingLabel="Searching the Qurʾān"
      error={res.error ? `Qurʾān search is unavailable: ${res.error.message}` : null}
      empty={res.data && res.data.items.length === 0 ? `No Qurʾān verses contain “${q}”` : null}
    >
      {res.data ? (
        <div className="ds-records">
          {res.data.items.map((verse) => (
            <VerseRecord
              key={`${verse.surah}:${verse.ayah}`}
              verse={verse}
              query={q}
              onOpen={() => onSearch(`${verse.surah}:${verse.ayah}`, 'quran')}
            />
          ))}
        </div>
      ) : null}
    </ResultsFrame>
  );
}

export interface QuranScopeProps {
  q: string;
  onSearch: (q: string, scope: SearchScope) => void;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

/** Qurʾān search with two modes, both rendered through the shared SourceRecord so
    the results match every other scope. A ``surah:ayah`` reference like `68:4`
    loads the verse and the passages that quote it; any other query is an Arabic
    term, matched against every verse to list the ayat that contain it. */
export function QuranScope({ q, onSearch, onOpenReader }: QuranScopeProps) {
  const ref = parseVerseRef(q);
  if (ref) {
    return (
      <VersePanel
        surah={ref.surah}
        ayah={ref.ayah}
        onSearch={onSearch}
        onOpenReader={onOpenReader}
      />
    );
  }
  if (q.trim()) {
    return <QuranTermResults q={q.trim()} onSearch={onSearch} />;
  }
  return (
    <Text as="p" size="sm" tone="muted">
      Type an Arabic word to find verses that contain it, or a reference like 68:4 to find passages
      that quote it.
    </Text>
  );
}
