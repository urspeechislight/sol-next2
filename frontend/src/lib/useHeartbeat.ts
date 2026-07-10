import { useEffect, useState } from 'react';

import { getHealth } from './api/client';
import type { HealthReport } from './types';

export type HeartbeatStatus = 'unknown' | 'ok' | 'degraded' | 'offline';

export interface Heartbeat {
  status: HeartbeatStatus;
  report: HealthReport | null;
}

const DEFAULT_INTERVAL_MS = 5000;

/** Poll /api/health every `intervalMs` and expose the backend's status. A failed
    fetch (an unreachable backend, the exact failure that showed as a bare 500)
    surfaces as 'offline' rather than a thrown error, so a dead backend reads as a
    clear state instead of a silent stall. */
export function useHeartbeat(intervalMs: number = DEFAULT_INTERVAL_MS): Heartbeat {
  const [beat, setBeat] = useState<Heartbeat>({ status: 'unknown', report: null });
  useEffect(() => {
    let active = true;
    const ping = () => {
      getHealth()
        .then((report) => {
          if (active) setBeat({ status: report.status === 'ok' ? 'ok' : 'degraded', report });
        })
        .catch(() => {
          if (active) setBeat({ status: 'offline', report: null });
        });
    };
    ping();
    const id = window.setInterval(ping, intervalMs);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [intervalMs]);
  return beat;
}
