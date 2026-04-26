// SecureDx AI — Admin Dashboard

import React from 'react'
import { Link } from 'react-router-dom'

const kpis = [
  { label: 'Active Users', value: '24', note: '+2 this week' },
  { label: 'Audit Events', value: '1,284', note: 'Last 24 hours' },
  { label: 'Failed Logins', value: '3', note: 'All investigated' },
  { label: 'Service Uptime', value: '99.97%', note: '30-day rolling' },
]

const quickLinks = [
  { title: 'User Management', description: 'Invite, disable, and assign roles', href: '/admin/users' },
  { title: 'System Health', description: 'Live API, DB, and inference service status', href: '/admin/system' },
  { title: 'Compliance Center', description: 'Review audit and break-glass records', href: '/compliance' },
]

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      <header className="card bg-gradient-to-r from-surface-900 to-surface-700 text-white">
        <p className="text-sm text-surface-200 mb-2">Administration</p>
        <h1 className="text-4xl font-display font-bold mb-2">Operations Overview</h1>
        <p className="text-surface-200">Control access, monitor platform health, and maintain compliance posture.</p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((item) => (
          <article key={item.label} className="card">
            <p className="text-sm text-surface-500">{item.label}</p>
            <p className="text-3xl font-display font-bold text-surface-900 mt-2">{item.value}</p>
            <p className="text-sm text-brand-700 mt-2">{item.note}</p>
          </article>
        ))}
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {quickLinks.map((item) => (
          <Link key={item.title} to={item.href} className="card card-interactive block">
            <h2 className="text-xl font-display font-bold text-surface-900">{item.title}</h2>
            <p className="text-surface-600 mt-2">{item.description}</p>
          </Link>
        ))}
      </section>
    </div>
  )
}
