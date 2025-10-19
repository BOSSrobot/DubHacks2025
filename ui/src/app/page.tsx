import React from 'react'
import { Bird } from 'lucide-react'

const abTests = [
  { id: 1, name: 'Hero CTA Button', variant: 'A vs B', winner: 'B' },
  { id: 2, name: 'Navigation Layout', variant: 'A vs B', winner: 'A' },
  { id: 3, name: 'Color Scheme', variant: 'A vs B', winner: 'B'},
  { id: 4, name: 'Pricing Display', variant: 'A vs B', winner: 'B'},
]

const page = () => {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-6">
      <div className="bg-white border border-gray-500 w-full max-w-3xl p-8">
        {/* Logo */}
        <div className="flex items-center gap-1 mb-8">
          <span className="text-4xl font-light">Flywheel</span>
          <Bird strokeWidth={.7} className="w-11 h-11" />
        </div>

        {/* A/B Tests Section */}
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4 text-gray-900">A/B Tests</h2>
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Test Name</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Variants</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Winner</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {abTests.map((test) => (
                  <tr key={test.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm text-gray-900">{test.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{test.variant}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{test.winner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Fine Tune Button */}
        <button className="w-full bg-white text-black py-3 border border-gray-500 font-light hover:bg-gray-100 transition-colors">
          Fine Tune
        </button>
      </div>
    </div>
  )
}

export default page