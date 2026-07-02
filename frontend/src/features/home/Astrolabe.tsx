import { useState } from 'react';
import type { Domain } from '../../lib/types';
import './Astrolabe.css';

// Geometry of the instrument, in the -100..100 svg viewBox.
const OUTER_RING_R = 86;
const TICK_COUNT = 72;
const TICK_MAJOR_EVERY = 6;
const TICK_INNER_MAJOR = 80;
const TICK_INNER_MINOR = 83;
const ORBIT_R = 60;
const INNER_RING_R = 22;
const INNER_RING_R2 = 14;
const MEDALLION_R = 5;
const NODE_R = 6;
const NODE_PULSE_R = 9;
const TAU = Math.PI * 2;
const TOP_ANGLE = -Math.PI / 2;

/** Small iconographic glyph per domain id, drawn in a 12x12 box centred at
    the node origin so it slots straight into the orbital disc. */
function NodeGlyph({ id }: { id: string }) {
  switch (id) {
    case 'hadith':
      return (
        <g className="astro__glyph">
          <rect x="-5" y="-1.6" width="4.2" height="3.2" rx="1.6" />
          <rect x="0.8" y="-1.6" width="4.2" height="3.2" rx="1.6" />
          <line x1="-0.8" y1="0" x2="0.8" y2="0" />
        </g>
      );
    case 'quran':
      return (
        <g className="astro__glyph">
          <path d="M-5 -3.5C-3 -4.2 -1 -4.2 0 -3v7c-1.6-0.6-3-0.6-5 0z" />
          <path d="M5 -3.5C3 -4.2 1 -4.2 0 -3v7c1.6-0.6 3-0.6 5 0z" />
          <line x1="0" y1="-3" x2="0" y2="4" />
        </g>
      );
    case 'fiqh':
      return (
        <g className="astro__glyph">
          <line x1="0" y1="-4.5" x2="0" y2="4.5" />
          <line x1="-3.5" y1="-3" x2="3.5" y2="-3" />
          <path d="M-3.5 -3l-1.6 3.2c0 1.1 0.8 1.7 1.6 1.7s1.6-0.6 1.6-1.7z" />
          <path d="M3.5 -3l-1.6 3.2c0 1.1 0.8 1.7 1.6 1.7s1.6-0.6 1.6-1.7z" />
          <line x1="-2" y1="4.5" x2="2" y2="4.5" />
        </g>
      );
    case 'theology':
      return (
        <g className="astro__glyph">
          <circle cx="0" cy="0" r="1.1" />
          <path d="M-3.2 0a3.2 3.2 0 0 1 6.4 0" />
          <path d="M-4.8 0a4.8 4.8 0 0 1 9.6 0" />
        </g>
      );
    case 'biography':
      return (
        <g className="astro__glyph">
          <path d="M-3.8 4.5V-1a3.8 3.8 0 0 1 7.6 0V4.5" />
          <circle cx="0" cy="-1" r="1.1" />
          <path d="M-1.6 2.8c0-0.9 0.7-1.6 1.6-1.6s1.6 0.7 1.6 1.6V4.5" />
        </g>
      );
    case 'sciences':
      return (
        <g className="astro__glyph">
          <circle cx="0" cy="0" r="3.5" />
          <line x1="0" y1="-3.5" x2="0" y2="3.5" />
          <line x1="-3.5" y1="0" x2="3.5" y2="0" />
          <line x1="-2.5" y1="-2.5" x2="2.5" y2="2.5" opacity="0.7" />
          <line x1="-2.5" y1="2.5" x2="2.5" y2="-2.5" opacity="0.7" />
        </g>
      );
    case 'devotional':
      return (
        <g className="astro__glyph">
          <path d="M2 -4a4 4 0 1 0 0 8 3 3 0 0 1 0 -8z" />
          <circle cx="-1.5" cy="0" r="0.4" className="astro__glyph-dot" />
        </g>
      );
    default:
      return <circle className="astro__glyph" cx="0" cy="0" r="3" />;
  }
}

export interface AstrolabeProps {
  domains: Domain[];
  onPickDomain: (id: string) => void;
}

/** The domains of knowledge as a living astrolabe: slowly counter-rotating
    rings, each domain an orbital node with its glyph. Hover names a node in
    the legend; click enters the domain in the Library. */
export function Astrolabe({ domains, onPickDomain }: AstrolabeProps) {
  const [hover, setHover] = useState<number | null>(null);
  const n = domains.length;
  const angleOf = (i: number) => TOP_ANGLE + (i / n) * TAU;

  return (
    <div className="astro">
      <svg viewBox="-100 -100 200 200" className="astro__svg" aria-label="Domains of knowledge">
        <circle cx="0" cy="0" r="92" className="astro__glow" />

        <g className="astro__ring astro__ring--outer">
          <circle cx="0" cy="0" r={OUTER_RING_R} className="astro__ring-line" />
          {Array.from({ length: TICK_COUNT }).map((_, i) => {
            const a = (i / TICK_COUNT) * TAU;
            const major = i % TICK_MAJOR_EVERY === 0;
            const r2 = major ? TICK_INNER_MAJOR : TICK_INNER_MINOR;
            return (
              <line
                key={i}
                x1={Math.cos(a) * OUTER_RING_R}
                y1={Math.sin(a) * OUTER_RING_R}
                x2={Math.cos(a) * r2}
                y2={Math.sin(a) * r2}
                className={major ? 'astro__tick astro__tick--major' : 'astro__tick'}
              />
            );
          })}
        </g>

        <g className="astro__ring astro__ring--mid">
          <circle cx="0" cy="0" r={ORBIT_R} className="astro__orbit" />
        </g>

        <g className="astro__ring astro__ring--inner">
          <circle cx="0" cy="0" r={INNER_RING_R} className="astro__inner-line" />
          <circle cx="0" cy="0" r={INNER_RING_R2} className="astro__inner-line astro__inner-line--faint" />
          <line x1={-INNER_RING_R} y1="0" x2={INNER_RING_R} y2="0" className="astro__cross" />
          <line x1="0" y1={-INNER_RING_R} x2="0" y2={INNER_RING_R} className="astro__cross" />
          <circle cx="0" cy="0" r={MEDALLION_R} className="astro__medallion" />
          <text x="0" y="0.5" className="astro__medallion-glyph">
            ع
          </text>
        </g>

        <g>
          {domains.map((d, i) => {
            const a = angleOf(i);
            return (
              <line
                key={d.id}
                x1={Math.cos(a) * INNER_RING_R}
                y1={Math.sin(a) * INNER_RING_R}
                x2={Math.cos(a) * ORBIT_R}
                y2={Math.sin(a) * ORBIT_R}
                className={hover === i ? 'astro__ray astro__ray--hot' : 'astro__ray'}
              />
            );
          })}
        </g>

        {domains.map((d, i) => {
          const a = angleOf(i);
          const cx = Math.cos(a) * ORBIT_R;
          const cy = Math.sin(a) * ORBIT_R;
          return (
            <g
              key={d.id}
              className={hover === i ? 'astro__node astro__node--hot' : 'astro__node'}
              transform={`translate(${cx} ${cy})`}
              role="button"
              tabIndex={0}
              aria-label={`Enter ${d.label}`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(i)}
              onBlur={() => setHover(null)}
              onClick={() => onPickDomain(d.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onPickDomain(d.id);
                }
              }}
            >
              <g className="astro__node-inner">
                <circle r={NODE_PULSE_R} className="astro__node-pulse" />
                <circle r={NODE_R} className="astro__node-disc" />
                <NodeGlyph id={d.id} />
              </g>
            </g>
          );
        })}
      </svg>

      <div className="astro__legend" aria-live="polite">
        {hover != null && domains[hover] ? (
          <>
            <span className="astro__legend-num">§ {String(hover + 1).padStart(2, '0')}</span>
            <span className="astro__legend-text">
              <span className="astro__legend-en">{domains[hover].label}</span>
              <span className="astro__legend-ar" dir="rtl">
                {domains[hover].label_ar}
              </span>
            </span>
            <span className="astro__legend-cta">Open →</span>
          </>
        ) : (
          <span className="astro__legend-hint">Hover a sphere to inspect · click to enter</span>
        )}
      </div>
    </div>
  );
}
