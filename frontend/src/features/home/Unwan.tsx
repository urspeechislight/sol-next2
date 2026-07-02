import './Unwan.css';

const PETALS = 8;
const PETAL_STEP = 360 / PETALS;

/** The landing page's ʿunwān: the illuminated headpiece band that opens the
    folio, drawn from the same eight-fold rosette geometry as the page glow.
    Twin gold rules run to diamond finials on either side of a center rosette;
    the strokes draw themselves once on load. Decorative only. */
export function Unwan() {
  return (
    <div className="unwan" aria-hidden="true">
      <svg className="unwan__svg" viewBox="0 0 1200 120" preserveAspectRatio="xMidYMid meet">
        <g className="unwan__draw">
          <line x1="52" y1="53" x2="484" y2="53" pathLength="1" />
          <line x1="52" y1="67" x2="484" y2="67" pathLength="1" />
          <line x1="716" y1="53" x2="1148" y2="53" pathLength="1" />
          <line x1="716" y1="67" x2="1148" y2="67" pathLength="1" />
          <path className="unwan__finial" d="M52 60 L34 50 L22 60 L34 70 Z" pathLength="1" />
          <path
            className="unwan__finial"
            d="M1148 60 L1166 50 L1178 60 L1166 70 Z"
            pathLength="1"
          />
          <circle cx="502" cy="60" r="4" pathLength="1" />
          <circle cx="698" cy="60" r="4" pathLength="1" />
        </g>
        <g className="unwan__rosette" transform="translate(600 60)">
          <circle cx="0" cy="0" r="46" pathLength="1" />
          <circle cx="0" cy="0" r="30" pathLength="1" />
          <circle cx="0" cy="0" r="8" pathLength="1" />
          {Array.from({ length: PETALS }).map((_, i) => (
            <g key={i} transform={`rotate(${i * PETAL_STEP})`}>
              <path d="M0 -46 C 10 -34, 10 -20, 0 -8 C -10 -20, -10 -34, 0 -46 Z" pathLength="1" />
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}
