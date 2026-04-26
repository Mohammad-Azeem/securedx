// services/frontend/src/pages/HelpPage.tsx

import React from 'react'

import { useState } from 'react'

export default function HelpPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const faqs = [
    {
      category: 'Getting Started',
      icon: '🚀',
      questions: [
        {
          q: 'How do I start a diagnostic analysis?',
          a: 'Navigate to the Patient List, select a patient, then fill in their vital signs and symptoms. Click "Run Diagnostic Analysis" to get AI-powered suggestions.',
        },
        {
          q: 'What does the confidence percentage mean?',
          a: 'The confidence percentage indicates how certain the AI is about a particular diagnosis based on the input data. Higher percentages indicate stronger matches with known patterns.',
        },
      ],
    },
    {
      category: 'Privacy & Security',
      icon: '🔒',
      questions: [
        {
          q: 'Is patient data secure?',
          a: 'Yes! All patient data remains on your local network. No PHI ever leaves your clinic. We are fully HIPAA §164.312 compliant.',
        },
        {
          q: 'What is the PHI Boundary?',
          a: 'The PHI Boundary ensures that all Protected Health Information stays within your local infrastructure and is never transmitted to external servers.',
        },
      ],
    },
    {
      category: 'AI Features',
      icon: '🤖',
      questions: [
        {
          q: 'How accurate is the AI?',
          a: 'Our AI maintains 85% diagnostic accuracy across common conditions. It improves over time through federated learning while maintaining patient privacy.',
        },
        {
          q: 'Can I provide feedback on diagnoses?',
          a: 'Absolutely! After each analysis, you can Accept, Modify, or Flag the AI\'s suggestions. This feedback helps improve the model for everyone.',
        },
      ],
    },
  ]

  const filteredFAQs = faqs.map((category) => ({
    ...category,
    questions: category.questions.filter(
      (q) =>
        q.q.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.a.toLowerCase().includes(searchTerm.toLowerCase())
    ),
  })).filter((category) => category.questions.length > 0)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="text-6xl mb-4">📚</div>
        <h1 className="text-4xl font-display font-bold text-surface-900 mb-3">
          Help Center
        </h1>
        <p className="text-xl text-surface-600">
          Find answers to common questions and learn how to use SecureDx AI
        </p>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <input
            type="text"
            placeholder="Search for help..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-12 text-lg"
          />
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-surface-400 text-2xl">
            🔍
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { icon: '📖', title: 'User Guide', desc: 'Step-by-step tutorials' },
          { icon: '🎥', title: 'Video Tutorials', desc: 'Watch and learn' },
          { icon: '💬', title: 'Contact Support', desc: 'Get personalized help' },
        ].map((link, i) => (
          <button key={i} className="card card-interactive text-left">
            <div className="text-4xl mb-3">{link.icon}</div>
            <h3 className="font-semibold text-surface-900 mb-1">{link.title}</h3>
            <p className="text-sm text-surface-600">{link.desc}</p>
          </button>
        ))}
      </div>

      {/* FAQs */}
      <div className="space-y-6">
        {filteredFAQs.map((category, i) => (
          <div key={i} className="card">
            <h2 className="text-2xl font-display font-bold text-surface-900 mb-4 flex items-center gap-3">
              <span className="text-3xl">{category.icon}</span>
              {category.category}
            </h2>
            <div className="space-y-4">
              {category.questions.map((item, j) => (
                <details key={j} className="group">
                  <summary className="cursor-pointer p-4 bg-surface-50 hover:bg-surface-100 rounded-xl transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-surface-900">
                        {item.q}
                      </span>
                      <span className="text-brand-500 group-open:rotate-180 transition-transform">
                        ▼
                      </span>
                    </div>
                  </summary>
                  <div className="p-4 text-surface-700 leading-relaxed">
                    {item.a}
                  </div>
                </details>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Still Need Help */}
      <div className="card bg-gradient-to-br from-brand-500 to-brand-700 text-white text-center">
        <h3 className="text-2xl font-bold mb-3">Still need help?</h3>
        <p className="text-brand-100 mb-6">
          Our support team is here to assist you
        </p>
        <button className="btn bg-white text-brand-600 hover:bg-brand-50">
          Contact IT Support
        </button>
      </div>
    </div>
  )
}
