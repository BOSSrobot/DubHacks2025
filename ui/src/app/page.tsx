'use client'

import React, { useState } from 'react'
import { Bird } from 'lucide-react'

const abTests = [
  { id: 1, name: 'Hero CTA Button', variant: 'A vs B', winner: 'B' },
  { id: 2, name: 'Navigation Layout', variant: 'A vs B', winner: 'A' },
  { id: 3, name: 'Color Scheme', variant: 'A vs B', winner: 'B'},
  { id: 4, name: 'Pricing Display', variant: 'A vs B', winner: 'B'},
]

const fineTunes = [
  { id: 1, modelName: 'flywheel-v1.2', timestamp: '2025-10-19 14:23:15' },
  { id: 2, modelName: 'flywheel-v1.1', timestamp: '2025-10-18 09:42:33' },
  { id: 3, modelName: 'flywheel-v1.0', timestamp: '2025-10-18 8:15:08' },
]

const TestItem = ({ name, variant, winner }: { name: string; variant: string; winner: string }) => (
  <div className="py-3 flex justify-between items-center border-b border-gray-200 last:border-0">
    <div className="flex-1">
      <p className="font-light text-gray-900">{name}</p>
      <p className="text-sm font-light text-gray-500">{variant}</p>
    </div>
    <div className="text-sm font-light text-gray-600">
      Winner: <span className="text-gray-900">{winner}</span>
    </div>
  </div>
)

const FineTuneItem = ({ modelName, timestamp }: { modelName: string; timestamp: string }) => (
  <div className="py-3 flex justify-between items-center border-b border-gray-200 last:border-0">
    <p className="font-light text-gray-900">{modelName}</p>
    <p className="text-sm font-light text-gray-500">{timestamp}</p>
  </div>
)

const page = () => {
  const [isTraining, setIsTraining] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showSuccess, setShowSuccess] = useState(false)

  const handleFineTune = () => {
    setIsTraining(true)
    setProgress(0)
    setShowSuccess(false)
    
    // Simulate training progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsTraining(false)
          setShowSuccess(true)
          setTimeout(() => {
            setShowSuccess(false)
            setProgress(0)
          }, 3000)
          return 100
        }
        return prev + 2
      })
    }, 100)
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-300">
        <div className="mx-auto px-6 py-4 flex items-center gap-1">
          <span className="text-5xl font-light">Flywheel</span>
          <Bird strokeWidth={.7} className="w-14 h-14" />
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* A/B Tests Section */}
          <div className="border border-gray-300 p-6">
            <h2 className="text-xl font-light mb-6 text-gray-900">A/B Tests</h2>
            <div className="space-y-0">
              {abTests.map((test) => (
                <TestItem key={test.id} name={test.name} variant={test.variant} winner={test.winner} />
              ))}
            </div>
          </div>

          {/* Fine Tune History Section */}
          <div className="border border-gray-300 p-6">
            <h2 className="text-xl font-light mb-6 text-gray-900">Fine Tune History</h2>
            <div className="space-y-0">
              {fineTunes.map((tune) => (
                <FineTuneItem key={tune.id} modelName={tune.modelName} timestamp={tune.timestamp} />
              ))}
            </div>
          </div>
        </div>

        {/* Fine Tune Card */}
        <div className="mt-8 border border-gray-300 p-6">
           {/* Status Text - Always reserves space */}
          <div className="space-y-4">
           <p className="text-sm font-light text-center h-5">
              {isTraining && (
                <span className="text-gray-600">
                  Tuning model: {progress}%
                </span>
              )}
              {showSuccess && (
                <span className="text-green-600">
                  ✓ Model fine-tuned successfully!
                </span>
              )}
              {!isTraining && !showSuccess && (
                <span className="text-gray-600">
                  Ready to tune...
                </span>
              )}
            </p>
          
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div 
                className="bg-black h-2 rounded-full transition-all duration-200 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <button 
              onClick={handleFineTune}
              disabled={isTraining}
              className="w-full bg-white text-black py-4 border border-gray-500 font-light text-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isTraining ? 'Tuning...' : 'Fine Tune'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default page