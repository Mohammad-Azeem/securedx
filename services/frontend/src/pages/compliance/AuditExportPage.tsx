// SecureDx AI — Audit Export

export default function AuditExportPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <header>
        <h1 className="text-4xl font-display font-bold text-surface-900">Audit Export</h1>
        <p className="text-surface-600 mt-2">Create regulator-ready export packages by date range.</p>
      </header>

      <section className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="input-group">
            <label className="input-label">From date</label>
            <input type="date" className="input-field" />
          </div>
          <div className="input-group">
            <label className="input-label">To date</label>
            <input type="date" className="input-field" />
          </div>
        </div>
        <div className="mt-4 flex gap-3">
          <button className="btn btn-primary">Generate Export</button>
          <button className="btn btn-secondary">Preview Contents</button>
        </div>
      </section>
    </div>
  )
}
