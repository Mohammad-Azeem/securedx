// SecureDx AI — User Management

import React from 'react'
const sampleUsers = [
  { name: 'Dr. Sarah Patel', email: 'physician@clinic.local', role: 'Physician', status: 'Active' },
  { name: 'Alex Johnson', email: 'admin@clinic.local', role: 'Admin', status: 'Active' },
  { name: 'Compliance Team', email: 'compliance@clinic.local', role: 'Compliance', status: 'Pending' },
]

export default function UserManagementPage() {
  return (
    <div className="space-y-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-display font-bold text-surface-900">User Management</h1>
          <p className="text-surface-600 mt-2">Manage role-based access and account lifecycle.</p>
        </div>
        <button className="btn btn-primary">Invite User</button>
      </header>

      <section className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-surface-200">
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Name</th>
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Email</th>
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Role</th>
                <th className="py-3 pr-4 text-sm text-surface-500 font-semibold">Status</th>
                <th className="py-3 text-sm text-surface-500 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sampleUsers.map((user) => (
                <tr key={user.email} className="border-b border-surface-100">
                  <td className="py-4 pr-4 font-semibold text-surface-900">{user.name}</td>
                  <td className="py-4 pr-4 text-surface-700">{user.email}</td>
                  <td className="py-4 pr-4">
                    <span className="badge badge-info">{user.role}</span>
                  </td>
                  <td className="py-4 pr-4">
                    <span className={user.status === 'Active' ? 'badge badge-success' : 'badge badge-warning'}>
                      {user.status}
                    </span>
                  </td>
                  <td className="py-4">
                    <button className="btn btn-ghost btn-sm">Edit</button>
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
