import './Ornament.css';

export type OrnamentCornerPos = 'tl' | 'tr' | 'bl' | 'br';

/** A manuscript corner cartouche pinned to one corner of its positioned
    parent; the same geometry rotated per position class. Decorative only. */
export function CornerOrnament({ pos }: { pos: OrnamentCornerPos }) {
  return (
    <svg
      className={`ds-corner ds-corner--${pos}`}
      width="56"
      height="56"
      viewBox="0 0 56 56"
      aria-hidden="true"
    >
      <g className="ds-corner__lines">
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

/** A soft gold rule with a diamond ornament at its centre: the quiet horizon
    line between sections. Decorative only. */
export function RuleOrnament() {
  return <div className="ds-rule-ornament" aria-hidden="true" />;
}

const ROSETTE_PETALS = 8;
const ROSETTE_STEP = 360 / ROSETTE_PETALS;

/** An eight-fold illumination rosette, used as a large faint watermark behind
    hero surfaces. Scales with its container. Decorative only. */
export function RosetteOrnament() {
  return (
    <svg className="ds-rosette" viewBox="-50 -50 100 100" aria-hidden="true">
      <g className="ds-rosette__lines">
        <circle cx="0" cy="0" r="46" />
        <circle cx="0" cy="0" r="30" />
        <circle cx="0" cy="0" r="8" />
        {Array.from({ length: ROSETTE_PETALS }).map((_, i) => (
          <g key={i} transform={`rotate(${i * ROSETTE_STEP})`}>
            <path d="M0 -46 C 10 -34, 10 -20, 0 -8 C -10 -20, -10 -34, 0 -46 Z" />
            <line x1="0" y1="-46" x2="0" y2="-8" opacity="0.5" />
          </g>
        ))}
      </g>
    </svg>
  );
}
