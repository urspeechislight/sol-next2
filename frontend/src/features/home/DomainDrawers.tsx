import { useEffect, useRef, useState } from 'react';
import { Eyebrow, Text, UnstyledButton } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { sumCount } from '../library/lib';
import './DomainDrawers.css';

export interface DomainDrawersProps {
  domains: Domain[];
  onOpenCategory: (slug: string) => void;
  onOpenDomain: (id: string) => void;
}

/** The domain arcade: a row of arched niches, each keyed to a domain, its
    Arabic caption written vertically like a spine. Hover previews, click
    pins; the open niche fans its categories out in a tray beneath. Escape or
    a click outside closes the pinned niche. */
export function DomainDrawers({ domains, onOpenCategory, onOpenDomain }: DomainDrawersProps) {
  const [pinned, setPinned] = useState<number | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const active = hover ?? pinned;
  const rootRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (pinned == null) return;
    const onDoc = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setPinned(null);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setPinned(null);
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [pinned]);

  const domain = active != null ? domains[active] : null;

  return (
    <section className="cab" aria-label="Domains of knowledge" ref={rootRef}>
      <header className="cab__head">
        <Eyebrow tracking="section">§ I</Eyebrow>
        <h2 className="cab__title">
          <em>Domains</em> of knowledge
        </h2>
        <span className="cab__meta">
          {domains.length} domains ·{' '}
          {domains.reduce((t, d) => t + sumCount(d.categories), 0).toLocaleString()} works
        </span>
      </header>

      <div className="cab__row">
        {domains.map((d, i) => (
          <UnstyledButton
            key={d.id}
            className={[
              'cdrawer',
              active === i ? 'cdrawer--active' : '',
              active != null && active !== i ? 'cdrawer--dim' : '',
            ]
              .filter(Boolean)
              .join(' ')}
            ariaLabel={`${d.label}, ${sumCount(d.categories).toLocaleString()} works`}
            ariaPressed={pinned === i}
            onClick={() => setPinned((p) => (p === i ? null : i))}
          >
            <span
              className="cdrawer__hover"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            >
              <span className="cdrawer__ar" dir="rtl">
                {d.label_ar}
              </span>
              <span className="cdrawer__rule" aria-hidden="true" />
              <span className="cdrawer__foot">
                <span className="cdrawer__num">{String(i + 1).padStart(2, '0')}</span>
                <span className="cdrawer__en">{d.label}</span>
                <span className="cdrawer__count">{sumCount(d.categories).toLocaleString()}</span>
              </span>
              <span className="cdrawer__handle" aria-hidden="true" />
            </span>
          </UnstyledButton>
        ))}
      </div>

      <div className={domain ? 'cab__tray cab__tray--open' : 'cab__tray'} aria-hidden={!domain}>
        {domain ? (
          <div className="ctray">
            <div className="ctray__head">
              <div className="ctray__head-l">
                <h3 className="ctray__title">
                  {domain.label}
                  <span className="ctray__title-ar" dir="rtl">
                    {' '}
                    · {domain.label_ar}
                  </span>
                </h3>
                {domain.blurb ? (
                  <Text as="p" size="sm" tone="muted" className="ctray__blurb">
                    {domain.blurb}
                  </Text>
                ) : null}
              </div>
              <UnstyledButton
                className="ctray__cta"
                onClick={() => onOpenDomain(domain.id)}
                ariaLabel={`Enter all of ${domain.label}`}
              >
                Enter all of {domain.label} <span className="ctray__cta-arrow">→</span>
              </UnstyledButton>
            </div>
            <div className="ctray__cats">
              {domain.categories.map((c, i) => (
                <UnstyledButton
                  key={c.slug}
                  className="ctray__cat"
                  onClick={() => onOpenCategory(c.slug)}
                >
                  <span className="ctray__cat-n">{String(i + 1).padStart(2, '0')}</span>
                  <span className="ctray__cat-body">
                    <span className="ctray__cat-en">{c.label}</span>
                    <span className="ctray__cat-ar" dir="rtl">
                      {c.label_ar}
                    </span>
                  </span>
                  <span className="ctray__cat-count">{c.count.toLocaleString()}</span>
                  <span className="ctray__cat-arrow" aria-hidden="true">
                    →
                  </span>
                </UnstyledButton>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
