// services/frontend/src/components/shared/AppLayout.tsx

import React from 'react'

import { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Determine role-based navigation
  const isPhysician = user?.roles?.includes('physician')
  const isAdmin = user?.roles?.includes('admin')
  const navItems = [
    ...(isPhysician ? [
      { path: '/physician', label: 'Dashboard', icon: '📊' },
      { path: '/physician/patients', label: 'Patients', icon: '👥' },
    ] : []),
    ...(isAdmin ? [
      { path: '/admin', label: 'Admin', icon: '⚙️' },
      { path: '/admin/users', label: 'Users', icon: '👤' },
    ] : []),
    { path: '/help', label: 'Help', icon: '❓' },
  ]

  return (
    <div className="min-h-screen">
      {/* Top Navigation Bar */}
      <nav className="card-glass sticky top-0 z-50 border-b border-surface-200">
        <div className="container mx-auto">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Brand */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden btn btn-ghost btn-sm"
                aria-label="Toggle menu"
              >
                ☰
              </button>
              
              <Link to="/" className="flex items-center gap-3 group">
                <div className="w-10 h-10 bg-gradient-to-br from-brand-500 to-brand-600 rounded-xl flex items-center justify-center text-white text-xl font-bold shadow-md group-hover:shadow-lg transition-all">
                  S
                </div>
                <div className="hidden sm:block">
                  <div className="text-lg font-display font-bold text-surface-900">
                    SecureDx
                  </div>
                  <div className="text-xs text-surface-500 -mt-1">
                    AI Clinical Assistant
                  </div>
                </div>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                    location.pathname.startsWith(item.path)
                      ? 'bg-brand-500 text-white shadow-md'
                      : 'text-surface-700 hover:bg-surface-100'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-3">
              {/* User Info */}
              <div className="hidden md:block text-right">
                <div className="text-sm font-semibold text-surface-900">
                  {user?.fullName || user?.email}
                </div>
                <div className="text-xs text-surface-500">
                  {user?.roles?.join(', ')}
                </div>
              </div>

              {/* Avatar */}
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold shadow-md">
                {(user?.fullName || user?.email || 'U')[0].toUpperCase()}
              </div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="btn btn-ghost btn-sm"
                title="Logout"
              >
                <span className="hidden sm:inline">Logout</span>
                <span className="sm:hidden">↪</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed top-16 left-0 bottom-0 w-64 card-glass border-r border-surface-200 z-40 lg:hidden animate-slide-in">
            <div className="p-4 space-y-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                    location.pathname.startsWith(item.path)
                      ? 'bg-brand-500 text-white'
                      : 'text-surface-700 hover:bg-surface-100'
                  }`}
                >
                  <span className="text-xl">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Page Content */}
      <main className="container mx-auto py-8 animate-fade-in">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t border-surface-200 bg-surface-50">
        <div className="container mx-auto py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-surface-500">
            <div>
              © 2026 SecureDx AI • HIPAA Compliant • Privacy First
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse"></div>
              <span>All systems operational</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
