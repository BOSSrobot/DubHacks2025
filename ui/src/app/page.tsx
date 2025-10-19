'use client'

import React, { useState } from 'react'
import { Bird, User } from 'lucide-react'
import { Line, LineChart, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"

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

// Sample loss data for the loss function graph
const lossData = [
  { epoch: 1, loss: 2.45 },
  { epoch: 2, loss: 2.12 },
  { epoch: 3, loss: 1.89 },
  { epoch: 4, loss: 1.75 },
  { epoch: 5, loss: 1.58 },
  { epoch: 6, loss: 1.42 },
  { epoch: 7, loss: 1.31 },
  { epoch: 8, loss: 1.18 },
]

const TestItem = ({ name, variant, winner, improvement, conversions, visitors }: { 
  name: string; 
  variant: string; 
  winner: string;
  improvement: string;
  conversions: number;
  visitors: number;
}) => (
  <div className="py-4 px-3 flex flex-col gap-3 border-b border-gray-200 last:border-0">
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
  <div className="py-4 px-3 flex justify-between items-center border-b border-gray-200 last:border-0">
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
    <div className="bg-gray-100 min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <span className="text-3xl font-light">Flywheel</span>
            <Bird strokeWidth={.7} className="w-9 h-9" />
          </div>
          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300 transition-colors cursor-pointer">
            <User strokeWidth={1.5} className="w-5 h-5 text-gray-600" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-88px)]">
        {/* Left Sidebar - A/B Tests */}
        <div className="w-80 flex-shrink-0 bg-white border-r border-gray-300 overflow-y-auto">
          <h2 className="text-xl font-light text-gray-900 p-4 border-b border-gray-300">A/B Tests</h2>
          <div>
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

        {/* Center Panel - Graph and Fine Tune */}
        <div className="flex-1 flex flex-col bg-white">
          {/* Loss Function Chart */}
          <div className="flex-1 border-b border-gray-300">
            <h2 className="text-xl font-light text-gray-900 p-4 border-b border-gray-300">Loss Function</h2>
            <div className="w-full h-1/2 py-4 pr-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lossData}>
                  <XAxis dataKey="epoch" tick={false} />
                  <YAxis domain={['dataMin - 0.2', 'dataMax + 0.2']} tick={false} axisLine={false} />
                  <Line type="monotone" dataKey="loss" stroke="#000000" strokeWidth={1} />
                  <Tooltip content={({ payload }) => {
                    if (payload && payload.length > 0) {
                      return (
                        <div className="bg-white border border-gray-300 p-2 rounded shadow">
                          <p className="text-gray-900 text-sm">
                            <span className="font-medium">Epoch:</span> {payload[0].payload.epoch}<br />
                            <span className="font-medium">Loss:</span> {payload[0].value}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Fine Tune Control */}
          <div className="p-4 border-b border-gray-300">
            <div className="space-y-3">
              <p className="text-sm font-light text-center h-5">
                {isTraining && (
                  <span className="text-gray-600">
                    Tuning model: {progress}%
                  </span>
                )}
                {showSuccess && (
                  <span className="text-green-600 font-light">
                    flywheel-v1.5 is ready to use!
                  </span>
                )}
                {!isTraining && !showSuccess && (
                  <span className="text-gray-500">
                    Ready to tune...
                  </span>
                )}
              </p>
            
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 h-2 overflow-hidden rounded-lg">
                <div 
                  className="bg-gray-700 h-2 transition-all duration-200 ease-out rounded-lg"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <button 
                onClick={handleFineTune}
                disabled={isTraining}
                className="w-full bg-black text-white py-3 font-light  rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isTraining ? 'Tuning...' : 'Fine Tune'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Fine Tune History */}
        <div className="w-80 flex-shrink-0 bg-white border-l border-gray-300 overflow-y-auto">
          <h2 className="text-xl font-light text-gray-900 p-4 border-b border-gray-300">Fine Tune History</h2>
          <div>
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
    </div>
  )
}

export default page