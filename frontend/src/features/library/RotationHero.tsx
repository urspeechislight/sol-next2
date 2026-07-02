import { useEffect, useMemo, useState } from 'react';
import { Dots, Eyebrow, MetaBadges, NavArrow, Text, UnstyledButton } from '../../lib/design-system';
import { getWorks } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { useAsync } from '../../lib/useAsync';
import { deathLabel } from '../../lib/utils';
import { rotationOrder, rotationPolicy } from './rotation';
import './RotationHero.css';

export interface RotationHeroProps {
  /** Scope key for the rotation policy AND the works query: a domain id, a
      category slug, or nothing for the whole corpus. */
  domain?: string;
  category?: string;
  onOpen: (urn: string) => void;
}

/** The rotating spotlight of primary sources: one landmark work at a time,
    auto-advancing, with its full card of facts. What rides the rotation is
    governed entirely by rotation.ts (the SSOT policy table). */
export function RotationHero({ domain, category, onOpen }: RotationHeroProps) {
  const policy = useMemo(() => rotationPolicy(category ?? domain ?? ''), [category, domain]);
  const res = useAsync(
    () =>
      getWorks({
        domain,
        category,
        canonical: 'primary_reference',
        limit: PAGE.facetLimit,
      }).then((page) => rotationOrder(page.items, policy)),
    [domain, category, policy],
  );

  const shelf = useMemo(() => res.data ?? [], [res.data]);
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    setIdx(0);
    if (shelf.length < 2) return;
    const id = setInterval(() => setIdx((i) => (i + 1) % shelf.length), policy.intervalMs);
    return () => clearInterval(id);
  }, [shelf.length, policy.intervalMs]);

  if (res.error) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load the landmark rotation: {res.error.message}
      </Text>
    );
  }
  if (shelf.length === 0) return null;
  const work = shelf[Math.min(idx, shelf.length - 1)];
  const go = (delta: number) => setIdx((i) => (i + delta + shelf.length) % shelf.length);

  return (
    <section className="rotor" aria-label="Primary sources on rotation">
      <div className="rotor__halo" aria-hidden="true" />
      <header className="rotor__head">
        <Eyebrow>Primary sources · أمهات الكتب</Eyebrow>
        <span className="rotor__index">
          {idx + 1} / {shelf.length}
        </span>
      </header>

      <div className="rotor__stage" key={work.stem}>
        <div className="rotor__copy">
          <p className="rotor__title-ar" dir="rtl">
            {work.title_ar}
          </p>
          {work.title_en ? <p className="rotor__title-en">{work.title_en}</p> : null}
          <p className="rotor__author">
            {work.author}
            {work.author_ar ? (
              <span className="rotor__author-ar" dir="rtl">
                {work.author_ar}
              </span>
            ) : null}
          </p>
          <div className="rotor__meta">
            <MetaBadges
              volumeCount={work.volume_count}
              sect={work.sect}
              death={deathLabel(work.death_year_ah)}
              pageCount={work.page_count}
            />
          </div>
          <UnstyledButton className="rotor__cta" onClick={() => onOpen(work.first_urn)}>
            Open the book <span className="rotor__cta-arrow">→</span>
          </UnstyledButton>
        </div>

        <div className="rotor__codex" aria-hidden="true">
          <div className="rotor__cover">
            <span className="rotor__cover-medallion">✻</span>
            <span className="rotor__cover-title" dir="rtl">
              {work.title_ar}
            </span>
            <span className="rotor__cover-rule" />
            <span className="rotor__cover-author" dir="rtl">
              {work.author_ar ?? work.author ?? ''}
            </span>
          </div>
        </div>
      </div>

      <footer className="rotor__foot">
        <NavArrow direction="back" label="Previous work" onClick={() => go(-1)} />
        <Dots
          count={shelf.length}
          active={idx}
          labelFor={(i) => `Show ${shelf[i].title_en ?? shelf[i].title_ar}`}
          onPick={setIdx}
        />
        <NavArrow direction="forward" label="Next work" onClick={() => go(1)} />
      </footer>
    </section>
  );
}
