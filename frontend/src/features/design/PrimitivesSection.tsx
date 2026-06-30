import { useState } from 'react';

import {
  Badge,
  Button,
  Chip,
  Divider,
  Heading,
  Highlight,
  Icon,
  ICON_NAMES,
  IconButton,
  Input,
  Link,
  Logo,
  Menu,
  NavArrow,
  Pager,
  Pill,
  Segmented,
  Spinner,
  Text,
} from '../../lib/design-system';
import type { BadgeVariant, ButtonVariant } from '../../lib/design-system';
import { viewHref } from '../../lib/routes';
import { Section, Spec } from './parts';

const BUTTON_VARIANTS: ButtonVariant[] = ['primary', 'secondary', 'gold', 'ghost', 'link'];
const BADGE_VARIANTS: BadgeVariant[] = ['default', 'success', 'warning', 'danger'];
const LANG_OPTIONS = [
  { value: 'en', label: 'EN' },
  { value: 'both', label: 'EN | AR' },
  { value: 'ar', label: 'AR' },
];
const SCOPE_OPTIONS = [
  { value: 'content', label: 'Content' },
  { value: 'title', label: 'Title' },
  { value: 'author', label: 'Author' },
];

function ControlsDemo() {
  const [pinned, setPinned] = useState(false);
  return (
    <>
      <Spec label="Button · variants">
        {BUTTON_VARIANTS.map((v) => (
          <Button key={v} variant={v}>
            {v}
          </Button>
        ))}
      </Spec>
      <Spec label="Button · sizes & icons">
        <Button size="sm" iconBefore="search">
          Small
        </Button>
        <Button size="md" iconAfter="arrow-right">
          Medium
        </Button>
        <Button variant="secondary" disabled>
          Disabled
        </Button>
      </Spec>
      <Spec label="IconButton">
        <IconButton label="Search" icon="search" />
        <IconButton label="Menu" icon="menu" size="sm" />
        <IconButton label="Close" icon="close" />
      </Spec>
      <Spec label="NavArrow · back / forward">
        <NavArrow direction="back" label="Back to catalog">
          Catalog
        </NavArrow>
        <NavArrow direction="forward" label="Next chapter">
          Next
        </NavArrow>
        <NavArrow direction="back" label="Back" />
        <NavArrow direction="forward" label="Forward" />
      </Spec>
      <Spec label="Pill">
        <Pill icon="menu" active={pinned} onClick={() => setPinned((p) => !p)}>
          Toggle
        </Pill>
        <Pill icon="search">Search</Pill>
        <Pill display>Display</Pill>
      </Spec>
      <Spec label="Badge">
        {BADGE_VARIANTS.map((v) => (
          <Badge key={v} variant={v}>
            {v}
          </Badge>
        ))}
      </Spec>
      <Spec label="Chip · removable filter token">
        <Chip icon="layers" onRemove={() => undefined}>
          Sunni Tafsir
        </Chip>
        <Chip onRemove={() => undefined} dir="rtl">
          فتح القدير
        </Chip>
        <Chip icon="bookmark">All volumes</Chip>
      </Spec>
    </>
  );
}

function FormsDemo() {
  const [lang, setLang] = useState('both');
  const [scope, setScope] = useState('content');
  const [text, setText] = useState('');
  return (
    <>
      <Spec label="Input">
        <Input
          value={text}
          onInput={setText}
          icon="search"
          ariaLabel="Demo search"
          placeholder="Search…"
        />
      </Spec>
      <Spec label="Menu">
        <Menu value={scope} options={SCOPE_OPTIONS} ariaLabel="Demo scope" onChange={setScope} />
      </Spec>
      <Spec label="Segmented">
        <Segmented label="Language" value={lang} options={LANG_OPTIONS} onChange={setLang} />
      </Spec>
    </>
  );
}

function TypographyDemo() {
  return (
    <>
      <Spec label="Text · tone">
        <Text tone="default">default</Text>
        <Text tone="muted">muted</Text>
        <Text tone="faint">faint</Text>
        <Text tone="accent">accent</Text>
        <Text tone="danger">danger</Text>
      </Spec>
      <Spec label="Text · font">
        <Text font="sans">Sans</Text>
        <Text font="serif">Serif</Text>
        <Text font="mono">Mono</Text>
        <Text font="arabic" dir="rtl">
          عربي
        </Text>
      </Spec>
      <Spec label="Heading · levels 1–4">
        <div className="ds-doc__stack">
          <Heading level={1}>Heading one</Heading>
          <Heading level={2}>Heading two</Heading>
          <Heading level={3}>Heading three</Heading>
          <Heading level={4}>Heading four</Heading>
        </div>
      </Spec>
      <Spec label="Link">
        <Link href={viewHref('design')} variant="default">
          default
        </Link>
        <Link href={viewHref('design')} variant="quiet">
          quiet
        </Link>
        <Link href={viewHref('design')} variant="accent">
          accent
        </Link>
      </Spec>
    </>
  );
}

function FeedbackDemo() {
  const [page, setPage] = useState(3);
  return (
    <>
      <Spec label="Spinner">
        <Spinner size="sm" />
        <Spinner size="md" label="Loading" />
      </Spec>
      <Spec label="Divider">
        <div className="ds-doc__stack">
          <Text tone="muted">above</Text>
          <Divider />
          <Text tone="muted">below</Text>
        </div>
      </Spec>
      <Spec label="Pager">
        <Pager page={page} totalPages={9} onPage={setPage} />
      </Spec>
      <Spec label="Logo">
        <Logo size="sm" />
        <Logo size="md" wordmark />
      </Spec>
      <Spec label="Highlight">
        <Text>
          <Highlight text="the isnād and the matn of the hadith" query="hadith" />
        </Text>
      </Spec>
    </>
  );
}

function IconsDemo() {
  return (
    <Spec label={`Icons · ${ICON_NAMES.length}`}>
      <div className="ds-doc__icons">
        {ICON_NAMES.map((name) => (
          <div key={name} className="ds-doc__icon">
            <Icon name={name} size="md" />
            <Text as="span" size="xs" font="mono" tone="faint">
              {name}
            </Text>
          </div>
        ))}
      </div>
    </Spec>
  );
}

export function PrimitivesSection() {
  return (
    <Section id="primitives" title="Primitives">
      <ControlsDemo />
      <FormsDemo />
      <TypographyDemo />
      <FeedbackDemo />
      <IconsDemo />
    </Section>
  );
}
