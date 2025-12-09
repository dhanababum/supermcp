import React from 'react';

const OwnershipChart = () => {
  const stakeholders = [
    { name: 'Jon Smith', initials: 'JS', percentage: '68.42%', color: 'bg-blue-500' },
    { name: 'Jane Smith', initials: 'JS', percentage: '10.52%', color: 'bg-blue-400' },
    { name: 'Unallocated Options', initials: 'UO', percentage: '21.05%', color: 'bg-blue-300' }
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Ownership</h2>
          <p className="text-sm text-gray-500">Equity distribution in your company</p>
        </div>
        <button className="text-sm text-brand-600 font-medium hover:text-brand-700">
          Download cap table
        </button>
      </div>

      {/* Donut Chart */}
      <div className="flex justify-center mb-6">
        <div className="relative w-48 h-48">
          <svg viewBox="0 0 100 100" className="transform -rotate-90">
            {/* Green segment (Jon Smith - 68.42%) */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="#a3e635"
              strokeWidth="20"
              strokeDasharray="171 251"
              strokeDashoffset="0"
            />
            {/* Yellow segment (Unallocated - 21.05%) */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="#fde047"
              strokeWidth="20"
              strokeDasharray="53 251"
              strokeDashoffset="-171"
            />
            {/* Blue segment (Jane Smith - 10.52%) */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="#60a5fa"
              strokeWidth="20"
              strokeDasharray="27 251"
              strokeDashoffset="-224"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-4xl">🎂</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-4 mb-6">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-300 rounded-full"></div>
          <span className="text-xs text-gray-600">Fully Diluted</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-lime-400 rounded-full"></div>
          <span className="text-xs text-gray-600">Undiluted</span>
        </div>
      </div>

      {/* Top Stakeholders */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Stakeholders</h3>
        <div className="space-y-3">
          {stakeholders.map((stakeholder, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-8 h-8 ${stakeholder.color} rounded-full flex items-center justify-center text-white text-xs font-semibold`}>
                  {stakeholder.initials}
                </div>
                <span className="text-sm text-gray-700">{stakeholder.name}</span>
              </div>
              <span className="text-sm font-semibold text-gray-900">{stakeholder.percentage}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OwnershipChart;

