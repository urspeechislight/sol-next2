// paragraphs.ts: split raw corpus page text into display blocks. The digitized
// pages carry a newline at every PRINT line boundary, so rendering them
// pre-wrap hard-breaks sentences wherever the screen column is narrower than
// the print measure (glaring in the bilingual half-column). A break is kept
// as a block boundary only when it looks structural: a blank line (a real
// paragraph break in the source), a short line (basmala, heading, poetry
// hemistich), or a line ending in terminal punctuation. Every other newline
// stays inside the block's text and collapses visually under
// white-space: normal, so the rendered DOM text (and anything copied from it)
// remains byte-identical to the corpus. Each block carries its start offset
// into the original string so offset-anchored sidecars (Quran citations)
// rebase exactly. Pure.

const SHORT_LINE = 45;
const TERMINAL_END = /[.!؟:»\]…]\s*$/;

export interface FlowBlock {
  /** Offset of the block's first character in the original page text. */
  start: number;
  /** Exact slice of the original text (internal newlines preserved). */
  text: string;
}

/** Split page text into display blocks at structural line breaks only. */
export function flowBlocks(text: string): FlowBlock[] {
  if (!text) return [];
  const blocks: FlowBlock[] = [];
  let blockStart = -1;
  let blockEnd = -1;
  const close = () => {
    if (blockStart >= 0) {
      blocks.push({ start: blockStart, text: text.slice(blockStart, blockEnd) });
      blockStart = -1;
    }
  };
  let offset = 0;
  for (const line of text.split('\n')) {
    const lineStart = offset;
    const lineEnd = offset + line.length;
    offset = lineEnd + 1;
    if (line.trim() === '') {
      close();
      continue;
    }
    if (blockStart < 0) blockStart = lineStart;
    blockEnd = lineEnd;
    const structural = line.trim().length < SHORT_LINE || TERMINAL_END.test(line.trimEnd());
    if (structural) close();
  }
  close();
  return blocks;
}
