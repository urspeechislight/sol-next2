import { highlightSegments } from '../../highlight';
import './Highlight.css';

export interface HighlightProps {
  text: string;
  query: string;
}

/** Render ``text`` with every diacritic-insensitive occurrence of ``query``
    wrapped in a themed <mark>. The highlight color is the ``--color-mark-bg``
    design token (tokens.css); the mark is never styled inline. */
export function Highlight({ text, query }: HighlightProps) {
  const segments = highlightSegments(text, query);
  return (
    <>
      {segments.map((seg, i) =>
        seg.match ? (
          <mark key={i} className="ds-mark">
            {seg.text}
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </>
  );
}
