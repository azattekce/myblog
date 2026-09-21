import { describe, expect, it } from 'vitest';
import { formatDate, shortHash } from './format';

describe('format', () => {
  it('uuid\'den 7 karakterlik git tarzı hash üretir', () => {
    expect(shortHash('3f2a9c1e-44b0-4c1d-9e8a-000000000000')).toBe('3f2a9c1');
  });
  it('geçersiz tarihte tire döner', () => {
    expect(formatDate(null)).toBe('—');
    expect(formatDate('olmayan-tarih')).toBe('—');
  });
  it('Türkçe ay adı ile biçimler', () => {
    expect(formatDate('2026-03-05T10:00:00Z')).toMatch(/Mart 2026/);
  });
});
