import { Container } from 'react-bootstrap';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <Container className="site-container">
      <div className="empty-state not-found">
        <code className="log-hash">fatal: 404</code>
        <h1 className="h3 mt-3">Bu sayfa hiç commit'lenmemiş</h1>
        <p className="text-body-secondary">Aradığın adres taşınmış, silinmiş ya da hiç var olmamış olabilir.</p>
        <Link to="/" className="btn btn-primary">
          Ana sayfaya dön
        </Link>
      </div>
    </Container>
  );
}
