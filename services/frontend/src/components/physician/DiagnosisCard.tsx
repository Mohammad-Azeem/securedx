// SecureDx AI — DiagnosisCard Component
// Displays a single differential diagnosis with confidence, urgency,
// evidence narrative, and physician feedback controls.

import type { DiagnosisSuggestion } from '../../types/inference'

interface Props {
  suggestion: DiagnosisSuggestion
  isSelected: boolean
  onSelect: () => void
  onFeedback: () => void
}

const URGENCY_CONFIG = {
  emergent: { label: 'EMERGENT', bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
  urgent:   { label: 'URGENT',   bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300' },
  routine:  { label: 'Routine',  bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
} as const

const CONFIDENCE_COLOR = (score: number) => {
  if (score >= 0.80) return 'bg-green-500'
  if (score >= 0.60) return 'bg-amber-500'
  return 'bg-red-400'
}

export function DiagnosisCard({ suggestion, isSelected, onSelect, onFeedback }: Props) {
  const urgency = URGENCY_CONFIG[suggestion.urgency as keyof typeof URGENCY_CONFIG] ?? URGENCY_CONFIG.routine
  const confidencePct = Math.round(suggestion.confidence * 100)

  return (
    <div
      className={`
        rounded-xl border-2 transition-all duration-150 cursor-pointer
        ${isSelected
          ? 'border-blue-500 shadow-md bg-blue-50'
          : 'border-gray-200 hover:border-gray-300 bg-white hover:shadow-sm'
        }
      `}
      onClick={onSelect}
    >
      {/* Card Header */}
      <div className="px-5 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Rank + ICD-10 */}
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex-shrink-0">
                {suggestion.rank}
              </span>
              <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {suggestion.icd10_code}
              </span>
              {suggestion.urgency !== 'routine' && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${urgency.bg} ${urgency.text} ${urgency.border}`}>
                  {urgency.label}
                </span>
              )}
            </div>

            {/* Diagnosis name */}
            <h3 className="text-base font-semibold text-gray-900 leading-tight">
              {suggestion.icd10_display}
            </h3>
          </div>

          {/* Confidence badge */}
          <div className="text-right flex-shrink-0">
            <span className={`text-lg font-bold ${
              suggestion.confidence >= 0.8 ? 'text-green-600' :
              suggestion.confidence >= 0.6 ? 'text-amber-600' : 'text-red-500'
            }`}>
              {confidencePct}%
            </span>
            <p className="text-xs text-gray-400">{suggestion.confidence_label}</p>
          </div>
        </div>

        {/* Confidence progress bar */}
        <div className="mt-3 w-full bg-gray-100 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${CONFIDENCE_COLOR(suggestion.confidence)}`}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
      </div>

      {/* Evidence Narrative (collapsed unless selected) */}
      {isSelected && (
        <div className="px-5 pb-4 border-t border-blue-100 mt-0">
          <div className="mt-3">
            <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">
              📋 Evidence Rationale
            </p>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {suggestion.evidence_narrative}
            </p>
          </div>

          {/* Referral flag */}
          {suggestion.referral_recommended && suggestion.referral_specialty && (
            <div className="mt-3 flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-md px-3 py-2">
              <span className="text-purple-600">🏥</span>
              <p className="text-sm text-purple-800">
                <strong>Referral considered:</strong> {suggestion.referral_specialty}
                {suggestion.urgency === 'urgent' && ' (Urgent)'}
              </p>
            </div>
          )}

          {/* Drug interaction alert */}
          {suggestion.drug_interaction_alert && (
            <div className="mt-2 flex items-start gap-2 bg-red-50 border border-red-200 rounded-md px-3 py-2">
              <span className="text-red-500 mt-0.5">⚠️</span>
              <p className="text-sm text-red-800">{suggestion.drug_interaction_alert}</p>
            </div>
          )}
        </div>
      )}

      {/* Action bar — always visible */}
      <div
        className="px-5 py-3 border-t border-gray-100 flex items-center gap-2"
        onClick={(e) => e.stopPropagation()}  // Prevent card collapse on button click
      >
        <button
          onClick={() => onFeedback()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-md hover:bg-green-700 transition-colors"
          title="Accept this diagnosis"
        >
          ✓ Accept
        </button>
        <button
          onClick={() => onFeedback()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 transition-colors"
          title="Accept with modifications"
        >
          ✏️ Modify
        </button>
        <button
          onClick={() => onFeedback()}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 text-gray-600 text-xs font-medium rounded-md hover:bg-gray-50 transition-colors"
          title="Reject this suggestion"
        >
          ✕ Reject
        </button>
        <button
          onClick={() => onFeedback()}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-amber-300 text-amber-700 text-xs font-medium rounded-md hover:bg-amber-50 transition-colors ml-auto"
          title="Flag for quality review"
        >
          🚩 Flag
        </button>
      </div>
    </div>
  )
}
