import { useEffect, useState } from 'react'
import { CheckCircle2, UsersRound, XCircle } from 'lucide-react'
import StatCard from '../components/StatCard'
import { api } from '../services/api'

function ExpandableDistributionList({ items, limit = 5, barClass = "accuracy" }) {
  const [expanded, setExpanded] = useState(false)

  if (!items || items.length === 0) return null

  const displayItems = expanded ? items : items.slice(0, limit)
  const hasMore = items.length > limit

  return (
    <div className="expandable-distribution">
      <div className="distribution-list compact">
        {displayItems.map((item) => (
          <div className="distribution-row" key={item.label}>
            <div className="distribution-meta">
              <strong>{item.label}</strong>
              <span>{item.value} warga</span>
            </div>
            <div className="k-bars">
              <div className={`k-bar ${barClass}`} style={{ width: `${Number(item.share || 0) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>

      {hasMore && (
        <button
          type="button"
          className="btn-expand"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Sembunyikan' : `Lihat Semua (${items.length})`}
        </button>
      )}
    </div>
  )
}

function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [statusDistribution, setStatusDistribution] = useState([])
  const [pendapatanDistribution, setPendapatanDistribution] = useState([])
  const [pekerjaanDistribution, setPekerjaanDistribution] = useState([])
  const [pendidikanDistribution, setPendidikanDistribution] = useState([])
  const [kondisiRumahDistribution, setKondisiRumahDistribution] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    api
      .getDashboard()
      .then((dashboardData) => {
        if (active) {
          setSummary(dashboardData.summary)
          setStatusDistribution(dashboardData.statusDistribution || [])
          setPendapatanDistribution(dashboardData.pendapatanDistribution || [])
          setPekerjaanDistribution(dashboardData.pekerjaanDistribution || [])
          setPendidikanDistribution(dashboardData.pendidikanDistribution || [])
          setKondisiRumahDistribution(dashboardData.kondisiRumahDistribution || [])
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

  return (
    <section className="page-section">
      <div className="page-heading">
        <span className="eyebrow">Ringkasan Data</span>
        <h1>Dashboard Admin</h1>
        <p>Statistik sistem klasifikasi penerima bantuan sosial.</p>
      </div>

      {error && <div className="form-error">{error}</div>}
      {loading && <div className="info-panel">Memuat statistik dari API...</div>}

      <div className="stats-grid">
        <StatCard icon={UsersRound} label="Jumlah Warga" value={summary?.totalWarga ?? '-'} tone="blue" />
        <StatCard icon={CheckCircle2} label="Warga Layak" value={summary?.layak ?? '-'} tone="green" />
        <StatCard icon={XCircle} label="Warga Tidak Layak" value={summary?.tidakLayak ?? '-'} tone="red" />
      </div>

      <div className="dashboard-grid">
        <div className="info-panel dashboard-panel">
          <h3>Distribusi Kondisi Rumah</h3>
          <ExpandableDistributionList items={kondisiRumahDistribution} barClass="accuracy" />
        </div>

        <div className="info-panel dashboard-panel">
          <h3>Distribusi Kelayakan</h3>
          <ExpandableDistributionList items={statusDistribution} barClass="accuracy" />
        </div>

        <div className="info-panel dashboard-panel dashboard-panel-wide">
          <h3>Distribusi Pendapatan</h3>
          <ExpandableDistributionList items={pendapatanDistribution} barClass="accuracy" />
        </div>

        <div className="info-panel dashboard-panel">
          <h3>Distribusi Pekerjaan</h3>
          <ExpandableDistributionList items={pekerjaanDistribution} barClass="accuracy" />
        </div>

        <div className="info-panel dashboard-panel">
          <h3>Distribusi Pendidikan</h3>
          <ExpandableDistributionList items={pendidikanDistribution} barClass="accuracy" />
        </div>
      </div>
    </section>
  )
}

export default Dashboard
