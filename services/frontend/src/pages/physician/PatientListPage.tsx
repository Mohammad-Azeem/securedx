// services/frontend/src/pages/physician/PatientListPage.tsx

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { patientsApi } from '../../api/patients'
import { useAuth } from '../../hooks/useAuth'
import { useState, useMemo } from 'react'

// Search and Filter Component
function SearchAndFilters({ 
  searchTerm, 
  onSearchChange,
  statusFilter,
  onStatusChange 
}: {
  searchTerm: string
  onSearchChange: (term: string) => void
  statusFilter: string
  onStatusChange: (status: string) => void
}) {
  return (
    <div className="card">
      <div className="flex flex-col md:flex-row gap-4">
        {/* Search */}
        <div className="flex-1">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by name or ID..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="input-field pl-12"
            />
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-surface-400 text-xl">
              🔍
            </div>
          </div>
        </div>

        {/* Status Filter */}
        <div className="flex gap-2">
          {['all', 'active', 'inactive'].map((status) => (
            <button
              key={status}
              onClick={() => onStatusChange(status)}
              className={`btn ${
                statusFilter === status ? 'btn-primary' : 'btn-secondary'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function PatientListPage() {
  const navigate = useNavigate()
  const { isAuthenticated, token } = useAuth()

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const { data: patients, isLoading, error } = useQuery({
    queryKey: ['patients'],
    queryFn: () => patientsApi.list(),
    enabled: isAuthenticated && !!token,
  })

  // ADD filtered patients logic
  const filteredPatients = useMemo(() => {
    if (!patients) return []
    
    return patients.filter((patient) => {
      // Search filter (filter patients whose name or pseudo_id includes the search term)
      const matchesSearch = 
        patient.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.pseudo_id?.toLowerCase().includes(searchTerm.toLowerCase())
      
      // Status filter
      const matchesStatus = 
        statusFilter === 'all' || patient.status === statusFilter
      
      return matchesSearch && matchesStatus
    })
  }, [patients, searchTerm, statusFilter])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="section-header">
          <div className="skeleton h-10 w-64"></div>
          <div className="skeleton h-6 w-96 mt-2"></div>
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="card">
              <div className="flex items-center gap-4">
                <div className="skeleton w-14 h-14 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-5 w-48"></div>
                  <div className="skeleton h-4 w-64"></div>
                </div>
                <div className="skeleton h-6 w-20 rounded-full"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <h4 className="font-semibold mb-1">Failed to load patients</h4>
            <p className="text-sm">Please try again or contact IT support.</p>
          </div>
        </div>
      </div>
    )
  }

  if (!patients || patients.length === 0) {
    return (
      <div className="space-y-6">
        <div className="section-header">
          <h1 className="section-title">Patient List</h1>
          <p className="section-subtitle">Today's schedule</p>
        </div>
        
        <div className="card text-center py-12">
          <div className="text-6xl mb-4">👥</div>
          <h3 className="text-xl font-semibold text-surface-900 mb-2">
            No patients scheduled
          </h3>
          <p className="text-surface-600">
            Your patient list will appear here when scheduled.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-display font-bold text-surface-900">
            Patient List
          </h1>
          <p className="text-surface-600 mt-2">
            {filteredPatients.length} patient{filteredPatients.length !== 1 ? 's' : ''} 
            {searchTerm && ' matching your search'}
          </p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={() => navigate('/help')}
          title="Patient creation is managed from your EHR integration"
        >
          <span className="text-xl mr-2">+</span>
          Add Patient (EHR)
        </button>
      </div>

      {/* Search and Filters */}
      <SearchAndFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
      />

      {/* Summary Cards - UPDATE to use filteredPatients */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-gradient-to-br from-brand-50 to-brand-100 border-2 border-brand-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-brand-700">
                {filteredPatients.length}
              </div>
              <div className="text-sm text-brand-600 font-medium mt-1">
                Total Patients
              </div>
            </div>
            <div className="w-12 h-12 bg-brand-500 rounded-xl flex items-center justify-center text-white text-2xl">
              👥
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-success-50 to-success-100 border-2 border-success-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-success-700">
                {patients.filter(p => p.status === 'active').length}
              </div>
              <div className="text-sm text-success-600 font-medium mt-1">
                Active
              </div>
            </div>
            <div className="w-12 h-12 bg-success-500 rounded-xl flex items-center justify-center text-white text-2xl">
              ✓
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-info-50 to-info-100 border-2 border-info-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-info-700">
                {Math.round(patients.reduce((sum, p) => sum + (p.age_years || 0), 0) / patients.length)}
              </div>
              <div className="text-sm text-info-600 font-medium mt-1">
                Avg Age
              </div>
            </div>
            <div className="w-12 h-12 bg-info-500 rounded-xl flex items-center justify-center text-white text-2xl">
              📊
            </div>
          </div>
        </div>
      </div>

      {/* Empty State for Search */}
      {filteredPatients.length === 0 && searchTerm && (
        <div className="card text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-surface-900 mb-2">
            No patients found
          </h3>
          <p className="text-surface-600 mb-4">
            Try adjusting your search or filters
          </p>
          <button
            onClick={() => {
              setSearchTerm('')
              setStatusFilter('all')
            }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Patient Cards, show them as cards - UPDATE to use filteredPatients */}
      {filteredPatients.length > 0 && (
        <div className="space-y-3">
          {filteredPatients.map((patient, index) => (
            <div
              key={patient.pseudo_id || index}
              onClick={() => navigate(`/physician/analyze/${patient.pseudo_id}`)}
              className="card card-interactive group animate-fade-in"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-center gap-4">
                {/* Avatar */}
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-md group-hover:shadow-xl group-hover:scale-110 transition-all">
                  {patient.display_name
                    ? patient.display_name.split(' ').map(n => n[0]).join('').slice(0, 2)
                    : '?'}
                </div>

                {/* Patient Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-semibold text-surface-900 truncate">
                      {patient.display_name || 'Unknown Patient'}
                    </h3>
                    <span className="badge badge-neutral flex-shrink-0">
                      {(patient.pseudo_id || '').slice(0, 8)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-surface-600">
                    <span className="flex items-center gap-1">
                      <span>👤</span>
                      {patient.age_years || '?'}y • {patient.sex || 'Unknown'}
                    </span>
                    {patient.last_visit_date && (
                      <span className="flex items-center gap-1">
                        <span>📅</span>
                        {new Date(patient.last_visit_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Status & Action */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className={`badge ${
                    patient.status === 'active' ? 'badge-success' : 'badge-neutral'
                  }`}>
                    {patient.status || 'Unknown'}
                  </span>
                  <div className="text-2xl text-surface-300 group-hover:text-brand-500 group-hover:translate-x-2 transition-all">
                    →
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {/* Quick Stats Footer */}
      <div className="card bg-surface-100">
        <div className="text-center text-sm text-surface-600">
          <p>
            📊 Showing all active patients • 
            <span className="text-brand-600 font-medium ml-1">
              Click any patient to start diagnostic analysis
            </span>
          </p>
        </div>
      </div>
    </div>
  )
}
