import { useState } from 'react'

import { downloadExport } from '../api/exports'

export default function ExportButtons({ resource, params }) {
  const [busy, setBusy] = useState('')

  const handle = async (format) => {
    setBusy(format)
    try {
      await downloadExport(resource, format, params)
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="export-buttons">
      <button className="ghost" disabled={busy} onClick={() => handle('csv')}>
        {busy === 'csv' ? 'Mengunduh…' : 'Export CSV'}
      </button>
      <button className="ghost" disabled={busy} onClick={() => handle('xlsx')}>
        {busy === 'xlsx' ? 'Mengunduh…' : 'Export Excel'}
      </button>
    </div>
  )
}
