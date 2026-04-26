// SecureDx AI — Main Application
// React 18 + React Router v6 + Keycloak OIDC

import React, { Suspense, lazy, type ReactNode } from 'react'
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './hooks/useAuth'
import AppLayout from './components/shared/AppLayout'
import { LoadingScreen } from './components/shared/LoadingScreen'
import { NotFoundPage } from './pages/NotFoundPage'
import HelpPage from './pages/HelpPage'


// Lazy-loaded pages (code splitting by role)
const PhysicianDashboard   = lazy(() => import('./pages/physician/Dashboard'))
const InferencePage        = lazy(() => import('./pages/physician/InferencePage'))
const FeedbackPage         = lazy(() => import('./pages/physician/FeedbackPage'))
const PatientListPage      = lazy(() => import('./pages/physician/PatientListPage'))

const AdminDashboard       = lazy(() => import('./pages/admin/AdminDashboard'))
const UserManagementPage   = lazy(() => import('./pages/admin/UserManagementPage'))
const SystemHealthPage     = lazy(() => import('./pages/admin/SystemHealthPage'))

const ComplianceDashboard  = lazy(() => import('./pages/compliance/ComplianceDashboard'))
const AuditLogPage         = lazy(() => import('./pages/compliance/AuditLogPage'))
const AuditExportPage      = lazy(() => import('./pages/compliance/AuditExportPage'))
const BreakGlassLogPage    = lazy(() => import('./pages/compliance/BreakGlassLogPage'))

const LoginPage            = lazy(() => import('./pages/LoginPage'))

// React Query client — no PHI in cache keys, 5 min stale time
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// Role-based route guard
function ProtectedRoute({
  children,
  requiredRoles,
}: {
  children: ReactNode
  requiredRoles?: string[]
}) {
  const { isAuthenticated, isLoading, hasRole } = useAuth()

  if (isLoading) return <LoadingScreen message="Verifying credentials..." />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (requiredRoles && !requiredRoles.some(r => hasRole(r))) {
    return <Navigate to="/login" replace />
  }
  return <React.Fragment>{children}</React.Fragment>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              {/* Public */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected — all authenticated users */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                {/* Physician routes */}
                <Route index element={<Navigate to="/physician" replace />} />
                <Route
                  path="physician"
                  element={
                    <ProtectedRoute requiredRoles={['physician', 'admin']}>
                      <PhysicianDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="physician/patients"
                  element={
                    <ProtectedRoute requiredRoles={['physician', 'admin']}>
                      <PatientListPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="physician/analyze/:patientId"
                  element={
                    <ProtectedRoute requiredRoles={['physician', 'admin']}>
                      <InferencePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="physician/feedback/:inferenceId"
                  element={
                    <ProtectedRoute requiredRoles={['physician', 'admin']}>
                      <FeedbackPage />
                    </ProtectedRoute>
                  }
                />

                {/* Admin routes */}
                <Route
                  path="admin"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <AdminDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/users"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <UserManagementPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/system"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <SystemHealthPage />
                    </ProtectedRoute>
                  }
                />

                {/* Compliance routes */}
                <Route
                  path="compliance"
                  element={
                    <ProtectedRoute requiredRoles={['compliance_officer', 'admin']}>
                      <ComplianceDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="compliance/audit"
                  element={
                    <ProtectedRoute requiredRoles={['compliance_officer', 'admin']}>
                      <AuditLogPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="compliance/export"
                  element={
                    <ProtectedRoute requiredRoles={['compliance_officer', 'admin']}>
                      <AuditExportPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="compliance/break-glass"
                  element={
                    <ProtectedRoute requiredRoles={['compliance_officer', 'admin']}>
                      <BreakGlassLogPage />
                    </ProtectedRoute>
                  }
                />
              </Route>

              <Route path="/help" element={<HelpPage />} />

              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
