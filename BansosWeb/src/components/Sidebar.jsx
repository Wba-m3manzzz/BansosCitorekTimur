import { useState, useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  Database,
  Home,
  LogOut,
  Settings2,
  TableProperties,
  Sun,
  Moon,
  X,
} from 'lucide-react'
import logoDesa from '../assets/logo desa.png'
import { api } from '../services/api'

const menuItems = [
  { label: 'Dashboard', path: '/admin/dashboard', icon: Home },
  { label: 'Data Warga', path: '/admin/data-warga', icon: Database },
  { label: 'Proses Klasifikasi', path: '/admin/proses-klasifikasi', icon: Settings2 },
  { label: 'Hasil Klasifikasi', path: '/admin/hasil-klasifikasi', icon: TableProperties },
]

function Sidebar({ isOpen, onClose }) {
  const navigate = useNavigate()
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('admin-theme') || 'dark'
  })

  useEffect(() => {
    localStorage.setItem('admin-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((prev) => {
      const nextTheme = prev === 'dark' ? 'light' : 'dark'
      window.dispatchEvent(new CustomEvent('admin-theme-change', { detail: nextTheme }))
      return nextTheme
    })
  }

  const handleLogout = async () => {
    const accessToken = localStorage.getItem('accessToken')
    const refreshToken = localStorage.getItem('refreshToken')

    try {
      if (accessToken && refreshToken) {
        await api.logout(accessToken, refreshToken)
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('isLoggedIn')
      localStorage.removeItem('adminProfile')
      navigate('/')
    }
  }

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-logo">
          <img src={logoDesa} alt="Logo Desa Citorek Timur" />
        </div>
        <div>
          <strong>KNN Bansos</strong>
          <span>Admin</span>
        </div>
        <button className="sidebar-close-btn" type="button" onClick={onClose} aria-label="Tutup Menu">
          <X size={20} />
        </button>
      </div>

      <nav className="sidebar-menu">
        {menuItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink key={item.path} to={item.path} className="sidebar-link" onClick={onClose}>
              <Icon size={19} />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      <button className="sidebar-link theme-toggle-btn" type="button" onClick={toggleTheme}>
        {theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
        <span>{theme === 'dark' ? 'Mode Terang' : 'Mode Gelap'}</span>
      </button>

      <button className="sidebar-link logout-link" type="button" onClick={handleLogout}>
        <LogOut size={19} />
        <span>Logout</span>
      </button>
    </aside>
  )
}

export default Sidebar
