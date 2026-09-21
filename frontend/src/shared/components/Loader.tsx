import { Spinner } from 'react-bootstrap';

export function Loader({ label = 'Yükleniyor' }: { label?: string }) {
  return (
    <div className="d-flex align-items-center gap-2 py-5 text-body-secondary" role="status">
      <Spinner animation="border" size="sm" />
      <span>{label}…</span>
    </div>
  );
}
