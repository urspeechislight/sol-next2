/* global React */

function HomeChangelog() {
  return (
    <aside className="changelog" aria-label="Recent additions">
      <div className="changelog__inner">
        <span className="changelog__line">
          Indexed today · 03 new texts · Tatawwur al-Muṣṭalah · 336 pp ·{' '}
          <button
            type="button"
            className="changelog__link"
            onClick={() => {
              /* /changelog route pending — wire navigate when it exists. */
            }}
          >
            all changes →
          </button>
        </span>
      </div>
    </aside>
  );
}

window.SOL_COMPS = window.SOL_COMPS || {};
window.SOL_COMPS.HomeChangelog = HomeChangelog;
