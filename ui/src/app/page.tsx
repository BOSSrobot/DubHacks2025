'use client'

import React, { useState } from 'react'
import { Bird } from 'lucide-react'

const abTests = [
  { id: 1, name: 'Hero CTA Button', variant: 'A vs B', winner: 'B', improvement: '+12.3%', conversions: 287, visitors: 2431 },
  { id: 2, name: 'Navigation Layout', variant: 'A vs B', winner: 'A', improvement: '+8.7%', conversions: 412, visitors: 4102 },
  { id: 3, name: 'Color Scheme', variant: 'A vs B', winner: 'B', improvement: '+15.2%', conversions: 198, visitors: 1823 },
  { id: 4, name: 'Pricing Display', variant: 'A vs B', winner: 'B', improvement: '+9.4%', conversions: 121, visitors: 1089 },
]

const fineTunes = [
  { id: 0, modelName: 'flywheel-v1.4', timestamp: '2025-10-19 14:23:15', status: 'active' },
  { id: 1, modelName: 'flywheel-v1.3', timestamp: '2025-10-19 14:23:15', status: 'archived' },
  { id: 2, modelName: 'flywheel-v1.2', timestamp: '2025-10-19 14:23:15', status: 'archived' },
  { id: 3, modelName: 'flywheel-v1.1', timestamp: '2025-10-18 09:42:33', status: 'archived' },
  { id: 4, modelName: 'flywheel-v1.0', timestamp: '2025-10-18 8:15:08', status: 'archived' },
]

const TestItem = ({ name, variant, winner, improvement, conversions, visitors }: { 
  name: string; 
  variant: string; 
  winner: string;
  improvement: string;
  conversions: number;
  visitors: number;
}) => (
  <div className="py-4 px-3 flex flex-col gap-3 border-b border-gray-200 last:border-0 hover:bg-gray-50 transition-colors rounded">
    <div className="flex justify-between items-start">
      <div className="flex-1">
        <p className="font-light text-gray-900">{name}</p>
        <p className="text-sm font-light text-gray-500">{variant}</p>
      </div>
      <div className="text-sm font-light text-gray-600">
        Winner: <span className="text-gray-900">{winner}</span>
      </div>
    </div>
    <div className="flex gap-4 text-xs font-light text-gray-600">
      <div className="flex items-center gap-1">
        <span className="text-green-600 font-medium">{improvement}</span>
        <span>improvement</span>
      </div>
      <div>
        <span className="text-gray-900">{conversions}</span> conversions
      </div>
      <div>
        <span className="text-gray-900">{visitors.toLocaleString()}</span> visitors
      </div>
    </div>
  </div>
)

const FineTuneItem = ({ modelName, timestamp, status }: { 
  modelName: string; 
  timestamp: string;
  status: string;
}) => (
  <div className="py-4 px-3 flex justify-between items-center border-b border-gray-200 last:border-0 hover:bg-gray-50 transition-colors rounded">
    <div className="flex items-center gap-2">
      <p className="font-light text-gray-900">{modelName}</p>
      {status === 'active' && (
        <span className="text-xs font-light bg-green-100 text-green-700 px-2 py-0.5 rounded">Active</span>
      )}
    </div>
    <p className="text-xs font-light text-gray-500">{timestamp}</p>
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
    <div className="bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="mx-auto px-6 py-5 flex items-center gap-1">
          <span className="text-4xl font-light">Flywheel</span>
          <Bird strokeWidth={.7} className="w-10 h-10" />
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* A/B Tests Section */}
          <div className="bg-white border border-gray-200 rounded-sm shadow-sm p-5 hover:shadow-md transition-shadow">
            <h2 className="text-xl font-light mb-6 text-gray-900 pb-2 border-b border-gray-100">A/B Tests</h2>
            <div className="space-y-1">
              {abTests.map((test) => (
                <TestItem 
                  key={test.id} 
                  name={test.name} 
                  variant={test.variant} 
                  winner={test.winner}
                  improvement={test.improvement}
                  conversions={test.conversions}
                  visitors={test.visitors}
                />
              ))}
            </div>
          </div>

          {/* Fine Tune History Section */}
          <div className="bg-white border border-gray-200 rounded-sm shadow-sm p-5 hover:shadow-md transition-shadow">
            <h2 className="text-xl font-light mb-6 text-gray-900 pb-2 border-b border-gray-100">Fine Tune History</h2>
            <div className="space-y-1">
              {fineTunes.map((tune) => (
                <FineTuneItem 
                  key={tune.id} 
                  modelName={tune.modelName} 
                  timestamp={tune.timestamp}
                  status={tune.status}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Fine Tune Card */}
        <div className="mt-6 bg-white border border-gray-200 rounded-sm shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="space-y-4">
            <p className="text-sm font-light text-center h-5">
              {isTraining && (
                <span className="text-gray-600">
                  Tuning model: {progress}%
                </span>
              )}
              {showSuccess && (
                <span className="text-green-600 font-light">
                  flywheel-v1.3 is ready to use!
                </span>
              )}
              {!isTraining && !showSuccess && (
                <span className="text-gray-500">
                  Ready to tune...
                </span>
              )}
            </p>
          
            {/* Progress Bar */}
            <div className="w-full bg-gray-200  h-2.5 overflow-hidden shadow-inner">
              <div 
                className="bg-gray-700 h-2.5  transition-all duration-200 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <button 
              onClick={handleFineTune}
              disabled={isTraining}
              className="w-full bg-white text-black border border-gray-300 py-4 rounded-lg font-light text-lg hover:bg-gray-50 transition-all disabled:opacity-80 disabled:cursor-not-allowed"
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