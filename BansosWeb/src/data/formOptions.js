export const pendapatanOptions = [
  { value: 400000, label: '< Rp 500.000' },
  { value: 500000, label: 'Rp 500.000' },
  { value: 750000, label: 'Rp 500.000 - Rp 1.000.000' },
  { value: 1500000, label: 'Rp 1.000.000 - Rp 2.000.000' },
  { value: 3000000, label: 'Rp 2.000.000 - Rp 4.000.000' },
  { value: 4500000, label: '> Rp 4.000.000' },
]

export const pekerjaanOptions = [
  'Tidak Bekerja',
  'Mengurus Rumah Tangga',
  'Buruh Harian Lepas',
  'Buruh Tani',
  'Petani/Pekebun',
  'Ustadz',
  'Pedagang',
  'Perdagangan',
  'Wiraswasta',
  'Karyawan Honorer',
  'Karyawan Swasta',
  'Perangkat Desa',
  'Perawat',
  'Guru',
  'Pensiunan',
  'PNS',
  'TNI',
]

export const kondisiRumahOptions = ['Layak', 'Sederhana', 'Kurang Layak', 'Tidak Layak']

export const pendidikanOptions = [
  'Tidak Sekolah',
  'SD',
  'SLTP/Sederajat',
  'SLTA/Sederajat',
  'D1',
  'D2',
  'D3',
  'D4',
  'S1',
  'S2',
  'S3',
]

export const PENDAPATAN_MANUAL_VALUE = 'manual'

export const getPendapatanOptionValue = (value) => {
  const numberValue = Number(value)
  if (numberValue < 500000) return 400000
  if (numberValue === 500000) return 500000
  if (numberValue <= 1000000) return 750000
  if (numberValue <= 2000000) return 1500000
  if (numberValue <= 4000000) return 3000000
  return 4500000
}

export const formatRupiah = (value) =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))

export const formatPendapatan = (item) => {
  if (item?.pendapatanNilai) {
    const val = Number(item.pendapatanNilai)
    const option = pendapatanOptions.find((opt) => opt.value === val)
    if (option) {
      return option.label
    }
    return formatRupiah(item.pendapatanNilai)
  }
  return item?.pendapatan || '-'
}
