import React, { useState, useEffect } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { api } from '../../../services/api';
import Notification from '../../../components/common/Notification';

const ServerEditModal = ({ server, isOpen, onClose, onSuccess }) => {
  const [schema, setSchema] = useState(null);
  const [uiSchema, setUiSchema] = useState({});
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({});
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (isOpen && server) {
      setLoading(true);
      // Fetch server details and connector schema in parallel
      Promise.all([
        api.getServer(server.id),
        api.getConnectorSchema(server.connector_id)
      ])
        .then(([serverData, connectorConfig]) => {
          
          // Extract the actual schema from the config structure
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
          if (extractedSchema && extractedSchema.properties) {
            Object.keys(extractedSchema.properties).forEach(key => {
              const prop = extractedSchema.properties[key];
              const uiField = extractedUiSchema[key];
              
              // Check if this is an object type field with textarea widget BEFORE anyOf processing
              const isObjectWithTextarea = prop.type === 'object' && uiField && uiField['ui:widget'] === 'textarea';
              
              // If property has anyOf with [type, null], simplify it
              if (prop.anyOf && Array.isArray(prop.anyOf)) {
                const nonNullType = prop.anyOf.find(t => t.type !== 'null');
                if (nonNullType) {
                  extractedSchema.properties[key] = {
                    ...nonNullType,
                    title: prop.title,
                    description: prop.description,
                    default: prop.default
                  };
                }
              }
              
              // Convert object type to string type if textarea widget is specified
              const finalProp = extractedSchema.properties[key];
              if (isObjectWithTextarea || (finalProp.type === 'object' && uiField && uiField['ui:widget'] === 'textarea')) {
                extractedSchema.properties[key] = {
                  ...finalProp,
                  type: 'string',
                  format: 'json',
                  default: finalProp.default && typeof finalProp.default === 'object' ? JSON.stringify(finalProp.default, null, 2) : finalProp.default
                };
              }
            });
          }
          
          setSchema(extractedSchema);
          setUiSchema(extractedUiSchema);
          
          // Pre-populate form with existing server configuration
          const existingConfig = serverData.configuration || {};
          const initialFormData = { ...existingConfig };
          
          // Convert object fields with textarea widget to JSON strings
          if (extractedSchema && extractedSchema.properties && extractedUiSchema) {
            Object.keys(extractedSchema.properties).forEach(key => {
              const prop = extractedSchema.properties[key];
              const uiField = extractedUiSchema[key];
              
              if (prop.type === 'string' && prop.format === 'json' && uiField && uiField['ui:widget'] === 'textarea') {
                // If existing value is an object, convert it to JSON string
                if (initialFormData[key] && typeof initialFormData[key] === 'object') {
                  initialFormData[key] = JSON.stringify(initialFormData[key], null, 2);
                }
              }
            });
          }
          
          setFormData(initialFormData);
        })
        .catch((error) => {
          console.error('Error fetching server or schema:', error);
          setNotification({
            type: 'error',
            message: `Failed to load server configuration: ${error.message}`
          });
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, server]);

  const handleFormSubmit = ({ formData: data }) => {
    // Convert JSON string fields back to objects for fields with textarea widget
    const processedData = { ...data };
    if (uiSchema && Object.keys(uiSchema).length > 0) {
      Object.keys(uiSchema).forEach(key => {
        const uiField = uiSchema[key];
        if (uiField && uiField['ui:widget'] === 'textarea' && processedData[key]) {
          const value = processedData[key];
          if (typeof value === 'string' && value.trim()) {
            try {
              processedData[key] = JSON.parse(value);
            } catch (e) {
              console.warn(`Failed to parse JSON for ${key}:`, e);
            }
          }
        }
      });
    }

    setLoading(true);
    api.updateServer(server.id, processedData)
      .then((response) => {
        setNotification({
          type: 'success',
          message: response.message || 'Server configuration updated successfully'
        });
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 1500);
      })
      .catch((error) => {
        console.error('Error updating server:', error);
        setNotification({
          type: 'error',
          message: `Failed to update server: ${error.message}`
        });
      })
      .finally(() => setLoading(false));
  };

  if (!isOpen || !server) return null;

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
                  Edit Server Configuration
                </h3>
                <p className="text-purple-100 text-sm mt-1">
                  Update configuration for {server.server_name}
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
            {loading && !schema ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600"></div>
                  <p className="mt-4 text-gray-600">Loading server configuration...</p>
                </div>
              </div>
            ) : schema ? (
              <div>
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
                disabled={loading}
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
                className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? 'Updating...' : 'Update Configuration'}
              </button>
            </div>
          )}
        </div>
      </div>

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

export default ServerEditModal;


