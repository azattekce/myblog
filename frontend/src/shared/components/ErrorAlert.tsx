import { Alert, Button } from 'react-bootstrap';

export function ErrorAlert({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Alert variant="danger" className="d-flex justify-content-between align-items-center gap-3">
      <span>{message}</span>
      {onRetry && (
        <Button size="sm" variant="outline-danger" onClick={onRetry}>
          Tekrar dene
        </Button>
      )}
    </Alert>
  );
}
