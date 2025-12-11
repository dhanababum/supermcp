import React, { useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import SuperuserActions from './SuperuserActions';
import { api, API_BASE_URL } from '../../../services/api';
import Notification from '../../../components/common/Notification';

const ConnectorCard = ({ connector, onConfigure, onDelete, onActivate, onRegisterUrl }) => {
  const { isSuperuser } = useAuth();
  const [updating, setUpdating] = useState(false);
  const [notification, setNotification] = useState(null);
  const [logoError, setLogoError] = useState(false);
  
  // Determine mode status
  const mode = connector.mode || 'unknown';
  const isDeactive = mode === 'deactive';
  const isActive = mode === 'active';
  const isSyncMode = mode === 'sync';

  // Get logo URL if available
  const logoUrl = connector.logo_name && connector.logo_name.trim() 
    ? `${API_BASE_URL}/api/connectors/${encodeURIComponent(connector.logo_name)}`
    : null;

  // Debug: log logo info
  React.useEffect(() => {
    if (connector.logo_name) {
      console.log('Connector logo_name:', connector.logo_name);
      console.log('Logo URL:', logoUrl);
    } else {
      console.log('No logo_name for connector:', connector.name, connector.logo_name);
    }
  }, [connector.logo_name, logoUrl, connector.name]);

  // Handle mode toggle for active/deactive connectors
  const handleModeToggle = async (newMode) => {
    if (!isSuperuser()) return;
    if (newMode === mode) return; // No change needed
    
    setUpdating(true);
    try {
      // Update connector mode via API
      await api.updateConnectorMode(connector.id, newMode);
      
      setNotification({
        type: 'success',
        message: `Connector mode updated to ${newMode}`
      });
      
      // Trigger refresh
      if (onDelete) {
        onDelete(); // This triggers refetch in parent
      }
    } catch (error) {
      console.error('Failed to update connector mode:', error);
      setNotification({
        type: 'error',
        message: `Failed to update mode: ${error.message}`
      });
    } finally {
      setUpdating(false);
    }
  };
  
  return (
    <>
      {/* Notification */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={4000}
          onClose={() => setNotification(null)}
        />
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
        <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-blue-500 rounded-lg flex items-center justify-center overflow-hidden">
          {logoUrl && !logoError ? (
            <img 
              src={logoUrl} 
              alt={`${connector.name} logo`}
              className="w-full h-full object-contain p-1"
              onError={(e) => {
                console.error('Failed to load logo:', logoUrl, e);
                setLogoError(true);
              }}
            />
          ) : (
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          )}
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          isActive 
            ? 'bg-green-100 text-green-700' 
            : isDeactive
            ? 'bg-yellow-100 text-yellow-700'
            : isSyncMode
            ? 'bg-blue-100 text-blue-700'
            : 'bg-gray-100 text-gray-700'
        }`}>
          {isActive ? 'Active' : isDeactive ? 'Not Activated' : isSyncMode ? 'Sync Mode' : mode}
        </span>
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{connector.name}</h3>
      <p className="text-sm text-gray-600 mb-4">{connector.description}</p>
      
      <div className="space-y-2 mb-4 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <span>Version:</span>
          <span className="font-medium text-gray-700">{connector.version}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>URL:</span>
          <span className="font-medium text-gray-700 truncate max-w-32" title={connector.url}>
            {connector.url}
          </span>
        </div>
      </div>
      
      <div className="space-y-2 pt-4 border-t border-gray-100">
        {/* Superuser: Mode Radio Buttons for Active/Deactive modes */}
        {isSuperuser() && (isActive || isDeactive) && (
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-2">Mode</label>
            <div className="flex items-center space-x-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name={`mode-${connector.id}`}
                  value="active"
                  checked={isActive}
                  onChange={() => handleModeToggle('active')}
                  disabled={updating}
                  className="w-4 h-4 text-green-600 focus:ring-green-500 cursor-pointer disabled:opacity-50"
                />
                <span className={`ml-2 text-sm ${isActive ? 'text-green-700 font-medium' : 'text-gray-600'}`}>
                  Active
                </span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name={`mode-${connector.id}`}
                  value="deactive"
                  checked={isDeactive}
                  onChange={() => handleModeToggle('deactive')}
                  disabled={updating}
                  className="w-4 h-4 text-yellow-600 focus:ring-yellow-500 cursor-pointer disabled:opacity-50"
                />
                <span className={`ml-2 text-sm ${isDeactive ? 'text-yellow-700 font-medium' : 'text-gray-600'}`}>
                  Deactive
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Sync Mode: Show Activate Button */}
        {isSyncMode && isSuperuser() && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-2">
            <div className="flex">
              <svg className="w-4 h-4 text-blue-400 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p className="text-xs text-blue-800">
                Sync mode connector. Click "Activate Connector" to fetch schema from URL.
              </p>
            </div>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {isSyncMode && isSuperuser() ? (
            // Sync Mode: Show Activate Connector button
            <button 
              onClick={() => onActivate && onActivate(connector)}
              className="flex-1 px-3 py-2 bg-brand-100 text-brand-700 text-sm font-medium rounded-lg hover:bg-brand-200 border border-brand-300 flex items-center justify-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Activate Connector
            </button>
          ) : isActive ? (
            // Active Mode: Show Create Server button
            <button 
              onClick={() => onConfigure(connector)}
              className="flex-1 px-3 py-2 bg-brand-100 text-brand-700 text-sm font-medium rounded-lg hover:bg-brand-200 border border-brand-300"
            >
              Create Server
            </button>
          ) : isDeactive && !isSuperuser() ? (
            // Non-superuser with deactive connector
            <div className="flex-1 px-3 py-2 bg-gray-100 text-gray-400 text-sm font-medium rounded-lg text-center cursor-not-allowed">
              Awaiting Activation
            </div>
          ) : null}
        </div>
        
        {/* Superuser Actions */}
        {isSuperuser() && (
          <div className="pt-2 border-t border-gray-100">
            <SuperuserActions 
              connector={connector} 
              onAccessUpdate={onDelete}
            />
          </div>
        )}
      </div>
      </div>
    </>
  );
};

export default ConnectorCard;

