import { useEffect, useState } from 'react'
import { Download, Search } from 'lucide-react'
import { api, getApiDownloadUrl } from '../services/api'

function HasilKlasifikasi() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('Semua')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    api
      .getHasilKlasifikasi({ search, status })
      .then((items) => {
        if (active) {
          setData(items)
          setError('')
        }
      })
      .catch((err) => {
        if (active) setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [search, status])

  const getFilenameFromHeader = (contentDisposition) => {
    const match = contentDisposition?.match(/filename="?([^"]+)"?/)
    return match?.[1] || 'hasil-klasifikasi.xlsx'
  }

  const handleExport = async () => {
    setExporting(true)
    setError('')

    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(getApiDownloadUrl('/api/download/hasil-klasifikasi'), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!response.ok) {
        let message = 'Gagal mengunduh hasil klasifikasi.'
        try {
          const errorResponse = await response.json()
          message = errorResponse.detail || message
        } catch {
          message = response.statusText || message
        }
        throw new Error(message)
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = getFilenameFromHeader(response.headers.get('content-disposition'))
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      setError(err.message)
    } finally {
      setExporting(false)
    }
  }

  return (
    <section className="page-section">
      <div className="page-heading row-heading">
        <div>
          <span className="eyebrow">Output Klasifikasi</span>
          <h1>Hasil Klasifikasi</h1>
          <p>Daftar status kelayakan warga berdasarkan data yang sudah dihitung API KNN.</p>
        </div>
        <button className="btn btn-secondary" type="button" onClick={handleExport} disabled={exporting}>
          <Download size={18} /> {exporting ? 'Mengunduh...' : 'Export Data'}
        </button>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="table-toolbar split">
        <div className="search-box">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Cari nama atau NIK..."
          />
        </div>
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option>Semua</option>
          <option>Layak</option>
          <option>Tidak Layak</option>
        </select>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>NIK</th>
              <th>Nama Warga</th>
              <th>Status Kelayakan</th>
              <th>Keterangan</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>{item.nik}</td>
                <td>{item.nama}</td>
                <td>
                  <span className={`badge ${item.status === 'Layak' ? 'success' : 'danger'}`}>
                    {item.status}
                  </span>
                </td>
                <td>{item.keterangan}</td>
              </tr>
            ))}
            {!loading && data.length === 0 && (
              <tr>
                <td colSpan="4" className="empty-table-message">
                  Data hasil klasifikasi tidak ditemukan.
                </td>
              </tr>
            )}
            {loading && (
              <tr>
                <td colSpan="4" className="empty-table-message">
                  Memuat hasil klasifikasi dari API...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default HasilKlasifikasi
