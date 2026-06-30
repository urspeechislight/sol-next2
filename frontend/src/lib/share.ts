// share.ts:the feature-side resolver the design-system ShareButton needs (the
// design system stays API-free). It builds a ShareResponse for a piece of
// content. The QR grid + server-rendered card image are backend-produced and
// absent here, so the share offers the link, caption, and social intents — the
// parts that work fully client-side. When a backend /share endpoint exists this
// is the one place to swap in its call.
import type { ShareContent, ShareResponse } from './types';

export function requestShare(content: ShareContent): Promise<ShareResponse> {
  return Promise.resolve({
    short_url: content.url.replace(/^https?:\/\//, ''),
    caption: `${content.arabic} — ${content.source}`,
    qr: [],
    image_url: null,
  });
}
