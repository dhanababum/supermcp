import React from 'react';

export const StatCard = ({ title, value, icon: Icon, colorClass }) => {
  // Map generic color names to specific semantic design tokens
  const colorStyles = {
    blue: 'bg-brand-50 text-brand-600',
    green: 'bg-success-50 text-success-700',
    purple: 'bg-brand-50 text-brand-700', // Mapping purple to brand for consistency or keeping distinct accent
    orange: 'bg-warning-50 text-warning-700',
  };

  return (
    <div className="card p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1 border-surface-200">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorStyles[colorClass] || colorStyles.blue} ring-1 ring-inset ring-black/5`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-surface-500">{title}</p>
          <p className="text-2xl font-semibold text-surface-900 mt-0.5 tracking-tight">{value}</p>
        </div>
      </div>
    </div>
  );
};
