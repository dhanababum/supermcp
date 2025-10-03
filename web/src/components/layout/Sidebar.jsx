import React from 'react';
import { MenuIcon, InfoIcon, ChevronRightIcon } from '../icons';
import { navigationItems } from '../../constants/navigation';

const Sidebar = ({ collapsed, onToggleCollapse, currentRoute, onRouteChange }) => {
  return (
    <div className={`${collapsed ? 'w-16' : 'w-64'} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}>
      {/* Logo and Toggle */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!collapsed && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white font-bold text-sm">
              C
            </div>
            <span className="font-semibold text-lg">Cake.</span>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <MenuIcon />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 overflow-y-auto">
        <div className="space-y-1">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onRouteChange(item.route)}
              className={`w-full flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-3 py-2 rounded-lg text-sm transition-colors ${
                currentRoute === item.route
                  ? 'bg-purple-50 text-purple-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              title={collapsed ? item.name : ''}
            >
              <div className="flex items-center space-x-3">
                <span className={currentRoute === item.route ? 'text-purple-600' : 'text-gray-500'}>
                  <item.icon />
                </span>
                {!collapsed && <span>{item.name}</span>}
              </div>
              {!collapsed && item.hasSubmenu && (
                <ChevronRightIcon />
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* What's New Section */}
      {!collapsed && (
        <div className="p-4 border-t border-gray-200">
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-3 border border-purple-200">
            <div className="text-purple-700 text-sm font-semibold mb-2">✨ What's New</div>
            <div className="space-y-2 text-xs text-gray-600">
              <div className="flex items-center space-x-2">
                <InfoIcon />
                <span>2FA security</span>
              </div>
              <div className="flex items-center space-x-2">
                <InfoIcon />
                <span>Bare trusts & SPVs</span>
              </div>
              <div className="flex items-center space-x-2">
                <InfoIcon />
                <span>Reporting</span>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-400">version: 0d5ba1f5</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;

