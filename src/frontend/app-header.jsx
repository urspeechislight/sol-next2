/* global React */

const { useState: _useStateAH } = React;
const { useEffect: _useEffectAH, useRef: _useRefAH } = React;

function AppHeader({ navigate, query, setQuery, theme, onToggleTheme }) {
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
            src={theme === 'night' ? 'logo-dark.png' : 'logo-bright.png'}
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

        <button
          type="button"
          onClick={onToggleTheme}
          aria-label={theme === 'day' ? 'Switch to night theme' : 'Switch to day theme'}
          title={theme === 'day' ? 'Switch to night theme' : 'Switch to day theme'}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 36,
            height: 36,
            padding: 0,
            background: 'transparent',
            border: '1px solid var(--color-border-2)',
            borderRadius: 6,
            color: 'var(--color-fg-2)',
            cursor: 'pointer',
            transition:
              'color 200ms var(--ease-out-strong), border-color 200ms var(--ease-out-strong)',
          }}
        >
          {theme === 'day' ? <SunGlyph /> : <MoonGlyph />}
        </button>
      </div>
    </header>
  );
}

function SunGlyph() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="8" cy="8" r="3" />
      <path d="M8 1.5V3M8 13v1.5M14.5 8H13M3 8H1.5M12.6 3.4 11.5 4.5M4.5 11.5 3.4 12.6M12.6 12.6 11.5 11.5M4.5 4.5 3.4 3.4" />
    </svg>
  );
}

function MoonGlyph() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M14 9.5A5.5 5.5 0 1 1 6.5 2 4.5 4.5 0 0 0 14 9.5Z" />
    </svg>
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
          width: 840,
          maxHeight: '80vh',
          overflowY: 'auto',
          columnCount: 2,
          columnGap: 36,
        }}
      >
        {DOMAINS.map((d) => (
          <div
            key={d.id}
            style={{ breakInside: 'avoid', marginBottom: 28, WebkitColumnBreakInside: 'avoid' }}
          >
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
              {d.categories.map((c) => (
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
