import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../services/api';

const ConnectorLogo = ({ logoName, connectorUrl, alt, size = 'md' }) => {
  const [logoState, setLogoState] = useState('primary'); // 'primary' | 'fallback' | 'error'

  // Reset state when inputs change
  useEffect(() => {
    setLogoState('primary');
  }, [logoName, connectorUrl]);

  // Construct URLs
  const primaryUrl = logoName && typeof logoName === 'string' && logoName.trim()
    ? `${API_BASE_URL}/api/connectors/${encodeURIComponent(logoName)}`
    : null;

  const getFallbackUrl = () => {
    if (!connectorUrl || typeof connectorUrl !== 'string' || !connectorUrl.trim()) {
      return null;
    }
    const cleanUrl = connectorUrl.trim().endsWith('/')
      ? connectorUrl.trim().slice(0, -1)
      : connectorUrl.trim();
    return `${cleanUrl}/logo.png`;
  };

  const fallbackUrl = getFallbackUrl();

  // Determine current image source
  let currentSrc = null;
  if (logoState === 'primary' && primaryUrl) {
    currentSrc = primaryUrl;
  } else if ((logoState === 'primary' || logoState === 'fallback') && fallbackUrl) {
    currentSrc = fallbackUrl;
  }

  const handleError = () => {
    if (logoState === 'primary' && fallbackUrl) {
      setLogoState('fallback');
    } else {
      setLogoState('error');
    }
  };

  // Determine dimensions and icon styles based on size
  let containerClasses = '';
  let svgClasses = '';

  switch (size) {
    case 'sm': // Used in ServerMetricsCard (w-8 h-8)
      containerClasses = 'w-8 h-8 bg-white border border-surface-200 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0';
      svgClasses = 'w-4 h-4 text-surface-500';
      break;
    case 'lg': // Used in ConnectorCard (w-12 h-12)
      containerClasses = 'w-12 h-12 bg-white border border-surface-200 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0';
      svgClasses = 'w-6 h-6 text-brand-500';
      break;
    case 'md': // Used in ServerTable (w-10 h-10)
    default:
      containerClasses = 'h-10 w-10 bg-white border border-surface-200 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0';
      svgClasses = 'w-5 h-5 text-brand-500';
      break;
  }

  if (currentSrc && logoState !== 'error') {
    return (
      <div className={containerClasses}>
        <img
          src={currentSrc}
          alt={alt || 'Connector Logo'}
          className="w-full h-full object-contain p-1"
          onError={handleError}
        />
      </div>
    );
  }

  // Fallback default SVG icon
  return (
    <div className={containerClasses}>
      <svg className={svgClasses} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
      </svg>
    </div>
  );
};

export default ConnectorLogo;
