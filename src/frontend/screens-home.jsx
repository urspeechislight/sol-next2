/* global React */

function HomeScreen({ navigate, query, setQuery }) {
  const EyebrowCmp = window.SOL_COMPS.HomeEyebrow;
  const HeroCmp = window.SOL_COMPS.HomeHero;
  const CabinetCmp = window.SOL_COMPS.DomainCabinet;
  const InstrumentCmp = window.SOL_COMPS.DailyInstrument;
  const DailyCmp = window.SOL_COMPS.DailySection;
  const ChangelogCmp = window.SOL_COMPS.HomeChangelog;

  return (
    <div className="celestial">
      <div className="celestial__stack">
        {EyebrowCmp && <EyebrowCmp />}

        {HeroCmp && <HeroCmp navigate={navigate} query={query} setQuery={setQuery} />}

        <SoftRule />

        {CabinetCmp && <CabinetCmp navigate={navigate} />}

        <SoftRule />

        {InstrumentCmp && <InstrumentCmp navigate={navigate} />}

        <SoftRule />

        {DailyCmp && <DailyCmp navigate={navigate} />}

        {ChangelogCmp && <ChangelogCmp />}
      </div>
    </div>
  );
}

function SoftRule() {
  return <div className="soft-rule" aria-hidden="true" />;
}

window.SOL_SCREENS = window.SOL_SCREENS || {};
window.SOL_SCREENS.HomeScreen = HomeScreen;
window.HomeScreen = HomeScreen;
