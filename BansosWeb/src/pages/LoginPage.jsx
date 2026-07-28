import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import logoDesa from '../assets/logo desa.png'
import { api } from '../services/api'

function LoginPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    document.documentElement.classList.remove('dark-theme')
  }, [])

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
    setError('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await api.login(form.username, form.password)
      localStorage.setItem('accessToken', response.accessToken)
      localStorage.setItem('refreshToken', response.refreshToken)
      localStorage.setItem('isLoggedIn', 'true')
      localStorage.setItem('adminProfile', JSON.stringify(response.admin))
      navigate('/admin/dashboard')
    } catch (err) {
      setError(err.message || 'Username atau password salah.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <Link className="brand login-brand" to="/">
        <div className="brand-logo">
          <img src={logoDesa} alt="Logo Desa Citorek Timur" />
        </div>
        <div>
          <strong>Desa Citorek Timur</strong>
          <span>Sistem Klasifikasi Bansos</span>
        </div>
      </Link>

      <section className="login-card">
        <div className="login-logo">
          <div className="login-logo-mark">
            <img src={logoDesa} alt="Logo Desa Citorek Timur" />
          </div>
          <span>Desa Citorek Timur</span>
        </div>
        <h1>Login Admin</h1>
        <p>Masuk untuk mengelola data warga dan klasifikasi KNN.</p>

        <form onSubmit={handleSubmit}>
          <label>
            Username
            <input
              required
              name="username"
              type="text"
              value={form.username}
              onChange={handleChange}
              placeholder="Masukkan username"
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              required
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              type="password"
              autoComplete="current-password"
            />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary full-width" type="submit" disabled={loading}>
            {loading ? 'Masuk...' : 'Login'}
          </button>
        </form>
      </section>
    </div>
  )
}

export default LoginPage
