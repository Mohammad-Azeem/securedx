// SecureDx AI — Feedback API

import { apiClient } from './apiClient'
import type { FeedbackRequest, FeedbackResponse } from '../types/inference'

export const feedbackApi = {
  /**
   * Submit physician feedback on a diagnosis
   */
  async submit(data: FeedbackRequest): Promise<FeedbackResponse> {
    const response = await apiClient.post<FeedbackResponse>('/feedback', data)
    return response.data
  },
}
