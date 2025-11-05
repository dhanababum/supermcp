import React, { useState, useEffect } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { api } from '../../../services/api';
import Notification from '../../../components/common/Notification';

const ConfigurationModal = ({ connector, onClose, onSuccess }) => {
  const [schema, setSchema] = useState(null);
  const [uiSchema, setUiSchema] = useState({});
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({});
  const [serverName, setServerName] = useState('');
  const [tokenExpiresAt, setTokenExpiresAt] = useState('');
  const [notification, setNotification] = useState(null);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [createdServer, setCreatedServer] = useState(null);

  useEffect(() => {
    if (connector) {
      setLoading(true);
      api.getConnectorSchema(connector.id)
        .then((connectorConfig) => {
          // Extract the actual schema from the config structure
          // The connector config has this structure:
          // { params: { properties: {...}, required: [...], ... }, ui_schema: {...} }
          // or just the schema directly
          let extractedSchema = connectorConfig;
          let extractedUiSchema = {};
          
          // If config has a 'params' property, use that as the schema
          if (connectorConfig && connectorConfig.params) {
            extractedSchema = connectorConfig.params;
          }
          
          // Extract UI schema if available
          if (connectorConfig && connectorConfig.ui_schema) {
            extractedUiSchema = connectorConfig.ui_schema;
          }
          
          // Preprocess schema to fix anyOf patterns for Optional fields
          // Pydantic generates anyOf: [{type: X}, {type: null}] for Optional[X]
          // But RJSF widgets like 'password' don't work with anyOf
          if (extractedSchema && extractedSchema.properties) {
            Object.keys(extractedSchema.properties).forEach(key => {
              const prop = extractedSchema.properties[key];
              const uiField = extractedUiSchema[key];
              
              // Check if this is an object type field with textarea widget BEFORE anyOf processing
              const isObjectWithTextarea = prop.type === 'object' && uiField && uiField['ui:widget'] === 'textarea';
              
              // If property has anyOf with [type, null], simplify it
              if (prop.anyOf && Array.isArray(prop.anyOf)) {
                // Find non-null type
                const nonNullType = prop.anyOf.find(t => t.type !== 'null');
                if (nonNullType) {
                  // Replace the property with the non-null type
                  // Keep other properties like title, description, default
                  extractedSchema.properties[key] = {
                    ...nonNullType,
                    title: prop.title,
                    description: prop.description,
                    default: prop.default
                  };
                }
              }
              
              // Convert object type to string type if textarea widget is specified
              // RJSF doesn't render textarea widgets for object types
              const finalProp = extractedSchema.properties[key];
              if (isObjectWithTextarea || (finalProp.type === 'object' && uiField && uiField['ui:widget'] === 'textarea')) {
                // Convert to string type with JSON format
                extractedSchema.properties[key] = {
                  ...finalProp,
                  type: 'string',
                  format: 'json',
                  // Convert default object to JSON string if it exists
                  default: finalProp.default && typeof finalProp.default === 'object' ? JSON.stringify(finalProp.default, null, 2) : finalProp.default
                };
              }
            });
          }
          
          setSchema(extractedSchema);
          setUiSchema(extractedUiSchema);
          
          // Initialize formData with JSON string conversion for object fields with textarea
          const initialFormData = {};
          if (extractedSchema && extractedSchema.properties && extractedUiSchema) {
            Object.keys(extractedSchema.properties).forEach(key => {
              const prop = extractedSchema.properties[key];
              const uiField = extractedUiSchema[key];
              
              // If this is an object type field with textarea widget, convert to string
              if (prop.type === 'string' && prop.format === 'json' && uiField && uiField['ui:widget'] === 'textarea') {
                // If there's a default value that's an object, convert it to JSON string
                if (prop.default && typeof prop.default === 'object') {
                  initialFormData[key] = JSON.stringify(prop.default, null, 2);
                }
              }
            });
          }
          setFormData(initialFormData);
        })
        .catch((error) => {
          console.error('Error fetching schema:', error);
          setNotification({
            type: 'error',
            message: `Failed to load connector schema: ${error.message}`
          });
        })
        .finally(() => setLoading(false));
    }
  }, [connector]);

  const handleFormSubmit = ({ formData: data }) => {
    if (!serverName.trim()) {
      setNotification({
        type: 'warning',
        message: 'Please enter a server name'
      });
      return;
    }

    // Convert JSON string fields back to objects for fields with textarea widget
    // that were originally object types
    const processedData = { ...data };
    if (uiSchema && Object.keys(uiSchema).length > 0) {
      Object.keys(uiSchema).forEach(key => {
        const uiField = uiSchema[key];
        if (uiField && uiField['ui:widget'] === 'textarea' && processedData[key]) {
          const value = processedData[key];
          // If it's a string, try to parse it as JSON
          if (typeof value === 'string' && value.trim()) {
            try {
              processedData[key] = JSON.parse(value);
            } catch (e) {
              // If parsing fails, keep as string (might be invalid JSON)
              // The backend validation will handle this
              console.warn(`Failed to parse JSON for ${key}:`, e);
            }
          }
        }
      });
    }

    const serverData = {
      connector_id: connector.id,
      server_name: serverName.trim(),
      configuration: processedData,
      token_expires_at: tokenExpiresAt || null
    };

    setLoading(true);
    api.createServer(serverData)
      .then((response) => {
        setCreatedServer(response);
        setShowTokenModal(true);
        onSuccess();
      })
      .catch((error) => {
        console.error('Error creating server:', error);
        setNotification({
          type: 'error',
          message: `Failed to create server: ${error.message}. Please check that the database is running and configured correctly.`
        });
      })
      .finally(() => setLoading(false));
  };

  const handleCopyToken = () => {
    if (createdServer?.token) {
      navigator.clipboard.writeText(createdServer.token);
      setNotification({
        type: 'success',
        message: 'Token copied to clipboard!'
      });
    }
  };

  const handleCloseTokenModal = () => {
    setShowTokenModal(false);
    setCreatedServer(null);
    onClose();
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
                      ...uiSchema,
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

      {/* Token Display Modal */}
      {showTokenModal && createdServer && (
        <div className="fixed inset-0 z-[60] overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-900 bg-opacity-75" onClick={handleCloseTokenModal}></div>
            
            <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
              <div className="mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mx-auto mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 text-center mb-2">
                  Server Created Successfully!
                </h3>
                <p className="text-sm text-gray-600 text-center">
                  Your server has been created. Please save the token below securely.
                </p>
              </div>

              <div className="space-y-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Server Name</p>
                      <p className="text-sm font-medium text-gray-900">{createdServer.server_name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Server ID</p>
                      <p className="text-sm font-medium text-gray-900">{createdServer.server_id}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <div>
                      <p className="text-sm font-semibold text-yellow-800 mb-1">Important: Save this token</p>
                      <p className="text-sm text-yellow-700">
                        This token will only be shown once. Make sure to copy and store it securely.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 mb-2">Access Token</p>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 bg-white border border-gray-300 rounded px-3 py-2 text-sm font-mono text-gray-900 overflow-x-auto">
                      {createdServer.token}
                    </code>
                    <button
                      onClick={handleCopyToken}
                      className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2"
                      title="Copy token"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Copy</span>
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleCloseTokenModal}
                  className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notification */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={4000}
          onClose={() => setNotification(null)}
        />
      )}
    </div>
  );
};

export default ConfigurationModal;

