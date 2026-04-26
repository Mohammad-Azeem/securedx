// SecureDx AI — SHAP Visualization Component

/*
For a 15-year-old:
This is the "Why?" chart. It shows the AI's reasoning:
- Long blue bars = "This made me MORE confident"
- Long red bars = "This made me LESS confident"
- Short bars = "This didn't matter much"

For an interviewer:
Interactive bar chart visualizing SHAP (Shapley) values:
- Positive values: Feature increases probability of diagnosis
- Negative values: Feature decreases probability
- Sorted by absolute value (most important first)
- Color-coded: Blue (positive), red (negative)
- Tooltip shows exact contribution value
*/

import React from 'react'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Label,
} from 'recharts'

interface ShapChartProps {
  shapValues: Record<string, number>
  topN?: number
}

export function ShapChart({ shapValues, topN = 10 }: ShapChartProps) {
  // Convert to array and sort by absolute value
  const data = Object.entries(shapValues)
    .map(([feature, value]) => ({
      feature: formatFeatureName(feature),
      value: value,
      absValue: Math.abs(value),
    }))
    .sort((a, b) => b.absValue - a.absValue)
    .slice(0, topN)
    .reverse() // Reverse so most important is at top

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      const impact = data.value > 0 ? 'increases' : 'decreases'
      const color = data.value > 0 ? 'text-blue-600' : 'text-red-600'
      
      return (
        <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
          <p className="font-medium text-gray-900">{data.feature}</p>
          <p className={`text-sm ${color} mt-1`}>
            {impact} confidence by {Math.abs(data.value * 100).toFixed(1)}%
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-3">
      <div>
        <h3 className="font-semibold text-gray-900">Feature Importance</h3>
        <p className="text-sm text-gray-600 mt-1">
          How each factor contributed to this diagnosis
        </p>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[-0.5, 0.5]}>
            <Label value="Impact on Confidence" position="bottom" />
          </XAxis>
          <YAxis dataKey="feature" type="category" width={110} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.value > 0 ? '#2563eb' : '#dc2626'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-600 rounded" />
          <span className="text-gray-600">Supports diagnosis</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-600 rounded" />
          <span className="text-gray-600">Against diagnosis</span>
        </div>
      </div>
    </div>
  )
}

/**
 * Convert technical feature names to human-readable labels.
 * 
 * For a 15-year-old:
 * Turns computer code like "temperature_f" into "Temperature"
 * 
 * For an interviewer:
 * Maps feature names to display labels.
 * Could be externalized to config for i18n support.
 */
function formatFeatureName(feature: string): string {
  const mapping: Record<string, string> = {
    temperature_f: 'Temperature',
    heart_rate_bpm: 'Heart Rate',
    respiratory_rate: 'Resp. Rate',
    oxygen_saturation: 'Oxygen Sat.',
    systolic_bp: 'Systolic BP',
    diastolic_bp: 'Diastolic BP',
    has_cough: 'Cough',
    has_fever: 'Fever',
    has_fatigue: 'Fatigue',
    has_chest_pain: 'Chest Pain',
    has_shortness_breath: 'SOB',
    age_years: 'Age',
    is_male: 'Male',
  }

  return mapping[feature] || feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}
