// SecureDx AI — Compliance Dashboard

import { Link } from 'react-router-dom'

const modules = [
  { title: 'Audit Log', desc: 'View immutable audit trail of user actions.', to: '/compliance/audit' },
  { title: 'Audit Export', desc: 'Generate export package for regulators.', to: '/compliance/export' },
  { title: 'Break-Glass', desc: 'Track emergency data access sessions.', to: '/compliance/break-glass' },
]

export default function ComplianceDashboard() {
  return (
    <div className="space-y-6">
      <header className="card bg-gradient-to-br from-info-50 to-brand-50 border border-info-100">
        <p className="text-sm text-info-700 mb-2">Compliance</p>
        <h1 className="text-4xl font-display font-bold text-surface-900">Governance Center</h1>
        <p className="text-surface-700 mt-2">Monitor policy enforcement, export evidence, and audit privileged access.</p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modules.map((item) => (
          <Link key={item.title} to={item.to} className="card card-interactive block">
            <h2 className="text-xl font-display font-bold text-surface-900">{item.title}</h2>
            <p className="text-surface-600 mt-2">{item.desc}</p>
          </Link>
        ))}
      </section>
    </div>
  )
}
