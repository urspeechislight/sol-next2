import type { CSSProperties } from 'react';

/** Point a CSS custom property at a token, for the styleguide's token-driven
    demos. Kept in its own module (not alongside components) so React Fast Refresh
    stays happy: a module must not mix component and non-component exports. */
export function cssVar(name: string, token: string): CSSProperties {
  return { [name]: `var(${token})` } as CSSProperties;
}
