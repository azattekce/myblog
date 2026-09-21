import { Col, Row } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { useApi } from '@/shared/utils/useApi';
import { useAuth } from '@/shared/auth/AuthContext';
import { postsApi } from '@/features/posts/api';
import { commentsApi } from '@/features/comments/api';

export function DashboardPage() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useApi(
    () => Promise.all([postsApi.admin.stats(), commentsApi.admin.counts()]),
    [],
  );

  if (loading) return <Loader />;
  if (error || !data) return <ErrorAlert message={error ?? 'Veri alınamadı'} onRetry={reload} />;
  const [stats, counts] = data;

  const figures = [
    { label: 'Yayında', value: stats.published, to: '/admin/posts?status=published' },
    { label: 'Taslak', value: stats.drafts, to: '/admin/posts?status=draft' },
    { label: 'Onay bekleyen yorum', value: counts.pending, to: '/admin/comments', highlight: counts.pending > 0 },
    { label: 'Onaylı yorum', value: counts.approved, to: '/admin/comments?status=approved' },
  ];

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4">
        <div>
          <h1 className="admin-title">Merhaba, {user?.display_name}</h1>
          <p className="text-body-secondary mb-0">Toplam {stats.total} yazı var.</p>
        </div>
        <Link to="/admin/posts/new" className="btn btn-primary">
          <i className="bi bi-plus-lg me-1" /> Yeni yazı
        </Link>
      </div>
      <Row xs={2} md={4} className="g-3">
        {figures.map((f) => (
          <Col key={f.label}>
            <Link to={f.to} className={`figure-tile${f.highlight ? ' is-alert' : ''}`}>
              <span className="figure-value">{f.value}</span>
              <span className="figure-label">{f.label}</span>
            </Link>
          </Col>
        ))}
      </Row>
    </>
  );
}
