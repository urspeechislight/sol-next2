// constants.test.ts — the paging contract PAGE mirrors. openapi-typescript
// strips numeric constraints, so schema.d.ts cannot type-check the backend's
// page-size default and cap; this test pins PAGE to the committed contract
// artifact (openapi.json) instead, so a backend change to either bound fails
// CI here rather than drifting silently.

import { describe, expect, it } from 'vitest';

import openapi from '../../openapi.json';
import { PAGE } from './constants';
import { API } from './routes';

interface LimitSchema {
  default?: number;
  maximum?: number;
}

interface ParameterShape {
  name: string;
  schema?: LimitSchema;
}

interface OperationShape {
  parameters?: ParameterShape[];
}

const doc = openapi as unknown as { paths: Record<string, Record<string, OperationShape>> };

function limitParams(): { path: string; schema: LimitSchema }[] {
  const out: { path: string; schema: LimitSchema }[] = [];
  for (const [path, ops] of Object.entries(doc.paths))
    for (const op of Object.values(ops))
      for (const p of op.parameters ?? [])
        if (p.name === 'limit' && p.schema) out.push({ path, schema: p.schema });
  return out;
}

describe('PAGE mirrors the served paging contract', () => {
  it('should match the works listing default with defaultLimit', () => {
    const works = limitParams().find((p) => p.path === `${API.BASE}${API.WORKS}`);
    expect(works).toBeDefined();
    expect(works?.schema.default).toBe(PAGE.defaultLimit);
  });

  it('should keep facetLimit within every served limit maximum', () => {
    const params = limitParams();
    expect(params.length).toBeGreaterThan(0);
    for (const p of params) {
      expect(p.schema.maximum, `limit maximum on ${p.path}`).toBeTypeOf('number');
      expect(
        p.schema.maximum ?? 0,
        `facetLimit exceeds the cap on ${p.path}`,
      ).toBeGreaterThanOrEqual(PAGE.facetLimit);
    }
  });
});
