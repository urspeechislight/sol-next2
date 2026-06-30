import { Text } from '../../lib/design-system';

import { cssVar } from './css-var';
import { Section, Spec, Swatch } from './parts';

const COLOR_GROUPS: { group: string; tokens: [string, string][] }[] = [
  {
    group: 'Surface & text',
    tokens: [
      ['bg', '--color-bg'],
      ['surface', '--color-surface'],
      ['surface-raised', '--color-surface-raised'],
      ['surface-sunken', '--color-surface-sunken'],
      ['text', '--color-text'],
      ['text-muted', '--color-text-muted'],
      ['text-faint', '--color-text-faint'],
      ['border', '--color-border'],
    ],
  },
  {
    group: 'Accent & status',
    tokens: [
      ['accent', '--color-accent'],
      ['accent-strong', '--color-accent-strong'],
      ['accent-deep', '--color-accent-deep'],
      ['accent-tint', '--color-accent-tint'],
      ['success', '--color-success'],
      ['warning', '--color-warning'],
      ['danger', '--color-danger'],
    ],
  },
  {
    group: 'Content & sect',
    tokens: [
      ['isnad', '--color-isnad'],
      ['matn', '--color-matn'],
      ['verse', '--color-verse'],
      ['ruling', '--color-ruling'],
      ['sunni', '--color-sunni'],
      ['shia', '--color-shia'],
    ],
  },
];

const TYPE_SIZES: [string, string][] = [
  ['3xl', '--text-3xl'],
  ['2xl', '--text-2xl'],
  ['xl', '--text-xl'],
  ['lg', '--text-lg'],
  ['md', '--text-md'],
  ['base', '--text-base'],
  ['sm', '--text-sm'],
  ['xs', '--text-xs'],
];

const SPACES: [string, string][] = [
  ['2xs', '--space-2xs'],
  ['xs', '--space-xs'],
  ['sm', '--space-sm'],
  ['gutter', '--space-gutter'],
  ['md', '--space-md'],
  ['lg', '--space-lg'],
  ['xl', '--space-xl'],
  ['2xl', '--space-2xl'],
  ['3xl', '--space-3xl'],
  ['4xl', '--space-4xl'],
];

const RADII: [string, string][] = [
  ['xs', '--radius-xs'],
  ['sm', '--radius-sm'],
  ['md', '--radius-md'],
  ['lg', '--radius-lg'],
  ['pill', '--radius-pill'],
];

const SHADOWS: [string, string][] = [
  ['sm', '--shadow-sm'],
  ['md', '--shadow-md'],
  ['lg', '--shadow-lg'],
  ['pop', '--shadow-pop'],
];

export function TokensSection() {
  return (
    <Section id="tokens" title="Tokens">
      {COLOR_GROUPS.map((c) => (
        <Spec key={c.group} label={`color · ${c.group}`}>
          <div className="ds-doc__swatches">
            {c.tokens.map(([name, token]) => (
              <Swatch key={token} name={name} token={token} />
            ))}
          </div>
        </Spec>
      ))}

      <Spec label="type scale">
        <div className="ds-doc__stack">
          {TYPE_SIZES.map(([name, token]) => (
            <p key={token} className="ds-doc__type" style={cssVar('--fs', token)}>
              {name} · The quick brown fox · الخط العربي
            </p>
          ))}
        </div>
      </Spec>

      <Spec label="spacing scale">
        <div className="ds-doc__stack">
          {SPACES.map(([name, token]) => (
            <div key={token} className="ds-doc__measure">
              <Text as="span" size="xs" font="mono" tone="muted" className="ds-doc__measure-label">
                {name}
              </Text>
              <span className="ds-doc__bar" style={cssVar('--bar', token)} />
            </div>
          ))}
        </div>
      </Spec>

      <Spec label="radii">
        {RADII.map(([name, token]) => (
          <div key={token} className="ds-doc__tile">
            <span className="ds-doc__radius" style={cssVar('--r', token)} />
            <Text as="span" size="xs" font="mono" tone="muted">
              {name}
            </Text>
          </div>
        ))}
      </Spec>

      <Spec label="elevation">
        {SHADOWS.map(([name, token]) => (
          <div key={token} className="ds-doc__tile">
            <span className="ds-doc__shadow" style={cssVar('--sh', token)} />
            <Text as="span" size="xs" font="mono" tone="muted">
              {name}
            </Text>
          </div>
        ))}
      </Spec>
    </Section>
  );
}
