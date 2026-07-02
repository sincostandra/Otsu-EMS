import { useEffect, useRef, useState } from 'react'

import api from '../../api/client'
import AnalyticsBlock from './AnalyticsBlock'

export default function KaiPanel() {
  const [presets, setPresets] = useState([])
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const resultRef = useRef(null)

  useEffect(() => {
    api
      .get('/analytics/presets/')
      .then(({ data }) => setPresets(data))
      .catch(() => setPresets([]))
  }, [])

  const run = async (payload) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/analytics/query/', payload)
      setResult(data)
      requestAnimationFrame(() =>
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }),
      )
    } catch (err) {
      setError(
        err.response?.status === 429
          ? 'Terlalu banyak permintaan. Coba lagi sebentar lagi.'
          : 'Gagal memproses pertanyaan. Coba lagi.',
      )
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = (e) => {
    e.preventDefault()
    const q = question.trim()
    if (q && !loading) run({ question: q })
  }

  const onChip = (p) => {
    if (loading) return
    setQuestion(p.question)
    run({ preset: p.id })
  }

  return (
    <section className="card kai-panel">
      <header className="kai-head">
        <span className="kai-logo">kAI</span>
        <div>
          <h3>Tanya kAI</h3>
          <p className="muted">
            Analitik absensi berbasis AI. Tanya dalam bahasa sehari-hari.
          </p>
        </div>
      </header>

      <form className="kai-ask" onSubmit={onSubmit}>
        <input
          type="text"
          value={question}
          maxLength={300}
          placeholder="Mis. Siapa yang paling sering telat 2 bulan terakhir?"
          onChange={(e) => setQuestion(e.target.value)}
          aria-label="Pertanyaan untuk kAI"
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Menganalisis…' : 'Tanya'}
        </button>
      </form>

      {presets.length > 0 && (
        <div className="kai-chips" role="list">
          {presets.map((p) => (
            <button
              key={p.id}
              type="button"
              role="listitem"
              className="kai-chip"
              disabled={loading}
              onClick={() => onChip(p)}
            >
              {p.question}
            </button>
          ))}
        </div>
      )}

      <div ref={resultRef} className="kai-result">
        {error && <p className="error">{error}</p>}

        {loading && <p className="muted kai-loading">kAI sedang menganalisis data…</p>}

        {!loading && result && (
          <>
            <div className="kai-result-head">
              <h3>{result.title}</h3>
              {result.period_label && (
                <span className="muted">{result.period_label}</span>
              )}
            </div>

            {result.blocks.map((block, i) => (
              <AnalyticsBlock key={i} block={block} />
            ))}

            {result.suggestions?.length > 0 && (
              <div className="kai-chips">
                {result.suggestions.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className="kai-chip"
                    disabled={loading}
                    onClick={() => onChip(p)}
                  >
                    {p.question}
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {!loading && !result && !error && (
          <p className="muted kai-hint">
            Pilih salah satu contoh di atas, atau ketik pertanyaanmu sendiri.
          </p>
        )}
      </div>
    </section>
  )
}
