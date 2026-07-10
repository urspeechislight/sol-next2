import { useHeartbeat } from '../../lib/useHeartbeat';
import type { HeartbeatStatus } from '../../lib/useHeartbeat';
import './HealthDot.css';

const TITLE: Record<HeartbeatStatus, string> = {
  unknown: 'Checking backend…',
  ok: 'Backend healthy',
  degraded: 'Backend degraded',
  offline: 'Backend unreachable',
};

/** A small status dot in the header that polls /api/health every 5 seconds and
    colours by result; a degraded probe names the failing subsystems in the tooltip,
    turning a silent backend outage into an at-a-glance signal. */
export function HealthDot() {
  const { status, report } = useHeartbeat();
  const failing = report?.checks.filter((check) => !check.ok).map((check) => check.name) ?? [];
  const title =
    status === 'degraded' && failing.length > 0 ? `Degraded: ${failing.join(', ')}` : TITLE[status];
  return (
    <span
      className={`health-dot health-dot--${status}`}
      role="status"
      title={title}
      aria-label={title}
    />
  );
}
