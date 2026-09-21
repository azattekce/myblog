import { http } from '@/shared/api/httpClient';
import type { Paged } from '@/shared/api/types';

export interface PublicComment {
  id: string;
  author_name: string;
  content: string;
  created_at: string;
}

export interface AdminComment extends PublicComment {
  post_id: string;
  post_title: string | null;
  post_slug: string | null;
  author_email: string | null;
  status: 'pending' | 'approved' | 'rejected';
}

export const commentsApi = {
  forPost: (postId: string) => http.get<PublicComment[]>(`/comments/post/${postId}`).then((r) => r.data),
  submit: (body: { post_id: string; author_name: string; author_email?: string; content: string; website?: string }) =>
    http.post<{ id: string; message: string }>('/comments', body).then((r) => r.data),
  admin: {
    list: (status: string | null, page: number) =>
      http
        .get<Paged<AdminComment>>('/comments/admin', { params: { ...(status ? { status } : {}), page } })
        .then((r) => r.data),
    counts: () => http.get<Record<'pending' | 'approved' | 'rejected', number>>('/comments/admin/counts').then((r) => r.data),
    approve: (id: string) => http.post(`/comments/admin/${id}/approve`),
    reject: (id: string) => http.post(`/comments/admin/${id}/reject`),
    remove: (id: string) => http.delete(`/comments/admin/${id}`),
  },
};
