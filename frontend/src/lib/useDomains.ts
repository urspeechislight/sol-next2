// useDomains.ts: the one cached fetch of the domain taxonomy. Every consumer
// (library rail, reader masthead, category labels) shares one request per
// session via useCachedAsync; the taxonomy is immutable corpus data.
import { getDomains } from './api/client';
import type { Domain } from './types';
import { type AsyncState, useCachedAsync } from './useAsync';

export function useDomains(): AsyncState<Domain[]> {
  return useCachedAsync<Domain[]>('domains', getDomains);
}
