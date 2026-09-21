import { useState, type FormEvent } from 'react';
import { Alert, Button, Container, Form } from 'react-bootstrap';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { errorMessage } from '@/shared/api/httpClient';
import { useAuth } from '@/shared/auth/AuthContext';

export function LoginPage() {
  const { login, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? '/admin';
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (isAdmin) return <Navigate to={from} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Container className="site-container">
      <div className="auth-card">
        <h1 className="h3 mb-1">Yazar girişi</h1>
        <p className="text-body-secondary mb-4">Yazıları ve yorumları yönetmek için giriş yapın.</p>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form onSubmit={submit}>
          <Form.Group className="mb-3" controlId="username">
            <Form.Label>Kullanıcı adı</Form.Label>
            <Form.Control autoComplete="username" required value={username} onChange={(e) => setUsername(e.target.value)} />
          </Form.Group>
          <Form.Group className="mb-4" controlId="password">
            <Form.Label>Parola</Form.Label>
            <Form.Control
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Form.Group>
          <Button type="submit" className="w-100" disabled={busy}>
            {busy ? 'Giriş yapılıyor…' : 'Giriş yap'}
          </Button>
        </Form>
      </div>
    </Container>
  );
}
