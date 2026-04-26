// SecureDx AI — API Client
// Axios instance with Keycloak token injection

import axios from 'axios'
import { getKeycloakToken } from '../hooks/useAuth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: inject auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = getKeycloakToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired - Keycloak will handle redirect
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
