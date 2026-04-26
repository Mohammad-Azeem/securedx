// SecureDx AI — Inference Type Definitions

/*
For an interviewer:
Shared types between frontend and backend.
In production, these would be auto-generated from OpenAPI spec
or shared via a monorepo package.

Benefits:
- Type safety across API boundary
- IDE autocomplete
- Compile-time error detection
- Self-documenting code
*/

export interface InferenceRequest {
  patient_pseudo_id: string
  vital_signs?: {
    temperature_f?: number
    heart_rate_bpm?: number
    respiratory_rate?: number
    oxygen_saturation?: number
    systolic_bp?: number
    diastolic_bp?: number
  }
  symptoms?: string[]
  lab_results?: Record<string, number>
}

export interface DiagnosisSuggestion {
  icd10_code: string
  diagnosis_name: string
  confidence: number
  rank: number
  supporting_features: Record<string, number>  // SHAP values
}

export interface InferenceResponse {
  inference_id: string
  patient_pseudo_id: string
  suggestions: DiagnosisSuggestion[]
  overall_confidence: number
  model_version: string
  evidence_narrative: string
  top_features: Array<{
    feature: string
    importance: number
  }>
  missing_features: string[]
}

export interface FeedbackRequest {
  inference_id: string
  decision: 'accept' | 'modify' | 'reject' | 'flag'
  modified_diagnosis_code?: string
  modified_diagnosis_name?: string
  physician_notes?: string
}

export interface FeedbackResponse {
  feedback_id: string
  queued_for_fl: boolean
  message: string
}
