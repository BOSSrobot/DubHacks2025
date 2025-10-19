'use client'

import React, { useState, useEffect } from 'react'
import { Cog, RefreshCw } from 'lucide-react'
import { Line, LineChart, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"

const TestItem = ({ name, description, totalTests, avgImprovement, isSelected, onClick }: { 
  name: string; 
  description: string; 
  totalTests: number;
  avgImprovement: string;
  isSelected?: boolean;
  onClick?: () => void;
}) => (
  <div 
    onClick={onClick}
    className={`mx-2 my-2 p-4 bg-white border rounded-lg cursor-pointer transition-all duration-200 ${
      isSelected 
        ? 'border-gray-600 bg-gray-50 shadow-sm' 
        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
    }`}
  >
    <div className="mb-2">
      <p className="font-medium text-gray-900 mb-1">{name}</p>
      <p className="text-sm font-light text-gray-500">{description}</p>
    </div>
    <div className="flex justify-between items-center text-sm font-light text-gray-600 pt-3 border-t border-gray-100">
      <div>
        <span className="text-gray-900">{totalTests}</span> tests
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-green-600">{avgImprovement}</span>
        <span>avg lift</span>
      </div>
    </div>
  </div>
)

const FineTuneItem = ({ modelName, timestamp, isSelected, onClick}: { 
  modelName: string; 
  timestamp: string;
  isSelected?: boolean;
  onClick?: () => void;
}) => (
  <div 
    onClick={onClick}
    className={`mx-2 my-2 p-3 bg-white border rounded-lg cursor-pointer transition-all duration-200 ${
      isSelected 
        ? 'border-gray-600 bg-gray-50 shadow-sm' 
        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
    }`}
  >
    <div className="flex items-center justify-between">
      <p className="font-medium text-gray-900">{modelName}</p>
      <p className="text-xs font-light text-gray-500">{timestamp}</p>
    </div>
  </div>
)

const IndividualTest = ({ name, variant, winner, improvement }: { 
  name: string; 
  variant: string; 
  winner: string;
  improvement: string;
}) => (
  <div className="p-4 bg-white border border-gray-200 rounded-lg">
    <div className="flex justify-between items-start mb-3">
      <div className="flex-1">
        <p className="font-medium text-gray-900 mb-1">{name}</p>
        <p className="text-sm font-light text-gray-500">{variant}</p>
      </div>
    </div>
    <div className="flex gap-4 text-sm font-light text-gray-600 pt-3 border-t border-gray-100">
    <div>
        Winner: <span className="text-gray-900 font-medium">{winner}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-green-600">{improvement}</span>
        <span>lift</span>
      </div>
      
    </div>
  </div>
)

const page = () => {
  const [abTests, setAbTests] = useState<Array<{
    id: number;
    name: string;
    description: string;
    totalTests: number;
    avgImprovement: string;
    tests: Array<{
      id: number;
      name: string;
      variant: string;
      winner: string;
      improvement: string;
    }>;
  }>>([])
  const [baseModels, setBaseModels] = useState<Array<{
    id: number;
    modelName: string;
    timestamp: string;  
  }>>([])
  const [fineTunes, setFineTunes] = useState<Array<{
    id: number;
    modelName: string;
    timestamp: string;
  }>>([])
  const [lossData, setLossData] = useState<Array<{
    epoch: number;
    loss: number;
  }>>([])
  const [selectedModel, setSelectedModel] = useState<string>('flywheel-v1.4')
  const [selectedTestSet, setSelectedTestSet] = useState<number | null>(null)
  const [lastClicked, setLastClicked] = useState<'model' | 'testSet'>('model')
  const [isTraining, setIsTraining] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showSuccess, setShowSuccess] = useState(false)

  const isBaseModel = baseModels.some(model => model.modelName === selectedModel)
  
  const selectedTestSetData = abTests.find(testSet => testSet.id === selectedTestSet)

  useEffect(() => {
    fetch('http://localhost:8080/api/abtests')
      .then(response => response.json())
      .then(data => {
        setAbTests(data)
        if (data.length > 0) {
          setSelectedTestSet(data[0].id)
        }
      })
      .catch(error => console.error('Error fetching A/B tests:', error))

    fetch('http://localhost:8080/api/basemodels')
      .then(response => response.json())
      .then(data => setBaseModels(data))
      .catch(error => {
        console.error('Error fetching base models:', error)
      })

    fetch('http://localhost:8080/api/finetunes')
      .then(response => response.json())
      .then(data => setFineTunes(data))
      .catch(error => console.error('Error fetching fine tunes:', error))
  }, [])

  // Fetch loss data whenever selected model changes (only for tuned models)
  useEffect(() => {
    if (!isBaseModel) {
      fetch(`http://localhost:8080/api/lossdata?model=${selectedModel}`)
        .then(response => response.json())
        .then(data => setLossData(data))
        .catch(error => console.error('Error fetching loss data:', error))
    }
  }, [selectedModel, isBaseModel])

  const handleReloadTests = () => {
    //fetch('http://localhost:8080/api/abtests')
    console.log("placeholder")
  }

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
            <img src="/logo.png" alt="Flywheel" className="h-10" />
          </div>
          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-88px)] max-w-[1800px] mx-auto">
        {/* Left Sidebar - Models */}
        <div className="w-96 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
          {/* Base Models Section */}
          <div className="flex-shrink-0">
            <div className="bg-white border-b border-gray-200">
              <h2 className="text-xl font-light text-gray-900 pt-3 pb-2 px-5">Base Models</h2>
            </div>
            <div className="p-2">
              {baseModels.map((model) => (
                <FineTuneItem 
                  key={model.id} 
                  modelName={model.modelName} 
                  timestamp={model.timestamp}
                  isSelected={selectedModel === model.modelName}
                  onClick={() => {
                    setSelectedModel(model.modelName)
                    setLastClicked('model')
                  }}
                />
              ))}
            </div>
          </div>

          {/* Tuned Models Section */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="bg-white border-b border-gray-200">
              <h2 className="text-xl font-light text-gray-900 pt-3 pb-2 px-5">Tuned Models</h2>
            </div>
            <div className="p-2 overflow-y-auto flex-1 scrollbar-hide">
              {fineTunes.map((tune) => (
                <FineTuneItem 
                  key={tune.id} 
                  modelName={tune.modelName} 
                  timestamp={tune.timestamp}
                  isSelected={selectedModel === tune.modelName}
                  onClick={() => {
                    setSelectedModel(tune.modelName)
                    setLastClicked('model')
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Middle Sidebar - A/B Tests */}
        <div className="w-96 flex-shrink-0 bg-white border-r border-gray-200 overflow-y-auto ">
          <div className="sticky top-0 bg-white z-10 border-b border-gray-200">
            <div className="flex items-center justify-between pt-3 pb-2 pl-5 pr-3">
              <h2 className="text-xl font-light text-gray-900">A/B Test Sets</h2>
              <button
                onClick={handleReloadTests}
                className="p-1 hover:bg-gray-100 rounded-md transition-colors group"
                aria-label="Reload A/B tests"
              >
                <RefreshCw className="w-5 h-5 text-gray-600 transition-transform group-hover:rotate-180 duration-300" strokeWidth={1} />
              </button>
            </div>
          </div>
          <div className="p-2">
            {abTests.map((test) => (
              <TestItem 
                key={test.id} 
                name={test.name} 
                description={test.description}
                totalTests={test.totalTests}
                avgImprovement={test.avgImprovement}
                isSelected={selectedTestSet === test.id}
                onClick={() => {
                  setSelectedTestSet(test.id)
                  setLastClicked('testSet')
                }}
              />
            ))}
          </div>
        </div>

        {/* Right Panel - Graph and Fine Tune */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Test Details or Loss Function Chart */}
            {lastClicked === 'testSet' && selectedTestSetData ? (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="p-5 border-b border-gray-200">
                  <h2 className="text-xl font-light text-gray-900">{selectedTestSetData.name}</h2>
                  <p className="text-sm font-light text-gray-500 mt-1">{selectedTestSetData.description}</p>
                </div>
                <div className="h-76 overflow-y-auto p-6 space-y-4">
                  {selectedTestSetData.tests.map((test) => (
                    <IndividualTest
                      key={test.id}
                      name={test.name}
                      variant={test.variant}
                      winner={test.winner}
                      improvement={test.improvement}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="flex items-center justify-between p-5 border-b border-gray-200">
                  <div>
                    <h2 className="text-xl font-light text-gray-900">Loss Function</h2>
                    <p className="text-sm font-light text-gray-500 mt-1">{selectedModel}</p>
                  </div>
                  <div className={`px-4 py-2 rounded-md font-light text-base border ${
                    isBaseModel 
                      ? 'bg-gray-50 text-gray-500 border-gray-200' 
                      : 'bg-green-50 text-green-700 border-green-200'
                  }`}>
                    Loss: {isBaseModel ? '--' : (lossData.length > 0 ? lossData[lossData.length - 1].loss : 0)}
                  </div>
                </div>
                <div className="w-full h-76 p-6 pr-20">
                  {isBaseModel ? (
                    <div className="h-full flex items-center justify-center">
                      <p className="text-gray-500 font-light text-lg">Foundational Models Do Not Have Loss Function</p>
                    </div>
                  ) : (
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
                  )}
                </div>
              </div>
            )}

            {/* Fine Tune Control */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
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
      </div>
    </div>
  )
}

export default page