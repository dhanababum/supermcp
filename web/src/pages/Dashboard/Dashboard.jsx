import React from 'react';
import { CompanyStats, OwnershipChart, ActivityPanel, FundingRounds, TotalOptions } from './components';

const Dashboard = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">JMobbin</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <CompanyStats />
        <OwnershipChart />
        <ActivityPanel />
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <FundingRounds />
        <TotalOptions />
      </div>
    </div>
  );
};

export default Dashboard;

