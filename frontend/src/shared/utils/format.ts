const dateFmt = new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
const shortFmt = new Intl.DateTimeFormat('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });

export function formatDate(iso: string | null | undefined, short = false): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return (short ? shortFmt : dateFmt).format(d);
}

/** Yazı kimliğinden git tarzı kısa hash üretir. */
export function shortHash(id: string): string {
  return id.replace(/-/g, '').slice(0, 7);
}

export function pluralize(count: number, word: string): string {
  return `${count} ${word}`;
}
