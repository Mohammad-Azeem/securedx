// services/frontend/src/pages/physician/Dashboard.tsx

import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'


// ADD at line 7 (after imports, before export default)

// Recent Activity Component
function RecentActivityFeed() {
  const activities = [
    {
      id: 1,
      type: 'diagnosis',
      patient: 'Patient A123',
      action: 'Diagnosed with Pneumonia',
      time: '2 hours ago',
      icon: '🎯',
      color: 'brand',
    },
    {
      id: 2,
      type: 'feedback',
      patient: 'Patient B456',
      action: 'Accepted AI suggestion',
      time: '4 hours ago',
      icon: '✅',
      color: 'success',
    },
    {
      id: 3,
      type: 'analysis',
      patient: 'Patient C789',
      action: 'Started diagnostic analysis',
      time: '6 hours ago',
      icon: '🔍',
      color: 'info',
    },
  ]

  return (
    <div className="space-y-3">
      {activities.map((activity, index) => (
        <div
          key={activity.id}
          className="flex items-start gap-4 p-4 bg-surface-50 rounded-xl hover:bg-surface-100 transition-colors cursor-pointer animate-slide-in"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div
            className={[
              'w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0',
              activity.color === 'success'
                ? 'bg-success-100'
                : activity.color === 'info'
                  ? 'bg-info-100'
                  : 'bg-brand-100',
            ].join(' ')}
          >
            {activity.icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-surface-900">
              {activity.action}
            </p>
            <p className="text-xs text-surface-500 mt-1">
              {activity.patient} • {activity.time}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

// Quick Action Card Component
function QuickActionCard({ 
  icon, 
  title, 
  description, 
  onClick, 
  gradient 
}: { 
  icon: string
  title: string
  description: string
  onClick: () => void
  gradient: string
}) {
  return (
    <button
      onClick={onClick}
      className="card card-interactive group text-left w-full"
    >
      <div className="flex items-start justify-between mb-4">
        <div 
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-2xl shadow-lg group-hover:shadow-xl transition-all group-hover:scale-110"
          style={{ background: gradient }}
        >
          {icon}
        </div>
        <div className="text-3xl text-surface-300 group-hover:text-brand-500 group-hover:translate-x-1 transition-all">
          →
        </div>
      </div>
      <h3 className="text-xl font-display font-bold text-surface-900 mb-2">
        {title}
      </h3>
      <p className="text-surface-600 text-sm leading-relaxed">
        {description}
      </p>
    </button>
  )
}

export default function PhysicianDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero Header with Gradient */}
      <div className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-brand-500 via-brand-600 to-brand-700 text-white shadow-xl">
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
        
        <div className="relative z-10">
          <h1 className="text-4xl md:text-5xl font-display font-bold mb-3">
            Welcome back, {user?.fullName || 'Doctor'}!
          </h1>
          <p className="text-xl text-brand-100 max-w-2xl">
            Ready to provide AI-powered clinical decision support to your patients
          </p>
          
          {/* Quick Stats in Header */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            {[
              { value: '18', label: 'Patients Today', change: '+3' },
              { value: '85%', label: 'AI Accuracy', change: '+2%' },
              { value: '142', label: 'This Week', change: '+12' },
              { value: '2.3s', label: 'Avg Time', change: '-0.5s' },
            ].map((stat, i) => (
              <div key={i} className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="text-sm text-brand-100 mt-1">{stat.label}</div>
                <div className="text-xs text-green-300 mt-2">
                  ↗ {stat.change}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-2xl font-display font-bold text-surface-900 mb-4">
              Quick Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <QuickActionCard
                icon="👥"
                title="View Patients"
                description="Access today's schedule and patient list"
                onClick={() => navigate('/physician/patients')}
                gradient="linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)"
              />
              <QuickActionCard
                icon="🔍"
                title="New Analysis"
                description="Start a diagnostic analysis"
                onClick={() => navigate('/physician/patients')}
                gradient="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
              />
              <QuickActionCard
                icon="📊"
                title="View Reports"
                description="Access analytics and insights"
                onClick={() => navigate('/compliance')}
                gradient="linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)"
              />
              <QuickActionCard
                icon="⚙️"
                title="Settings"
                description="Manage your preferences"
                onClick={() => navigate('/help')}
                gradient="linear-gradient(135deg, #6b7280 0%, #4b5563 100%)"
              />
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="card">
            <h3 className="text-xl font-display font-bold text-surface-900 mb-4">
              Performance Metrics
            </h3>
            <div className="space-y-4">
              {[
                { label: 'Diagnostic Accuracy', value: 85, color: 'success', target: 90 },
                { label: 'Patient Satisfaction', value: 92, color: 'brand', target: 95 },
                { label: 'Avg Response Time', value: 78, color: 'info', target: 80 },
              ].map((metric, i) => (
                <div key={i}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-surface-700">
                      {metric.label}
                    </span>
                    <span className="text-sm font-bold text-surface-900">
                      {metric.value}% 
                      <span className="text-xs text-surface-500 ml-1">
                        / {metric.target}%
                      </span>
                    </span>
                  </div>
                  <div className="h-2 bg-surface-100 rounded-full overflow-hidden">
                    <div
                      className={[
                        'h-full rounded-full transition-all duration-1000',
                        metric.color === 'success'
                          ? 'bg-success-500'
                          : metric.color === 'info'
                            ? 'bg-info-500'
                            : 'bg-brand-500',
                      ].join(' ')}
                      style={{ width: `${metric.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Activity & Status */}
        <div className="space-y-6">
          {/* Recent Activity */}
          <div className="card">
            <h3 className="text-xl font-display font-bold text-surface-900 mb-4">
              Recent Activity
            </h3>
            <RecentActivityFeed />
            <button className="btn btn-ghost w-full mt-4 text-sm">
              View All Activity →
            </button>
          </div>

          {/* System Status */}
          <div className="card">
            <h3 className="text-xl font-display font-bold text-surface-900 mb-4">
              System Status
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Inference Engine', status: 'online', uptime: '99.9%' },
                { name: 'Database', status: 'online', uptime: '100%' },
                { name: 'PHI Boundary', status: 'secure', uptime: '100%' },
              ].map((system, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-success-50 rounded-lg border border-success-200">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse"></div>
                    <div>
                      <div className="text-sm font-semibold text-surface-900">
                        {system.name}
                      </div>
                      <div className="text-xs text-success-600">
                        Uptime: {system.uptime}
                      </div>
                    </div>
                  </div>
                  <span className="badge badge-success">
                    {system.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="card bg-gradient-to-br from-info-50 to-info-100 border-2 border-info-200">
            <div className="flex items-start gap-3">
              <span className="text-3xl">🔒</span>
              <div>
                <h4 className="font-semibold text-info-900 mb-2">
                  Privacy First
                </h4>
                <p className="text-sm text-info-800 leading-relaxed">
                  All patient data remains on your local network. HIPAA §164.312 compliant.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
