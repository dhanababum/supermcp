import React, { useState, useEffect } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { api } from '../../../services/api';

const ConfigurationModal = ({ connector, onClose, onSuccess }) => {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({});
  const [serverName, setServerName] = useState('');
  const [tokenExpiresAt, setTokenExpiresAt] = useState('');

  useEffect(() => {
    if (connector) {
      setLoading(true);
      api.getConnectorSchema(connector.id)
        .then((connectorConfig) => {
          // Extract the actual schema from the config structure
          // The connector config has this structure:
          // { params: { properties: {...}, required: [...], ... } }
          // or just the schema directly
          let extractedSchema = connectorConfig;
          
          // If config has a 'params' property, use that as the schema
          if (connectorConfig && connectorConfig.params) {
            extractedSchema = connectorConfig.params;
          }
          
          console.log('Connector config:', connectorConfig);
          console.log('Extracted schema:', extractedSchema);
          setSchema(extractedSchema);
        })
        .catch((error) => {
          console.error('Error fetching schema:', error);
          alert('Failed to load connector schema: ' + error.message);
        })
        .finally(() => setLoading(false));
    }
  }, [connector]);

  const handleFormSubmit = ({ formData: data }) => {
    if (!serverName.trim()) {
      alert('⚠️ Please enter a server name');
      return;
    }

    const serverData = {
      connector_id: connector.id,
      server_name: serverName.trim(),
      configuration: data,
      token_expires_at: tokenExpiresAt || null
    };

    api.createServer(serverData)
      .then((response) => {
        const message = [
          `✅ ${response.message}`,
          ``,
          `Server ID: ${response.server_id}`,
          `Connector: ${response.connector_id}`,
          `Server Name: ${response.server_name}`,
          `Token: ${response.token}`,
          ``,
          `⚠️ Please save this token securely. It won't be shown again!`
        ].join('\n');
        alert(message);
        onSuccess();
        onClose();
      })
      .catch((error) => {
        console.error('Error creating server:', error);
        alert(`❌ Failed to create server: ${error.message}\n\nPlease check that the database is running and configured correctly.`);
      });
  };

  if (!connector) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-white">
                  Create Server
                </h3>
                <p className="text-purple-100 text-sm mt-1">
                  Create a new {connector.name} MCP server instance
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="px-6 py-6 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600"></div>
                  <p className="mt-4 text-gray-600">Loading configuration schema...</p>
                </div>
              </div>
            ) : schema ? (
              <div>
                {/* Server Name Input */}
                <div className="mb-6 pb-6 border-b border-gray-200">
                  <label htmlFor="serverName" className="block text-sm font-medium text-gray-700 mb-2">
                    Server Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="serverName"
                    value={serverName}
                    onChange={(e) => setServerName(e.target.value)}
                    placeholder={`e.g., ${connector.name} Production`}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    A friendly name to identify this server instance
                  </p>
                </div>

                {/* Token Expiry Date Input */}
                <div className="mb-6 pb-6 border-b border-gray-200">
                  <label htmlFor="tokenExpiresAt" className="block text-sm font-medium text-gray-700 mb-2">
                    Token Expiry Date (Optional)
                  </label>
                  <input
                    type="datetime-local"
                    id="tokenExpiresAt"
                    value={tokenExpiresAt}
                    onChange={(e) => setTokenExpiresAt(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    When should the generated token expire? Leave blank for no expiration
                  </p>
                </div>

                {/* Configuration Form */}
                <div className="rjsf-form-wrapper">
                  <h4 className="text-sm font-semibold text-gray-700 mb-4">Configuration</h4>
                  <Form
                    schema={schema}
                    validator={validator}
                    formData={formData}
                    onChange={(e) => setFormData(e.formData)}
                    onSubmit={handleFormSubmit}
                    uiSchema={{
                      'ui:submitButtonOptions': {
                        norender: true
                      }
                    }}
                  >
                    <div></div>
                  </Form>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-red-600">Failed to load configuration schema</p>
              </div>
            )}
          </div>

          {/* Footer */}
          {schema && !loading && (
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-end space-x-3 border-t border-gray-200">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const form = document.querySelector('.rjsf-form-wrapper form');
                  if (form) {
                    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                  }
                }}
                className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
              >
                Create Server
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigurationModal;

