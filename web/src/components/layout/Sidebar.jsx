import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { MenuIcon, InfoIcon, ChevronRightIcon, SuperMCPIcon } from '../icons';
import { navigationItems } from '../../constants/navigation';

const Sidebar = ({ collapsed, onToggleCollapse }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get current route from location
  const getCurrentRoute = () => {
    const path = location.pathname;
    if (path.startsWith('/servers') || path === '/servers') return 'servers';
    if (path.startsWith('/server-tools')) return 'server-tools';
    if (path.startsWith('/connectors')) return 'connectors';
    if (path.startsWith('/mcp-client')) return 'mcp-client';
    if (path.startsWith('/oauth/callback')) return 'oauth-callback';
    return 'dashboard';
  };
  
  const currentRoute = getCurrentRoute();
  
  const handleLogout = async () => {
    try {
      await fetch('http://localhost:9000/auth/cookie/logout', {
        method: 'POST',
        credentials: 'include',
      });
      navigate('/auth/login');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/auth/login');
    }
  };
  return (
    <div className={`${collapsed ? 'w-16' : 'w-64'} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}>
      {/* Logo and Toggle */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!collapsed ? (
          <div className="flex items-center space-x-2">
            <SuperMCPIcon className="w-8 h-8" />
            <span className="font-semibold text-lg">SuperMCP</span>
          </div>
        ) : (
          <div className="flex items-center justify-center w-full">
            <SuperMCPIcon className="w-8 h-8" />
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
            <Link
              key={item.id}
              to={`/${item.route}`}
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
            </Link>
          ))}
        </div>
      </nav>

      {/* Logout Button */}
      <div className="p-3 border-t border-gray-200">
        <button
          onClick={handleLogout}
          className={`w-full flex items-center ${collapsed ? 'justify-center' : 'justify-start'} px-3 py-2 rounded-lg text-sm transition-colors text-red-600 hover:bg-red-50`}
          title={collapsed ? 'Logout' : ''}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          {!collapsed && <span className="ml-3">Logout</span>}
        </button>
      </div>

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

