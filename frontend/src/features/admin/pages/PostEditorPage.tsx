import { useEffect, useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Nav, Row } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { errorMessage } from '@/shared/api/httpClient';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { MarkdownView } from '@/shared/components/MarkdownView';
import { useApi } from '@/shared/utils/useApi';
import { postsApi } from '@/features/posts/api';
import type { PostWrite } from '@/features/posts/types';

const EMPTY: PostWrite = { title: '', summary: '', content: '', slug: '', category_id: '', tags: [], cover_image_url: '' };

export function parseTags(raw: string): string[] {
  return Array.from(
    new Set(
      raw
        .split(',')
        .map((t) => t.trim().toLowerCase())
        .filter(Boolean),
    ),
  ).slice(0, 10);
}

export function PostEditorPage() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const [form, setForm] = useState<PostWrite>(EMPTY);
  const [tagText, setTagText] = useState('');
  const [status, setStatus] = useState<'draft' | 'published'>('draft');
  const [tab, setTab] = useState<'write' | 'preview'>('write');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const categories = useApi(() => postsApi.categories(), []);
  const existing = useApi(() => (id ? postsApi.admin.get(id) : Promise.resolve(null)), [id]);

  useEffect(() => {
    const p = existing.data;
    if (!p) return;
    setForm({
      title: p.title,
      summary: p.summary,
      content: p.content,
      slug: p.slug,
      category_id: p.category?.id ?? '',
      tags: p.tags,
      cover_image_url: p.cover_image_url ?? '',
    });
    setTagText(p.tags.join(', '));
    setStatus(p.status);
  }, [existing.data]);

  const set = <K extends keyof PostWrite>(key: K, value: PostWrite[K]) => {
    setSaved(false);
    setForm((f) => ({ ...f, [key]: value }));
  };

  const save = async (publish: boolean) => {
    setBusy(true);
    setError(null);
    const body: PostWrite = {
      ...form,
      slug: form.slug?.trim() || null,
      category_id: form.category_id || null,
      cover_image_url: form.cover_image_url?.trim() || null,
      tags: parseTags(tagText),
    };
    try {
      if (isNew) {
        const res = await postsApi.admin.create({ ...body, publish });
        navigate(`/admin/posts/${res.id}`, { replace: true });
      } else {
        await postsApi.admin.update(id, body);
        if (publish && status === 'draft') await postsApi.admin.publish(id);
        await existing.reload();
      }
      setSaved(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void save(false);
  };

  if (!isNew && existing.loading) return <Loader />;
  if (!isNew && existing.error) return <ErrorAlert message={existing.error} onRetry={existing.reload} />;

  return (
    <Form onSubmit={onSubmit} className="editor">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
        <h1 className="admin-title mb-0">{isNew ? 'Yeni yazı' : 'Yazıyı düzenle'}</h1>
        <div className="d-flex gap-2">
          <Button type="submit" variant="outline-secondary" disabled={busy}>
            {status === 'published' ? 'Kaydet' : 'Taslak olarak kaydet'}
          </Button>
          {status === 'draft' && (
            <Button variant="primary" disabled={busy} onClick={() => save(true)}>
              Kaydet ve yayınla
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {saved && !error && <Alert variant="success">Kaydedildi.</Alert>}

      <Row className="g-4">
        <Col lg={8}>
          <Form.Group className="mb-3" controlId="title">
            <Form.Label>Başlık</Form.Label>
            <Form.Control
              value={form.title}
              onChange={(e) => set('title', e.target.value)}
              required
              minLength={3}
              maxLength={200}
              size="lg"
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="summary">
            <Form.Label>Özet</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={form.summary}
              maxLength={500}
              onChange={(e) => set('summary', e.target.value)}
            />
          </Form.Group>

          <Nav variant="tabs" activeKey={tab} onSelect={(k) => setTab((k as 'write' | 'preview') ?? 'write')}>
            <Nav.Item>
              <Nav.Link eventKey="write">Yaz</Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="preview">Önizleme</Nav.Link>
            </Nav.Item>
          </Nav>
          {tab === 'write' ? (
            <Form.Control
              as="textarea"
              aria-label="İçerik (Markdown)"
              className="editor-body"
              value={form.content}
              onChange={(e) => set('content', e.target.value)}
              required
              minLength={10}
              placeholder="Markdown ile yaz. Kod blokları için ```python gibi dil belirtebilirsin."
            />
          ) : (
            <div className="editor-preview">
              {form.content ? <MarkdownView source={form.content} /> : <p className="text-body-secondary">Boş.</p>}
            </div>
          )}
        </Col>

        <Col lg={4}>
          <div className="editor-side">
            <Form.Group className="mb-3" controlId="slug">
              <Form.Label>Adres (slug)</Form.Label>
              <Form.Control
                value={form.slug ?? ''}
                onChange={(e) => set('slug', e.target.value)}
                placeholder="Boş bırakılırsa başlıktan üretilir"
                className="font-mono"
              />
            </Form.Group>
            <Form.Group className="mb-3" controlId="category">
              <Form.Label>Kategori</Form.Label>
              <Form.Select value={form.category_id ?? ''} onChange={(e) => set('category_id', e.target.value)}>
                <option value="">Kategori yok</option>
                {categories.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3" controlId="tags">
              <Form.Label>Etiketler</Form.Label>
              <Form.Control
                value={tagText}
                onChange={(e) => {
                  setSaved(false);
                  setTagText(e.target.value);
                }}
                placeholder="python, fastapi, docker"
              />
              <Form.Text>Virgülle ayır, en fazla 10.</Form.Text>
            </Form.Group>
            <Form.Group className="mb-3" controlId="cover">
              <Form.Label>Kapak görseli URL</Form.Label>
              <Form.Control
                type="url"
                value={form.cover_image_url ?? ''}
                onChange={(e) => set('cover_image_url', e.target.value)}
                placeholder="https://…"
              />
            </Form.Group>
            {!isNew && (
              <p className="small text-body-secondary mb-0">
                Durum: <strong>{status === 'published' ? 'Yayında' : 'Taslak'}</strong>
              </p>
            )}
          </div>
        </Col>
      </Row>
    </Form>
  );
}
