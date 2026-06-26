import { useState } from 'react';
import type { ShareContent, ShareResponse } from '../../types';
import { Button, type ButtonVariant, type ButtonSize } from './Button';
import { ShareSheet } from './ShareSheet';

export interface ShareButtonProps {
  content: ShareContent;
  /** Feature-supplied resolver (keeps the design system free of API imports). */
  requestShare: (content: ShareContent) => Promise<ShareResponse>;
  variant?: ButtonVariant;
  size?: ButtonSize;
  label?: string;
}

/** The single, low-noise share affordance: opens the ShareSheet on demand. */
export function ShareButton({
  content,
  requestShare,
  variant = 'ghost',
  size = 'sm',
  label = 'Share',
}: ShareButtonProps) {
  const [response, setResponse] = useState<ShareResponse | null>(null);

  const open = async () => {
    const r = await requestShare(content);
    setResponse(r);
  };

  return (
    <>
      <Button variant={variant} size={size} iconBefore="share" ariaLabel="Share" onClick={open}>
        {label}
      </Button>
      {response ? (
        <ShareSheet content={content} response={response} onClose={() => setResponse(null)} />
      ) : null}
    </>
  );
}
