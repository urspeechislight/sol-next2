import { RosetteOrnament } from '../../lib/design-system';
import './HomeGlow.css';

/** The illuminated canvas behind the landing hero: the app's paper surface
    warmed by two soft gold halos and a large faint illumination rosette.
    Purely decorative; content floats above it. */
export function HomeGlow() {
  return (
    <div className="hglow" aria-hidden="true">
      <div className="hglow__base" />
      <div className="hglow__halo hglow__halo--n" />
      <div className="hglow__halo hglow__halo--s" />
      <div className="hglow__rosette">
        <RosetteOrnament />
      </div>
    </div>
  );
}
