import React from 'react';

const FundingRounds = () => {
  return (
    <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Funding rounds</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Bootstrapped</span>
          <button className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
            Update
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-purple-600">▼</span>
              <span className="text-gray-700">$20.00 committed</span>
            </div>
          </div>
          <div className="relative">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-purple-600 to-purple-400" style={{ width: '0%' }}></div>
            </div>
            <div className="absolute left-0 top-0 h-2 w-0 border-l-2 border-purple-600"></div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-700">$0.00 committed</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-900">$110.00 Raise goal</span>
            <span className="text-sm text-purple-600 font-medium">23 days left</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FundingRounds;

