import { cx } from "../../utils";
import "./QRCode.css";

export interface QRCodeProps {
  /** module grid — true = dark. Produced by the backend in production. */
  matrix: boolean[][];
  label?: string;
  className?: string;
}

/** Pure renderer of a QR module grid, themed ink-on-paper for scannability. */
export function QRCode({ matrix, label = "QR code", className }: QRCodeProps) {
  const n = matrix.length || 1;
  return (
    <svg
      className={cx("ds-qr", className)}
      viewBox={`0 0 ${n} ${n}`}
      role="img"
      aria-label={label}
      shapeRendering="crispEdges"
    >
      <rect x="0" y="0" width={n} height={n} className="ds-qr__bg" />
      {matrix.map((row, r) =>
        row.map((on, c) =>
          on ? <rect key={`${r}-${c}`} x={c} y={r} width="1" height="1" className="ds-qr__mod" /> : null,
        ),
      )}
    </svg>
  );
}
