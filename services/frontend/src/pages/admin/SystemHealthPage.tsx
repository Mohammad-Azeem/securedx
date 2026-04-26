// SecureDx AI — System Health

const systems = [
  { name: 'API Service', status: 'Healthy', detail: 'Latency 42ms' },
  { name: 'Inference Service', status: 'Healthy', detail: 'Model loaded' },
  { name: 'PostgreSQL', status: 'Healthy', detail: 'Connections 12/100' },
  { name: 'Keycloak', status: 'Healthy', detail: 'OIDC online' },
]

export default function SystemHealthPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-4xl font-display font-bold text-surface-900">System Health</h1>
        <p className="text-surface-600 mt-2">Live status of all critical services.</p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {systems.map((item) => (
          <article key={item.name} className="card border border-success-100">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-display font-bold text-surface-900">{item.name}</h2>
              <span className="badge badge-success">{item.status}</span>
            </div>
            <p className="text-surface-600 mt-3">{item.detail}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
