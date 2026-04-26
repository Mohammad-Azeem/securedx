// SecureDx AI — Inference TypeScript Types
// Mirror of the backend Pydantic schemas

// Add this interface to the file
export interface InferenceRequest {
  patient_pseudo_id: string
  patient_age_years?: number
  patient_sex?: 'male' | 'female' | 'other' | 'unknown'
  lab_results?: any[]
  vital_signs?: any
  symptoms?: any[]
  medications?: any[]
  imaging_metadata?: any[]
  diagnosis_history?: any[]
}

export interface ShapFeature {
  feature_name: string
  feature_value: string
  shap_value: number
  direction: 'supporting' | 'opposing'
  magnitude: 'strong' | 'moderate' | 'weak'
}

export interface DiagnosisSuggestion {
  rank: number
  icd10_code: string
  icd10_display: string
  confidence: number
  confidence_label: 'High' | 'Moderate' | 'Low'
  evidence_narrative: string
  top_features: ShapFeature[]
  referral_recommended: boolean
  referral_specialty: string | null
  urgency: 'routine' | 'urgent' | 'emergent' | null
  drug_interaction_alert: string | null
}

export interface InferenceResponse {
  patient_pseudo_id: string
  encounter_id: string
  suggestions: DiagnosisSuggestion[]
  missing_data_prompts: string[]
  overall_confidence: number
  model_version: string
  inference_latency_ms: number
  disclaimer: string
  generated_at: string
}

export type FeedbackDecision = 'accept' | 'modify' | 'reject' | 'flag'

export interface FeedbackRequest {
  inference_id: string
  patient_pseudo_id: string
  decision: FeedbackDecision
  original_icd10_code: string
  corrected_icd10_code?: string
  quality_rating?: number
  reason_code?: string
  notes?: string
}

export interface FeedbackResponse {
  feedback_id: string
  inference_id: string
  decision: FeedbackDecision
  message: string
  queued_for_training: boolean
}
