'use client'

import React, { useState, useEffect } from 'react'
import { Bird, Cog } from 'lucide-react'
import { Line, LineChart, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"

const TestItem = ({ name, variant, winner, improvement, conversions, visitors }: { 
  name: string; 
  variant: string; 
  winner: string;
  improvement: string;
  conversions: number;
  visitors: number;
}) => (
  <div className="mx-2 my-2 p-4 bg-white border border-gray-200 rounded-lg transition-all duration-200">
    <div className="flex justify-between items-start mb-3">
      <div className="flex-1">
        <p className="font-medium text-gray-900 mb-1">{name}</p>
        <p className="text-sm font-light text-gray-500">{variant}</p>
      </div>
      <div className="text-sm font-light text-gray-600">
        Winner: <span className="text-gray-900 font-medium">{winner}</span>
      </div>
    </div>
    <div className="flex gap-4 text-sm font-light text-gray-600 pt-3 border-t border-gray-100">
      <div className="flex items-center gap-1.5">
        <span className="text-green-600">{improvement}</span>
        <span>lift</span>
      </div>
      <div>
        <span className="text-gray-900">{conversions}</span> conv.
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
  <div className="mx-2 my-2 p-4 bg-white border border-gray-200 rounded-lg">
    <div className="flex items-start justify-between mb-2">
      <p className="font-medium text-gray-900">{modelName}</p>
      {status === 'active' && (
        <span className="bg-green-50 text-green-700 px-2 py-1 rounded-md font-light text-xs border border-green-200">Active</span>
      )}
    </div>
    <p className="text-xs font-light text-gray-500">{timestamp}</p>
  </div>
)

const page = () => {
  const [abTests, setAbTests] = useState<Array<{
    id: number;
    name: string;
    variant: string;
    winner: string;
    improvement: string;
    conversions: number;
    visitors: number;
  }>>([])
  const [fineTunes, setFineTunes] = useState<Array<{
    id: number;
    modelName: string;
    timestamp: string;
    status: string;
  }>>([])
  const [lossData, setLossData] = useState<Array<{
    epoch: number;
    loss: number;
  }>>([])
  const [isTraining, setIsTraining] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    fetch('http://localhost:8080/api/abtests')
      .then(response => response.json())
      .then(data => setAbTests(data))
      .catch(error => console.error('Error fetching A/B tests:', error))

    fetch('http://localhost:8080/api/finetunes')
      .then(response => response.json())
      .then(data => setFineTunes(data))
      .catch(error => console.error('Error fetching fine tunes:', error))

    fetch('http://localhost:8080/api/lossdata')
      .then(response => response.json())
      .then(data => setLossData(data))
      .catch(error => console.error('Error fetching loss data:', error))
  }, [])

  const handleFineTune = () => {
    setIsTraining(true)
    setProgress(0)
    setShowSuccess(false)
    
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
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="mx-auto px-8 py-5 flex items-center justify-between max-w-[1800px]">
          <div className="flex items-center gap-1">
            <span className="text-3xl font-light">Flywheel</span>
            <Bird strokeWidth={.7} className="w-9 h-9" />
          </div>
          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-88px)] max-w-[1800px] mx-auto">
        {/* Left Sidebar - A/B Tests */}
        <div className="w-96 flex-shrink-0 bg-white border-r border-gray-200 overflow-y-auto ">
          <div className="sticky top-0 bg-white z-10">
            <h2 className="text-xl font-light text-gray-900 pt-5 pb-2 px-5">A/B Tests</h2>
          </div>
          <div className="p-2">
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
        <div className="flex-1 flex flex-col overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Loss Function Chart */}
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="flex items-center justify-between p-5 border-b border-gray-200">
                <h2 className="text-xl font-light text-gray-900">Loss Function</h2>
                <div className="bg-green-50 text-green-700 px-4 py-2 rounded-md font-light text-base border border-green-200">
                  Loss: {lossData.length > 0 ? lossData[lossData.length - 1].loss : 0}
                </div>
              </div>
              <div className="w-full h-76 p-6 pr-12">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lossData}>
                    <XAxis dataKey="epoch" tick={false} />
                    <YAxis domain={['dataMin - 0.2', 'dataMax + 0.2']} tick={false}  axisLine={false} />
                    <Line type="monotone" dataKey="loss" stroke="#141414" strokeWidth={1} />
                    <Tooltip content={({ payload }) => {
                      if (payload && payload.length > 0) {
                        return (
                          <div className="bg-white border border-gray-300 p-2 rounded">
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
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="space-y-4">
                <div className="text-center">
                  <p className="text-base font-light h-7 flex items-center justify-center">
                    {isTraining && (
                      <span className="flex items-center justify-center text-gray-600 gap-2">
                        Tuning model...
                        <Cog className="w-5 h-5 animate-spin stroke-1" />
                      </span>
                    )}
                    {showSuccess && (
                      <span className="text-green-600 font-light">
                        flywheel-v1.5 is ready to use!
                      </span>
                    )}
                    {!isTraining && !showSuccess && (
                      <span className="text-gray-500">
                        Ready to tune
                      </span>
                    )}
                  </p>
                </div>
              
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 h-2.5 overflow-hidden rounded-full">
                  <div 
                    className="bg-gray-800 h-2.5 transition-all duration-200 ease-out rounded-full"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                
                <button 
                  onClick={handleFineTune}
                  disabled={isTraining}
                  className="w-full bg-black text-white py-3.5 text-base font-light rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isTraining ? 'Tuning...' : 'Fine Tune'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Fine Tune History */}
        <div className="w-96 flex-shrink-0 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="sticky top-0 bg-white z-10">
            <h2 className="text-xl font-light text-gray-900 pt-5 pb-2 px-5">Fine Tune History</h2>
          </div>
          <div className="p-2">
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