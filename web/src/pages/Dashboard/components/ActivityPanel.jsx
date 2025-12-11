import React from 'react';
import { ChevronRightIcon } from '../../../components/icons';

const ActivityPanel = () => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Activity</h2>
        <p className="text-sm text-gray-500">Last 30 days vs Previous</p>
      </div>

      <div className="flex items-center justify-between py-4 border-b border-gray-100">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
            🔔
          </div>
          <span className="text-sm font-semibold text-gray-900">1</span>
          <span className="text-sm text-gray-600">ACTION ITEMS</span>
        </div>
        <ChevronRightIcon />
      </div>

      <div className="space-y-6 mt-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Options vested</span>
            <span className="text-sm text-gray-900">-</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Options granted</span>
            <span className="text-sm text-gray-900">-</span>
          </div>
        </div>

        <div>
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-2xl font-bold text-gray-900">2</span>
            <span className="text-green-600">📈</span>
          </div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Offers created</span>
            <span className="text-sm text-gray-900">-</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Offers signed</span>
            <span className="text-sm text-gray-900">-</span>
          </div>
        </div>

        <div>
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-2xl font-bold text-gray-900">2</span>
            <span className="text-green-600">📈</span>
          </div>
          <div className="text-sm text-gray-600">Announcements sent</div>
        </div>
      </div>
    </div>
  );
};

export default ActivityPanel;

