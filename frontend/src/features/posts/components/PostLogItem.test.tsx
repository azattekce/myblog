import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { PostLogItem } from './PostLogItem';
import type { PostSummary } from '../types';

const post: PostSummary = {
  id: 'abcdef12-0000-0000-0000-000000000000',
  title: 'Outbox pattern ile güvenilir event yayını',
  slug: 'outbox-pattern',
  summary: 'Transaction ve mesaj yayınını atomik yapmak.',
  status: 'published',
  author_name: 'Yazar',
  cover_image_url: null,
  reading_time: 6,
  comment_count: 2,
  tags: ['rabbitmq', 'ddd'],
  category: { id: 'c1', name: 'Mimari', slug: 'mimari' },
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  published_at: '2026-01-02T00:00:00Z',
};

describe('PostLogItem', () => {
  it('hash, başlık bağlantısı, etiketler ve istatistikleri gösterir', () => {
    render(
      <MemoryRouter>
        <ul>
          <PostLogItem post={post} />
        </ul>
      </MemoryRouter>,
    );
    expect(screen.getByText('abcdef1')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: post.title })).toHaveAttribute('href', '/posts/outbox-pattern');
    expect(screen.getByRole('link', { name: '#rabbitmq' })).toHaveAttribute('href', '/?tag=rabbitmq');
    expect(screen.getByText('6 dk okuma')).toBeInTheDocument();
    expect(screen.getByText('2 yorum')).toBeInTheDocument();
  });
});
