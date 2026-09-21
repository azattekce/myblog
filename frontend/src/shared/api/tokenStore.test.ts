import { describe, expect, it, vi } from 'vitest';
import { tokenStore } from './tokenStore';

describe('tokenStore', () => {
  it('token bellekte tutulur ve dinleyicilere bildirilir', () => {
    const listener = vi.fn();
    const off = tokenStore.subscribe(listener);
    tokenStore.set('abc');
    expect(tokenStore.get()).toBe('abc');
    expect(listener).toHaveBeenCalledWith('abc');
    off();
    tokenStore.set(null);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(window.localStorage.length).toBe(0); // XSS'e karşı kalıcı depolama kullanılmaz
  });
});
