export default function Pagination({ page, count, pageSize, onChange }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  if (totalPages <= 1) return null

  return (
    <div className="pagination">
      <button
        className="ghost"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        ‹ Sebelumnya
      </button>
      <span className="muted">
        Halaman {page} / {totalPages} · {count} data
      </span>
      <button
        className="ghost"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        Berikutnya ›
      </button>
    </div>
  )
}
