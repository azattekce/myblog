import { useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Row, Table } from 'react-bootstrap';
import { errorMessage } from '@/shared/api/httpClient';
import { ErrorAlert } from '@/shared/components/ErrorAlert';
import { Loader } from '@/shared/components/Loader';
import { useApi } from '@/shared/utils/useApi';
import { postsApi } from '@/features/posts/api';
import { ConfirmButton } from '../components/ConfirmButton';

export function CategoriesPage() {
  const { data, error, loading, reload } = useApi(() => postsApi.categories(), []);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await postsApi.admin.createCategory(name.trim(), description.trim(), imageUrl.trim() || null);
      setName('');
      setDescription('');
      setImageUrl('');
      await reload();
    } catch (err) {
      setFormError(errorMessage(err));
    }
  };

  const remove = async (id: string) => {
    setFormError(null);
    try {
      await postsApi.admin.removeCategory(id);
      await reload();
    } catch (err) {
      setFormError(errorMessage(err));
    }
  };

  return (
    <Row className="g-4">
      <Col lg={7}>
        <h1 className="admin-title">Kategoriler</h1>
        {loading && <Loader />}
        {error && <ErrorAlert message={error} onRetry={reload} />}
        {data && data.length === 0 && <p className="empty-state">Henüz kategori yok.</p>}
        {data && data.length > 0 && (
          <Table className="admin-table align-middle">
            <thead>
              <tr>
                <th />
                <th>Ad</th>
                <th>Yazı</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.map((c) => (
                <tr key={c.id}>
                  <td style={{ width: 48 }}>
                    {c.image_url && (
                      <img
                        src={c.image_url}
                        alt={c.name}
                        width={36}
                        height={36}
                        className="rounded-circle"
                        style={{ objectFit: 'cover' }}
                      />
                    )}
                  </td>
                  <td>
                    <div className="fw-semibold">{c.name}</div>
                    {c.description && <div className="small text-body-secondary">{c.description}</div>}
                  </td>
                  <td>{c.post_count}</td>
                  <td className="text-end">
                    <ConfirmButton label="Sil" confirmLabel="Emin misin?" onConfirm={() => remove(c.id)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Col>
      <Col lg={5}>
        <Form onSubmit={submit} className="editor-side">
          <h2 className="h5 mb-3">Yeni kategori</h2>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Form.Group className="mb-3" controlId="cat-name">
            <Form.Label>Ad</Form.Label>
            <Form.Control value={name} onChange={(e) => setName(e.target.value)} required minLength={2} maxLength={60} />
          </Form.Group>
          <Form.Group className="mb-3" controlId="cat-desc">
            <Form.Label>Açıklama</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={description}
              maxLength={300}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="cat-image">
            <Form.Label>Profil resmi URL</Form.Label>
            <Form.Control
              type="url"
              value={imageUrl}
              placeholder="https://..."
              onChange={(e) => setImageUrl(e.target.value)}
            />
            {imageUrl && (
              <img
                src={imageUrl}
                alt="Önizleme"
                width={48}
                height={48}
                className="rounded-circle mt-2"
                style={{ objectFit: 'cover' }}
              />
            )}
          </Form.Group>
          <Button type="submit" variant="primary">
            Ekle
          </Button>
        </Form>
      </Col>
    </Row>
  );
}
