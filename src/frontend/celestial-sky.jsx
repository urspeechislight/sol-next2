/* global React */
// Celestial backdrop — fixed-position behind every screen in night mode.
// Three layers: radial gradient base, two warm halos, faint scholarly
// grid, ~140 deterministic twinkling stars. Mounts once at the AppRoot.

const { useMemo: _useMemoCS } = React;

function SkyBackdrop({ active }) {
  const stars = _useMemoCS(() => {
    const out = [];
    let s = 23;
    const rand = () => {
      s = (s * 1664525 + 1013904223) >>> 0;
      return (s >>> 8) / 0xffffff;
    };
    for (let i = 0; i < 140; i++) {
      out.push({
        x: rand() * 100,
        y: rand() * 100,
        r: 0.05 + rand() * 0.18,
        op: 0.2 + rand() * 0.55,
        d: rand() * 6,
      });
    }
    return out;
  }, []);

  if (!active) return null;

  return (
    <div className="sky" aria-hidden="true">
      <div className="sky__base" />
      <div className="sky__halo sky__halo--n" />
      <div className="sky__halo sky__halo--s" />
      <div className="sky__grid" />
      <svg className="sky__stars" viewBox="0 0 100 100" preserveAspectRatio="none">
        {stars.map((st, i) => (
          <circle
            key={i}
            cx={st.x}
            cy={st.y}
            r={st.r}
            fill="var(--color-accent-strong)"
            opacity={st.op}
          >
            <animate
              attributeName="opacity"
              values={`${st.op};${st.op * 0.3};${st.op}`}
              dur="6s"
              begin={`${st.d}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </svg>
    </div>
  );
}

window.SOL_COMPS = window.SOL_COMPS || {};
window.SOL_COMPS.SkyBackdrop = SkyBackdrop;
