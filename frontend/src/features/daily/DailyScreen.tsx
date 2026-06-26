import { Badge, Button, Card, Divider, Heading, Text } from "../../lib/design-system";
import "../screens.css";
import "./DailyScreen.css";

export interface DailyScreenProps {
  onOpenReader: () => void;
}

export function DailyScreen({ onOpenReader }: DailyScreenProps) {
  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">Daily · اليوم</Text>
        <Heading level={1}>Today’s reading</Heading>
        <Text as="p" size="sm" tone="muted" font="mono">١٢ ربيع الأول ١٤٤٧ · 14 June 2026</Text>
      </header>
      <div className="daily__grid">
        <Card variant="flat" pad="lg">
          <Text size="xs" tone="faint" weight="semibold" className="daily__label">Qurʾān · Al-Māʾida 5:6</Text>
          <p className="daily__ayah" dir="rtl">﴿يَا أَيُّهَا الَّذِينَ آمَنُوا إِذَا قُمْتُمْ إِلَى الصَّلَاةِ فَاغْسِلُوا وُجُوهَكُمْ وَأَيْدِيَكُمْ إِلَى الْمَرَافِقِ﴾</p>
          <p className="daily__ayah-en"><Text size="md" tone="muted" font="serif">O you who believe, when you rise for prayer, wash your faces and your hands up to the elbows.</Text></p>
          <div className="daily__tafsir">
            <Text size="xs" tone="accent" font="arabic" dir="rtl">جامع البيان</Text>
            <Text as="p" size="sm" tone="muted">The command attaches the obligation of ablution to the intention of prayer, not the mere standing.</Text>
          </div>
        </Card>
        <Card variant="flat" pad="lg">
          <div className="daily__hadith-head">
            <Text size="xs" tone="faint" weight="semibold" className="daily__label">Hadith</Text>
            <Badge variant="success"><span dir="rtl">صحيح</span></Badge>
          </div>
          <p className="daily__matn" dir="rtl">إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى.</p>
          <p className="daily__matn-en"><Text size="md" tone="muted" font="serif">Actions are but by intentions, and each person shall have only what they intended.</Text></p>
          <Text as="p" size="sm" tone="faint" font="arabic" dir="rtl">عن عمر بن الخطاب رضي الله عنه</Text>
          <Divider />
          <div className="daily__sources">
            <span className="daily__src"><Text size="sm" font="arabic" dir="rtl">صحيح البخاري</Text><Text size="xs" tone="faint" font="mono">№ 1</Text><Badge>Sunnī</Badge></span>
            <span className="daily__src"><Text size="sm" font="arabic" dir="rtl">صحيح مسلم</Text><Text size="xs" tone="faint" font="mono">№ 1907</Text></span>
          </div>
        </Card>
        <Card variant="raised" pad="lg" className="daily__pick">
          <Text size="xs" tone="accent" weight="semibold" className="daily__label">Continue reading</Text>
          <Text as="p" size="md" className="daily__rationale">Continue the Book of Purification: today’s verse and hadith both turn on intention and ablution.</Text>
          <Button variant="gold" iconBefore="reader" onClick={onOpenReader}>Open: Intention in Purification</Button>
        </Card>
      </div>
    </section>
  );
}
