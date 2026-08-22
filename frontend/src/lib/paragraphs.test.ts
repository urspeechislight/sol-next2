// Tests for the display-block splitter: print-margin newlines flow, structural
// breaks (blank lines, short lines, terminal punctuation) become boundaries,
// and every block is an exact offset-anchored slice of the original text.
import { describe, expect, it } from 'vitest';

import { flowBlocks } from './paragraphs';

const LONG_A = 'الحمد لله الذي سمك سماء العلم ، وزينها ببروجها للناظرين ، وعلق عليها';
const LONG_B = 'قناديل الأنوار بشموس النبوة وأقمار الإمامة لمن أراد سلوك مسالك اليقين ،';
const LONG_C = 'وجعل نجومها رجوما لوساوس الشياطين ، وحفظها بثواقب شهبها عن شبهات المضلين .';

describe('flowBlocks', () => {
  it('should keep a print-margin break inside one block', () => {
    const blocks = flowBlocks(`${LONG_A}\n${LONG_B}`);
    expect(blocks.map((b) => b.text)).toEqual([`${LONG_A}\n${LONG_B}`]);
  });

  it('should close a block at a line ending in terminal punctuation', () => {
    const blocks = flowBlocks(`${LONG_A}\n${LONG_C}\n${LONG_B}`);
    expect(blocks.map((b) => b.text)).toEqual([`${LONG_A}\n${LONG_C}`, LONG_B]);
  });

  it('should keep a short standalone line as its own block', () => {
    const blocks = flowBlocks(`بسم الله الرحمن الرحيم\n${LONG_A}\n${LONG_B}`);
    expect(blocks[0]?.text).toBe('بسم الله الرحمن الرحيم');
    expect(blocks[1]?.text).toBe(`${LONG_A}\n${LONG_B}`);
  });

  it('should treat a blank line as a paragraph boundary', () => {
    const blocks = flowBlocks(`${LONG_A}\n\n${LONG_B}`);
    expect(blocks.map((b) => b.text)).toEqual([LONG_A, LONG_B]);
  });

  it('should keep consecutive short lines as separate blocks', () => {
    const blocks = flowBlocks('شطر أول قصير\nشطر ثان قصير');
    expect(blocks.map((b) => b.text)).toEqual(['شطر أول قصير', 'شطر ثان قصير']);
  });

  it('should return no blocks for empty text', () => {
    expect(flowBlocks('')).toEqual([]);
  });

  it('should anchor every block at its exact offset in the original text', () => {
    const text = `بسم الله الرحمن الرحيم\n${LONG_A}\n${LONG_C}\n\nشطر قصير`;
    for (const block of flowBlocks(text)) {
      expect(text.slice(block.start, block.start + block.text.length)).toBe(block.text);
    }
  });
});
