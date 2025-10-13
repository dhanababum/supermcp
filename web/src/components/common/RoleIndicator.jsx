import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const RoleIndicator = () => {
  const { user, isSuperuser } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center space-x-2">
      <div className={`px-2 py-1 text-xs font-medium rounded-full ${
        isSuperuser() 
          ? 'bg-purple-100 text-purple-700' 
          : 'bg-blue-100 text-blue-700'
      }`}>
        {isSuperuser() ? 'Superuser' : 'User'}
      </div>
      <span className="text-sm text-gray-600">{user.email}</span>
    </div>
  );
};

export default RoleIndicator;
