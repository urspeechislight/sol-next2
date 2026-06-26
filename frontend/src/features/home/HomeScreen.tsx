import { Badge, Button, Card, Heading, Icon, Inline, Text } from "../../lib/design-system";
import type { BadgeVariant, IconName } from "../../lib/design-system";
import { ASSETS } from "../../lib/routes";
import type { NavView } from "../../app/shell/nav";
import "./HomeScreen.css";

type Status = "live" | "preview" | "soon";

interface Surface {
  icon: IconName;
  arabic: string;
  english: string;
  desc: string;
  status: Status;
  target: NavView | "reader" | null;
}

const STATUS_BADGE: Record<Status, [BadgeVariant, string]> = {
  live: ["success", "Live"],
  preview: ["warning", "Preview"],
  soon: ["default", "Soon"],
};

const SURFACES: Surface[] = [
  { icon: "reader", arabic: "القراءة", english: "Reader", desc: "Bilingual manuscript reading: isnād, matn and footnotes across three reader themes.", status: "live", target: "reader" },
  { icon: "library", arabic: "المكتبة", english: "Library", desc: "Browse the collection by domain: the Six Books, the Four Books, the schools of law.", status: "live", target: "library" },
  { icon: "daily", arabic: "اليوم", english: "Daily", desc: "A verse, a hadith and a chapter to continue, with parallels and tafsīr.", status: "live", target: "daily" },
  { icon: "graph", arabic: "الإسناد", english: "Transmission graph", desc: "Trace a narrator through teachers, students and the works that cite them.", status: "preview", target: "graph" },
  { icon: "node", arabic: "الرجال", english: "Rijāl", desc: "Narrator biographies: teachers, students and reliability gradings across traditions.", status: "soon", target: null },
  { icon: "layers", arabic: "التوحيد", english: "Canonical", desc: "Deduplicated narrator profiles with merge confidence across editions.", status: "soon", target: null },
  { icon: "calendar", arabic: "التاريخ", english: "History", desc: "Persons and dated events anchored to the Hijrī calendar.", status: "soon", target: null },
  { icon: "grid", arabic: "الاستخراج", english: "Pipeline", desc: "Span-by-span provenance: patterns, behaviour routing, entities and units.", status: "soon", target: null },
];

export interface HomeScreenProps {
  onNav: (view: NavView) => void;
  onOpenReader: () => void;
}

function SurfaceCard({ s, onNav, onOpenReader }: { s: Surface; onNav: (v: NavView) => void; onOpenReader: () => void }) {
  const [tone, label] = STATUS_BADGE[s.status];
  const active = s.status !== "soon";
  const open = () => {
    if (s.target === "reader") onOpenReader();
    else if (s.target) onNav(s.target);
  };
  return (
    <Card variant="flat" pad="md" interactive={active} className="surface-card">
      <div className="surface-card__top">
        <span className="surface-card__icon"><Icon name={s.icon} size="lg" /></span>
        <Badge variant={tone}>{label}</Badge>
      </div>
      <Heading level={3} font="arabic" dir="rtl">{s.arabic}</Heading>
      <Text as="p" size="md" weight="semibold">{s.english}</Text>
      <Text as="p" size="sm" tone="muted" className="surface-card__desc">{s.desc}</Text>
      {active ? <Button variant="ghost" size="sm" iconAfter="arrow-right" onClick={open}>Open</Button> : null}
    </Card>
  );
}

export function HomeScreen({ onNav, onOpenReader }: HomeScreenProps) {
  return (
    <>
      <section className="home__hero">
        <span className="home__mark"><img src={ASSETS.LOGO_MARK} alt="SOL" /></span>
        <Text size="xs" tone="accent" weight="semibold" className="home__eyebrow">SOL · a workbench for the classical tradition</Text>
        <Heading level={1} className="home__title">Read the sources, trace the chains.</Heading>
        <Text as="p" size="md" tone="muted" className="home__lede">
          Digitized Arabic manuscripts: hadith, fiqh, tafsīr and history, read Arabic-first with English alongside, every isnād one tap from its transmission graph.
        </Text>
        <Inline gap="sm" justify="center">
          <Button variant="gold" iconBefore="reader" onClick={onOpenReader}>Start reading</Button>
          <Button variant="secondary" iconBefore="daily" onClick={() => onNav("daily")}>Today’s reading</Button>
        </Inline>
      </section>

      <Card variant="raised" pad="lg" className="home-continue">
        <div>
          <Text size="xs" tone="accent" weight="semibold" className="home-continue__eyebrow">Continue reading</Text>
          <Heading level={3} font="arabic" dir="rtl" className="home-continue__title">المغني · باب الوضوء</Heading>
          <Text as="p" size="sm" tone="muted">Ibn Qudāma al-Maqdisī · page 4 of 312</Text>
        </div>
        <Button variant="secondary" iconBefore="reader" onClick={onOpenReader}>Resume</Button>
      </Card>

      <Text size="xs" tone="faint" weight="semibold" className="home__section">The workbench</Text>
      <div className="home__grid">
        {SURFACES.map((s) => <SurfaceCard key={s.english} s={s} onNav={onNav} onOpenReader={onOpenReader} />)}
      </div>
    </>
  );
}
