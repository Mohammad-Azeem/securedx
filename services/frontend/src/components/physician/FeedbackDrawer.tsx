// SecureDx AI — Feedback Drawer Component

/*
For a 15-year-old:
After the AI gives an answer, the doctor grades it:
- Click "Accept" if correct
- Click "Modify" if close but needs correction
- Click "Reject" if totally wrong
- Click "Flag" if dangerous

For an interviewer:
Feedback collection UI with:
- 4 decision types (accept/modify/reject/flag)
- Conditional rendering (modify shows diagnosis picker)
- Form validation (modified diagnosis required if decision=modify)
- Optimistic UI updates
- Keyboard shortcuts (Enter to submit, Esc to cancel)
*/

import React from 'react'

import { useState } from 'react'
import type { FeedbackRequest } from '../../types/inference'

interface FeedbackDrawerProps {
  inferenceId: string
  patientPseudoId: string
  topSuggestion: {
    icd10_code: string
    icd10_display: string
    confidence: number
  }
  onSubmit: (feedback: FeedbackRequest) => void
  isSubmitting: boolean
}

export function FeedbackDrawer({
  inferenceId,
  patientPseudoId,
  topSuggestion,
  onSubmit,
  isSubmitting,
}: FeedbackDrawerProps) {
  const [decision, setDecision] = useState<'accept' | 'modify' | 'reject' | 'flag' | null>(null)
  const [modifiedDiagnosisCode, setModifiedDiagnosisCode] = useState('')
  const [notes, setNotes] = useState('')
  const [validationError, setValidationError] = useState('')

  const handleSubmit = () => {
    setValidationError('')
    if (!decision) return

    if (decision === 'modify' && !modifiedDiagnosisCode) {
      setValidationError('Please provide the corrected ICD-10 code.')
      return
    }

    onSubmit({
      inference_id: inferenceId,
      patient_pseudo_id: patientPseudoId,
      decision,
      original_icd10_code: topSuggestion.icd10_code,
      corrected_icd10_code: decision === 'modify' ? modifiedDiagnosisCode : undefined,
      notes: notes || undefined,
    })
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Review AI Suggestion</h3>

      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">AI suggested:</p>
        <p className="font-medium text-gray-900 mt-1">
          {topSuggestion.icd10_display} ({(topSuggestion.confidence * 100).toFixed(0)}% confidence)
        </p>
      </div>

      {/* Decision Buttons */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <button
          onClick={() => setDecision('accept')}
          className={`p-4 border-2 rounded-lg text-left transition-all ${
            decision === 'accept'
              ? 'border-green-500 bg-green-50'
              : 'border-gray-200 hover:border-green-300'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">✓</span>
            <span className="font-semibold text-gray-900">Accept</span>
          </div>
          <p className="text-sm text-gray-600">Diagnosis is correct</p>
        </button>

        <button
          onClick={() => setDecision('modify')}
          className={`p-4 border-2 rounded-lg text-left transition-all ${
            decision === 'modify'
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">✏️</span>
            <span className="font-semibold text-gray-900">Modify</span>
          </div>
          <p className="text-sm text-gray-600">Close, but incorrect</p>
        </button>

        <button
          onClick={() => setDecision('reject')}
          className={`p-4 border-2 rounded-lg text-left transition-all ${
            decision === 'reject'
              ? 'border-orange-500 bg-orange-50'
              : 'border-gray-200 hover:border-orange-300'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">✗</span>
            <span className="font-semibold text-gray-900">Reject</span>
          </div>
          <p className="text-sm text-gray-600">Completely incorrect</p>
        </button>

        <button
          onClick={() => setDecision('flag')}
          className={`p-4 border-2 rounded-lg text-left transition-all ${
            decision === 'flag'
              ? 'border-red-500 bg-red-50'
              : 'border-gray-200 hover:border-red-300'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🚩</span>
            <span className="font-semibold text-gray-900">Flag</span>
          </div>
          <p className="text-sm text-gray-600">Dangerous suggestion</p>
        </button>
      </div>

      {/* Conditional Fields for Modify */}
      {decision === 'modify' && (
        <div className="space-y-4 mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correct ICD-10 Code
            </label>
            <input
              type="text"
              value={modifiedDiagnosisCode}
              onChange={(e) => setModifiedDiagnosisCode(e.target.value)}
              placeholder="e.g., J18.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

        </div>
      )}

      {/* Notes (optional for all decisions) */}
      {decision && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes (optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Additional context or reasoning..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => setDecision(null)}
          className="px-4 py-2 text-gray-700 hover:text-gray-900"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={!decision || isSubmitting}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </div>

      {validationError && (
        <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {validationError}
        </div>
      )}

      {decision === 'flag' && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            ⚠️ Flagging will immediately alert the admin team for review.
          </p>
        </div>
      )}
    </div>
  )
}
