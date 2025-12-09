import React from 'react';
import { InfoIcon } from '../../../components/icons';

const CompanyStats = () => {
  const stats = [
    { icon: '👥', iconBg: 'bg-brand-100', iconColor: 'text-brand-600', value: '2', label: 'Stakeholders', 
      svg: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /> 
    },
    { icon: '⏰', iconBg: 'bg-blue-100', iconColor: 'text-blue-600', value: '30', label: 'Total shares',
      svg: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    },
    { icon: '📄', iconBg: 'bg-green-100', iconColor: 'text-green-600', value: '38', label: 'Total securities',
      svg: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    },
    { icon: '💰', iconBg: 'bg-yellow-100', iconColor: 'text-yellow-600', value: '$100', label: 'Valuation',
      svg: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    },
    { icon: '🧮', iconBg: 'bg-blue-100', iconColor: 'text-blue-600', value: '$2.63157', label: 'Share price',
      svg: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    }
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="space-y-6">
        {stats.map((stat, index) => (
          <div key={index} className={`flex items-center space-x-3 ${index < stats.length - 1 ? 'pb-4 border-b border-gray-100' : ''}`}>
            <div className={`w-10 h-10 ${stat.iconBg} rounded-lg flex items-center justify-center`}>
              <svg className={`w-6 h-6 ${stat.iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {stat.svg}
              </svg>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900">{stat.value}</div>
              <div className="text-sm text-gray-500 flex items-center space-x-1">
                <span>{stat.label}</span>
                <InfoIcon />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CompanyStats;

