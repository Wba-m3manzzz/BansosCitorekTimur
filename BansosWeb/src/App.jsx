import { Navigate, Route, Routes, useLocation, Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Menu } from 'lucide-react'
import Sidebar from './components/Sidebar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import DataWarga from './pages/DataWarga'
import ProsesKlasifikasi from './pages/ProsesKlasifikasi'
import HasilKlasifikasi from './pages/HasilKlasifikasi'
import { api } from './services/api'
import './App.css'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('accessToken')
  const [checking, setChecking] = useState(() => Boolean(token))
  const [authorized, setAuthorized] = useState(false)

  useEffect(() => {
    if (!token) {
      return
    }

    let active = true

    api.getMe()
      .then(() => {
        if (active) setAuthorized(true)
      })
      .catch(() => {
        if (active) setAuthorized(false)
      })
      .finally(() => {
        if (active) setChecking(false)
      })

    return () => {
      active = false
    }
  }, [token])

  if (checking) {
    return (
      <div className="admin-shell" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontFamily: 'inherit',
        fontSize: '1rem',
      }}>
        Memverifikasi sesi login...
      </div>
    )
  }

  return authorized ? children : <Navigate to="/login" replace />
}

function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 })
  }, [pathname])

  return null
}

function AdminLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('admin-theme') || 'dark')

  useEffect(() => {
    const handleThemeChange = (event) => {
      setTheme(event.detail || 'light')
    }

    document.documentElement.classList.remove('dark-theme')
    window.addEventListener('admin-theme-change', handleThemeChange)

    return () => {
      window.removeEventListener('admin-theme-change', handleThemeChange)
    }
  }, [])

  return (
    <div className={`admin-shell ${theme === 'dark' ? 'dark-theme' : ''}`}>
      {/* Mobile Top Header */}
      <header className="mobile-header">
        <button
          className="menu-toggle-btn-mobile"
          type="button"
          onClick={() => setIsSidebarOpen(true)}
          aria-label="Buka Menu"
        >
          <Menu size={22} />
        </button>
        <span className="mobile-brand-title">KNN Bansos</span>
      </header>

      {/* Persistent Sidebar / Drawer overlay */}
      {isSidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)} />
      )}

      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      
      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  )
}

function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="data-warga" element={<DataWarga />} />
          <Route path="proses-klasifikasi" element={<ProsesKlasifikasi />} />
          <Route path="hasil-klasifikasi" element={<HasilKlasifikasi />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App
