import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { tokenStore } from './tokenStore';
import type { ProblemDetails } from './types';

export const CSRF_HEADER = { 'X-CSRF-Protection': '1' } as const;

export const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

http.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshing) {
    refreshing = axios
      .post<{ access_token: string }>('/api/identity/auth/refresh', null, {
        withCredentials: true,
        headers: CSRF_HEADER,
      })
      .then((res) => {
        tokenStore.set(res.data.access_token);
        return res.data.access_token;
      })
      .catch(() => {
        tokenStore.set(null);
        return null;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

http.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ProblemDetails>) => {
    const original = error.config as RetriableConfig | undefined;
    const isAuthCall = original?.url?.startsWith('/identity/auth/');
    if (error.response?.status === 401 && original && !original._retried && !isAuthCall && tokenStore.get()) {
      original._retried = true;
      const token = await refreshAccessToken();
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return http(original);
      }
    }
    return Promise.reject(error);
  },
);

export function errorMessage(err: unknown, fallback = 'Bir şeyler ters gitti. Lütfen tekrar deneyin.'): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as ProblemDetails | undefined;
    if (data?.errors?.length) return data.errors.map((e) => `${e.field}: ${e.message}`).join(' · ');
    if (data?.detail) return data.detail;
    if (!err.response) return 'Sunucuya ulaşılamıyor. Bağlantınızı kontrol edin.';
  }
  return fallback;
}
