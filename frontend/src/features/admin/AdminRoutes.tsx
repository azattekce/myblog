import { Container, Nav } from 'react-bootstrap';
import { NavLink, Route, Routes } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { PostListPage } from './pages/PostListPage';
import { PostEditorPage } from './pages/PostEditorPage';
import { CommentModerationPage } from './pages/CommentModerationPage';
import { CategoriesPage } from './pages/CategoriesPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

export default function AdminRoutes() {
  return (
    <Container className="site-container admin">
      <Nav variant="underline" className="admin-nav mb-4">
        <Nav.Link as={NavLink} to="/admin" end>
          Özet
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/posts">
          Yazılar
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/comments">
          Yorumlar
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/categories">
          Kategoriler
        </Nav.Link>
      </Nav>
      <Routes>
        <Route index element={<DashboardPage />} />
        <Route path="posts" element={<PostListPage />} />
        <Route path="posts/new" element={<PostEditorPage />} />
        <Route path="posts/:id" element={<PostEditorPage />} />
        <Route path="comments" element={<CommentModerationPage />} />
        <Route path="categories" element={<CategoriesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Container>
  );
}
