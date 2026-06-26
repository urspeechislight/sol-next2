import { useState } from "react";
import type { ReactNode } from "react";
import "../lib/design-system/tokens.css";
import "../lib/design-system/base.css";
import {
  Badge, Button, Card, Divider, Heading, Icon, Input, Link, Logo,
  Select, Spinner, Text, Textarea,
} from "../lib/design-system";
import type { IconName } from "../lib/design-system";
import { THEME } from "../lib/constants";
import "./DesignSystem.css";

type Swatch = [string, string];
const SURFACE: Swatch[] = [
  ["Background", "--color-bg"], ["Surface", "--color-surface"],
  ["Raised", "--color-surface-raised"], ["Sunken", "--color-surface-sunken"],
];
const ACCENT: Swatch[] = [
  ["Accent", "--color-accent"], ["Strong", "--color-accent-strong"],
  ["Deep", "--color-accent-deep"], ["Tint", "--color-accent-tint"],
];
const SECT: Swatch[] = [
  ["Sunni", "--color-sunni"], ["Shia", "--color-shia"],
  ["Isnad", "--color-isnad"], ["Matn", "--color-matn"],
];
const ICONS: IconName[] = [
  "library", "reader", "graph", "search", "book", "scroll", "star", "quote",
  "filter", "compass", "share", "qr", "bookmark", "users", "globe", "settings",
];

function Section({ eyebrow, title, children }: { eyebrow: string; title: string; children: ReactNode }) {
  return (
    <section className="pv-sec">
      <div className="pv-eyebrow">{eyebrow}</div>
      <Heading level={2}>{title}</Heading>
      {children}
    </section>
  );
}

function Swatches({ items }: { items: Swatch[] }) {
  return (
    <div className="pv-grid-4">
      {items.map(([name, tok]) => (
        <div key={tok} className="pv-swatch">
          <div className="pv-swatch__chip" style={{ background: `var(${tok})` }} />
          <div className="pv-swatch__meta">
            <Text size="xs" weight="medium">{name}</Text>
            <div className="pv-swatch__tok">{tok}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function TypeRow({ tk, children }: { tk: string; children: ReactNode }) {
  return (
    <div className="pv-type-row">
      <span className="pv-type-row__tk">{tk}</span>
      <div>{children}</div>
    </div>
  );
}

function ColorSection() {
  return (
    <Section eyebrow="Foundations" title="Color">
      <Text as="p" size="sm" tone="muted">
        A private palette feeds a semantic layer; dark mode re-points the same names.
      </Text>
      <div className="pv-lbl">Surfaces &amp; text</div>
      <Swatches items={SURFACE} />
      <div className="pv-lbl">Accent · gold</div>
      <Swatches items={ACCENT} />
      <div className="pv-lbl">Sect &amp; grade</div>
      <Swatches items={SECT} />
    </Section>
  );
}

function TypeSection() {
  return (
    <Section eyebrow="Foundations" title="Typography">
      <TypeRow tk="3xl · 40"><Heading level={1}>A manuscript, made legible</Heading></TypeRow>
      <TypeRow tk="2xl · 30"><Heading level={2}>The Book of Purification</Heading></TypeRow>
      <TypeRow tk="xl · 24"><Heading level={3}>Water and its categories</Heading></TypeRow>
      <TypeRow tk="md · 16"><Text size="md">Body: narration-based interpretation.</Text></TypeRow>
      <TypeRow tk="sm · 13"><Text size="sm" tone="muted">Secondary: chain of transmission</Text></TypeRow>
      <TypeRow tk="mono"><Text size="sm" font="mono" tone="faint">urn:sol:book:muslim · p.1</Text></TypeRow>
      <div className="pv-lbl">Arabic · Amiri display + naskh body</div>
      <Card variant="flat" pad="lg">
        <div className="pv-ar-d">كِتَابُ الطَّهَارَةِ</div>
        <div className="pv-ar-b">الطَّهَارَةُ فِي اللُّغَةِ النَّظَافَةُ وَالنَّزَاهَةُ عَنِ الْأَقْذَارِ.</div>
      </Card>
    </Section>
  );
}

function ButtonSection() {
  return (
    <Section eyebrow="Primitives" title="Buttons">
      <div className="pv-row">
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="gold">Gold</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="secondary" disabled>Disabled</Button>
      </div>
      <div className="pv-lbl">With icons · small</div>
      <div className="pv-row">
        <Button variant="gold" size="sm" iconBefore="reader">Open reader</Button>
        <Button variant="secondary" size="sm" iconBefore="graph">Transmission graph</Button>
        <Button variant="ghost" size="sm" iconBefore="filter">Filter</Button>
      </div>
    </Section>
  );
}

function BadgeSection() {
  return (
    <Section eyebrow="Primitives" title="Badges &amp; feedback">
      <div className="pv-row">
        <Badge>default</Badge>
        <Badge variant="success">success · ثقة</Badge>
        <Badge variant="warning">warning · صدوق</Badge>
        <Badge variant="danger">danger · ضعيف</Badge>
        <Spinner size="sm" />
        <Spinner size="md" />
      </div>
    </Section>
  );
}

function FormSection() {
  const [q, setQ] = useState("");
  const [domain, setDomain] = useState("hadith");
  const [note, setNote] = useState("");
  return (
    <Section eyebrow="Primitives" title="Forms">
      <div className="pv-row" style={{ alignItems: "flex-end" }}>
        <Input value={q} label="Search" id="pv-q" icon="search" type="search" placeholder="Search narrators, books…" onInput={setQ} />
        <Select
          value={domain} ariaLabel="Domain"
          options={[{ value: "hadith", label: "Hadith" }, { value: "fiqh", label: "Jurisprudence" }, { value: "tafsir", label: "Exegesis" }]}
          onChange={setDomain}
        />
        <Textarea id="pv-note" label="Note" value={note} rows={2} placeholder="A short note…" onChange={setNote} />
      </div>
    </Section>
  );
}

function CardSection() {
  return (
    <Section eyebrow="Primitives" title="Cards &amp; links">
      <div className="pv-row">
        <Card variant="flat" pad="md"><Text weight="semibold">Flat</Text></Card>
        <Card variant="raised" pad="md"><Text weight="semibold">Raised</Text></Card>
        <Card variant="sunken" pad="md"><Text weight="semibold">Sunken</Text></Card>
      </div>
      <div className="pv-row">
        <Link href="#" variant="default">Default link</Link>
        <Link href="#" variant="quiet">Quiet link</Link>
        <Link href="#" variant="accent">Accent link</Link>
      </div>
      <Divider />
    </Section>
  );
}

function IconSection() {
  return (
    <Section eyebrow="Primitives" title="Icons">
      <div className="pv-icons">
        {ICONS.map((n) => (
          <div key={n} className="pv-icon-cell">
            <Icon name={n} size="lg" title={n} />
            <span className="pv-icon-cell__n">{n}</span>
          </div>
        ))}
      </div>
    </Section>
  );
}

function BrandSection() {
  return (
    <Section eyebrow="Primitives" title="Brand">
      <div className="pv-row">
        <Logo size="lg" />
        <Logo size="md" />
        <Logo size="sm" wordmark={false} />
      </div>
    </Section>
  );
}

export function DesignSystem() {
  const [dark, setDark] = useState(false);
  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute(THEME.ATTR, next ? THEME.DARK : THEME.LIGHT);
  };
  return (
    <>
      <div className="pv-top">
        <Logo size="sm" />
        <div className="pv-top__sub">Design System · tokens &amp; primitives</div>
        <div className="pv-top__actions">
          <Button variant="gold" size="sm" iconBefore={dark ? "sun" : "moon"} onClick={toggle}>
            {dark ? "Light" : "Dark"}
          </Button>
        </div>
      </div>
      <main className="pv">
        <ColorSection />
        <TypeSection />
        <ButtonSection />
        <BadgeSection />
        <FormSection />
        <CardSection />
        <IconSection />
        <BrandSection />
      </main>
    </>
  );
}
