import React from 'react';

const TotalOptions = () => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Total options</h2>
        <span className="px-2 py-1 bg-brand-100 text-brand-700 text-xs font-medium rounded">1 pool</span>
      </div>

      <div className="mb-4">
        <div className="text-2xl font-bold text-gray-900 mb-1">0%</div>
        <div className="text-sm text-gray-500">▼ Allocated</div>
      </div>

      <div className="relative h-2 bg-gray-200 rounded-full mb-4">
        <div className="absolute h-full bg-brand-600 rounded-full" style={{ width: '0%' }}></div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-900">8</span>
        <span className="text-sm text-gray-600">Total options</span>
      </div>
    </div>
  );
};

export default TotalOptions;

