import { Link } from 'react-router-dom';
import { useApi } from '@/shared/utils/useApi';
import { postsApi } from '../api';

export function Sidebar({ activeTag, activeCategory }: { activeTag?: string | null; activeCategory?: string | null }) {
  const categories = useApi(() => postsApi.categories(), []);
  const tags = useApi(() => postsApi.tags(), []);

  return (
    <aside className="sidebar" aria-label="Kategoriler ve etiketler">
      <section className="mb-4">
        <h2 className="sidebar-heading">Kategoriler</h2>
        {categories.data && categories.data.length > 0 ? (
          <ul className="list-unstyled mb-0">
            {categories.data.map((c) => (
              <li key={c.id}>
                <Link
                  to={activeCategory === c.slug ? '/' : `/?category=${c.slug}`}
                  className={`sidebar-link ${activeCategory === c.slug ? 'active' : ''}`}
                >
                  <span>{c.name}</span>
                  <span className="sidebar-count">{c.post_count}</span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-body-secondary small mb-0">Henüz kategori yok.</p>
        )}
      </section>
      <section>
        <h2 className="sidebar-heading">Etiketler</h2>
        <div className="d-flex flex-wrap gap-2">
          {tags.data?.map((t) => (
            <Link
              key={t.tag}
              to={activeTag === t.tag ? '/' : `/?tag=${t.tag}`}
              className={`tag-chip ${activeTag === t.tag ? 'active' : ''}`}
            >
              #{t.tag} <span className="opacity-75">{t.count}</span>
            </Link>
          ))}
          {tags.data?.length === 0 && <p className="text-body-secondary small mb-0">Etiketler yazılarla birlikte gelir.</p>}
        </div>
      </section>
    </aside>
  );
}
