import { Heading, Text } from '../../lib/design-system';

export interface ScopeHeadProps {
  breadcrumb: string;
  labelAr: string;
  /** The English line under the heading, e.g. "Shia Hadith, General · 484 works". */
  line: string;
}

/** The Arabic-led scope header shared by the library's works panes: the
    breadcrumb, the Arabic heading, and the count line. */
export function ScopeHead({ breadcrumb, labelAr, line }: ScopeHeadProps) {
  return (
    <header className="works__head">
      <Text size="xs" tone="faint" font="mono" className="works__crumb">
        {breadcrumb}
      </Text>
      <Heading level={2} font="arabic" dir="rtl">
        {labelAr}
      </Heading>
      <Text as="p" size="sm" tone="muted">
        {line}
      </Text>
    </header>
  );
}
