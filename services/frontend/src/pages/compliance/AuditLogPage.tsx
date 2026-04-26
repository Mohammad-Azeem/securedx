// SecureDx AI — Audit Log

const events = [
  { time: '09:14', actor: 'physician@clinic.local', action: 'Viewed patient record', resource: 'Patient d3f99dbb' },
  { time: '09:05', actor: 'admin@clinic.local', action: 'Updated user role', resource: 'User physician@clinic.local' },
  { time: '08:50', actor: 'system', action: 'Inference request processed', resource: 'Encounter e7b1f9' },
]

export default function AuditLogPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-4xl font-display font-bold text-surface-900">Audit Log</h1>
        <p className="text-surface-600 mt-2">Tamper-evident trail of security and clinical actions.</p>
      </header>

      <section className="card">
        <div className="space-y-3">
          {events.map((event) => (
            <article key={`${event.time}-${event.actor}`} className="p-4 rounded-xl bg-surface-50 border border-surface-200">
              <p className="text-sm text-surface-500">{event.time}</p>
              <p className="font-semibold text-surface-900 mt-1">{event.action}</p>
              <p className="text-surface-700 mt-1">{event.actor}</p>
              <p className="text-sm text-surface-500 mt-1">{event.resource}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
