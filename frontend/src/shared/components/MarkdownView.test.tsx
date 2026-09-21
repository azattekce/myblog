import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MarkdownView } from './MarkdownView';

describe('MarkdownView', () => {
  it('ham HTML/script render etmez (XSS koruması)', () => {
    const { container } = render(<MarkdownView source={'# Başlık\n\n<script>alert(1)</script><img src=x onerror=alert(1)>'} />);
    expect(container.querySelector('h1')?.textContent).toBe('Başlık');
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
  });
});
