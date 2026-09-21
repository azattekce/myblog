import { useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Row } from 'react-bootstrap';
import { errorMessage } from '@/shared/api/httpClient';
import { formatDate } from '@/shared/utils/format';
import { useApi } from '@/shared/utils/useApi';
import { commentsApi } from './api';

export function CommentSection({ postId }: { postId: string }) {
  const { data: comments } = useApi(() => commentsApi.forPost(postId), [postId]);
  const [form, setForm] = useState({ author_name: '', author_email: '', content: '', website: '' });
  const [status, setStatus] = useState<{ kind: 'success' | 'danger'; text: string } | null>(null);
  const [sending, setSending] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setSending(true);
    setStatus(null);
    try {
      const res = await commentsApi.submit({
        post_id: postId,
        author_name: form.author_name,
        content: form.content,
        author_email: form.author_email || undefined,
        website: form.website || undefined,
      });
      setStatus({ kind: 'success', text: res.message });
      setForm({ author_name: '', author_email: '', content: '', website: '' });
    } catch (err) {
      setStatus({ kind: 'danger', text: errorMessage(err) });
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="comments" aria-labelledby="comments-title">
      <h2 id="comments-title" className="section-title">
        Yorumlar {comments && comments.length > 0 && <span className="text-body-secondary">({comments.length})</span>}
      </h2>

      {comments && comments.length === 0 && (
        <p className="text-body-secondary">Henüz yorum yok. Düşüncelerinizi aşağıdan paylaşabilirsiniz.</p>
      )}
      <ul className="list-unstyled comment-list">
        {comments?.map((c) => (
          <li key={c.id} className="comment">
            <div className="comment-head">
              <strong>{c.author_name}</strong>
              <time dateTime={c.created_at}>{formatDate(c.created_at, true)}</time>
            </div>
            <p className="comment-body">{c.content}</p>
          </li>
        ))}
      </ul>

      <Form onSubmit={submit} className="comment-form" noValidate={false}>
        <h3 className="h6 mb-3">Yorum yaz</h3>
        {status && <Alert variant={status.kind}>{status.text}</Alert>}
        <Row className="g-3">
          <Col md={6}>
            <Form.Group controlId="c-name">
              <Form.Label>Adınız</Form.Label>
              <Form.Control
                required
                minLength={2}
                maxLength={60}
                value={form.author_name}
                onChange={(e) => setForm({ ...form, author_name: e.target.value })}
              />
            </Form.Group>
          </Col>
          <Col md={6}>
            <Form.Group controlId="c-email">
              <Form.Label>E-posta (isteğe bağlı, yayınlanmaz)</Form.Label>
              <Form.Control
                type="email"
                maxLength={254}
                value={form.author_email}
                onChange={(e) => setForm({ ...form, author_email: e.target.value })}
              />
            </Form.Group>
          </Col>
          <Col xs={12} className="hp-field" aria-hidden="true">
            <Form.Control
              tabIndex={-1}
              autoComplete="off"
              name="website"
              value={form.website}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
            />
          </Col>
          <Col xs={12}>
            <Form.Group controlId="c-content">
              <Form.Label>Yorumunuz</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                required
                minLength={3}
                maxLength={2000}
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
              />
              <Form.Text>Yorumlar onaylandıktan sonra yayınlanır.</Form.Text>
            </Form.Group>
          </Col>
        </Row>
        <Button type="submit" className="mt-3" disabled={sending}>
          {sending ? 'Gönderiliyor…' : 'Yorumu gönder'}
        </Button>
      </Form>
    </section>
  );
}
