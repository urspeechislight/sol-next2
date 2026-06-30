import { Badge, Button, Heading, Highlight, Inline, Text } from "../../lib/design-system";
import type { IconName } from "../../lib/design-system";
import type { NavView } from "../../app/shell/nav";
import { hadithBadge } from "../../lib/variants";
import "./HomeScreen.css";

// A live surface: shown as a prominent column with an action. The three things
// the workbench actually does today — everything else is demoted to the roadmap.
interface LiveSurface {
  icon: IconName;
  arabic: string;
  english: string;
  desc: string;
  go: string;
  target: NavView | "reader";
}

interface ComingSurface {
  arabic: string;
  english: string;
  preview?: boolean;
}

const LIVE: LiveSurface[] = [
  {
    icon: "reader",
    arabic: "القراءة",
    english: "Reader",
    desc: "Bilingual manuscript reading: isnād, matn and footnotes across three reader themes.",
    go: "Open the reader",
    target: "reader",
  },
  {
    icon: "library",
    arabic: "المكتبة",
    english: "Library",
    desc: "Browse the collection by domain: the Six Books, the Four Books, the schools of law.",
    go: "Browse",
    target: "library",
  },
  {
    icon: "daily",
    arabic: "اليوم",
    english: "Daily",
    desc: "A verse, a hadith and a chapter to continue — with parallels and tafsīr.",
    go: "Today's reading",
    target: "daily",
  },
];

const COMING: ComingSurface[] = [
  { arabic: "الإسناد", english: "Transmission graph", preview: true },
  { arabic: "الرجال", english: "Rijāl" },
  { arabic: "التوحيد", english: "Canonical" },
  { arabic: "التاريخ", english: "History" },
  { arabic: "الاستخراج", english: "Pipeline" },
];

const TAGS = ["Arabic-first", "Bilingual", "Isnād-linked"];

const REFS = [
  { ar: "صحيح مسلم", pg: "§1907" },
  { ar: "سنن النسائي", pg: "§75" },
  { ar: "مسند أحمد", pg: "§169" },
];

export interface HomeScreenProps {
  onNav: (view: NavView) => void;
  onOpenReader: () => void;
}

function openTarget(
  target: LiveSurface["target"],
  onNav: (view: NavView) => void,
  onOpenReader: () => void,
) {
  if (target === "reader") onOpenReader();
  else onNav(target);
}

export function HomeScreen({ onNav, onOpenReader }: HomeScreenProps) {
  return (
    <div className="home">
      <section className="home-hero">
        <div className="home-hero__copy">
          <Text size="xs" tone="accent" weight="semibold" className="home-eyebrow">
            SOL · a workbench for the classical tradition
          </Text>
          <Heading level={1} className="home-hero__title">
            Read the sources.
            <br />
            <em>Trace the chains.</em>
          </Heading>
          <Text as="p" size="md" tone="muted" className="home-hero__lede">
            Digitized Arabic manuscripts — hadith, fiqh, tafsīr and history — read Arabic-first with
            English alongside, every isnād one tap from its transmission graph.
          </Text>
          <Inline gap="lg" align="center" className="home-hero__cta">
            <Button variant="gold" iconBefore="reader" onClick={onOpenReader}>
              Start reading
            </Button>
            <Button variant="ghost" iconAfter="arrow-right" onClick={() => onNav("library")}>
              Browse the library
            </Button>
          </Inline>
          <ul className="home-tags" aria-label="At a glance">
            {TAGS.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>

        <div
          className="home-artifact"
          data-reader-theme="classical"
          aria-label="Example reading: the opening hadith of Ṣaḥīḥ al-Bukhārī"
        >
          <div className="home-artifact__top">
            <span className="home-artifact__id">
              <span className="home-artifact__num">١</span>
              Ṣaḥīḥ al-Bukhārī · Kitāb al-Īmān
            </span>
            <Badge surface="reader" variant={hadithBadge('sahih')} dot>
              ṣaḥīḥ
            </Badge>
          </div>
          <Text as="p" font="arabic" dir="rtl" className="home-artifact__isnad">
            حَدَّثَنَا عَبْدُ اللَّهِ بْنُ مَسْلَمَةَ الْقَعْنَبِيُّ، عَنْ مَالِكٍ
          </Text>
          <Text as="p" font="arabic" dir="rtl" className="home-artifact__matn">
            <Highlight
              text="إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى"
              query="النيات"
            />
          </Text>
          <Text as="p" className="home-artifact__en">
            “Actions are but by intentions, and each person shall have only what they intended.”
          </Text>
          <div className="home-artifact__refs">
            <span className="home-artifact__refs-label">Also cited</span>
            {REFS.map((r) => (
              <span key={r.pg} className="home-artifact__ref">
                <span className="home-artifact__ref-ar">{r.ar}</span>
                <span className="home-artifact__ref-pg">{r.pg}</span>
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="home-surfaces">
        <Text size="xs" tone="faint" weight="semibold" className="home-surfaces__label">
          The workbench — three ways in
        </Text>
        <div className="home-surfaces__row">
          {LIVE.map((s) => (
            <article key={s.english} className="home-surf">
              <Text font="arabic" dir="rtl" className="home-surf__ar">
                {s.arabic}
              </Text>
              <Heading level={3} className="home-surf__en">
                {s.english}
              </Heading>
              <Text as="p" size="sm" tone="muted" className="home-surf__desc">
                {s.desc}
              </Text>
              <Button
                variant="link"
                iconAfter="arrow-right"
                onClick={() => openTarget(s.target, onNav, onOpenReader)}
              >
                {s.go}
              </Button>
            </article>
          ))}
        </div>

        <div className="home-roadmap">
          <span className="home-roadmap__label">In progress</span>
          <ul className="home-roadmap__items">
            {COMING.map((c) => (
              <li
                key={c.english}
                className={c.preview ? "home-roadmap__item home-roadmap__item--preview" : "home-roadmap__item"}
              >
                <span className="home-roadmap__ar" dir="rtl">
                  {c.arabic}
                </span>
                <span className="home-roadmap__en">{c.english}</span>
                {c.preview ? <span className="home-roadmap__tag">Preview</span> : null}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
