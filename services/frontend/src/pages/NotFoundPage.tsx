// SecureDx AI — 404 Page

import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="card max-w-lg w-full text-center">
        <div className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-sm font-semibold mb-6">
          Error 404
        </div>
        <h1 className="text-5xl font-display font-bold text-surface-900 mb-3">
          Page not found
        </h1>
        <p className="text-surface-600 mb-8">
          This route does not exist anymore, or your session redirected to an outdated URL.
        </p>
        <Link
          to="/"
          className="btn btn-primary btn-lg"
        >
          Go to dashboard
        </Link>
      </div>
    </div>
  )
}
