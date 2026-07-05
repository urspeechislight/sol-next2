import type { ReactNode } from 'react';

import { Inline, Stack, Text } from '../../lib/design-system';
import type { ExtractionEntity, ExtractionSpan, ExtractionUnit } from '../../lib/types';
import { behaviorTone } from './behaviors';

// Indent for the raw-JSON <details> dump; named so the value reads as a
// formatting choice, not a stray count.
const JSON_INDENT = 2;

/** Read a string field out of a decoded JSON object without trusting its
    shape; a missing or non-string value renders as ''. */
function textField(obj: unknown, key: string): string {
  if (obj && typeof obj === 'object') {
    const value = (obj as Record<string, unknown>)[key];
    if (typeof value === 'string') return value;
  }
  return '';
}

/** Span text with each in-range entity anchor wrapped in a <mark>. Anchors
    that overlap a previous one, or fall outside the text, are skipped here;
    they still appear in the entity list below, so nothing is hidden. */
function anchoredText(text: string, entities: ExtractionEntity[]): ReactNode[] {
  const nodes: ReactNode[] = [];
  let cursor = 0;
  const anchors = [...entities].sort((a, b) => a.char_start - b.char_start);
  for (const entity of anchors) {
    if (entity.char_start < cursor || entity.char_end > text.length) continue;
    if (entity.char_start > cursor) nodes.push(text.slice(cursor, entity.char_start));
    nodes.push(
      <mark
        key={entity.entity_id}
        className="xtr-anchor"
        title={`${entity.entity_type} ${entity.char_start}..${entity.char_end}`}
      >
        {text.slice(entity.char_start, entity.char_end)}
      </mark>,
    );
    cursor = entity.char_end;
  }
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes;
}

/** One unit row: its type and behavior tags, the citation head split off the
    chain (when the compilation printed one), then the Arabic text. Shared
    with the inspector's orphan section, so a unit renders identically
    whether or not its span starts on the page. */
export function UnitRow({ unit }: { unit: ExtractionUnit }) {
  const citationHead = textField(unit.metadata, 'citation_head');
  return (
    <div className="xtr-unit">
      <Inline gap="xs" align="center">
        <span className="xtr-tag">{unit.unit_type}</span>
        <span className={`xtr-dot xtr-tone--${behaviorTone(unit.behavior)}`} />
        <span className="xtr-mono">{unit.unit_id}</span>
      </Inline>
      {citationHead ? (
        <p className="xtr-crumb" dir="rtl" lang="ar">
          {citationHead}
        </p>
      ) : null}
      <p className="xtr-ar" dir="rtl" lang="ar">
        {unit.text_ar}
      </p>
    </div>
  );
}

/** One entity row: type, role, anchored text, char range, confidence, extractor. */
function EntityRow({ entity }: { entity: ExtractionEntity }) {
  const extractor = textField(entity.provenance, 'extractor_id');
  const role = textField(entity.metadata, 'role_in_context');
  return (
    <div className="xtr-entity">
      <span className="xtr-tag">{entity.entity_type}</span>
      {role ? <span className="xtr-tag">{role}</span> : null}
      <span className="xtr-ar xtr-entity__text" dir="rtl" lang="ar">
        {entity.text_ar}
      </span>
      <span className="xtr-mono">
        {entity.char_start}..{entity.char_end}
      </span>
      <span className="xtr-mono">
        {entity.confidence === null ? 'conf n/a' : `conf ${entity.confidence.toFixed(2)}`}
      </span>
      {extractor ? <span className="xtr-mono">{extractor}</span> : null}
    </div>
  );
}

interface SpanCardProps {
  span: ExtractionSpan;
  units: ExtractionUnit[];
  entities: ExtractionEntity[];
}

/** Everything the pipeline recorded for one span: behavior + type header,
    hierarchy breadcrumb, the text with entity anchors marked, the pattern
    matches that fed behavior routing, the units split out of the span, each
    entity's anchors/provenance, and the raw metadata JSON. */
export function SpanCard({ span, units, entities }: SpanCardProps) {
  return (
    <Stack gap="sm" className="xtr-span">
      <Inline gap="xs" align="center" wrap>
        <span className={`xtr-chip xtr-tone--${behaviorTone(span.behavior)}`}>
          {span.behavior}
        </span>
        <span className="xtr-tag">{span.span_type}</span>
        <span className="xtr-mono">{span.span_id}</span>
        <Text as="span" size="xs" tone="faint">
          pages {span.page_start}..{span.page_end} · depth {span.hierarchy_depth}
        </Text>
      </Inline>
      {span.hierarchy_path.length > 0 ? (
        <p className="xtr-crumb" dir="rtl" lang="ar">
          {span.hierarchy_path.join(' ‹ ')}
        </p>
      ) : null}
      <p className="xtr-ar xtr-span__text" dir="rtl" lang="ar">
        {anchoredText(span.text_ar, entities)}
      </p>
      {span.patterns.length > 0 ? (
        <Inline gap="xs" wrap>
          {span.patterns.map((pattern, index) => (
            <span
              key={`${pattern.pattern_id}-${index}`}
              className="xtr-pattern"
              title={`${pattern.matched_text} @ ${pattern.char_start}..${pattern.char_end}`}
            >
              {pattern.pattern_id}
            </span>
          ))}
        </Inline>
      ) : null}
      {units.length > 0 ? (
        <Stack gap="xs">
          {units.map((unit) => (
            <UnitRow key={unit.unit_id} unit={unit} />
          ))}
        </Stack>
      ) : null}
      {entities.length > 0 ? (
        <Stack gap="xs">
          {entities.map((entity) => (
            <EntityRow key={entity.entity_id} entity={entity} />
          ))}
        </Stack>
      ) : null}
      <details className="xtr-raw">
        <summary>raw span metadata</summary>
        <pre className="xtr-json">{JSON.stringify(span.metadata, null, JSON_INDENT)}</pre>
      </details>
    </Stack>
  );
}
