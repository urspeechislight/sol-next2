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
        <VerseSide verse={daily.verse} navigate={navigate} />
        <HadithSide hadith={daily.hadith} navigate={navigate} />
      </div>
    </section>
  );
}

function VerseSide({ verse, navigate }) {
  if (!verse) return null;
  const cite = `Q ${verse.surah_n}:${verse.ayah_n}`;
  const tafsirUrn = verse.tafsirs && verse.tafsirs[0] ? verse.tafsirs[0].urn : null;
  return (
    <section className="daily__col daily__verse" aria-label="Verse of the day">
      <header className="daily__col-head">
        <span className="mono-eyebrow">§ I · Verse of the day</span>
        <span className="mono-cite">{cite}</span>
      </header>

      <p className="ar-display ar-glow" lang="ar" dir="rtl" data-text={verse.ayah_ar}>
        {verse.ayah_ar}
      </p>

      {verse.ayah_en && <p className="en-translation">{verse.ayah_en}</p>}

      {verse.tafsirs && verse.tafsirs.length > 0 && (
        <div className="tafsir">
          <h3 className="meta-head">§ Tafsīr</h3>
          {verse.tafsirs.slice(0, 2).map((t, i) => (
            <article key={t.urn || i} className="tafsir__entry">
              <header className="tafsir__src">
                <em>{t.book}</em>
                <span className="meta-sep"> · </span>
                <span>{t.author}</span>
              </header>
              <p className="tafsir__excerpt">{t.excerpt_en}</p>
            </article>
          ))}
        </div>
      )}

      {tafsirUrn && (
        <button
          type="button"
          className="quiet-link"
          onClick={() => navigate({ route: 'reader', urn: tafsirUrn })}
        >
          Read full sūrah →
        </button>
      )}
    </section>
  );
}

function HadithSide({ hadith, navigate }) {
  if (!hadith) return null;
  const cite = `${hadith.source.book} ${hadith.source.n}`;
  return (
    <section className="daily__col daily__hadith" aria-label="Hadith of the day">
      <header className="daily__col-head">
        <span className="mono-eyebrow">§ II · Hadith of the day</span>
        <span className="mono-cite">{cite}</span>
      </header>

      <p className="ar-display ar-glow" lang="ar" dir="rtl" data-text={hadith.matn_ar}>
        {hadith.matn_ar}
      </p>

      {hadith.matn_en && <p className="en-translation">{hadith.matn_en}</p>}

      <div className="hadith-meta">
        <h3 className="meta-head">§ Chain</h3>
        <p className="hadith-isnad" lang="ar" dir="rtl">
          {hadith.isnad_ar}
        </p>
        {hadith.note && <p className="tafsir__excerpt">{hadith.note}</p>}
      </div>

      {hadith.source.urn && (
        <button
          type="button"
          className="quiet-link"
          onClick={() => navigate({ route: 'reader', urn: hadith.source.urn })}
        >
          Read in context →
        </button>
      )}
    </section>
  );
}

window.SOL_COMPS = window.SOL_COMPS || {};
window.SOL_COMPS.DailySection = DailySection;
window.DailySection = DailySection;
