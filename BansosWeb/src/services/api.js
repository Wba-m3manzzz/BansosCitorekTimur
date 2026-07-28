const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const token = localStorage.getItem('accessToken')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    })
  } catch (error) {
    throw new Error(
      `Gagal menghubungi API di ${API_BASE_URL}. Pastikan backend berjalan dan konfigurasi CORS sesuai.`,
      { cause: error },
    )
  }

  if (response.status === 401) {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('isLoggedIn')
    localStorage.removeItem('adminProfile')
  }

  if (!response.ok) {
    let message = 'Terjadi kesalahan saat menghubungi API.'
    try {
      const error = await response.json()
      message = error.detail || message
    } catch {
      message = response.statusText || message
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

function buildQuery(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value && value !== 'Semua') {
      query.set(key, value)
    }
  })
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

export const api = {
  sendChatMessage: (message, conversationId) =>
    request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
  login: (username, password) =>
    request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  logout: (accessToken, refreshToken) =>
    request('/api/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ accessToken, refreshToken }),
    }),
  getMe: () => request('/api/auth/me'),
  getDashboard: () => request('/api/dashboard'),
  getSummary: () => request('/api/summary'),
  getMetadata: () => request('/api/metadata'),
  getEvaluasiK: () => request('/api/evaluasi-k'),
  getWarga: (params) => request(`/api/warga${buildQuery(params)}`),
  getWargaByNik: (nik) => request(`/api/warga/by-nik/${encodeURIComponent(nik)}`),
  getWargaByName: (name) => request(`/api/warga/by-name/${encodeURIComponent(name)}`),
  createWarga: (payload) =>
    request('/api/warga', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateWarga: (id, payload) =>
    request(`/api/warga/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteWarga: (id) =>
    request(`/api/warga/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),
  getHasilKlasifikasi: (params) => request(`/api/hasil-klasifikasi${buildQuery(params)}`),
  predict: (payload) =>
    request('/api/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  processAll: () =>
    request('/api/process-all', {
      method: 'POST',
    }),
  processWarga: (id) =>
    request(`/api/process-warga/${encodeURIComponent(id)}`, {
      method: 'POST',
    }),
}

export const getApiDownloadUrl = (path) => `${API_BASE_URL}${path}`
