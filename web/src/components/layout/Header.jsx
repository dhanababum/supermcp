import React from 'react';
import { RoleIndicator } from '../common';

const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center text-white text-sm">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="font-semibold">JMobbin</span>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">Free</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                </svg>
              </div>
              <span className="text-gray-700">Issue overseas equity right</span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-2 bg-blue-50 text-blue-700 text-sm rounded-lg">
            <span className="font-semibold">33.</span>
            <span>Getting started 🚀</span>
          </div>
          <button className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white relative">
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-600 rounded-full"></span>
            🔔
          </button>
          <button className="p-2 hover:bg-gray-100 rounded-lg text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </button>
          <button className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
            Invite co-pilots
          </button>
          <button className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
            Upgrade
          </button>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Company</span>
            <span className="text-sm text-gray-700">Portal</span>
          </div>
          <RoleIndicator />
        </div>
      </div>
    </header>
  );
};

export default Header;

