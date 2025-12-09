import React from 'react';
import { RoleIndicator } from '../common';

const Header = () => {
  return (
    <header className="bg-white border-b border-surface-200 px-6 py-4 shadow-soft z-20">
      <div className="flex items-center justify-between">
        {/* Left: Breadcrumbs / Context (Placeholder) */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
             <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 font-bold text-xs border border-brand-200">
               JM
             </div>
             <div className="flex flex-col">
                <span className="text-sm font-semibold text-surface-900 leading-tight">JMobbin</span>
                <span className="text-xs text-surface-500">Free Plan</span>
             </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-4">
          {/* Action Buttons */}
          <div className="hidden md:flex items-center space-x-2">
             <button className="btn-secondary text-xs py-1.5 h-8">
               Invite Team
             </button>
             <button className="btn-primary text-xs py-1.5 h-8 bg-brand-600 hover:bg-brand-700">
               Upgrade
             </button>
          </div>

          <div className="h-6 w-px bg-surface-200 mx-2"></div>

          {/* Notifications */}
          <button className="p-2 text-surface-400 hover:text-surface-600 hover:bg-surface-50 rounded-full relative transition-colors">
            <span className="absolute top-2 right-2 w-2 h-2 bg-error-500 rounded-full border-2 border-white"></span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          
          <RoleIndicator />
        </div>
      </div>
    </header>
  );
};

export default Header;
