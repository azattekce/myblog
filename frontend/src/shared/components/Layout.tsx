import { Button, Container, Nav, Navbar } from 'react-bootstrap';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../utils/useTheme';

export function Layout() {
  const { user, isAdmin, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="d-flex flex-column min-vh-100">
      <a href="#main" className="visually-hidden-focusable skip-link">
        İçeriğe geç
      </a>
      <Navbar expand="md" className="site-nav" collapseOnSelect>
        <Container className="site-container">
          <Navbar.Brand as={Link} to="/" className="brand">
            <span className="brand-mark" aria-hidden="true" />
            commit/log
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="main-nav" />
          <Navbar.Collapse id="main-nav">
            <Nav className="ms-auto align-items-md-center gap-md-1">
              <Nav.Link as={NavLink} to="/" end eventKey="home">
                Yazılar
              </Nav.Link>
              <Nav.Link as={NavLink} to="/about" eventKey="about">
                Hakkımda
              </Nav.Link>
              {isAdmin && (
                <Nav.Link as={NavLink} to="/admin" eventKey="admin">
                  Yönetim
                </Nav.Link>
              )}
              {user && (
                <Nav.Link
                  as="button"
                  className="btn btn-link nav-link"
                  onClick={async () => {
                    await logout();
                    navigate('/');
                  }}
                >
                  Çıkış yap
                </Nav.Link>
              )}
              <Button
                variant="link"
                className="nav-link theme-toggle"
                onClick={toggle}
                aria-label={theme === 'light' ? 'Koyu temaya geç' : 'Açık temaya geç'}
              >
                <i className={`bi ${theme === 'light' ? 'bi-moon-stars' : 'bi-sun'}`} />
              </Button>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <main id="main" className="flex-grow-1 py-4 py-md-5">
        <Outlet />
      </main>

      <footer className="site-footer">
        <Container className="site-container d-flex flex-wrap justify-content-between gap-2">
          <span>© {new Date().getFullYear()} commit/log</span>
          {!user && (
            <Link to="/login" className="footer-link">
              Yazar girişi
            </Link>
          )}
        </Container>
      </footer>
    </div>
  );
}
