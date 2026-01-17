import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { MenuIcon, ChevronRightIcon, SuperMCPLightIcon } from '../icons';
import { navigationItems } from '../../constants/navigation';
import { API_BASE_URL } from '../../constants/env';

const Sidebar = ({ collapsed, onToggleCollapse }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const getCurrentRoute = () => {
    const path = location.pathname;
    if (path.startsWith('/servers') || path === '/servers') return 'servers';
    if (path.startsWith('/server-tools')) return 'server-tools';
    if (path.startsWith('/connectors')) return 'connectors';
    if (path.startsWith('/mcp-client')) return 'mcp-client';
    return 'dashboard';
  };
  
  const currentRoute = getCurrentRoute();
  
  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/cookie/logout`, {
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
    <div className={`${collapsed ? 'w-20' : 'w-64'} bg-white border-r border-surface-200 transition-all duration-300 flex flex-col shadow-sidebar`}>
      {/* Logo and Toggle */}
      <div className={`flex items-center h-16 px-4 border-b border-surface-100 ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed && <SuperMCPLightIcon className="h-7" />}
        {collapsed && <SuperMCPLightIcon className="h-7 w-7" />}
        <button
          onClick={onToggleCollapse}
          className={`p-2 rounded-lg hover:bg-surface-100 text-surface-400 hover:text-surface-600 transition-all duration-200 ${collapsed ? 'mt-2' : ''}`}
        >
          <MenuIcon />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-5 overflow-y-auto">
        <div className="space-y-1">
          {navigationItems.map((item) => {
            const isActive = currentRoute === item.route;
            return (
              <Link
                key={item.id}
                to={`/${item.route}`}
                className={`relative flex items-center ${collapsed ? 'justify-center' : ''} px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group ${
                  isActive
                    ? 'bg-brand-50 text-brand-600 font-medium'
                    : 'text-surface-600 hover:bg-surface-50 hover:text-surface-900'
                }`}
                title={collapsed ? item.name : ''}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-brand-500 rounded-r-full" />
                )}
                <span className={`flex-shrink-0 ${isActive ? 'text-brand-500' : 'text-surface-400 group-hover:text-surface-600'} transition-colors`}>
                  <item.icon />
                </span>
                {!collapsed && (
                  <span className="ml-3">{item.name}</span>
                )}
                {!collapsed && item.hasSubmenu && (
                  <ChevronRightIcon className={`ml-auto w-4 h-4 ${isActive ? 'text-brand-500' : 'text-surface-400'}`} />
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Logout Button */}
      <div className="p-3 border-t border-surface-100">
        <button
          onClick={handleLogout}
          className={`w-full flex items-center ${collapsed ? 'justify-center' : ''} px-3 py-2.5 rounded-lg text-sm transition-all duration-200 text-surface-500 hover:text-error-600 hover:bg-error-50`}
          title={collapsed ? 'Logout' : ''}
        >
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          {!collapsed && <span className="ml-3 font-medium">Logout</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
