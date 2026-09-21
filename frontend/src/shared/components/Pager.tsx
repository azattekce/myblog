import { Pagination } from 'react-bootstrap';

export function Pager({ page, pages, onChange }: { page: number; pages: number; onChange: (p: number) => void }) {
  if (pages <= 1) return null;
  const items = [];
  for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++) {
    items.push(
      <Pagination.Item key={p} active={p === page} onClick={() => onChange(p)}>
        {p}
      </Pagination.Item>,
    );
  }
  return (
    <Pagination className="mt-4" aria-label="Sayfalar">
      <Pagination.Prev disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Önceki sayfa" />
      {items}
      <Pagination.Next disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Sonraki sayfa" />
    </Pagination>
  );
}
