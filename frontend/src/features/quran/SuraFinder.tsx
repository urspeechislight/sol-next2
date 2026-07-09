import { useState } from 'react';

import { Highlight, Input, Spinner, Text, UnstyledButton } from '../../lib/design-system';
import { LoadMoreFoot } from '../../lib/LoadMoreFoot';
import { searchQuran } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { SURAHS, matchSurahs, parseVerseRef, surahName } from '../../lib/surahs';
import type { VerseRef } from '../../lib/surahs';
import { emptyPage, type Ayah } from '../../lib/types';
import { usePaged } from '../../lib/usePaged';
import { countLabel, cx, formatCount } from '../../lib/utils';
import './SuraFinder.css';

export interface SuraFinderProps {
  currentSurah: number;
  onPick: (surah: number) => void;
  onJump: (surah: number, ayah: number) => void;
}

/** The rail's one Qurʾān finder: the same query grammar as the search
    overlay's Qurʾān scope, in place. Typing filters the sūra list live (name
    EN/AR or number, via the shared name fold); a ``55:5`` reference offers a
    direct jump; Enter runs the fold-insensitive whole-Qurʾān verse search
    (the same endpoint the overlay uses) and lists matching āyāt with honest
    paging. All parsing/matching comes from lib/surahs: nothing is
    re-implemented here. */
export function SuraFinder({ currentSurah, onPick, onJump }: SuraFinderProps) {
  const [filter, setFilter] = useState('');
  const [term, setTerm] = useState('');
  const ref = parseVerseRef(filter);
  const validRef: VerseRef | null =
    ref && ref.surah >= 1 && ref.surah <= SURAHS.length ? ref : null;
  const names = matchSurahs(filter);

  const verses = usePaged(
    (offset) =>
      term
        ? searchQuran(term, { limit: PAGE.defaultLimit, offset })
        : Promise.resolve(emptyPage<Ayah>()),
    [term],
  );

  const change = (value: string) => {
    setFilter(value);
    if (!value.trim()) setTerm('');
  };
  const submit = () => {
    if (validRef) {
      onJump(validRef.surah, validRef.ayah);
      return;
    }
    setTerm(filter.trim());
  };
  const clear = () => {
    setFilter('');
    setTerm('');
  };

  return (
    <>
      <Input
        value={filter}
        type="search"
        icon="search"
        surface="reader"
        hideLabel
        label="Find in the Qurʾān"
        placeholder="Sūra, 55:5, or a word…"
        onInput={change}
        onSubmit={submit}
        onClear={clear}
        clearLabel="Clear finder"
      />
      {validRef ? (
        <UnstyledButton
          className="qfind__jump"
          onClick={() => onJump(validRef.surah, validRef.ayah)}
          ariaLabel={`Go to verse ${validRef.surah}:${validRef.ayah}`}
        >
          Go to {validRef.surah}:{validRef.ayah} · {surahName(validRef.surah).en} →
        </UnstyledButton>
      ) : null}
      {ref && !validRef ? (
        <Text as="p" size="xs" tone="muted">
          There is no sūra {ref.surah}; the Qurʾān has {SURAHS.length}.
        </Text>
      ) : null}
      {term ? (
        <div className="qfind__verses">
          {verses.loading && verses.items.length === 0 ? (
            <Spinner label="Searching the Qurʾān" />
          ) : null}
          {verses.error ? (
            <Text as="p" size="sm" tone="danger">
              Qurʾān search is unavailable: {verses.error.message}
            </Text>
          ) : null}
          {!verses.loading && verses.total === 0 && !verses.error ? (
            <Text as="p" size="sm" tone="muted">
              No verses contain “{term}”.
            </Text>
          ) : null}
          <ul className="qfind__list">
            {verses.items.map((v) => (
              <li key={`${v.surah}:${v.ayah}`}>
                <UnstyledButton
                  className="qfind__verse"
                  onClick={() => onJump(v.surah, v.ayah)}
                  ariaLabel={`Go to verse ${v.surah}:${v.ayah}`}
                >
                  <span className="qfind__ref" dir="ltr">
                    {v.surah}:{v.ayah}
                  </span>
                  <span className="qfind__text" dir="rtl" lang="ar">
                    <Highlight text={v.text_plain} query={term} />
                  </span>
                </UnstyledButton>
              </li>
            ))}
          </ul>
          {verses.total !== null && verses.total > 0 ? (
            <LoadMoreFoot
              line={`Showing ${formatCount(verses.items.length)} of ${countLabel(verses.total, 'verse')}`}
              loading={verses.loading}
              spinnerLabel="Loading more verses"
              hasMore={verses.hasMore}
              onMore={verses.more}
              moreLabel="More"
              moreVariant="link"
            />
          ) : null}
        </div>
      ) : (
        <ul className="quran__list">
          {names.map((s) => (
            <li key={s.n}>
              <UnstyledButton
                className={cx('quran__surah', s.n === currentSurah && 'quran__surah--current')}
                onClick={() => onPick(s.n)}
              >
                <span className="quran__surah-n">{s.n}</span>
                <span className="quran__surah-en">{s.en}</span>
                <span className="quran__surah-ar" dir="rtl">
                  {s.ar}
                </span>
              </UnstyledButton>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
