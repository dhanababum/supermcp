import React from 'react';

export const StatCard = ({ title, value, icon: Icon, colorClass }) => {
  const colorStyles = {
    blue: 'bg-brand-50 text-brand-500',
    green: 'bg-brand-50 text-brand-500',
    purple: 'bg-brand-100 text-brand-600',
    orange: 'bg-warning-50 text-warning-700',
  };

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-surface-500 mb-1">{title}</p>
          <p className="text-2xl font-semibold text-surface-900">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${colorStyles[colorClass] || colorStyles.blue}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};
