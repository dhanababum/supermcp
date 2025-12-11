import React from 'react';

const SuperMCPIcon = ({ className = "w-8 h-8", ...props }) => {
  return (
    <svg 
      className={className} 
      viewBox="0 0 32 32" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      {/* Background circle with gradient */}
      <defs>
        <linearGradient id="superMCPGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="100%" stopColor="#3B82F6" />
        </linearGradient>
        <linearGradient id="connectorGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#10B981" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>
      </defs>
      
      {/* Main background circle */}
      <circle cx="16" cy="16" r="15" fill="url(#superMCPGradient)" stroke="white" strokeWidth="1"/>
      
      {/* Central hub/processor */}
      <rect x="12" y="12" width="8" height="8" rx="2" fill="white" opacity="0.9"/>
      
      {/* Connection lines */}
      <line x1="16" y1="4" x2="16" y2="10" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <line x1="16" y1="22" x2="16" y2="28" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <line x1="4" y1="16" x2="10" y2="16" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <line x1="22" y1="16" x2="28" y2="16" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      
      {/* Diagonal connections */}
      <line x1="6.5" y1="6.5" x2="11" y2="11" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
      <line x1="25.5" y1="6.5" x2="21" y2="11" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
      <line x1="6.5" y1="25.5" x2="11" y2="21" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
      <line x1="25.5" y1="25.5" x2="21" y2="21" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
      
      {/* Connection nodes */}
      <circle cx="16" cy="6" r="2" fill="url(#connectorGradient)"/>
      <circle cx="16" cy="26" r="2" fill="url(#connectorGradient)"/>
      <circle cx="6" cy="16" r="2" fill="url(#connectorGradient)"/>
      <circle cx="26" cy="16" r="2" fill="url(#connectorGradient)"/>
      
      {/* Corner nodes */}
      <circle cx="8" cy="8" r="1.5" fill="white" opacity="0.8"/>
      <circle cx="24" cy="8" r="1.5" fill="white" opacity="0.8"/>
      <circle cx="8" cy="24" r="1.5" fill="white" opacity="0.8"/>
      <circle cx="24" cy="24" r="1.5" fill="white" opacity="0.8"/>
      
      {/* Central processor detail */}
      <rect x="13" y="13" width="6" height="6" rx="1" fill="url(#superMCPGradient)" opacity="0.8"/>
      <circle cx="15" cy="15" r="1" fill="white"/>
      <circle cx="17" cy="15" r="1" fill="white"/>
      <circle cx="15" cy="17" r="1" fill="white"/>
      <circle cx="17" cy="17" r="1" fill="white"/>
    </svg>
  );
};

export default SuperMCPIcon;

