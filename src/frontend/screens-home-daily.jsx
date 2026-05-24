/* global React */

const { useEffect: _useEffectDR, useState: _useStateDR } = React;

function DailySection({ navigate }) {
  const [daily, setDaily] = _useStateDR(window.SOL_DATA.DAILY);

  _useEffectDR(() => {
    const onUpdate = () => setDaily(window.SOL_DATA.DAILY);
    window.addEventListener('sol-data:DAILY', onUpdate);
    return () => window.removeEventListener('sol-data:DAILY', onUpdate);
  }, []);

  return (
    <section className="daily" aria-labelledby="daily-head">
      <header className="daily__head">
        <span className="daily__eyebrow">§ II · Today</span>
        <h2 id="daily-head" className="daily__title">
          The <em>Daily Pair</em>
        </h2>
      </header>

      <div className="daily__pair">
        <VerseCard verse={daily.verse} navigate={navigate} index={0} />
        <HadithCard hadith={daily.hadith} navigate={navigate} index={1} />
      </div>
    </section>
  );
}

function VerseCard({ verse, navigate, index }) {
  if (!verse) return null;
  const cite = `Q ${verse.surah_n}:${verse.ayah_n}`;
  const tafsirUrn = verse.tafsirs && verse.tafsirs[0] ? verse.tafsirs[0].urn : null;
  return (
    <article className="daily__card" style={{ '--index': index }}>
      <header className="daily__card-head">
        <span className="mono-eyebrow">§ Verse of the day</span>
        <span className="mono-cite">{cite}</span>
      </header>
      <AyahReveal text={verse.ayah_ar} />
      {verse.ayah_en && <p className="en-body">{verse.ayah_en}</p>}
      {tafsirUrn && (
        <button
          type="button"
          className="quiet-link"
          onClick={() => navigate({ route: 'reader', urn: tafsirUrn })}
        >
          Read full sūrah →
        </button>
      )}
    </article>
  );
}

function HadithCard({ hadith, navigate, index }) {
  if (!hadith) return null;
  const cite = `${hadith.source.book} ${hadith.source.n}`;
  return (
    <article className="daily__card" style={{ '--index': index }}>
      <header className="daily__card-head">
        <span className="mono-eyebrow">§ Hadith of the day</span>
        <span className="mono-cite">{cite}</span>
      </header>
      <AyahReveal text={hadith.matn_ar} />
      {hadith.matn_en && <p className="en-body">{hadith.matn_en}</p>}
      {hadith.source.urn && (
        <button
          type="button"
          className="quiet-link"
          onClick={() => navigate({ route: 'reader', urn: hadith.source.urn })}
        >
          Read in context →
        </button>
      )}
    </article>
  );
}

/* Reading-cursor reveal — each word is wrapped in a span carrying its
   index. CSS staggers an animation that brightens each word in turn,
   gives it an accent glow at peak, then settles. The whole sequence
   loops with a pause so the surface keeps quietly breathing. */
function AyahReveal({ text }) {
  const words = (text || '').split(/\s+/).filter(Boolean);
  return (
    <p
      className="ar-display ar-reveal"
      lang="ar"
      dir="rtl"
      style={{ '--word-count': words.length }}
    >
      {words.map((w, i) => (
        <span key={i} className="ar-reveal__word" style={{ '--i': i }}>
          {w}
          {i < words.length - 1 ? ' ' : ''}
        </span>
      ))}
    </p>
  );
}

window.SOL_COMPS = window.SOL_COMPS || {};
window.SOL_COMPS.DailySection = DailySection;
window.DailySection = DailySection;
