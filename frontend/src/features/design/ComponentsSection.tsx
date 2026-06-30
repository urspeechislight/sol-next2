import {
  Badge,
  IsnadNode,
  MatchRow,
  NarratorLink,
  Text,
  TitleLockup,
  TocItem,
} from '../../lib/design-system';
import type { BadgeVariant } from '../../lib/design-system';
import { reliabilityBadge } from '../../lib/variants';
import { Section } from './parts';

const GRADE_VARIANTS: BadgeVariant[] = ['default', 'success', 'warning', 'danger'];

function ReaderLabel({ children }: { children: string }) {
  return (
    <Text as="p" size="xs" font="mono" tone="muted">
      {children}
    </Text>
  );
}

export function ComponentsSection() {
  return (
    <Section id="components" title="Reader components">
      <Text as="p" tone="muted" className="ds-doc__lead">
        These render on the reading surface, shown here inside a classical reader theme.
      </Text>
      <div className="ds-doc__reader" data-reader-theme="classical">
        <ReaderLabel>TitleLockup · EN | AR mode (Issue 01)</ReaderLabel>
        <TitleLockup
          titleAr="تطور المصطلح النحوي البصري"
          titleEn="The Evolution of Basran Grammatical Terminology"
          author="Yaḥyā Ababina"
          mode="both"
        />

        <ReaderLabel>Badge · reader surface · tones + dot</ReaderLabel>
        <div className="ds-doc__reader-row">
          {GRADE_VARIANTS.map((v) => (
            <Badge key={v} surface="reader" variant={v}>
              {v}
            </Badge>
          ))}
          <Badge surface="reader" variant="success" dot>
            ṣaḥīḥ
          </Badge>
        </div>

        <ReaderLabel>TocItem</ReaderLabel>
        <div className="ds-doc__reader-panel">
          <TocItem titleAr="باب النية" titleEn="The Book of Intention" page={3} current />
          <TocItem titleAr="باب الإيمان" titleEn="The Book of Faith" page={11} />
        </div>

        <ReaderLabel>MatchRow</ReaderLabel>
        <div className="ds-doc__reader-panel">
          <MatchRow page={12} snippet="إنما الأعمال بالنيات وإنما لكل امرئ ما نوى" query="النيات" />
        </div>

        <ReaderLabel>NarratorLink (inline in isnād)</ReaderLabel>
        <Text as="p" font="arabic" dir="rtl">
          حدثنا <NarratorLink active>عبد الله بن مسلمة</NarratorLink> عن{' '}
          <NarratorLink>مالك بن أنس</NarratorLink>
        </Text>

        <ReaderLabel>IsnadNode (chain)</ReaderLabel>
        <div className="ds-doc__reader-panel">
          <IsnadNode
            index={0}
            showLine
            nameEn="ʿAbd Allāh b. Maslama"
            nameAr="عبد الله بن مسلمة"
            died={221}
            role="narrator"
            grade="thiqa"
            gradeVariant={reliabilityBadge('thiqa')}
          />
          <IsnadNode
            index={1}
            nameEn="Mālik b. Anas"
            nameAr="مالك بن أنس"
            died={179}
            role="narrator"
          />
        </div>
      </div>
    </Section>
  );
}
