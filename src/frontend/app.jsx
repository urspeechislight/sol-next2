/* global React, ReactDOM */
const { useState, useEffect } = React;

function AppRoot() {
  const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/ {
    appTheme: 'day',
    readerTheme: 'classical',
    arabicFont: 'scheherazade',
    langMode: 'ar',
    fontSize: 20,
    isnadStyle: 'tree',
    accentHue: 30,
    bookPattern: 'star8',
  }; /*EDITMODE-END*/

  const [tweaks, setTweak] = window.useTweaks(TWEAK_DEFAULTS);
  useAppTheme(tweaks);

  // Routing
  const [route, setRoute] = useState({ name: 'home' });
  const [query, setQuery] = useState('');
  const navigate = (r) => {
    if (r.route === 'home') setRoute({ name: 'home' });
    else if (r.route === 'library') setRoute({ name: 'library', cat: r.cat });
    else if (r.route === 'search') {
      if (r.q !== undefined) setQuery(r.q);
      setRoute({ name: 'search', q: r.q ?? query });
    } else if (r.route === 'reader') setRoute({ name: 'reader', urn: r.urn, page: r.p });
    window.scrollTo(0, 0);
  };

  const isReader = route.name === 'reader';

  return (
    <div data-screen-label={routeLabel(route)} style={{ minHeight: '100vh' }}>
      <SkyBackdrop active={tweaks.appTheme === 'night'} />
      {!isReader && (
        <AppHeader
          navigate={navigate}
          query={query}
          setQuery={setQuery}
          route={route}
          theme={tweaks.appTheme}
          onToggleTheme={() => setTweak('appTheme', tweaks.appTheme === 'day' ? 'night' : 'day')}
        />
      )}
      <main>
        {route.name === 'home' && (
          <window.HomeScreen navigate={navigate} query={query} setQuery={setQuery} />
        )}
        {route.name === 'library' && <window.LibraryScreen cat={route.cat} navigate={navigate} />}
        {route.name === 'search' && (
          <window.SearchScreen q={route.q} navigate={navigate} setQuery={setQuery} />
        )}
        {route.name === 'reader' && (
          <window.ReaderScreen
            urn={route.urn}
            page={route.page}
            navigate={navigate}
            readerSettings={{
              theme: tweaks.readerTheme,
              langMode: tweaks.langMode,
              fontSize: tweaks.fontSize,
            }}
            setReaderSettings={(s) =>
              setTweak({ readerTheme: s.theme, langMode: s.langMode, fontSize: s.fontSize })
            }
            isnadStyle={tweaks.isnadStyle}
          />
        )}
      </main>
      {!isReader && <AppFooter />}

      <TweaksPanelContent tweaks={tweaks} setTweak={setTweak} />
    </div>
  );
}

function routeLabel(r) {
  if (r.name === 'home') return '01 Home, Browse corpus';
  if (r.name === 'library') return '02 Library, Category';
  if (r.name === 'search') return '03 Search results';
  if (r.name === 'reader') return '04 Reader';
  return r.name;
}

const AppHeader = window.SOL_APP_HEADER.AppHeader;
const SkyBackdrop = window.SOL_COMPS.SkyBackdrop;
const AppFooter = window.SOL_APP_HEADER.AppFooter;

function useAppTheme(tweaks) {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tweaks.appTheme);
    const fontMap = {
      scheherazade: "'Scheherazade New','Amiri',serif",
      amiri: "'Amiri','Scheherazade New',serif",
      noto: "'Noto Naskh Arabic',serif",
      reem: "'Reem Kufi',sans-serif",
    };
    document.documentElement.style.setProperty('--font-arabic', fontMap[tweaks.arabicFont]);
    document.documentElement.style.setProperty(
      '--font-arabic-display',
      tweaks.arabicFont === 'reem' ? fontMap.reem : "'Amiri','Scheherazade New',serif",
    );
  }, [tweaks.appTheme, tweaks.arabicFont]);

  useEffect(() => {
    window.SOL_BOOK_PATTERN = tweaks.bookPattern;
    document.documentElement.setAttribute('data-book-pattern', tweaks.bookPattern);
    window.dispatchEvent(new CustomEvent('sol-pattern-change', { detail: tweaks.bookPattern }));
  }, [tweaks.bookPattern]);
}

function TweaksPanelContent({ tweaks, setTweak }) {
  return (
    <window.TweaksPanel title="Tweaks">
      <window.TweakSection label="Appearance" />
      <window.TweakRadio
        label="App theme"
        value={tweaks.appTheme}
        options={[
          { value: 'day', label: 'Day (paper)' },
          { value: 'night', label: 'Night (lamp)' },
        ]}
        onChange={(v) => setTweak('appTheme', v)}
      />
      <window.TweakSlider
        label="Accent hue"
        value={tweaks.accentHue}
        min={0}
        max={360}
        step={5}
        unit="°"
        onChange={(v) => setTweak('accentHue', v)}
      />

      <window.TweakSection label="Arabic typography" />
      <window.TweakSelect
        label="Typeface"
        value={tweaks.arabicFont}
        options={[
          { value: 'scheherazade', label: 'Scheherazade New' },
          { value: 'amiri', label: 'Amiri (naskh)' },
          { value: 'noto', label: 'Noto Naskh' },
          { value: 'reem', label: 'Reem Kufi' },
        ]}
        onChange={(v) => setTweak('arabicFont', v)}
      />

      <window.TweakSection label="Reader" />
      <window.TweakRadio
        label="Theme"
        value={tweaks.readerTheme}
        options={[
          { value: 'classical', label: 'Classical' },
          { value: 'bright', label: 'Bright' },
          { value: 'dark', label: 'Dark' },
        ]}
        onChange={(v) => setTweak('readerTheme', v)}
      />
      <window.TweakRadio
        label="Language"
        value={tweaks.langMode}
        options={[
          { value: 'ar', label: 'AR' },
          { value: 'both', label: 'AR/EN' },
          { value: 'en', label: 'EN' },
        ]}
        onChange={(v) => setTweak('langMode', v)}
      />
      <window.TweakSlider
        label="Font size"
        value={tweaks.fontSize}
        min={14}
        max={28}
        step={1}
        unit="px"
        onChange={(v) => setTweak('fontSize', v)}
      />

      <window.TweakSection label="Book covers" />
      <window.TweakSelect
        label="Pattern"
        value={tweaks.bookPattern}
        options={[
          { value: 'star8', label: '8-point star (khātim)' },
          { value: 'girih', label: 'Girih lattice' },
          { value: 'arch', label: 'Mihrab arch' },
          { value: 'arabesque', label: 'Arabesque' },
          { value: 'kufic', label: 'Squared kufic' },
          { value: 'gradient', label: 'Plain gradient' },
        ]}
        onChange={(v) => setTweak('bookPattern', v)}
      />

      <window.TweakSection label="Isnād visualization" />
      <window.TweakSelect
        label="Style"
        value={tweaks.isnadStyle}
        options={[
          { value: 'tree', label: 'Vertical tree' },
          { value: 'horizontal', label: 'Horizontal flow' },
          { value: 'graph', label: 'Force-directed graph' },
          { value: 'cards', label: 'Stacked cards' },
        ]}
        onChange={(v) => setTweak('isnadStyle', v)}
      />
    </window.TweaksPanel>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<AppRoot />);
