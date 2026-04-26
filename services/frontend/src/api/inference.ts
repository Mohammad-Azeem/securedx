// SecureDx AI — Inference API
// Typed API calls for diagnosis workflow

import { apiClient } from './apiClient'
import type { InferenceRequest, InferenceResponse } from '../types/inference'

export const inferenceApi = {
  /**
   * Run diagnostic analysis for a patient
   */
  async analyze(patientId: string, data?: Partial<InferenceRequest>): Promise<InferenceResponse> {
    const response = await apiClient.post<InferenceResponse>('/inference/analyze', {
      patient_pseudo_id: patientId,
      ...data,
    })
    return response.data
  },
}
