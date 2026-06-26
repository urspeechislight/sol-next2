import { cx } from "../../utils";
import type { ShareFormat } from "../../types";
import { Logo } from "./Logo";
import { QRCode } from "./QRCode";
import "./ShareCard.css";

export interface ShareCardProps {
  kicker: string;
  arabic: string;
  latin: string;
  source: string;
  format?: ShareFormat;
  shortUrl?: string;
  qr?: boolean[][];
}

/** The shareable card. Token-driven so it renders identically in the in-app
    preview and on the server (same tokens + fonts). One source of truth. */
export function ShareCard({ kicker, arabic, latin, source, format = "square", shortUrl, qr }: ShareCardProps) {
  return (
    <div className={cx("ds-sharecard", `ds-sharecard--${format}`)}>
      <div className="ds-sharecard__head">
        <Logo size="sm" />
        <span className="ds-sharecard__kicker">{kicker}</span>
      </div>
      <div className="ds-sharecard__body">
        <p className="ds-sharecard__ar" dir="rtl">{arabic}</p>
        <p className="ds-sharecard__en">{latin}</p>
      </div>
      <div className="ds-sharecard__foot">
        <div className="ds-sharecard__src">
          <span className="ds-sharecard__source" dir="rtl">{source}</span>
          {shortUrl ? <span className="ds-sharecard__url">{shortUrl}</span> : null}
        </div>
        {qr ? <QRCode matrix={qr} /> : null}
      </div>
    </div>
  );
}
