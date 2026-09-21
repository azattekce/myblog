import { useState } from 'react';
import { Badge, Button, ButtonGroup } from 'react-bootstrap';
import { Link, useSearchParams } from 'react-router-dom';
import { errorMessage } from '@/shared/api/httpClient';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { Pager } from '@/shared/components/Pager';
import { useApi } from '@/shared/utils/useApi';
import { formatDate } from '@/shared/utils/format';
import { commentsApi } from '@/features/comments/api';
import { ConfirmButton } from '../components/ConfirmButton';

const TABS = [
  { key: 'pending', label: 'Bekleyen' },
  { key: 'approved', label: 'Onaylı' },
  { key: 'rejected', label: 'Reddedilen' },
] as const;

export function CommentModerationPage() {
  const [params, setParams] = useSearchParams();
  const status = params.get('status') ?? 'pending';
  const page = Number(params.get('page') ?? 1) || 1;
  const [actionError, setActionError] = useState<string | null>(null);
  const counts = useApi(() => commentsApi.admin.counts(), []);
  const { data, error, loading, reload } = useApi(() => commentsApi.admin.list(status, page), [status, page]);

  const run = async (fn: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await fn();
      await Promise.all([reload(), counts.reload()]);
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
        <h1 className="admin-title mb-0">Yorumlar</h1>
        <ButtonGroup size="sm" aria-label="Yorum durumu">
          {TABS.map((t) => (
            <Button
              key={t.key}
              variant={status === t.key ? 'secondary' : 'outline-secondary'}
              onClick={() => setParams({ status: t.key })}
            >
              {t.label}
              {counts.data && (
                <Badge bg="light" text="dark" className="ms-2">
                  {counts.data[t.key]}
                </Badge>
              )}
            </Button>
          ))}
        </ButtonGroup>
      </div>

      {actionError && <ErrorAlert message={actionError} />}
      {loading && <Loader />}
      {error && <ErrorAlert message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <p className="empty-state">Burada bekleyen bir şey yok.</p>}

      <ul className="comment-list moderation">
        {data?.items.map((c) => (
          <li key={c.id} className="comment">
            <div className="comment-head">
              <strong>{c.author_name}</strong>
              {c.author_email && <span className="text-body-secondary small">{c.author_email}</span>}
              <time className="small text-body-secondary">{formatDate(c.created_at, true)}</time>
            </div>
            <div className="small mb-2">
              {c.post_slug ? (
                <Link to={`/posts/${c.post_slug}`} target="_blank" rel="noreferrer">
                  {c.post_title ?? c.post_slug}
                </Link>
              ) : (
                <span className="text-body-secondary">Yazı bilgisi yok</span>
              )}
            </div>
            <p className="comment-body">{c.content}</p>
            <div className="d-flex gap-1">
              {c.status !== 'approved' && (
                <Button size="sm" variant="outline-success" onClick={() => run(() => commentsApi.admin.approve(c.id))}>
                  Onayla
                </Button>
              )}
              {c.status !== 'rejected' && (
                <Button size="sm" variant="outline-secondary" onClick={() => run(() => commentsApi.admin.reject(c.id))}>
                  Reddet
                </Button>
              )}
              <ConfirmButton label="Sil" confirmLabel="Kalıcı sil?" onConfirm={() => run(() => commentsApi.admin.remove(c.id))} />
            </div>
          </li>
        ))}
      </ul>
      {data && (
        <Pager page={data.page} pages={data.pages} onChange={(n) => setParams({ status, page: String(n) })} />
      )}
    </>
  );
}
