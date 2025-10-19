import React from 'react'
import { Bird } from 'lucide-react'

const page = () => {
  return (
    <div className="flex items-center gap-1 items-center">
      <span className="text-2xl font-light">Flywheel</span>
      <Bird strokeWidth={1} className="w-8 h-8" />
    </div>
  )
}

export default page