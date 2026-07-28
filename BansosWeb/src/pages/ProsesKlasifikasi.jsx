import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, FileInput, Play, RotateCw, RotateCcw, Search } from 'lucide-react'
import {
  PENDAPATAN_MANUAL_VALUE,
  formatPendapatan,
  kondisiRumahOptions,
  pekerjaanOptions,
  pendidikanOptions,
  pendapatanOptions,
} from '../data/formOptions'
import { api } from '../services/api'

const initialForm = {
  nik: '',
  nama: '',
  pendapatan: '',
  pendapatanManual: '',
  kondisiRumah: '',
  tanggungan: '',
  pendidikan: '',
  pekerjaan: '',
}

function ProsesKlasifikasi() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('manual')
  const [form, setForm] = useState(initialForm)
  const [warga, setWarga] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingWarga, setLoadingWarga] = useState(true)
  const [processingId, setProcessingId] = useState('')
  const [search, setSearch] = useState('')
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    api
      .getWarga()
      .then((items) => {
        if (active) {
          setWarga(items)
          setError('')
        }
      })
      .catch((err) => {
        if (active) setError(err.message)
      })
      .finally(() => {
        if (active) setLoadingWarga(false)
      })

    return () => {
      active = false
    }
  }, [])

  const filteredWarga = warga.filter((item) => {
    const keyword = search.toLowerCase()
    return item.nama.toLowerCase().includes(keyword) || item.nik.includes(keyword)
  })

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
    setSuccess('')
    setError('')
  }

  const buildManualPayload = () => ({
    nik: form.nik,
    nama: form.nama,
    pendapatan:
      form.pendapatan === PENDAPATAN_MANUAL_VALUE ? form.pendapatanManual : form.pendapatan,
    kondisiRumah: form.kondisiRumah,
    tanggungan: Number(form.tanggungan),
    pendidikan: form.pendidikan,
    pekerjaan: form.pekerjaan,
  })

  const handleProcess = async (event) => {
    event.preventDefault()
    setLoading(true)
    setSuccess('')
    setError('')

    try {
      const created = await api.createWarga(buildManualPayload())
      const processed = await api.processWarga(created.id)
      setWarga((prev) => [processed, ...prev])
      setSuccess(`Data ${processed.nama} berhasil diproses. Hasil prediksi: ${processed.status}.`)
      window.setTimeout(() => {
        navigate('/admin/hasil-klasifikasi')
      }, 900)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleProcessAll = async () => {
    setLoading(true)
    setProcessingId('all')
    setSuccess('')
    setError('')

    try {
      const result = await api.processAll()
      const latestRows = await api.getWarga()
      setWarga(latestRows)
      setSuccess(`${result.processed} data warga berhasil diproses ulang.`)
      window.setTimeout(() => {
        navigate('/admin/hasil-klasifikasi')
      }, 900)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setProcessingId('')
    }
  }

  const handleProcessOne = async (item) => {
    setLoading(true)
    setProcessingId(item.id)
    setSuccess('')
    setError('')

    try {
      const processed = await api.processWarga(item.id)
      setWarga((prev) => prev.map((row) => (row.id === item.id ? processed : row)))
      setSuccess(`Data ${processed.nama} berhasil diproses. Hasil prediksi: ${processed.status}.`)
      window.setTimeout(() => {
        navigate('/admin/hasil-klasifikasi')
      }, 900)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setProcessingId('')
    }
  }

  const handleReset = () => {
    setForm(initialForm)
    setSuccess('')
    setError('')
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <span className="eyebrow">Input Data Sosial Ekonomi</span>
        <h1>Proses Klasifikasi</h1>
        <p>
          Masukkan data warga untuk menjalankan klasifikasi kelayakan penerima
          bantuan sosial menggunakan algoritma K-Nearest Neighbor.
        </p>
      </div>

      <div className="process-mode-tabs">
        <button
          className={mode === 'manual' ? 'active' : ''}
          type="button"
          onClick={() => {
            setMode('manual')
            setSuccess('')
          }}
        >
          <FileInput size={18} />
          Input Data Sosial Ekonomi
        </button>
        <button
          className={mode === 'data-warga' ? 'active' : ''}
          type="button"
          onClick={() => {
            setMode('data-warga')
            setSuccess('')
          }}
        >
          <Database size={18} />
          Ambil dari Data Warga
        </button>
      </div>

      <div className="classification-layout">
        {mode === 'manual' ? (
          <>
            <form className="classification-form" onSubmit={handleProcess}>
              <div className="form-section-title">
                <h2>Input Data Sosial Ekonomi Warga</h2>
                <p>Lengkapi kriteria sosial ekonomi warga sebelum memproses klasifikasi.</p>
              </div>

              <div className="classification-fields">
                <label>
                  NIK
                  <input
                    required
                    name="nik"
                    value={form.nik}
                    onChange={handleChange}
                    placeholder="Masukkan NIK"
                  />
                </label>
                <label>
                  Nama
                  <input
                    required
                    name="nama"
                    value={form.nama}
                    onChange={handleChange}
                    placeholder="Masukkan nama"
                  />
                </label>
                <label>
                  Pendapatan Per Bulan
                  <select required name="pendapatan" value={form.pendapatan} onChange={handleChange}>
                    <option value="">Pilih pendapatan</option>
                    {pendapatanOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                    <option value={PENDAPATAN_MANUAL_VALUE}>Lainnya</option>
                  </select>
                </label>
                {form.pendapatan === PENDAPATAN_MANUAL_VALUE && (
                  <label>
                    Pendapatan Manual
                    <input
                      required
                      type="number"
                      min="0"
                      name="pendapatanManual"
                      value={form.pendapatanManual}
                      onChange={handleChange}
                      placeholder="Masukkan nominal pendapatan"
                    />
                  </label>
                )}
                <label>
                  Kondisi Rumah
                  <select
                    required
                    name="kondisiRumah"
                    value={form.kondisiRumah}
                    onChange={handleChange}
                  >
                    <option value="">Pilih kondisi rumah</option>
                    {kondisiRumahOptions.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Jumlah Tanggungan
                  <input
                    required
                    min="0"
                    name="tanggungan"
                    type="number"
                    value={form.tanggungan}
                    onChange={handleChange}
                    placeholder="Masukkan jumlah tanggungan"
                  />
                </label>
                <label>
                  Pendidikan Terakhir
                  <select required name="pendidikan" value={form.pendidikan} onChange={handleChange}>
                    <option value="">Pilih pendidikan</option>
                    {pendidikanOptions.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label className="wide-field">
                  Pekerjaan
                  <select required name="pekerjaan" value={form.pekerjaan} onChange={handleChange}>
                    <option value="">Pilih pekerjaan</option>
                    {pekerjaanOptions.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="classification-actions">
                <button className="btn btn-primary" type="submit" disabled={loading}>
                  {loading ? <RotateCw className="spin" size={18} /> : <Play size={18} />}
                  {loading ? 'Memproses...' : 'Simpan & Proses Klasifikasi'}
                </button>
                <button className="btn btn-secondary" type="button" onClick={handleReset}>
                  <RotateCcw size={18} />
                  Reset
                </button>
              </div>
            </form>
            {error && <div className="form-error">{error}</div>}
            {success && <div className="success-alert">{success}</div>}
          </>
        ) : (
          <>
            <section className="classification-form">
              <div className="form-section-title">
                <h2>Proses Data Warga</h2>
                <p>
                  Data berikut diambil dari API. Cari warga berdasarkan NIK atau nama, lalu
                  proses satu per satu atau proses semua data.
                </p>
              </div>

              <div className="table-toolbar split process-data-toolbar">
                <div className="search-box">
                  <Search size={18} />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Cari nama atau NIK..."
                  />
                </div>
                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={handleProcessAll}
                  disabled={loading || loadingWarga}
                >
                  {processingId === 'all' ? <RotateCw className="spin" size={18} /> : <Play size={18} />}
                  {processingId === 'all' ? 'Memproses...' : 'Proses Semua'}
                </button>
              </div>

              <div className="mini-table">
                <table>
                  <thead>
                    <tr>
                      <th>NIK</th>
                      <th>Nama Warga</th>
                      <th>Pendapatan</th>
                      <th>Tanggungan</th>
                      <th>Kondisi Rumah</th>
                      <th>Pekerjaan</th>
                      <th>Tingkat Pendidikan</th>
                      <th>Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredWarga.map((item) => (
                      <tr key={item.id}>
                        <td>{item.nik}</td>
                        <td>{item.nama}</td>
                        <td>{formatPendapatan(item)}</td>
                        <td>{item.tanggungan}</td>
                        <td>{item.kondisiRumah}</td>
                        <td>{item.pekerjaan}</td>
                        <td>{item.pendidikan}</td>
                        <td>
                          <button
                            className="btn btn-secondary table-process-btn"
                            type="button"
                            onClick={() => handleProcessOne(item)}
                            disabled={loading}
                          >
                            {processingId === item.id ? (
                              <RotateCw className="spin" size={16} />
                            ) : (
                              <Play size={16} />
                            )}
                            {processingId === item.id ? 'Proses...' : 'Proses'}
                          </button>
                        </td>
                      </tr>
                    ))}
                    {!loadingWarga && filteredWarga.length === 0 && (
                      <tr>
                        <td colSpan="8" className="empty-table-message">
                          Data warga tidak ditemukan.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="classification-summary">
                <strong>{filteredWarga.length} data ditampilkan</strong>
                <span>Total master data warga: {warga.length} data.</span>
              </div>
            </section>
            {error && <div className="form-error">{error}</div>}
            {success && <div className="success-alert">{success}</div>}
          </>
        )}
      </div>
    </section>
  )
}

export default ProsesKlasifikasi
