import { useState } from 'react';

import { getExtractionBooks } from '../../lib/api/client';
import { DataView } from '../../lib/DataView';
import { Eyebrow, FacetChip, Heading, Inline, Stack, Text } from '../../lib/design-system';
import type { ExtractionBookSummary } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { BookInspector } from './BookInspector';
import './extraction.css';

/** Dev-only extraction inspector: the manuscript artifact rendered near-raw
    so a developer or admin can validate what segment+extract produced for a
    book. A valid route (#/extraction) deliberately absent from the nav bar;
    the backend additionally gates /api/dev behind SOL_DEV_TOOLS, and when
    that is off the API's 404 renders here as the error state. */
export function ExtractionScreen() {
  const books = useAsync(getExtractionBooks, []);
  const [picked, setPicked] = useState('');
  return (
    <div className="xtr">
      <Stack gap="xs">
        <Eyebrow>Developer · extraction</Eyebrow>
        <Heading level={1}>Extraction inspector</Heading>
        <Text as="p" size="sm" tone="muted">
          Spans, units, and entities exactly as segment+extract wrote them to the manuscript
          artifact. Add a book with scripts/build_manuscript_index.py --urn &lt;URN&gt;.
        </Text>
      </Stack>
      <DataView
        result={books}
        loadingLabel="Loading the artifact"
        errorText="Could not read the extraction artifact (SOL_DEV_TOOLS off, or index unbuilt)"
        isEmpty={(list) => list.length === 0}
        emptyText="The manuscript artifact holds no books yet."
      >
        {(list) => <BookPicker list={list} picked={picked} onPick={setPicked} />}
      </DataView>
    </div>
  );
}

interface BookPickerProps {
  list: ExtractionBookSummary[];
  picked: string;
  onPick: (urn: string) => void;
}

/** One chip per extracted book; the active book's inspector below. The
    inspector remounts per URN (key) so its page state restarts at the new
    book's first extracted page. */
function BookPicker({ list, picked, onPick }: BookPickerProps) {
  const active = list.find((book) => book.urn === picked) ?? list[0];
  return (
    <Stack gap="lg">
      <Inline gap="xs" wrap>
        {list.map((book) => (
          <FacetChip
            key={book.urn}
            label={book.title_ar}
            count={book.units}
            on={book.urn === active.urn}
            onToggle={() => onPick(book.urn)}
            ariaLabel={`Inspect ${book.urn}`}
          />
        ))}
      </Inline>
      <BookInspector key={active.urn} book={active} />
    </Stack>
  );
}
