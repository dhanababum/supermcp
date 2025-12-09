import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const RoleIndicator = () => {
  const { user, isSuperuser } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center space-x-3 pl-4 border-l border-surface-200">
      <div className={`px-2.5 py-0.5 text-xs font-semibold rounded-full tracking-wide ${
        isSuperuser() 
          ? 'bg-brand-100 text-brand-700 border border-brand-200' 
          : 'bg-surface-100 text-surface-700 border border-surface-200'
      }`}>
        {isSuperuser() ? 'SUPERUSER' : 'USER'}
      </div>
      <span className="text-sm font-medium text-surface-600">{user.email}</span>
    </div>
  );
};

export default RoleIndicator;
