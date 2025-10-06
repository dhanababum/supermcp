import React, { useState, useEffect, useCallback } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';

const ToolTemplateModal = ({ isOpen, onClose, onSuccess, server }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Select template, 2: Fill form, 3: Review

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch templates from the API endpoint
      const response = await fetch(`http://localhost:9000/api/connectors/${server.connector_id}/templates`);
      
      // Check if response is ok
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Check content type to ensure we're getting JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('Expected JSON but got:', text.substring(0, 200));
        throw new Error('Server returned HTML instead of JSON. Please check the server URL.');
      }
      
      const data = await response.json();
      setTemplates(data || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setError(`Failed to load templates: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [server.connector_id]);

  useEffect(() => {
    if (isOpen && server) {
      fetchTemplates();
    }
  }, [isOpen, server, fetchTemplates]);

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setFormData({});
    setStep(2);
  };

  const handleFormChange = ({ formData: data }) => {
    setFormData(data);
  };

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
      setSelectedTemplate(null);
    } else if (step === 3) {
      setStep(2);
    }
  };

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
    } else if (step === 2) {
      setStep(3);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      // Create the tool based on template and form data
      const toolData = {
        connector_id: server.connector_id,
        template_name: selectedTemplate.name,
        template_params: formData,
        tool_name: `${selectedTemplate.name}_${Date.now()}`, // Generate unique name
        description: selectedTemplate.description
      };

      // Call the API to create the tool
      const response = await fetch('http://localhost:9000/api/tools/from-template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(toolData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create tool');
      }

      const result = await response.json();
      console.log('Tool created:', result);
      
      // Call success callback
      if (onSuccess) {
        onSuccess();
      }
      
      handleClose();
      
    } catch (error) {
      console.error('Error creating tool:', error);
      setError('Failed to create tool: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setTemplates([]);
      setSelectedTemplate(null);
      setFormData({});
      setError(null);
      setStep(1);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-gray-100">
        <div className="p-8">
          <div className="flex justify-between items-center mb-8 pb-6 border-b border-gray-100">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">Create New Tool</h3>
                <p className="text-sm text-gray-500">Configure your tool from available templates</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              disabled={loading}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Step 1: Template Selection */}
          {step === 1 && (
            <div>
              <div className="mb-6">
                <h4 className="text-xl font-semibold text-gray-900 mb-2">Select a Template</h4>
                <p className="text-sm text-gray-600">Choose from available templates to create your tool</p>
              </div>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading templates...</p>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <p className="text-red-600">{error}</p>
                  <button
                    onClick={fetchTemplates}
                    className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  >
                    Retry
                  </button>
                </div>
                  ) : templates.length > 0 ? (
                    <div className="space-y-6">
                      <div>
                        <label htmlFor="template-select" className="block text-sm font-semibold text-gray-700 mb-3">
                          Choose a Template
                        </label>
                        <select
                          id="template-select"
                          onChange={(e) => {
                            const selectedTemplate = templates.find(t => t.name === e.target.value);
                            if (selectedTemplate) {
                              handleTemplateSelect(selectedTemplate);
                            }
                          }}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-4 focus:ring-purple-100 focus:border-purple-500 transition-all duration-200 bg-white hover:border-gray-300"
                          defaultValue=""
                        >
                          <option value="" disabled>Select a template...</option>
                          {templates.map((template, index) => (
                            <option key={index} value={template.name}>
                              {template.name} - {template.description}
                            </option>
                          ))}
                        </select>
                        <div className="mt-2 text-sm text-gray-500 flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {templates.length} template{templates.length !== 1 ? 's' : ''} available
                        </div>
                      </div>
                      {selectedTemplate && (
                        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl">
                          <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </div>
                            <div>
                              <h5 className="font-semibold text-blue-900">Selected: {selectedTemplate.name}</h5>
                              <p className="text-sm text-blue-700 mt-1">{selectedTemplate.description}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-600">No templates available for this connector.</p>
                      <p className="text-sm text-gray-500 mt-2">The connector may not support template-based tool creation.</p>
                    </div>
                  )}
            </div>
          )}

          {/* Step 2: Form Configuration */}
          {step === 2 && selectedTemplate && (
            <div>
              <div className="mb-6">
                <h4 className="text-xl font-semibold text-gray-900 mb-2">Configure Tool Parameters</h4>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Template:</span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs font-medium">
                      {selectedTemplate.name}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-2">{selectedTemplate.description}</p>
              </div>
              
              {/* Generate JSON Schema from template format */}
              <div className="template-form-container">
                <style>{`
                  .template-form-container .form-group {
                    margin-bottom: 1.5rem;
                    position: relative;
                    animation: slideInUp 0.3s ease-out;
                  }
                  
                  .template-form-container .form-group label {
                    display: block;
                    margin-bottom: 0.75rem;
                    font-weight: 600;
                    color: #1f2937;
                    font-size: 0.875rem;
                    text-transform: capitalize;
                  }
                  
                  .template-form-container .form-group input {
                    width: 100%;
                    padding: 0.875rem 1rem;
                    border: 2px solid #e5e7eb;
                    border-radius: 0.75rem;
                    font-size: 0.875rem;
                    line-height: 1.25rem;
                    background-color: #ffffff;
                    transition: all 0.2s ease-in-out;
                    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                  }
                  
                  .template-form-container .form-group input:hover {
                    border-color: #d1d5db;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                  }
                  
                  .template-form-container .form-group input:focus {
                    outline: none;
                    border-color: #8b5cf6;
                    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1), 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    transform: translateY(-1px);
                  }
                  
                  .template-form-container .form-group input::placeholder {
                    color: #9ca3af;
                    font-style: italic;
                  }
                  
                  .template-form-container .form-group .field-error {
                    color: #dc2626;
                    font-size: 0.75rem;
                    margin-top: 0.5rem;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                  }
                  
                  .template-form-container .form-group .field-error::before {
                    content: "⚠";
                    font-size: 0.875rem;
                  }
                  
                  .template-form-container .form-group .field-description {
                    color: #6b7280;
                    font-size: 0.75rem;
                    margin-top: 0.25rem;
                    font-style: italic;
                  }
                  
                  .template-form-container .form-group .required {
                    color: #dc2626;
                    margin-left: 0.25rem;
                  }
                  
                  .template-form-container .form-group .form-control {
                    position: relative;
                  }
                  
                  .template-form-container .form-group .form-control:focus-within {
                    transform: translateY(-1px);
                  }
                  
                  .template-form-container .form-group input[type="number"] {
                    appearance: none;
                    -moz-appearance: textfield;
                  }
                  
                  .template-form-container .form-group input[type="number"]::-webkit-outer-spin-button,
                  .template-form-container .form-group input[type="number"]::-webkit-inner-spin-button {
                    -webkit-appearance: none;
                    margin: 0;
                  }
                  
                  .template-form-container .form-group:focus-within label {
                    color: #8b5cf6;
                  }
                  
                  @keyframes slideInUp {
                    from {
                      opacity: 0;
                      transform: translateY(10px);
                    }
                    to {
                      opacity: 1;
                      transform: translateY(0);
                    }
                  }
                `}</style>
                {(() => {
                  const jsonSchema = {
                    type: selectedTemplate.type || "object",
                    properties: selectedTemplate.properties || {},
                    required: selectedTemplate.required || [],
                    title: `${selectedTemplate.name} Configuration`
                  };
                  
                  return (
                    <Form
                      schema={jsonSchema}
                      formData={formData}
                      onChange={handleFormChange}
                      validator={validator}
                      onSubmit={handleNext}
                      uiSchema={{
                        "ui:submitButtonOptions": {
                          "norender": true
                        },
                        "ui:order": selectedTemplate.required || [],
                        ...Object.keys(selectedTemplate.properties || {}).reduce((uiSchema, key) => {
                          const prop = selectedTemplate.properties[key];
                          uiSchema[key] = {
                            "ui:placeholder": `Enter ${key}${prop.type === 'integer' ? ' (number)' : ''}`,
                            "ui:widget": prop.type === 'integer' ? 'updown' : 'text',
                            "ui:classNames": "template-form-field",
                            "ui:options": {
                              classNames: "template-input-field"
                            }
                          };
                          return uiSchema;
                        }, {})
                      }}
                    />
                  );
                })()}
              </div>
              
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && selectedTemplate && (
            <div>
              <div className="mb-6">
                <h4 className="text-xl font-semibold text-gray-900 mb-2">Review Tool Configuration</h4>
                <p className="text-sm text-gray-600">Review your tool configuration before creating</p>
              </div>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-xl">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Template Name</label>
                    <p className="text-sm text-gray-900 font-medium">{selectedTemplate.name}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-xl">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Generated Tool Name</label>
                    <p className="text-sm text-gray-900 font-medium">{selectedTemplate.name}_{Date.now()}</p>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-xl">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                  <p className="text-sm text-gray-900">{selectedTemplate.description}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">Input Parameters</label>
                  {Object.keys(formData).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(formData).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center py-3 px-4 bg-white border border-gray-200 rounded-lg shadow-sm">
                          <span className="font-semibold text-gray-700 capitalize">{key}</span>
                          <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                      <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-sm text-gray-500 italic">No parameters configured</p>
                    </div>
                  )}
                </div>
                
                <div className="bg-gray-50 p-4 rounded-xl">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">Raw Form Data</label>
                  <pre className="text-xs bg-white p-3 rounded-lg border overflow-x-auto text-gray-800">
                    {JSON.stringify(formData, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Modal Footer */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handleBack}
              disabled={loading || step === 1}
              className="px-6 py-3 text-gray-700 text-sm font-semibold rounded-xl border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back</span>
            </button>
            <div className="flex space-x-3">
              <button
                onClick={handleClose}
                disabled={loading}
                className="px-6 py-3 text-gray-700 text-sm font-semibold rounded-xl border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 transition-all duration-200"
              >
                Cancel
              </button>
              {step < 3 ? (
                <button
                  onClick={handleNext}
                  disabled={loading || (step === 1 && !selectedTemplate) || (step === 2 && !selectedTemplate)}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white text-sm font-semibold rounded-xl hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 transition-all duration-200 flex items-center space-x-2 shadow-lg hover:shadow-xl"
                >
                  <span>Next</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white text-sm font-semibold rounded-xl hover:from-green-700 hover:to-green-800 disabled:opacity-50 transition-all duration-200 flex items-center space-x-2 shadow-lg hover:shadow-xl"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Creating...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span>Create Tool</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolTemplateModal;
