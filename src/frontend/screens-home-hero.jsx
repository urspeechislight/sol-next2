/* global React */

const { useEffect: _useEffectFR, useRef: _useRefFR, useState: _useStateFR } = React;

const SUGGESTIONS = ['Bukhari 1.1.2', 'Kashf al-Asrar', 'في فضل العلم'];

const LAST_READ_URN_KEY = 'sol:last-read-urn';
const LAST_READ_PAGE_KEY = 'sol:last-read-page';
const LAST_READ_TITLE_KEY = 'sol:last-read-title';
const LAST_READ_CHAPTER_KEY = 'sol:last-read-chapter';
const LAST_READ_TOTAL_KEY = 'sol:last-read-total';

const CITATION_RE = /^[A-Za-zāīūṣṭḍẓʾʿ؀-ۿ\- ]+\s+\d+(\.\d+){1,3}$/;

function parseSearchQuery(q) {
  const trimmed = q.trim();
  if (!trimmed) return { type: 'empty', q: '' };
  if (CITATION_RE.test(trimmed)) return { type: 'citation', q: trimmed };
  return { type: 'free', q: trimmed };
}

function HomeHero({ navigate, query, setQuery }) {
  const inputRef = _useRefFR(null);
  const [resume, setResume] = _useStateFR(null);

  _useEffectFR(() => {
    const urn = window.localStorage.getItem(LAST_READ_URN_KEY);
    const page = window.localStorage.getItem(LAST_READ_PAGE_KEY);
    if (!urn || !page) return;
    setResume({
      urn,
      page: Number(page),
      title: window.localStorage.getItem(LAST_READ_TITLE_KEY) || urn,
      chapter: window.localStorage.getItem(LAST_READ_CHAPTER_KEY) || '',
      total: Number(window.localStorage.getItem(LAST_READ_TOTAL_KEY)) || 0,
    });
  }, []);

  const submit = (e) => {
    e.preventDefault();
    const parsed = parseSearchQuery(query);
    if (parsed.type === 'empty') return;
    navigate({ route: 'search', q: parsed.q });
  };

  const submitWith = (q) => {
    setQuery(q);
    navigate({ route: 'search', q });
  };

  return (
    <section className="primary" aria-label="Search the corpus">
      <div className="primary__inner">
        {resume ? (
          <ResumeCard
            resume={resume}
            navigate={navigate}
            onSearchClick={() => inputRef.current?.focus()}
          />
        ) : (
          <SearchCard
            query={query}
            setQuery={setQuery}
            onSubmit={submit}
            onPick={submitWith}
            inputRef={inputRef}
          />
        )}
      </div>
    </section>
  );
}

function SearchCard({ query, setQuery, onSubmit, onPick, inputRef }) {
  return (
    <form className="search-card" onSubmit={onSubmit} role="search">
      <label className="search-card__field">
        <Loupe />
        <input
          ref={inputRef}
          type="search"
          className="search-card__input"
          placeholder='Search any line in any book — e.g. "Bukhari 1.1.2" or "في فضل العلم"'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search any line in any book"
        />
        <kbd className="search-card__kbd" aria-hidden="true">
          ⌘K
        </kbd>
      </label>

      <div className="search-card__suggestions">
        {SUGGESTIONS.map((s, i) => (
          <React.Fragment key={s}>
            {i > 0 && (
              <span className="search-card__sep" aria-hidden="true">
                ·
              </span>
            )}
            <button
              type="submit"
              className="search-card__suggestion"
              onClick={(e) => {
                e.preventDefault();
                onPick(s);
              }}
            >
              {s}
            </button>
          </React.Fragment>
        ))}
      </div>
    </form>
  );
}

function ResumeCard({ resume, navigate, onSearchClick }) {
  return (
    <article className="resume-card">
      <span className="resume-card__eyebrow">§ CONTINUE READING</span>
      <h2 className="resume-card__title">{resume.title}</h2>
      {resume.chapter && <p className="resume-card__chapter">{resume.chapter}</p>}
      <p className="resume-card__page">
        page {resume.page}
        {resume.total ? ` of ${resume.total}` : ''}
      </p>
      <button
        type="button"
        className="resume-card__cta"
        onClick={() => navigate({ route: 'reader', urn: resume.urn, p: resume.page })}
      >
        Resume
      </button>
      <button type="button" className="resume-card__alt" onClick={onSearchClick}>
        or search any line
      </button>
    </article>
  );
}

function Loupe() {
  return (
    <svg
      className="search-card__loupe"
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
      <circle cx="7" cy="7" r="4.5" />
      <path d="M10.5 10.5 L14 14" />
    </svg>
  );
}

window.SOL_COMPS = window.SOL_COMPS || {};
window.SOL_COMPS.HomeHero = HomeHero;
