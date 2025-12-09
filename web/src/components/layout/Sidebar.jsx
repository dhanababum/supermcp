import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { MenuIcon, ChevronRightIcon, SuperMCPIcon } from '../icons';
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
    <div className={`${collapsed ? 'w-16' : 'w-64'} bg-gradient-to-b from-white to-slate-50 border-r border-slate-200 transition-all duration-300 flex flex-col shadow-sm`}>
      {/* Logo and Toggle */}
      <div className={`flex items-center p-5 border-b border-slate-200 bg-white ${collapsed ? 'justify-center flex-col space-y-3' : 'justify-between'}`}>
        {!collapsed ? (
          <>
            <div className="flex items-center space-x-3">
               <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-brand-600 rounded-xl flex items-center justify-center">
                 <SuperMCPIcon className="w-5 h-5 text-white" />
               </div>
               <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">SuperMCP</span>
            </div>
            <button
              onClick={onToggleCollapse}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-all duration-200"
            >
              <MenuIcon />
            </button>
          </>
        ) : (
          <>
            <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-brand-600 rounded-xl flex items-center justify-center">
               <SuperMCPIcon className="w-5 h-5 text-white" />
            </div>
            <button
              onClick={onToggleCollapse}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-all duration-200"
            >
              <MenuIcon />
            </button>
          </>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-1">
          {navigationItems.map((item) => {
             const isActive = currentRoute === item.route;
             return (
              <Link
                key={item.id}
                to={`/${item.route}`}
                className={`relative w-full flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-4 py-3 text-sm transition-all duration-200 group ${
                  isActive
                    ? 'text-brand-600'
                    : 'text-slate-600 hover:text-brand-600'
                }`}
                title={collapsed ? item.name : ''}
              >
                <div className="flex items-center space-x-3 relative">
                  <span className={`${isActive ? 'text-brand-600' : 'text-slate-500 group-hover:text-brand-600'} transition-colors`}>
                    <item.icon />
                  </span>
                  {!collapsed && (
                    <span className={`font-medium ${isActive ? 'font-semibold' : ''}`}>
                      {item.name}
                    </span>
                  )}
                </div>
                {!collapsed && item.hasSubmenu && (
                  <ChevronRightIcon className={`w-4 h-4 ${isActive ? 'text-brand-600' : 'text-slate-400'}`} />
                )}
                {/* Elegant underline for active item */}
                {isActive && (
                  <div className="absolute bottom-0 left-3 right-3 h-0.5 bg-gradient-to-r from-brand-500 to-brand-400 rounded-full" />
                )}
                {/* Subtle hover effect */}
                {!isActive && (
                  <div className="absolute inset-0 bg-slate-100 opacity-0 group-hover:opacity-100 rounded-lg transition-opacity duration-200 -z-10" />
                )}
              </Link>
            );
          })}
      </nav>

      {/* Logout Button */}
      <div className="p-3 border-t border-slate-200 bg-white">
        <button
          onClick={handleLogout}
          className={`w-full flex items-center ${collapsed ? 'justify-center' : 'justify-start'} px-4 py-3 rounded-lg text-sm transition-all duration-200 text-slate-600 hover:text-error-600 hover:bg-error-50 group`}
          title={collapsed ? 'Logout' : ''}
        >
          <svg className="w-5 h-5 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          {!collapsed && <span className="ml-3 font-medium">Logout</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
