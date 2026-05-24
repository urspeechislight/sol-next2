/* global React */

function HomeScreen({ navigate, query, setQuery }) {
  const HeroCmp = window.SOL_COMPS.HomeHero;
  const DailyCmp = window.SOL_COMPS.DailySection;
  const ChangelogCmp = window.SOL_COMPS.HomeChangelog;

  return (
    <>
      {HeroCmp && <HeroCmp navigate={navigate} query={query} setQuery={setQuery} />}
      {DailyCmp && <DailyCmp navigate={navigate} />}
      {ChangelogCmp && <ChangelogCmp />}
    </>
  );
}

window.SOL_SCREENS = window.SOL_SCREENS || {};
window.SOL_SCREENS.HomeScreen = HomeScreen;
window.HomeScreen = HomeScreen;
