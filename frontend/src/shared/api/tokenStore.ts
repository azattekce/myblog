// Access token yalnızca bellekte tutulur (XSS ile localStorage'dan çalınamaz).
// Refresh token HttpOnly + SameSite=Strict cookie'dedir; JavaScript erişemez.
let accessToken: string | null = null;
const listeners = new Set<(token: string | null) => void>();

export const tokenStore = {
  get: () => accessToken,
  set(token: string | null) {
    accessToken = token;
    listeners.forEach((l) => l(token));
  },
  subscribe(listener: (token: string | null) => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
