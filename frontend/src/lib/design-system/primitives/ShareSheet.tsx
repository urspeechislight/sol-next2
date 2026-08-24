import { useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import type { ShareContent, ShareResponse } from '../../types';
import { SHARE_FORMATS, SHARE_PLATFORMS, type ShareFormat } from '../../constants';
import type { IconName } from '../internal/icons';
import { Button } from './Button';
import { Segmented } from './Segmented';
import { Icon } from './Icon';
import { ShareCard } from './ShareCard';
import { FOCUSABLE, useEscape, useFocusScope } from './useDismiss';
import './ShareSheet.css';

export interface ShareSheetProps {
  content: ShareContent;
  response: ShareResponse;
  onClose: () => void;
}

/** Share popover: live card preview, format switch, platform row, copy/download/QR.
    Presentational: the feature supplies content plus the resolved share response. */
export function ShareSheet({ content, response, onClose }: ShareSheetProps) {
  useEscape(onClose);
  const sheet = useRef<HTMLDivElement>(null);
  useFocusScope(sheet, true);

  /** Modal Tab discipline: focus cycles inside the sheet, never past it. */
  const trapTab = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'Tab' || !sheet.current) return;
    const items = [...sheet.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
    const first = items[0];
    const last = items[items.length - 1];
    if (!first || !last) return;
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
  const [format, setFormat] = useState<ShareFormat>('square');
  const [showQr, setShowQr] = useState(response.qr.length > 0);
  const [copied, setCopied] = useState(false);

  const link = `https://${response.short_url}`;
  const copy = async () => {
    if (!navigator.clipboard) return;
    await navigator.clipboard.writeText(link);
    setCopied(true);
  };
  const openIntent = (id: string) => {
    const url = encodeURIComponent(link);
    const text = encodeURIComponent(response.caption);
    if (id === 'x')
      window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank', 'noopener');
    else if (id === 'facebook')
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'noopener');
    else if (response.image_url) window.open(response.image_url, '_blank', 'noopener');
  };

  return (
    <div className="ds-sheet-scrim" onClick={onClose}>
      <div
        ref={sheet}
        className="ds-sheet"
        role="dialog"
        aria-label="Share"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={trapTab}
      >
        <div className="ds-sheet__head">
          <span className="ds-sheet__title">Share</span>
          <Button
            variant="ghost"
            size="sm"
            iconBefore="close"
            ariaLabel="Close"
            onClick={onClose}
          />
        </div>
        <div className="ds-sheet__preview">
          <ShareCard
            kicker={content.kicker}
            arabic={content.arabic}
            latin={content.latin}
            source={content.source}
            format={format}
            shortUrl={response.short_url}
            qr={showQr ? response.qr : undefined}
          />
        </div>
        <Segmented
          label="Card format"
          value={format}
          options={SHARE_FORMATS.map((f) => ({ value: f.value, label: f.label }))}
          onChange={(v) => setFormat(v as ShareFormat)}
        />
        <div className="ds-sheet__platforms">
          {SHARE_PLATFORMS.map((p) => (
            <button
              key={p.id}
              type="button"
              className="ds-sheet__platform"
              aria-label={`Share to ${p.label}`}
              onClick={() => openIntent(p.id)}
            >
              <Icon name={p.icon as IconName} size="md" />
              <span>{p.label}</span>
            </button>
          ))}
        </div>
        <div className="ds-sheet__actions">
          <Button
            variant="secondary"
            size="sm"
            iconBefore={copied ? 'check' : 'copy'}
            onClick={copy}
          >
            {copied ? 'Copied' : response.short_url}
          </Button>
          {response.image_url ? (
            <Button
              variant="secondary"
              size="sm"
              iconBefore="download"
              onClick={() => openIntent('download')}
            >
              Image
            </Button>
          ) : null}
          {response.qr.length > 0 ? (
            <Button
              variant={showQr ? 'secondary' : 'ghost'}
              size="sm"
              iconBefore="qr"
              ariaPressed={showQr}
              onClick={() => setShowQr((v) => !v)}
            >
              QR
            </Button>
          ) : null}
        </div>
        <p className="ds-sheet__note">
          Copy the link or share to X / Facebook. Instagram and TikTok have no web-post API.
        </p>
      </div>
    </div>
  );
}
