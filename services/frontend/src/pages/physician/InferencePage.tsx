// services/frontend/src/pages/physician/InferencePage.tsx

import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { patientsApi } from '../../api/patients'
import { inferenceApi } from '../../api/inference'
import { feedbackApi } from '../../api/feedback'
import { useAuth } from '../../hooks/useAuth'
import { ShapChart } from '../../components/physician/ShapChart'
import { FeedbackDrawer } from '../../components/physician/FeedbackDrawer'
import type { InferenceResponse, FeedbackRequest } from '../../types/inference'

interface VitalSignsForm {
  temperature_f: number
  heart_rate_bpm: number
  respiratory_rate: number
  oxygen_saturation: number
  systolic_bp: number
  diastolic_bp: number
  cough: boolean
  fever: boolean
  fatigue: boolean
  chest_pain: boolean
  shortness_of_breath: boolean
}

// Beautiful Diagnosis Result Card
function DiagnosisCard({ result }: { result: InferenceResponse }) {
  if (!result.suggestions || result.suggestions.length === 0) return null

  const topSuggestion = result.suggestions[0]
  const confidence = (topSuggestion.confidence * 100).toFixed(0)

  return (
    <div className="card bg-gradient-to-br from-brand-500 to-brand-700 text-white animate-fade-in">
      <div className="flex items-start gap-6 mb-6">
        {/* Icon */}
        <div className="w-16 h-16 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center text-4xl flex-shrink-0">
          🎯
        </div>
        
        {/* Diagnosis Info */}
        <div className="flex-1">
          <h3 className="text-2xl font-display font-bold mb-2">
            {topSuggestion.icd10_display}
          </h3>
          <p className="text-brand-100 text-sm font-medium">
            ICD-10: {topSuggestion.icd10_code}
          </p>
        </div>

        {/* Confidence Badge */}
        <div className="text-right">
          <div className="text-5xl font-bold mb-1">{confidence}%</div>
          <div className="text-sm text-brand-100">Confidence</div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-6">
        <div className="h-3 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-white rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      {/* Evidence Narrative */}
      <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
        <div className="flex items-start gap-2 mb-2">
          <span className="text-xl">💡</span>
          <h4 className="font-semibold text-lg">Why this diagnosis?</h4>
        </div>
        <p className="text-brand-50 leading-relaxed">
          {topSuggestion.evidence_narrative}
        </p>
      </div>
    </div>
  )
}

// ADD this Progress Steps component

function ProgressSteps({ currentStep }: { currentStep: number }) {
  const steps = [
    { num: 1, label: 'Patient Info', icon: '👤' },
    { num: 2, label: 'Vital Signs', icon: '🩺' },
    { num: 3, label: 'Analysis', icon: '🔍' },
    { num: 4, label: 'Results', icon: '🎯' },
  ]

  return (
    <div className="card bg-surface-50">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <React.Fragment key={step.num}>
            <div className="flex flex-col items-center flex-1">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold transition-all ${
                  step.num <= currentStep
                    ? 'bg-brand-500 text-white shadow-lg scale-110'
                    : 'bg-surface-200 text-surface-500'
                }`}
              >
                {step.num < currentStep ? '✓' : step.icon}
              </div>
              <div
                className={`text-sm font-medium mt-2 ${
                  step.num <= currentStep ? 'text-brand-600' : 'text-surface-400'
                }`}
              >
                {step.label}
              </div>
            </div>
            {index < steps.length - 1 && (
              <div className="flex-1 h-1 bg-surface-200 mx-2">
                <div
                  className={`h-full transition-all duration-500 ${
                    step.num < currentStep ? 'bg-brand-500' : 'bg-surface-200'
                  }`}
                  style={{ width: step.num < currentStep ? '100%' : '0%' }}
                />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}

export default function InferencePage() {
  const { patientId } = useParams<{ patientId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { isAuthenticated, token } = useAuth()
  
  const [inferenceResult, setInferenceResult] = useState<InferenceResponse | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [currentStep, setCurrentStep] = useState(2) // Start at step 2 (vital signs)
  const suggestions = inferenceResult?.suggestions ?? []


  // Fetch patients 
  const { data: patient, isLoading: patientLoading } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => patientsApi.get(patientId!),
    enabled: !!patientId && isAuthenticated && !!token,
  })

  // Form : collect vital signs and symptoms
  const { register, handleSubmit, formState: { errors } } = useForm<VitalSignsForm>({
    defaultValues: {
      temperature_f: 98.6,
      heart_rate_bpm: 75,
      respiratory_rate: 16,
      oxygen_saturation: 98,
      systolic_bp: 120,
      diastolic_bp: 80,
      cough: false,
      fever: false,
      fatigue: false,
      chest_pain: false,
      shortness_of_breath: false,
    },
  })

  // Inference mutation
  const inferenceMutation = useMutation({
    mutationFn: (data: VitalSignsForm) => {
      const symptoms = []
      if (data.cough) symptoms.push({ snomed_code: '49727002', display_name: 'Cough' })
      if (data.fever) symptoms.push({ snomed_code: '386661006', display_name: 'Fever' })
      if (data.fatigue) symptoms.push({ snomed_code: '84229001', display_name: 'Fatigue' })
      if (data.chest_pain) symptoms.push({ snomed_code: '29857009', display_name: 'Chest pain' })
      if (data.shortness_of_breath) symptoms.push({ snomed_code: '267036007', display_name: 'Shortness of breath' })

      return inferenceApi.analyze(patientId!, {
        vital_signs: {
          temperature_celsius: Number(((data.temperature_f - 32) * (5 / 9)).toFixed(1)),
          heart_rate: data.heart_rate_bpm,
          respiratory_rate: data.respiratory_rate,
          spo2_percent: data.oxygen_saturation,
          systolic_bp: data.systolic_bp,
          diastolic_bp: data.diastolic_bp,
        },
        symptoms,
      })
    },
    // AI responds On success, store the inference result and show the feedback drawer
    onSuccess: (data) => {
      setInferenceResult(data)
      setShowFeedback(true)
      setCurrentStep(4) // Move to results step
    },
  })

  // Feedback mutation - submit physician feedback on the inference results
  const feedbackMutation = useMutation({
    mutationFn: (feedback: FeedbackRequest) => feedbackApi.submit(feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      navigate('/physician/patients')
    },
  })

  //submit handler for the form: send data to (AI) inference API and get results
  const onSubmit = (data: VitalSignsForm) => {
    setCurrentStep(3) // Move to analysis step
    inferenceMutation.mutate(data)
  }

  const handleFeedbackSubmit = (feedback: FeedbackRequest) => {
    feedbackMutation.mutate(feedback)
  }

  if (patientLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="alert alert-danger">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <h4 className="font-semibold mb-1">Patient not found</h4>
            <p className="text-sm">Unable to load patient data.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Patient Header */}
      <div className="card bg-gradient-to-r from-surface-50 to-surface-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-xl shadow-lg">
              {patient.display_name
                ? patient.display_name.split(' ').map(n => n[0]).join('').slice(0, 2)
                : '?'}
            </div>
            <div>
              <h1 className="text-3xl font-display font-bold text-surface-900">
                {patient.display_name}
              </h1>
              <p className="text-surface-600 mt-1">
                {patient.age_years}y • {patient.sex} • ID: {(patient.pseudo_id || patientId || '').slice(0, 8)}...
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/physician/patients')}
            className="btn btn-ghost"
          >
            ← Back
          </button>
        </div>
      </div>

      {/* ADD THIS: Progress Steps */}
      <ProgressSteps currentStep={currentStep} />

      {/* Vital Signs Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="card">
        <h2 className="text-2xl font-display font-bold text-surface-900 mb-6">
          Clinical Assessment
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Vital Signs */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-surface-700 mb-4 flex items-center gap-2">
              <span>🩺</span> Vital Signs
            </h3>
            
            <div className="input-group">
              <label className="input-label">Temperature (°F)</label>
              <input
                type="number"
                step="0.1"
                {...register('temperature_f', { required: true, min: 95, max: 110 })}
                className={`input-field ${errors.temperature_f ? 'input-error' : ''}`}
              />
              {errors.temperature_f && (
                <p className="input-error-message">Must be between 95-110°F</p>
              )}
            </div>

            <div className="input-group">
              <label className="input-label">Heart Rate (bpm)</label>
              <input
                type="number"
                {...register('heart_rate_bpm', { required: true, min: 40, max: 200 })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Respiratory Rate (per min)</label>
              <input
                type="number"
                {...register('respiratory_rate', { required: true, min: 8, max: 40 })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Oxygen Saturation (%)</label>
              <input
                type="number"
                {...register('oxygen_saturation', { required: true, min: 70, max: 100 })}
                className="input-field"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="input-group">
                <label className="input-label">Systolic BP</label>
                <input
                  type="number"
                  {...register('systolic_bp', { required: true, min: 80, max: 200 })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Diastolic BP</label>
                <input
                  type="number"
                  {...register('diastolic_bp', { required: true, min: 40, max: 130 })}
                  className="input-field"
                />
              </div>
            </div>
          </div>

          {/* Symptoms */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-surface-700 mb-4 flex items-center gap-2">
              <span>📋</span> Symptoms
            </h3>
            
            {[
              { name: 'cough', label: 'Cough', icon: '🤧' },
              { name: 'fever', label: 'Fever', icon: '🌡️' },
              { name: 'fatigue', label: 'Fatigue', icon: '😴' },
              { name: 'chest_pain', label: 'Chest Pain', icon: '💔' },
              { name: 'shortness_of_breath', label: 'Shortness of Breath', icon: '🫁' },
            ].map((symptom) => (
              <label
                key={symptom.name}
                className="flex items-center gap-3 p-4 border-2 border-surface-200 rounded-xl hover:border-brand-300 hover:bg-brand-50 cursor-pointer transition-all"
              >
                <input
                  type="checkbox"
                  {...register(symptom.name as any)}
                  className="w-5 h-5 text-brand-600 rounded border-surface-300 focus:ring-2 focus:ring-brand-500"
                />
                <span className="text-xl">{symptom.icon}</span>
                <span className="font-medium text-surface-700">{symptom.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-8 flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/physician/patients')}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={inferenceMutation.isPending}
            className="btn btn-primary btn-lg"
          >
            {inferenceMutation.isPending ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Analyzing...
              </>
            ) : (
              <>
                <span className="text-xl">🔍</span>
                Run Diagnostic Analysis
              </>
            )}
          </button>
        </div>

        {inferenceMutation.isError && (
          <div className="alert alert-danger mt-4">
            <p>Failed to run inference. Please try again.</p>
          </div>
        )}
      </form>

      {/* Diagnosis Result */}
      {inferenceResult && <DiagnosisCard result={inferenceResult} />}

      {/* Alternative Diagnoses */}
      {inferenceResult && suggestions.length > 1 && (
        <div className="card">
          <h3 className="text-xl font-display font-bold text-surface-900 mb-4">
            Alternative Diagnoses
          </h3>
          <div className="space-y-3">
            {suggestions.slice(1, 4).map((suggestion, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 bg-surface-50 border-2 border-surface-200 rounded-xl hover:border-brand-300 transition-colors"
              >
                <div>
                  <div className="font-semibold text-surface-900">
                    {suggestion.icd10_display}
                  </div>
                  <div className="text-sm text-surface-500 mt-1">
                    ICD-10: {suggestion.icd10_code}
                  </div>
                </div>
                <div className="text-2xl font-bold text-brand-600">
                  {(suggestion.confidence * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SHAP Chart */}
      {inferenceResult && suggestions[0]?.top_features && (
        <div className="card">
          <h3 className="text-xl font-display font-bold text-surface-900 mb-4">
            Feature Importance
          </h3>
          <ShapChart
            shapValues={Object.fromEntries(
              (suggestions[0]?.top_features ?? []).map((f) => [
                f.feature_name,
                f.shap_value,
              ])
            )}
            topN={8}
          />
        </div>
      )}

      {/* Feedback Drawer */}
      {showFeedback && inferenceResult && suggestions.length > 0 && (
        <FeedbackDrawer
          inferenceId={inferenceResult.encounter_id}
          patientPseudoId={inferenceResult.patient_pseudo_id}
          topSuggestion={suggestions[0]}
          onSubmit={handleFeedbackSubmit}
          isSubmitting={feedbackMutation.isPending}
        />
      )}
    </div>
  )
}
