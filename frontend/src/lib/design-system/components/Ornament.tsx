import './Ornament.css';

const ROSETTE_PETALS = 8;
const ROSETTE_STEP = 360 / ROSETTE_PETALS;

/** An eight-fold illumination rosette, used as a large faint watermark behind
    glowing surfaces. Scales with its container. Decorative only. */
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
