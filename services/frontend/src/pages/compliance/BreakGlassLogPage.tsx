// SecureDx AI — Break-Glass Log

const sessions = [
  { id: 'BG-1021', actor: 'physician@clinic.local', openedAt: '2026-03-16 08:42', reason: 'Emergency triage', status: 'Closed' },
  { id: 'BG-1020', actor: 'admin@clinic.local', openedAt: '2026-03-15 21:04', reason: 'After-hours escalation', status: 'Closed' },
]

export default function BreakGlassLogPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-4xl font-display font-bold text-surface-900">Break-Glass Sessions</h1>
        <p className="text-surface-600 mt-2">Emergency access history with rationale and closure status.</p>
      </header>

      <section className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-surface-200">
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Session ID</th>
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Actor</th>
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Opened At</th>
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Reason</th>
                <th className="py-3 text-sm text-surface-500 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((row) => (
                <tr key={row.id} className="border-b border-surface-100">
                  <td className="py-4 pr-4 font-semibold text-surface-900">{row.id}</td>
                  <td className="py-4 pr-4 text-surface-700">{row.actor}</td>
                  <td className="py-4 pr-4 text-surface-700">{row.openedAt}</td>
                  <td className="py-4 pr-4 text-surface-700">{row.reason}</td>
                  <td className="py-4">
                    <span className="badge badge-success">{row.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
