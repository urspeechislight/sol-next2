import { RosetteOrnament } from './Ornament';
import './PageGlow.css';

/** The page-wide illumination: warm halos and a faint rosette laid once
    behind a whole screen, bleeding to the viewport edges. Cards above it use
    translucent surfaces so the glow reads through them. The host screen must
    be position: relative with its content above z-index 0. */
export function PageGlow() {
  return (
    <div className="ds-pageglow" aria-hidden="true">
      <div className="ds-pageglow__halo ds-pageglow__halo--n" />
      <div className="ds-pageglow__halo ds-pageglow__halo--s" />
      <div className="ds-pageglow__rosette">
        <RosetteOrnament />
      </div>
    </div>
  );
}
