/* global React */
// App-level header + footer + browse menu, extracted from app.jsx
// so app.jsx itself stays focused on the root + routing.

const { useState: _useStateAH } = React;
const { useEffect: _useEffectAH, useRef: _useRefAH } = React;

function AppHeader({ navigate, query, setQuery, route }) {
  const { Text, Icon } = window.SOL_PRIMS;
  const [browseOpen, setBrowseOpen] = useState(false);
  const headerSearchRef = _useRefAH(null);

  _useEffectAH(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        headerSearchRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        borderBottom: '1px solid var(--color-border-1)',
        background: 'color-mix(in oklch, var(--color-bg-0) 88%, transparent)',
        backdropFilter: 'blur(8px)',
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: '0 auto',
          padding: '0 24px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <button
          onClick={() => navigate({ route: 'home' })}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-fg-1)',
            fontFamily: 'inherit',
            padding: 0,
          }}
        >
          <img
            src="logo-dark.png"
            alt="Shia Online Library"
            style={{ height: 44, width: 'auto', display: 'block', objectFit: 'contain' }}
          />
          <Text
            family="display"
            size="lg"
            weight="semibold"
            style={{ lineHeight: 1.05, letterSpacing: '-0.015em', whiteSpace: 'nowrap' }}
          >
            Shia Online Library
          </Text>
        </button>

        <div style={{ position: 'relative', marginLeft: 16 }}>
          <button
            onClick={() => setBrowseOpen(!browseOpen)}
            style={{ ...navLink(browseOpen), display: 'inline-flex', alignItems: 'center', gap: 4 }}
          >
            Browse <Icon name="chevronDown" size={14} />
          </button>
          {browseOpen && (
            <BrowseMenu
              navigate={(r) => {
                setBrowseOpen(false);
                navigate(r);
              }}
              onClose={() => setBrowseOpen(false)}
            />
          )}
        </div>

        <button
          style={navLink(route.name === 'search')}
          onClick={() => navigate({ route: 'search', q: '' })}
        >
          Search
        </button>
        <button
          style={navLink(false)}
          onClick={() => navigate({ route: 'library', cat: 'shia-tafsir' })}
        >
          Qurʾan
        </button>
        <button
          style={navLink(false)}
          onClick={() => navigate({ route: 'library', cat: 'shia-hadith-general' })}
        >
          Hadith
        </button>
        <button
          style={navLink(false)}
          onClick={() => navigate({ route: 'library', cat: 'shia-fiqh-principles' })}
        >
          Fiqh
        </button>

        <div style={{ flex: 1 }} />

        <form
          role="search"
          onSubmit={(e) => {
            e.preventDefault();
            const q = query.trim();
            if (q) navigate({ route: 'search', q });
          }}
          style={{ width: 280 }}
        >
          <label
            className="header-search"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              height: 36,
              padding: '0 12px',
              background: 'var(--color-bg-1)',
              border: '1px solid var(--color-border-2)',
              borderRadius: 6,
              cursor: 'text',
            }}
          >
            <span
              style={{ color: 'var(--color-fg-3)', display: 'inline-flex', alignItems: 'center' }}
            >
              <Icon name="search" size={14} />
            </span>
            <input
              ref={headerSearchRef}
              type="search"
              placeholder="Search corpus…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search the corpus"
              style={{
                flex: 1,
                minWidth: 0,
                height: '100%',
                padding: 0,
                background: 'transparent',
                border: 0,
                outline: 'none',
                color: 'var(--color-fg-1)',
                fontFamily: 'inherit',
                fontSize: 'var(--text-sm)',
              }}
            />
          </label>
        </form>

        <div
          title="Pipeline status"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-success-soft)',
            color: 'var(--color-success)',
            fontSize: 'var(--text-xs)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'currentColor',
              boxShadow: '0 0 6px currentColor',
            }}
          />
          online
        </div>
      </div>
    </header>
  );
}

function navLink(active) {
  return {
    background: active ? 'var(--color-bg-2)' : 'transparent',
    border: 'none',
    cursor: 'pointer',
    color: active ? 'var(--color-fg-1)' : 'var(--color-fg-2)',
    fontWeight: active ? 500 : 400,
    padding: '7px 12px',
    borderRadius: 'var(--radius-md)',
    fontFamily: 'inherit',
    fontSize: 'var(--text-sm)',
  };
}

function BrowseMenu({ navigate, onClose }) {
  const { Stack } = window.SOL_PRIMS;
  const { DOMAINS } = window.SOL_DATA;
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 50 }} />
      <div
        style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: 0,
          background: 'var(--color-bg-1)',
          border: '1px solid var(--color-border-2)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: 24,
          zIndex: 51,
          width: 760,
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 28,
        }}
      >
        {DOMAINS.map((d) => (
          <div key={d.id}>
            <div
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--color-accent)',
                marginBottom: 10,
                display: 'flex',
                alignItems: 'baseline',
                gap: 8,
              }}
            >
              <span>{d.label}</span>
              <span
                style={{
                  fontFamily: 'var(--font-arabic-display)',
                  fontWeight: 400,
                  color: 'var(--color-fg-3)',
                  fontSize: 13,
                }}
                dir="rtl"
              >
                {d.label_ar}
              </span>
            </div>
            <Stack gap={1}>
              {d.categories.slice(0, 5).map((c) => (
                <button
                  key={c.slug}
                  onClick={() => navigate({ route: 'library', cat: c.slug })}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--color-fg-2)',
                    padding: '5px 0',
                    fontFamily: 'inherit',
                    fontSize: 'var(--text-sm)',
                    textAlign: 'left',
                  }}
                >
                  <span>{c.label}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, opacity: 0.55 }}>
                    {c.count}
                  </span>
                </button>
              ))}
              {d.categories.length > 5 && (
                <span
                  style={{
                    fontSize: 11,
                    color: 'var(--color-fg-3)',
                    marginTop: 4,
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  + {d.categories.length - 5} more
                </span>
              )}
            </Stack>
          </div>
        ))}
      </div>
    </>
  );
}

function AppFooter() {
  const { Text } = window.SOL_PRIMS;
  const { MonoLabel } = window.SOL_COMPS;
  return (
    <footer className="app-footer">
      <span className="app-footer__rule" aria-hidden="true" />
      <Text
        as="div"
        family="display"
        size="2xl"
        style={{ fontStyle: 'italic', letterSpacing: '-0.015em' }}
      >
        Shia Online Library
      </Text>
      <MonoLabel tone="tertiary" size={11}>
        MMXXVI
      </MonoLabel>
    </footer>
  );
}

window.SOL_APP_HEADER = { AppHeader, AppFooter };
