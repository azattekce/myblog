import { describe, expect, it } from 'vitest';
import { parseTags } from './PostEditorPage';

describe('parseTags', () => {
  it('virgülle ayırır, küçültür, tekrarları ve boşları atar', () => {
    expect(parseTags(' Python, fastapi ,python,, Docker ')).toEqual(['python', 'fastapi', 'docker']);
  });
  it('en fazla 10 etiket döner', () => {
    expect(parseTags(Array.from({ length: 15 }, (_, i) => `t${i}`).join(','))).toHaveLength(10);
  });
});
