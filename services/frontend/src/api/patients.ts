// SecureDx AI — Patients API

import { apiClient } from './apiClient'

export interface Patient {
  pseudo_id: string
  display_name: string  // Pseudonymous display like "Patient A123"
  age_years: number | null
  sex: 'male' | 'female' | 'other' | 'unknown'
  last_visit_date: string | null
  status: 'active' | 'inactive'
}

export const patientsApi = {
  /**
   * Get today's patient schedule
   */
  async list(): Promise<Patient[]> {
    const response = await apiClient.get<Patient[]>('/patients')
    return response.data
  },

  /**
   * Get patient details (de-identified)
   */
  async get(patientId: string): Promise<Patient> {
    const response = await apiClient.get<Patient>(`/patients/${patientId}`)
    return response.data
  },
}
