import { useEffect, useMemo, useState } from 'react'
import { Edit, Plus, Search, Trash2, X } from 'lucide-react'
import {
  PENDAPATAN_MANUAL_VALUE,
  formatPendapatan,
  getPendapatanOptionValue,
  kondisiRumahOptions,
  pekerjaanOptions,
  pendidikanOptions,
  pendapatanOptions,
} from '../data/formOptions'
import { api } from '../services/api'

const emptyForm = {
  nik: '',
  nama: '',
  pendapatan: '',
  pendapatanManual: '',
  tanggungan: '',
  kondisiRumah: '',
  pekerjaan: '',
  pendidikan: '',
}

function DataWarga() {
  const [data, setData] = useState([])
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    api
      .getWarga()
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
  }, [])

  const filteredData = useMemo(() => {
    const keyword = search.toLowerCase()
    return data.filter(
      (item) => item.nama.toLowerCase().includes(keyword) || item.nik.includes(keyword),
    )
  }, [data, search])

  const openAddModal = () => {
    setEditingId(null)
    setForm(emptyForm)
    setError('')
    setModalOpen(true)
  }

  const openEditModal = (item) => {
    setEditingId(item.id)
    setForm({
      nik: item.nik,
      nama: item.nama,
      pendapatan: getPendapatanOptionValue(item.pendapatanNilai),
      pendapatanManual: '',
      tanggungan: item.tanggungan,
      kondisiRumah: item.kondisiRumah,
      pekerjaan: item.pekerjaan,
      pendidikan: item.pendidikan,
    })
    setError('')
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const buildPayload = () => ({
    nik: form.nik,
    nama: form.nama,
    pendapatan:
      form.pendapatan === PENDAPATAN_MANUAL_VALUE ? form.pendapatanManual : form.pendapatan,
    tanggungan: Number(form.tanggungan),
    kondisiRumah: form.kondisiRumah,
    pekerjaan: form.pekerjaan,
    pendidikan: form.pendidikan,
  })

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const payload = buildPayload()
      if (editingId) {
        const updated = await api.updateWarga(editingId, payload)
        setData((prev) => prev.map((item) => (item.id === editingId ? updated : item)))
      } else {
        const created = await api.createWarga(payload)
        setData((prev) => [created, ...prev])
      }
      closeModal()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    setError('')
    try {
      await api.deleteWarga(id)
      setData((prev) => prev.filter((item) => item.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page-section">
      <div className="page-heading row-heading">
        <div>
          <span className="eyebrow">Master Data</span>
          <h1>Data Warga</h1>
          <p>Kelola data warga yang akan digunakan dalam klasifikasi.</p>
        </div>
        <button className="btn btn-primary" type="button" onClick={openAddModal}>
          <Plus size={18} /> Tambah Data
        </button>
      </div>

      {error && <div className="form-error">{error}</div>}
      {loading && <div className="info-panel">Memuat data warga dari API...</div>}

      <div className="table-toolbar">
        <div className="search-box">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Cari nama atau NIK..."
          />
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>NIK</th>
              <th>Nama Warga</th>
              <th>Pendapatan</th>
              <th>Jumlah Tanggungan</th>
              <th>Kondisi Rumah</th>
              <th>Pekerjaan</th>
              <th>Tingkat Pendidikan</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr key={item.id}>
                <td>{item.nik}</td>
                <td>{item.nama}</td>
                <td>{formatPendapatan(item)}</td>
                <td>{item.tanggungan}</td>
                <td>{item.kondisiRumah}</td>
                <td>{item.pekerjaan}</td>
                <td>{item.pendidikan}</td>
                <td>
                  <div className="action-group">
                    <button type="button" onClick={() => openEditModal(item)} aria-label="Edit data">
                      <Edit size={16} />
                    </button>
                    <button type="button" onClick={() => handleDelete(item.id)} aria-label="Hapus data">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!loading && filteredData.length === 0 && (
              <tr>
                <td colSpan="8" className="empty-table-message">
                  Data warga tidak ditemukan.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {modalOpen && (
        <div className="modal-backdrop">
          <section className="modal">
            <div className="modal-header">
              <h2>{editingId ? 'Edit Data Warga' : 'Tambah Data Warga'}</h2>
              <button type="button" onClick={closeModal} aria-label="Tutup modal">
                <X size={18} />
              </button>
            </div>
            <form className="form-grid" onSubmit={handleSubmit}>
              <label>
                NIK
                <input
                  required
                  value={form.nik}
                  onChange={(event) => setForm({ ...form, nik: event.target.value })}
                />
              </label>
              <label>
                Nama Warga
                <input
                  required
                  value={form.nama}
                  onChange={(event) => setForm({ ...form, nama: event.target.value })}
                />
              </label>
              <label>
                Pendapatan
                <select
                  required
                  value={form.pendapatan}
                  onChange={(event) => setForm({ ...form, pendapatan: event.target.value })}
                >
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
                    value={form.pendapatanManual}
                    onChange={(event) =>
                      setForm({ ...form, pendapatanManual: event.target.value })
                    }
                    placeholder="Masukkan nominal pendapatan"
                  />
                </label>
              )}
              <label>
                Jumlah Tanggungan
                <input
                  required
                  type="number"
                  min="0"
                  value={form.tanggungan}
                  onChange={(event) => setForm({ ...form, tanggungan: event.target.value })}
                />
              </label>
              <label>
                Kondisi Rumah
                <select
                  required
                  value={form.kondisiRumah}
                  onChange={(event) => setForm({ ...form, kondisiRumah: event.target.value })}
                >
                  <option value="">Pilih kondisi</option>
                  {kondisiRumahOptions.map((option) => (
                    <option key={option}>{option}</option>
                  ))}
                </select>
              </label>
              <label>
                Pekerjaan
                <select
                  required
                  value={form.pekerjaan}
                  onChange={(event) => setForm({ ...form, pekerjaan: event.target.value })}
                >
                  <option value="">Pilih pekerjaan</option>
                  {pekerjaanOptions.map((option) => (
                    <option key={option}>{option}</option>
                  ))}
                </select>
              </label>
              <label>
                Tingkat Pendidikan
                <select
                  required
                  value={form.pendidikan}
                  onChange={(event) => setForm({ ...form, pendidikan: event.target.value })}
                >
                  <option value="">Pilih pendidikan</option>
                  {pendidikanOptions.map((option) => (
                    <option key={option}>{option}</option>
                  ))}
                </select>
              </label>
              <div className="modal-actions">
                <button className="btn btn-secondary" type="button" onClick={closeModal}>
                  Batal
                </button>
                <button className="btn btn-primary" type="submit" disabled={saving}>
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </section>
  )
}

export default DataWarga
