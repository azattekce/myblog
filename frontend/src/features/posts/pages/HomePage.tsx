import { useEffect, useState, type FormEvent } from 'react';
import { Col, Container, Form, Row } from 'react-bootstrap';
import { Link, useSearchParams } from 'react-router-dom';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { Pager } from '@/shared/components/Pager';
import { useApi } from '@/shared/utils/useApi';
import { postsApi } from '../api';
import { PostLogItem } from '../components/PostLogItem';
import { Sidebar } from '../components/Sidebar';

export function HomePage() {
  const [params, setParams] = useSearchParams();
  const page = Number(params.get('page') ?? 1) || 1;
  const tag = params.get('tag');
  const category = params.get('category');
  const q = params.get('q');
  const [search, setSearch] = useState(q ?? '');

  useEffect(() => setSearch(q ?? ''), [q]);

  const { data, error, loading, reload } = useApi(
    () => postsApi.list({ page, size: 10, tag, category, q }),
    [page, tag, category, q],
  );

  const update = (next: Record<string, string | null>) => {
    const p = new URLSearchParams(params);
    Object.entries(next).forEach(([k, v]) => (v ? p.set(k, v) : p.delete(k)));
    setParams(p);
    window.scrollTo({ top: 0 });
  };

  const onSearch = (e: FormEvent) => {
    e.preventDefault();
    update({ q: search.trim() || null, page: null });
  };

  const filtered = Boolean(tag || category || q);

  return (
    <Container className="site-container">
      <header className="hero">
        <h1 className="hero-title">commit/log</h1>
        <p className="hero-lede">
          Yazılım mimarisi, backend sistemleri ve üretimde öğrendiklerim üzerine kısa ve uzun notlar.
        </p>
      </header>

      <Row className="g-5">
        <Col lg={8}>
          <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
            <Form onSubmit={onSearch} className="search-form" role="search">
              <Form.Control
                type="search"
                value={search}
                placeholder="Yazılarda ara"
                aria-label="Yazılarda ara"
                onChange={(e) => setSearch(e.target.value)}
              />
            </Form>
            {filtered && (
              <div className="d-flex align-items-center gap-2 small">
                <span className="text-body-secondary">
                  {tag && <>#{tag} </>}
                  {category && <>{category} </>}
                  {q && <>“{q}” </>}
                  filtresi
                </span>
                <Link to="/" className="clear-filter">
                  Temizle
                </Link>
              </div>
            )}
          </div>

          {loading && <Loader />}
          {error && <ErrorAlert message={error} onRetry={reload} />}
          {data && data.items.length === 0 && (
            <div className="empty-state">
              {filtered ? (
                <p>
                  Bu filtreyle eşleşen yazı yok. <Link to="/">Tüm yazıları göster</Link>
                </p>
              ) : (
                <p>İlk yazı henüz yayınlanmadı. Yönetim panelinden yeni bir yazı oluşturabilirsiniz.</p>
              )}
            </div>
          )}
          {data && data.items.length > 0 && (
            <>
              <ol className="commit-log">
                {data.items.map((p) => (
                  <PostLogItem key={p.id} post={p} />
                ))}
              </ol>
              <Pager page={data.page} pages={data.pages} onChange={(p) => update({ page: String(p) })} />
            </>
          )}
        </Col>
        <Col lg={4}>
          <Sidebar activeTag={tag} activeCategory={category} />
        </Col>
      </Row>
    </Container>
  );
}
