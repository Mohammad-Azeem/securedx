// SecureDx AI — Loading Screen

import React from 'react'

interface Props {
  message?: string
}

export function LoadingScreen({ message = 'Loading...' }: Props) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="animate-spin w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full mb-4" />
      <p className="text-gray-600 font-medium">{message}</p>
    </div>
  )
}
