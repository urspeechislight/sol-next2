import { useMemo } from 'react';
import './HomeSky.css';

// Deterministic star positions: a small LCG so the field never reshuffles
// between renders (and needs no randomness source).
const STAR_COUNT = 110;
const LCG_SEED = 23;
const LCG_MULTIPLIER = 1664525;
const LCG_INCREMENT = 1013904223;
const LCG_SHIFT = 8;
const LCG_RANGE = 0xffffff;

interface Star {
  x: number;
  y: number;
  r: number;
  op: number;
  delay: number;
}

function starField(): Star[] {
  let s = LCG_SEED;
  const rand = () => {
    s = (s * LCG_MULTIPLIER + LCG_INCREMENT) >>> 0;
    return (s >>> LCG_SHIFT) / LCG_RANGE;
  };
  return Array.from({ length: STAR_COUNT }, () => ({
    x: rand() * 100,
    y: rand() * 100,
    r: 0.05 + rand() * 0.16,
    op: 0.2 + rand() * 0.5,
    delay: rand() * 6,
  }));
}

/** The illuminated canvas behind the landing hero: the app's paper surface
    warmed by two gold halos, a masked chart grid, and a field of slowly
    twinkling gilded motes. Purely decorative; content floats above it. */
export function HomeSky() {
  const stars = useMemo(() => starField(), []);
  return (
    <div className="hsky" aria-hidden="true">
      <div className="hsky__base" />
      <div className="hsky__halo hsky__halo--n" />
      <div className="hsky__halo hsky__halo--s" />
      <div className="hsky__grid" />
      <svg className="hsky__stars" viewBox="0 0 100 100" preserveAspectRatio="none">
        {stars.map((st, i) => (
          <circle key={i} cx={st.x} cy={st.y} r={st.r} className="hsky__star" opacity={st.op}>
            <animate
              attributeName="opacity"
              values={`${st.op};${st.op * 0.3};${st.op}`}
              dur="6s"
              begin={`${st.delay}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </svg>
    </div>
  );
}

/** A manuscript corner cartouche; the same geometry rotated per corner by its
    position class. */
export function Cornerpiece({ pos }: { pos: 'tl' | 'tr' | 'bl' | 'br' }) {
  return (
    <svg
      className={`hsky-corner hsky-corner--${pos}`}
      width="56"
      height="56"
      viewBox="0 0 56 56"
      aria-hidden="true"
    >
      <g className="hsky-corner__lines">
        <path d="M2 2 L26 2" />
        <path d="M2 2 L2 26" />
        <path d="M2 8 L8 8 L8 2" />
        <path d="M14 2 L14 6 L18 6 L18 2" />
        <path d="M2 14 L6 14 L6 18 L2 18" />
        <circle cx="22" cy="22" r="3" />
        <path d="M22 16 L22 19 M16 22 L19 22" />
      </g>
    </svg>
  );
}
