// SecureDx AI — Authentication Hook
// Integrates with Keycloak for secure OIDC auth

import React from 'react'

import { createContext, useContext, useEffect, useState, ReactNode, useRef } from 'react'
import Keycloak from 'keycloak-js'
//import { createClient } from '@supabase/supabase-js'


const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost/auth'
const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'securedx'
const KEYCLOAK_CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'securedx-frontend'
const TOKEN_STORAGE_KEY = 'securedx_access_token'

/*
const supabase = createClient(
  'https://xxx.supabase.co',
  'your-anon-key'
)
*/

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  token: string | null
  login: () => void
  logout: () => void
  hasRole: (role: string) => boolean
}

interface User {
  id: string
  email: string
  fullName: string
  roles: string[]
  clinicId: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

let keycloakInstance: Keycloak | null = null

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)

  // Rule #1: Use a ref to prevent double-init in Strict Mode
  const isInitialized = useRef(false)

  useEffect(() => {
    if (isInitialized.current) return
    isInitialized.current = true

    const initKeycloak = async () => {
      try {
        if (!keycloakInstance) {
          keycloakInstance = new Keycloak({
            url: KEYCLOAK_URL,
            realm: KEYCLOAK_REALM,
            clientId: KEYCLOAK_CLIENT_ID,
          })
        }

        const authenticated = await keycloakInstance.init({
          onLoad: 'check-sso',
          silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
          pkceMethod: 'S256',
        })

        if (authenticated && keycloakInstance.tokenParsed) {
          const parsed = keycloakInstance.tokenParsed as any
          setUser({
            id: parsed.sub,
            email: parsed.email || '',
            fullName: parsed.name || parsed.preferred_username || '',
            roles: parsed.realm_access?.roles || [],
            clinicId: parsed.clinic_id || '',
          })
          const initialToken = keycloakInstance.token || null
          setToken(initialToken)
          if (initialToken) {
            localStorage.setItem(TOKEN_STORAGE_KEY, initialToken)
          }
          setIsAuthenticated(true)
          
          // Auto-refresh token
          setInterval(() => {
            keycloakInstance?.updateToken(70)
              .then((refreshed) => {
                const latestToken = keycloakInstance?.token || null
                setToken(latestToken)
                if (latestToken) {
                  localStorage.setItem(TOKEN_STORAGE_KEY, latestToken)
                }
                if (refreshed) {
                  console.debug('Token refreshed')
                }
              })
              .catch(() => {
                console.error('Failed to refresh token')
                logout()
              })
          }, 60000)
        } else {
          localStorage.removeItem(TOKEN_STORAGE_KEY)
        }
      } catch (error) {
        console.error('Keycloak init failed', error)
        localStorage.removeItem(TOKEN_STORAGE_KEY)
      } finally {
        setIsLoading(false)
      }
    }

    initKeycloak()
  }, [])

  const login = () => {
    keycloakInstance?.login()
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    keycloakInstance?.logout()
  }

  const hasRole = (role: string) => {
    return user?.roles.includes(role) || false
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        token,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}


export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

/*
// needs to be updated and implemented properly(other needs to be updated to use keycloak instead of supabase) --- IGNORE ---
// Hook for supabase auth for costless transition (to be removed after full Keycloak integration)
// Free tier of supabase allows 5000 monthly active users, which is sufficient for early stages and testing
// social login, email auth, row level security
export function useAuth() {
  const login = () => supabase.auth.signInWithPassword({
    email: 'user@example.com',
    password: 'password'
  })
  
  const logout = () => supabase.auth.signOut()
  
  return { login, logout }
}
*/

// Export keycloak instance for axios interceptor
export function getKeycloakToken(): string | undefined {
  return keycloakInstance?.token || localStorage.getItem(TOKEN_STORAGE_KEY) || undefined
}
