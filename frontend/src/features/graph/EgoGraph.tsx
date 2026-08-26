// EgoGraph.tsx:the bespoke radial-fan ego view over /api/narrators/{id}/graph.
// The selected narrator sits at the centre; its teachers or students fan out
// one ring per depth hop. Clicking a node re-centres the graph on it (a fresh
// fetch), direction and depth staying as set. The SVG carries the visual; an
// adjacent numbered neighbour list mirrors it for keyboard and screen-reader
// users, and is the one accessible path to re-centre (mirrors the observatory
// pattern). Colors and spacing come only from tokens.css classes/vars; the
// geometry (ring radii, node angles) is computed here in JS.
import { useState } from 'react';

import { Inline, Segmented, Spinner, Text, UnstyledButton } from '../../lib/design-system';
import type { SegmentedOption } from '../../lib/design-system';
import { ErrorText, EmptyText } from '../../lib/DataView';
import { getNarratorGraph } from '../../lib/api/client';
import type { NarratorGraphDirection } from '../../lib/api/client';
import type { NarratorGraph, NarratorGraphNode } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { deathLabel } from '../../lib/utils';
import './EgoGraph.css';

/** The frontend deliberately offers depth 1–2 (the backend allows 3): ring 2
    of a well-connected narrator already brushes the 400-node walk cap. */
const DEPTH_OPTIONS: SegmentedOption[] = [
  { value: '1', label: '1 hop' },
  { value: '2', label: '2 hops' },
];

const DIRECTION_OPTIONS: SegmentedOption[] = [
  { value: 'students', label: 'Students' },
  { value: 'teachers', label: 'Teachers' },
];

// Geometry: viewBox units. Ring 0 is the centre node; each depth hop is one
// concentric ring. Ring radii leave room for the Arabic label lines.
const VIEW = { w: 640, h: 560, cx: 320, cy: 280 } as const;
const RING_RADIUS: readonly number[] = [0, 150, 265];

interface Placed {
  node: NarratorGraphNode;
  x: number;
  y: number;
}

/** Place every node on its depth ring, evenly spread by angle; the root sits
    at the centre. Deterministic in the server's node order. */
function place(nodes: readonly NarratorGraphNode[]): Placed[] {
  return nodes.map((node) => {
    if (node.depth === 0 || RING_RADIUS[node.depth] === undefined) {
      return { node, x: VIEW.cx, y: VIEW.cy };
    }
    const ring = nodes.filter((n) => n.depth === node.depth);
    const index = ring.indexOf(node);
    const angle = (index / ring.length) * Math.PI * 2 - Math.PI / 2;
    const radius = RING_RADIUS[node.depth] ?? 0;
    return { node, x: VIEW.cx + Math.cos(angle) * radius, y: VIEW.cy + Math.sin(angle) * radius };
  });
}

/** The short label line under a node's dot: the first two name tokens plus
    the death year, so a dense ring stays readable. */
function shortName(nameAr: string): string {
  return nameAr
    .split(' ')
    .filter((token) => token && token !== 'بن')
    .slice(0, 2)
    .join(' ');
}

function EgoNode({
  placed,
  onClick,
}: {
  placed: Placed;
  onClick: (node: NarratorGraphNode) => void;
}) {
  const { node, x, y } = placed;
  return (
    <g
      className={node.depth === 0 ? 'ego__node ego__node--root' : 'ego__node'}
      transform={`translate(${x} ${y})`}
      onClick={() => onClick(node)}
    >
      <circle r={node.depth === 0 ? 14 : 9} className="ego__dot" />
      <text y={node.depth === 0 ? 32 : 24} className="ego__name">
        {shortName(node.primary_name_ar)}
      </text>
      {node.death_year_ah != null ? (
        <text y={node.depth === 0 ? 48 : 38} className="ego__meta">
          {deathLabel(node.death_year_ah)}
        </text>
      ) : null}
    </g>
  );
}

export function EgoGraph({ entryId }: { entryId: number }) {
  const [rootId, setRootId] = useState(entryId);
  const [direction, setDirection] = useState<NarratorGraphDirection>('students');
  const [depth, setDepth] = useState(1);

  const result = useAsync(
    () => getNarratorGraph(rootId, { direction, depth: Number(depth) }),
    [rootId, direction, depth],
  );

  return (
    <div className="ego">
      <Inline gap="sm" align="center" wrap>
        <Segmented
          label="Graph direction"
          value={direction}
          options={DIRECTION_OPTIONS}
          onChange={(v) => setDirection(v as NarratorGraphDirection)}
        />
        <Segmented
          label="Relation depth"
          value={String(depth)}
          options={DEPTH_OPTIONS}
          onChange={(v) => setDepth(Number(v))}
        />
      </Inline>
      <EgoGraphBody result={result} direction={direction} onRecenter={setRootId} />
    </div>
  );
}

function EgoGraphBody({
  result,
  direction,
  onRecenter,
}: {
  result: { data: NarratorGraph | null; error: Error | null; loading: boolean };
  direction: NarratorGraphDirection;
  onRecenter: (id: number) => void;
}) {
  if (result.loading) return <Spinner label="Loading transmission graph" className="ego__state" />;
  if (result.error) {
    return (
      <div className="ego__state">
        <ErrorText>Could not load the transmission graph: {result.error.message}</ErrorText>
      </div>
    );
  }
  const graph = result.data;
  if (!graph) return null;
  const root = graph.nodes.find((n) => n.depth === 0);
  const neighbours = graph.nodes.filter((n) => n.depth > 0);
  const placed = place(graph.nodes);
  const byId = new Map(placed.map((p) => [p.node.id, p]));
  const noun = direction === 'students' ? 'students' : 'teachers';

  return (
    <div className="ego__body">
      {graph.truncated ? (
        <p className="ego__truncated" role="status">
          <Text size="sm" tone="danger">
            Truncated — the expansion hit the narrator cap before completing. Reduce the depth for a
            complete view.
          </Text>
        </p>
      ) : null}
      {neighbours.length === 0 ? (
        <div className="ego__state">
          <EmptyText>{`No recorded ${noun} for this narrator.`}</EmptyText>
        </div>
      ) : (
        <svg
          viewBox={`0 0 ${VIEW.w} ${VIEW.h}`}
          className="ego__svg"
          role="img"
          aria-label={`Transmission graph of ${root?.primary_name_ar ?? 'the narrator'}: ${neighbours.length} ${noun} within ${graph.depth} ${graph.depth === 1 ? 'hop' : 'hops'}. Use the numbered list below to explore.`}
        >
          <g className="ego__rings" aria-hidden="true">
            {RING_RADIUS.slice(1, graph.depth + 1).map((r) => (
              <circle key={r} cx={VIEW.cx} cy={VIEW.cy} r={r} />
            ))}
          </g>
          <g className="ego__edges" aria-hidden="true">
            {graph.edges.map((e, i) => {
              const from = byId.get(e.from_id);
              const to = byId.get(e.to_id);
              if (!from || !to) return null;
              return (
                <line
                  key={`${e.from_id}-${e.to_id}-${i}`}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                />
              );
            })}
          </g>
          {placed.map((p) => (
            <EgoNode key={p.node.id} placed={p} onClick={(n) => onRecenter(n.id)} />
          ))}
        </svg>
      )}
      <div className="ego__list">
        <Text size="xs" tone="muted" weight="semibold" className="ego__listlabel">
          {`${root?.primary_name_ar ?? ''} — ${neighbours.length} ${noun} (numbered by ring, then name order; select to re-centre)`}
        </Text>
        <ol className="ego__neighbours">
          {[...neighbours]
            .sort((a, b) => a.depth - b.depth || a.id - b.id)
            .map((n) => (
              <li key={n.id} className="ego__neighbour">
                <UnstyledButton className="ego__pick" onClick={() => onRecenter(n.id)}>
                  <span className="ego__pick-ar" dir="rtl">
                    {n.primary_name_ar}
                  </span>
                  <span className="ego__pick-meta">
                    {deathLabel(n.death_year_ah) || 'date unknown'}
                  </span>
                </UnstyledButton>
              </li>
            ))}
        </ol>
      </div>
    </div>
  );
}
