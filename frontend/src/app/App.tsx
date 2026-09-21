import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/shared/auth/AuthContext';
import { RequireAdmin } from '@/shared/auth/RequireAdmin';
import { Layout } from '@/shared/components/Layout';
import { Loader } from '@/shared/components/Loader';
import { HomePage } from '@/features/posts/pages/HomePage';
import { PostPage } from '@/features/posts/pages/PostPage';
import { LoginPage } from '@/features/auth/LoginPage';
import { AboutPage } from '@/pages/AboutPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

// Yönetim paneli yalnızca yazar için; ziyaretçi paketine eklenmesin diye ayrı chunk olarak yüklenir
const AdminRoutes = lazy(() => import('@/features/admin/AdminRoutes'));

export function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="posts/:slug" element={<PostPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route
              path="admin/*"
              element={
                <RequireAdmin>
                  <Suspense fallback={<Loader />}>
                    <AdminRoutes />
                  </Suspense>
                </RequireAdmin>
              }
            />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
