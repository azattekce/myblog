import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { Loader } from '../components/Loader';

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { ready, isAdmin } = useAuth();
  const location = useLocation();
  if (!ready) return <Loader />;
  if (!isAdmin) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}
