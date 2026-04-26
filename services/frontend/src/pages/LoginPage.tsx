// services/frontend/src/pages/LoginPage.tsx

import React from 'react'

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated, login } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/physician')
    }
  }, [isAuthenticated, navigate])

  const handleLogin = () => {
    login()
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Brand Story */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-500 to-brand-700 p-12 flex-col justify-between relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>

        {/* Content */}
        <div className="relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            
  
          </div>

          {/* Value Props */}
          <div className="space-y-8 max-w-md">
            <div>
              <h1 className="text-4xl font-display font-bold text-white mb-4 leading-tight">
                <p style={{ textAlign: "center" }}>AI-powered diagnostics,</p>
                <br />
                <p style={{ textAlign: "center" }}>Privacy First.</p>
              </h1>
              <div className="text-lg text-brand-100 leading-relaxed">
                <p style={{ textAlign: "center" }}>Assist physicians with differential diagnoses while keeping
                all patient data secure and local.</p>
              </div>
            </div>

            {/* Features */}
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div>
                  <div className="font-semibold text-white mb-1">
                    <p style={{ textAlign: "center" }}>🔒 HIPAA Compliant</p>
                  </div>
                  <div className="text-sm text-brand-100">
                    <p style={{ textAlign: "center" }}>All PHI stays on your local network. Zero external data sharing.</p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div>
                  <div className="font-semibold text-white mb-1">
                    <p style={{ textAlign: "center" }}>🎯 85% Accuracy</p>
                  </div>
                  <div className="text-sm text-brand-100">
                    <p style={{ textAlign: "center" }}>AI-powered differential diagnoses with explainable reasoning.</p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div>
                  <div className="font-semibold text-white mb-1">
                    <p style={{ textAlign: "center" }}>🤝 Federated Learning</p>
                  </div>
                  <div className="text-sm text-brand-100">
                    <p style={{ textAlign: "center" }}>Improve together without sharing sensitive patient data.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10">
          <div className="text-sm text-brand-100">
            <p style={{ textAlign: "center" }}>Trusted by healthcare providers worldwide</p>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-surface-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo - deleted */}

          {/* Login Card */}
          <div className="card">
            <div className="mb-8">
              <h2 className="text-3xl font-display font-bold text-surface-900 mb-2">
                Welcome Back
              </h2>
              <p className="text-surface-600">
                Sign in with your hospital credentials
              </p>
            </div>

            {/* SSO Login Button */}
            <button
              onClick={handleLogin}
              className="btn btn-primary w-full btn-lg mb-6"
            >
              <span className="text-lg mr-2">🔐</span>
              Sign in with Keycloak SSO
            </button>

            {/* Divider */}
            <div className="divider"></div>

            {/* Trust Indicators */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm text-surface-600">
                <div className="w-5 h-5 rounded-full bg-success-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs">✓</span>
                </div>
                <span>Secure single sign-on authentication</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-surface-600">
                <div className="w-5 h-5 rounded-full bg-success-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs">✓</span>
                </div>
                <span>End-to-end encrypted connections</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-surface-600">
                <div className="w-5 h-5 rounded-full bg-success-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs">✓</span>
                </div>
                <span>HIPAA § 164.312 compliant access controls</span>
              </div>
            </div>
          </div>

          {/* Footer Links */}
          <div className="mt-8 text-center text-sm text-surface-500">
            <p>Need help? Contact IT Support</p>
          </div>
        </div>
      </div>
    </div>
  )
}
