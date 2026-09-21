import { useEffect } from 'react';
import { Container } from 'react-bootstrap';
import { Link, useParams } from 'react-router-dom';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { MarkdownView } from '@/shared/components/MarkdownView';
import { formatDate, shortHash } from '@/shared/utils/format';
import { useApi } from '@/shared/utils/useApi';
import { CommentSection } from '@/features/comments/CommentSection';
import { postsApi } from '../api';

export function PostPage() {
  const { slug = '' } = useParams();
  const { data: post, error, loading, reload } = useApi(() => postsApi.bySlug(slug), [slug]);

  useEffect(() => {
    if (post) document.title = `${post.title} — commit/log`;
    return () => {
      document.title = 'commit/log — yazılım notları';
    };
  }, [post]);

  if (loading) return <Container className="site-container"><Loader /></Container>;
  if (error || !post)
    return (
      <Container className="site-container">
        <ErrorAlert message={error ?? 'Yazı bulunamadı'} onRetry={reload} />
        <Link to="/">Tüm yazılara dön</Link>
      </Container>
    );

  return (
    <Container className="site-container">
      <article className="article">
        <header className="article-header">
          <div className="log-meta mb-3">
            <code className="log-hash">{shortHash(post.id)}</code>
            <time dateTime={post.published_at ?? undefined}>{formatDate(post.published_at)}</time>
            <span>{post.reading_time} dk okuma</span>
            {typeof post.view_count === 'number' && post.view_count > 0 && <span>{post.view_count} görüntülenme</span>}
          </div>
          <h1 className="article-title">{post.title}</h1>
          {post.summary && <p className="article-lede">{post.summary}</p>}
          <div className="d-flex flex-wrap gap-2 mt-3">
            {post.category && (
              <Link to={`/?category=${post.category.slug}`} className="log-category">
                {post.category.name}
              </Link>
            )}
            {post.tags.map((t) => (
              <Link key={t} to={`/?tag=${t}`} className="tag-chip">
                #{t}
              </Link>
            ))}
          </div>
        </header>
        {post.cover_image_url && (
          <img src={post.cover_image_url} alt="" className="article-cover" loading="lazy" />
        )}
        <MarkdownView source={post.content} />
      </article>
      <CommentSection postId={post.id} />
    </Container>
  );
}
