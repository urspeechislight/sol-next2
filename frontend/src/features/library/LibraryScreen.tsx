import { useState } from "react";
import { Badge, Button, Card, Heading, Inline, Link, Text } from "../../lib/design-system";
import "../screens.css";
import "./LibraryScreen.css";

type Sect = "sunni" | "shia" | "";

interface Book {
  arabic: string;
  latin: string;
  author: string;
  meta: string;
  cat: string;
  sect: Sect;
  blurb: string;
}

const BOOKS: Book[] = [
  { arabic: "صحيح مسلم", latin: "Ṣaḥīḥ Muslim", author: "مسلم بن الحجاج", meta: "ت 261هـ · 875م", cat: "hadith", sect: "sunni", blurb: "The second of the Six Books; prized for the rigour of its isnāds." },
  { arabic: "صحيح البخاري", latin: "Ṣaḥīḥ al-Bukhārī", author: "محمد بن إسماعيل البخاري", meta: "ت 256هـ · 870م", cat: "hadith", sect: "sunni", blurb: "The foremost Sunni collection, organised by juristic chapter." },
  { arabic: "الكافي", latin: "Al-Kāfī", author: "محمد بن يعقوب الكليني", meta: "ت 329هـ · 941م", cat: "hadith", sect: "shia", blurb: "The earliest of the Four Books of the Imāmiyya." },
  { arabic: "المغني", latin: "Al-Mughnī", author: "موفّق الدين ابن قدامة", meta: "ت 620هـ · 1223م", cat: "fiqh", sect: "sunni", blurb: "The great Ḥanbalī compendium of comparative jurisprudence." },
  { arabic: "الأم", latin: "Al-Umm", author: "محمد بن إدريس الشافعي", meta: "ت 204هـ · 820م", cat: "fiqh", sect: "sunni", blurb: "The foundational corpus of the Shāfiʿī school." },
  { arabic: "جامع البيان", latin: "Jāmiʿ al-Bayān", author: "محمد بن جرير الطبري", meta: "ت 310هـ · 923م", cat: "tafsir", sect: "", blurb: "The encyclopaedic narration-based commentary on the Qurʾān." },
  { arabic: "السيرة النبوية", latin: "Al-Sīra al-Nabawiyya", author: "عبد الملك بن هشام", meta: "ت 218هـ · 833م", cat: "sira", sect: "", blurb: "The received recension of Ibn Isḥāq’s life of the Prophet ﷺ." },
  { arabic: "تهذيب الكمال", latin: "Tahdhīb al-Kamāl", author: "جمال الدين المزّي", meta: "ت 742هـ · 1341م", cat: "rijal", sect: "", blurb: "The biographical dictionary of the narrators of the Six Books." },
];

const CATS: [string, string][] = [
  ["", "All"], ["hadith", "Hadith"], ["fiqh", "Fiqh"], ["tafsir", "Tafsīr"], ["sira", "Sīra"], ["rijal", "Rijāl"],
];

export interface LibraryScreenProps {
  onOpenReader: () => void;
}

function SectBadge({ sect }: { sect: Sect }) {
  if (sect === "sunni") return <Badge>Sunnī</Badge>;
  if (sect === "shia") return <Badge>Shīʿa</Badge>;
  return null;
}

function BookCard({ b, onOpenReader }: { b: Book; onOpenReader: () => void }) {
  return (
    <Link href="#read" variant="default" className="book-card" ariaLabel={`Open ${b.latin}`} onActivate={onOpenReader}>
      <Card variant="flat" pad="md" interactive className="book-card__inner">
        <div className="book-card__top">
          <Heading level={3} font="arabic" dir="rtl">{b.arabic}</Heading>
          <SectBadge sect={b.sect} />
        </div>
        <Text as="p" size="sm" tone="muted" font="serif">{b.latin}</Text>
        <Text as="p" size="sm" tone="muted" font="arabic" dir="rtl">{b.author}</Text>
        <Text as="p" size="sm" tone="faint" className="book-card__blurb">{b.blurb}</Text>
        <div className="book-card__meta">
          <Text size="xs" tone="faint" font="mono">{b.meta}</Text>
          <Text size="xs" tone="accent" font="mono">{b.cat}</Text>
        </div>
      </Card>
    </Link>
  );
}

export function LibraryScreen({ onOpenReader }: LibraryScreenProps) {
  const [cat, setCat] = useState("");
  const items = BOOKS.filter((b) => !cat || b.cat === cat);
  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">Library · المكتبة</Text>
        <Heading level={1}>Browse the collection</Heading>
        <Text as="p" size="md" tone="muted" className="scr__lede">
          Canonical works of hadith, jurisprudence, exegesis and history, read Arabic-first with English alongside.
        </Text>
      </header>
      <Inline gap="xs" className="lib__cats">
        {CATS.map(([value, label]) => (
          <Button key={value} variant={value === cat ? "secondary" : "ghost"} size="sm" onClick={() => setCat(value)}>{label}</Button>
        ))}
      </Inline>
      <div className="lib__grid">
        {items.map((b) => <BookCard key={b.latin} b={b} onOpenReader={onOpenReader} />)}
      </div>
    </section>
  );
}
