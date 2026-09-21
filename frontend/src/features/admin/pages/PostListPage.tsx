import { useState } from 'react';
import { Badge, Button, ButtonGroup, Table } from 'react-bootstrap';
import { Link, useSearchParams } from 'react-router-dom';
import { errorMessage } from '@/shared/api/httpClient';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { Pager } from '@/shared/components/Pager';
import { useApi } from '@/shared/utils/useApi';
import { formatDate } from '@/shared/utils/format';
import { postsApi } from '@/features/posts/api';
import type { PostSummary } from '@/features/posts/types';
import { ConfirmButton } from '../components/ConfirmButton';

const FILTERS = [
  { key: null, label: 'Tümü' },
  { key: 'published', label: 'Yayında' },
  { key: 'draft', label: 'Taslak' },
] as const;

export function PostListPage() {
  const [params, setParams] = useSearchParams();
  const status = params.get('status');
  const page = Number(params.get('page') ?? 1) || 1;
  const [actionError, setActionError] = useState<string | null>(null);
  const { data, error, loading, reload } = useApi(() => postsApi.admin.list({ page, status }), [page, status]);

  const run = async (fn: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await fn();
      await reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  const setFilter = (next: Record<string, string | null>) => {
    const p = new URLSearchParams(params);
    Object.entries(next).forEach(([k, v]) => (v ? p.set(k, v) : p.delete(k)));
    setParams(p);
  };

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
        <h1 className="admin-title mb-0">Yazılar</h1>
        <div className="d-flex gap-2">
          <ButtonGroup size="sm" aria-label="Durum filtresi">
            {FILTERS.map((f) => (
              <Button
                key={f.label}
                variant={status === f.key ? 'secondary' : 'outline-secondary'}
                onClick={() => setFilter({ status: f.key, page: null })}
              >
                {f.label}
              </Button>
            ))}
          </ButtonGroup>
          <Link to="/admin/posts/new" className="btn btn-primary btn-sm">
            <i className="bi bi-plus-lg me-1" /> Yeni yazı
          </Link>
        </div>
      </div>

      {actionError && <ErrorAlert message={actionError} />}
      {loading && <Loader />}
      {error && <ErrorAlert message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <p className="empty-state">Bu filtrede yazı yok.</p>}
      {data && data.items.length > 0 && (
        <div className="table-responsive">
          <Table hover className="admin-table align-middle">
            <thead>
              <tr>
                <th>Başlık</th>
                <th>Durum</th>
                <th className="d-none d-md-table-cell">Güncellendi</th>
                <th className="text-end">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p: PostSummary) => (
                <tr key={p.id}>
                  <td>
                    <Link to={`/admin/posts/${p.id}`} className="fw-semibold">
                      {p.title}
                    </Link>
                    <div className="small text-body-secondary font-mono">/{p.slug}</div>
                  </td>
                  <td>
                    {p.status === 'published' ? (
                      <Badge bg="success-subtle" text="success-emphasis">
                        Yayında
                      </Badge>
                    ) : (
                      <Badge bg="secondary-subtle" text="secondary-emphasis">
                        Taslak
                      </Badge>
                    )}
                  </td>
                  <td className="d-none d-md-table-cell small">{formatDate(p.updated_at, true)}</td>
                  <td className="text-end text-nowrap">
                    {p.status === 'published' ? (
                      <>
                        <Link to={`/posts/${p.slug}`} className="btn btn-sm btn-link" target="_blank" rel="noreferrer">
                          Görüntüle
                        </Link>
                        <Button size="sm" variant="link" onClick={() => run(() => postsApi.admin.unpublish(p.id))}>
                          Yayından kaldır
                        </Button>
                      </>
                    ) : (
                      <Button size="sm" variant="link" onClick={() => run(() => postsApi.admin.publish(p.id))}>
                        Yayınla
                      </Button>
                    )}
                    <ConfirmButton
                      label="Sil"
                      confirmLabel="Emin misin?"
                      onConfirm={() => run(() => postsApi.admin.remove(p.id))}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
      {data && <Pager page={data.page} pages={data.pages} onChange={(n) => setFilter({ page: String(n) })} />}
    </>
  );
}
