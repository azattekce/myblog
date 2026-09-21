import { Link } from 'react-router-dom';
import { formatDate, shortHash } from '@/shared/utils/format';
import type { PostSummary } from '../types';

export function PostLogItem({ post }: { post: PostSummary }) {
  return (
    <li className="log-entry">
      <div className="log-meta">
        <code className="log-hash" title="Yazı kimliği">
          {shortHash(post.id)}
        </code>
        <time dateTime={post.published_at ?? undefined}>{formatDate(post.published_at, true)}</time>
      </div>
      <h2 className="log-title">
        <Link to={`/posts/${post.slug}`} className="stretched-link-lite">
          {post.title}
        </Link>
      </h2>
      {post.summary && <p className="log-summary">{post.summary}</p>}
      <div className="log-foot">
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
        <span className="log-stat">{post.reading_time} dk okuma</span>
        {post.comment_count > 0 && <span className="log-stat">{post.comment_count} yorum</span>}
      </div>
    </li>
  );
}
