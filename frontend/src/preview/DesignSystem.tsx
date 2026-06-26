import { useState } from 'react';
import type { ReactNode } from 'react';
import '../lib/design-system/tokens.css';
import '../lib/design-system/base.css';
import {
  Badge,
  Button,
  Card,
  Divider,
  Heading,
  Icon,
  Inline,
  Input,
  Link,
  Logo,
  Pager,
  QRCode,
  Segmented,
  Select,
  Spinner,
  Stack,
  Text,
} from '../lib/design-system';
import type { IconName } from '../lib/design-system';
import { THEME } from '../lib/constants';
import './DesignSystem.css';

const ICONS: IconName[] = [
  'library',
  'reader',
  'graph',
  'search',
  'book',
  'star',
  'share',
  'settings',
];
const SWATCHES = ['--color-surface', '--color-accent', '--color-success', '--color-danger'];

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card variant="raised" className="ds-demo__section">
      <Stack gap={4}>
        <Heading level={3}>{title}</Heading>
        {children}
      </Stack>
    </Card>
  );
}

function ButtonsSection() {
  return (
    <Section title="Buttons">
      <Inline gap={2}>
        <Button variant="primary">Primary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="danger">Danger</Button>
      </Inline>
      <Inline gap={2} align="center">
        <Button size="sm">Small</Button>
        <Button size="md">Medium</Button>
        <Button size="lg" iconBefore="star">
          Large
        </Button>
      </Inline>
    </Section>
  );
}

function TypeSection() {
  return (
    <Section title="Type">
      <Text as="h1">Heading one</Text>
      <Text as="h2">Heading two</Text>
      <Text as="body">Body copy in the parchment surface.</Text>
      <Text as="muted">Muted secondary text.</Text>
      <Text as="arabic" dir="rtl">
        بسم الله الرحمن الرحيم
      </Text>
      <Link href="#" variant="accent">
        An accent link
      </Link>
    </Section>
  );
}

function BadgesSection() {
  return (
    <Section title="Badges & Status">
      <Inline gap={2}>
        <Badge>Default</Badge>
        <Badge variant="success">Success</Badge>
        <Badge variant="warning">Warning</Badge>
        <Badge variant="danger">Danger</Badge>
      </Inline>
      <Inline gap={3} align="center">
        <Spinner size="sm" />
        <Spinner size="md" />
      </Inline>
    </Section>
  );
}

function FormsSection() {
  const [text, setText] = useState('');
  const [sel, setSel] = useState('en');
  const [seg, setSeg] = useState('both');
  return (
    <Section title="Forms">
      <Input value={text} placeholder="Search the corpus…" type="search" onInput={setText} />
      <Select
        value={sel}
        options={[
          { value: 'en', label: 'English' },
          { value: 'ar', label: 'Arabic' },
        ]}
        onChange={setSel}
      />
      <Segmented
        label="Language"
        value={seg}
        options={[
          { value: 'en', label: 'EN' },
          { value: 'both', label: 'EN | AR' },
          { value: 'ar', label: 'AR' },
        ]}
        onChange={setSeg}
      />
    </Section>
  );
}

function DataSection() {
  const [page, setPage] = useState(3);
  const qr = Array.from({ length: 9 }, (_, r) =>
    Array.from({ length: 9 }, (_, c) => (r + c) % 2 === 0),
  );
  return (
    <Section title="Data & Navigation">
      <Pager page={page} totalPages={12} onPage={setPage} />
      <Divider />
      <Inline gap={4} align="center">
        <QRCode matrix={qr} />
        <div className="ds-demo__icons">
          {ICONS.map((n) => (
            <Icon key={n} name={n} size="md" title={n} />
          ))}
        </div>
      </Inline>
    </Section>
  );
}

function BrandSection() {
  return (
    <Section title="Brand & Color">
      <Logo size="lg" />
      <div className="ds-demo__swatches">
        {SWATCHES.map((v) => (
          <div key={v} className="ds-demo__swatch" data-token={v} title={v} />
        ))}
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
    <div className="ds-demo">
      <div className="ds-demo__bar">
        <Logo size="md" />
        <Button variant="ghost" size="sm" iconBefore={dark ? 'sun' : 'moon'} onClick={toggle}>
          {dark ? 'Light' : 'Dark'}
        </Button>
      </div>
      <div className="ds-demo__grid">
        <ButtonsSection />
        <TypeSection />
        <BadgesSection />
        <FormsSection />
        <DataSection />
        <BrandSection />
      </div>
    </div>
  );
}
