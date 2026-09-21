import { http } from '@/shared/api/httpClient';
import type { Paged } from '@/shared/api/types';
import type { Category, PostDetail, PostStats, PostSummary, PostWrite, TagCount } from './types';

export interface PostFilter {
  page?: number;
  size?: number;
  tag?: string | null;
  category?: string | null;
  q?: string | null;
}

const clean = (o: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(o).filter(([, v]) => v !== null && v !== undefined && v !== ''));

export const postsApi = {
  list: (f: PostFilter) => http.get<Paged<PostSummary>>('/posts', { params: clean({ ...f }) }).then((r) => r.data),
  bySlug: (slug: string) => http.get<PostDetail>(`/posts/slug/${encodeURIComponent(slug)}`).then((r) => r.data),
  tags: () => http.get<TagCount[]>('/posts/tags').then((r) => r.data),
  categories: () => http.get<Category[]>('/posts/categories').then((r) => r.data),

  admin: {
    stats: () => http.get<PostStats>('/posts/admin/stats').then((r) => r.data),
    list: (p: { page: number; status?: string | null; q?: string | null }) =>
      http.get<Paged<PostSummary>>('/posts/admin/posts', { params: clean({ ...p, size: 20 }) }).then((r) => r.data),
    get: (id: string) => http.get<PostDetail>(`/posts/admin/posts/${id}`).then((r) => r.data),
    create: (body: PostWrite) => http.post<{ id: string }>('/posts/admin/posts', body).then((r) => r.data),
    update: (id: string, body: PostWrite) => http.put(`/posts/admin/posts/${id}`, body),
    publish: (id: string) => http.post(`/posts/admin/posts/${id}/publish`),
    unpublish: (id: string) => http.post(`/posts/admin/posts/${id}/unpublish`),
    remove: (id: string) => http.delete(`/posts/admin/posts/${id}`),
    createCategory: (name: string, description: string, imageUrl?: string | null) =>
      http
        .post<{ id: string }>('/posts/admin/categories', { name, description, image_url: imageUrl || null })
        .then((r) => r.data),
    removeCategory: (id: string) => http.delete(`/posts/admin/categories/${id}`),
  },
};
