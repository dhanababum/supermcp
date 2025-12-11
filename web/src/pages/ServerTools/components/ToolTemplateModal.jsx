import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../../services/api';

const ToolTemplateModal = ({ isOpen, onClose, onSuccess, server }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Select template, 2: Fill form, 3: Review
  const [toolName, setToolName] = useState('');
  const [toolDescription, setToolDescription] = useState('');

  // Function to extract placeholders from template string
  const extractPlaceholders = useCallback((str) => {
    const regex = /\{([^}]+)\}/g;
    const placeholders = [];
    let match;
    while ((match = regex.exec(str)) !== null) {
      placeholders.push(match[1]);
    }
    return [...new Set(placeholders)]; // Remove duplicates
  }, []);


  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch templates using the API service
      const data = await api.getConnectorTemplates(server.connector_id);
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
    setStep(3);
  };


  const handleBack = () => {
    if (step === 3) {
      setStep(1);
      setSelectedTemplate(null);
    } else if (step === 4) {
      setStep(3);
    }
  };

  const handleNext = () => {
    if (step === 1) {
      // User selected a template, move to step 3 (form configuration)
      if (selectedTemplate) {
        setStep(3);
      } else {
        return;
      }
    } else if (step === 3) {
      // User configured form, move to step 4 (review)
      // Validate that tool name is provided
      if (!toolName.trim()) {
        setError('Tool name is required. Please enter a tool name.');
        return;
      }
      setStep(4);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      // Generate inputSchema from Dynamic Template Strings
      const generateInputSchemaFromTemplateStrings = () => {
        const properties = {};
        const required = [];
        
        // Process each form field to extract placeholders from template strings
        Object.entries(formData).forEach(([key, value]) => {
          if (typeof value === 'string' && value.includes('{')) {
            // Extract placeholders from template string
            const placeholders = extractPlaceholders(value);
            
            // Add each placeholder as a property to the schema
            placeholders.forEach(placeholder => {
              if (!properties[placeholder]) {
                properties[placeholder] = {
                  type: "string",
                  description: `Value for placeholder {${placeholder}} in ${key}`
                };
                required.push(placeholder);
              }
            });
          }
        });
        
        return {
          type: "object",
          properties,
          required
        };
      };

      // Create the tool using the servers/{server_id}/tools endpoint format
      const toolData = {
        name: toolName || `${selectedTemplate.name}_${Date.now()}`,
        title: null,
        icons: null,
        description: toolDescription || selectedTemplate.description,
        inputSchema: generateInputSchemaFromTemplateStrings(),
        outputSchema: {
          type: "object",
          properties: {
            result: {
              type: "string"
            }
          },
          required: ["result"]
        },
        annotations: null,
        meta: {
          "_fastmcp": {
            tags: []
          }
        },
        // Include template information for tracking
        template_name: selectedTemplate?.name || null,
        template_args: formData || {}
      };

      // Call the API to create the tool using the API service
      const result = await api.createServerTool(server.id, toolData);
      
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
      setToolName('');
      setToolDescription('');
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
              <div className="w-10 h-10 bg-gradient-to-br from-brand-500 to-blue-500 rounded-xl flex items-center justify-center">
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
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading templates...</p>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <p className="text-red-600">{error}</p>
                  <button
                    onClick={fetchTemplates}
                    className="mt-4 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700"
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
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-500 transition-all duration-200 bg-white hover:border-gray-300"
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
                        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-blue-50 border border-blue-200 rounded-xl">
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
          {step === 3 && selectedTemplate && (
            <div>
              <div className="mb-6">
                <h4 className="text-xl font-semibold text-gray-900 mb-2">Configure Tool Parameters</h4>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Template:</span>
                    <span className="px-2 py-1 bg-brand-100 text-brand-700 rounded-lg text-xs font-medium">
                      {selectedTemplate.name}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-2">{selectedTemplate.description}</p>
              </div>

              {/* Tool Name and Description Input Fields */}
              <div className="mb-8 space-y-6">
                <div className="p-6 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl">
                  <h5 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Tool Information
                  </h5>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Tool Name <span className="text-red-500">*</span>
                      </label>
                      <p className="text-xs text-gray-500 mb-3">
                        Enter a unique name for your tool
                      </p>
                      <input
                        type="text"
                        value={toolName}
                        onChange={(e) => setToolName(e.target.value)}
                        placeholder="Enter tool name (e.g., 'Hello World Tool')"
                        className="w-full px-4 py-3 border-2 border-green-200 rounded-xl shadow-sm focus:outline-none focus:ring-4 focus:ring-green-100 focus:border-green-500 transition-all duration-200 bg-white hover:border-green-300"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Tool Description
                      </label>
                      <p className="text-xs text-gray-500 mb-3">
                        Provide a description of what this tool does
                      </p>
                      <textarea
                        value={toolDescription}
                        onChange={(e) => setToolDescription(e.target.value)}
                        placeholder="Enter tool description (e.g., 'A tool that greets users with personalized messages')"
                        className="w-full px-4 py-3 border-2 border-green-200 rounded-xl shadow-sm focus:outline-none focus:ring-4 focus:ring-green-100 focus:border-green-500 transition-all duration-200 bg-white hover:border-green-300 resize-none"
                        rows={3}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Enhanced Form with Dynamic Template String Input for String Properties */}
              <div className="space-y-6">
                {Object.entries(selectedTemplate.inputSchema?.properties || {}).map(([key, prop]) => (
                  <div key={key} className="p-6 border border-gray-200 rounded-xl bg-white shadow-sm">
                    {prop.type === 'string' ? (
                      // String properties get Dynamic Template String Input functionality
                      <div>
                        <div className="mb-4">
                          <label className="block text-lg font-semibold text-gray-900 mb-2">
                            {key} <span className="text-blue-600 text-sm">(String - Dynamic Template String)</span>
                          </label>
                          <p className="text-sm text-gray-600 mb-3">
                            This is a string property. You can use dynamic template strings with placeholders like <code className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{'{placeholder}'}</code>
                          </p>
                        </div>
                        
                        {/* Template String Input */}
                        <div className="mb-6 p-6 bg-gradient-to-r from-blue-50 to-blue-50 border border-blue-200 rounded-xl">
                          <h5 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            Template String for {key}
                          </h5>
                          <p className="text-sm text-gray-600 mb-4">
                            Enter your template string with placeholders in curly braces like <code className="bg-gray-200 px-1 rounded">{'{name}'}</code>
                          </p>
                          <textarea
                            value={formData[key] || ''}
                            onChange={(e) => {
                              const newFormData = { ...formData, [key]: e.target.value };
                              setFormData(newFormData);
                            }}
                            placeholder={`Enter template string for ${key}, e.g., "Hello {name}, you are {age} years old"`}
                            className="w-full px-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 bg-white hover:border-blue-300 resize-none"
                            rows={3}
                          />
                          {formData[key] && extractPlaceholders(formData[key]).length > 0 && (
                            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                              <p className="text-sm font-medium text-blue-700 mb-1">Detected placeholders:</p>
                              <p className="text-sm text-blue-600">{extractPlaceholders(formData[key]).join(', ')}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      // Non-string properties get regular form inputs
                      <div>
                        <label className="block text-lg font-semibold text-gray-900 mb-2">
                          {key} <span className="text-gray-500 text-sm">({prop.type})</span>
                        </label>
                        <p className="text-sm text-gray-500 mb-4">
                          This is a {prop.type} property. Enter a direct value.
                        </p>
                        <input
                          type={prop.type === 'integer' ? 'number' : 'text'}
                          value={formData[key] || ''}
                          onChange={(e) => {
                            const value = prop.type === 'integer' ? parseInt(e.target.value) || 0 : e.target.value;
                            setFormData(prev => ({ ...prev, [key]: value }));
                          }}
                          placeholder={`Enter ${key} (${prop.type})`}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-4 focus:ring-gray-100 focus:border-gray-500 transition-all duration-200 bg-white hover:border-gray-300"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
            </div>
          )}

          {/* Step 3: Review */}
          {step === 4 && selectedTemplate && (
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
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Tool Name</label>
                    <p className="text-sm text-gray-900 font-medium">{toolName || 'Not specified'}</p>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-xl">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Template Description</label>
                  <p className="text-sm text-gray-900">{selectedTemplate.description}</p>
                </div>

                {toolDescription && (
                  <div className="bg-green-50 p-4 rounded-xl border border-green-200">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Tool Description</label>
                    <p className="text-sm text-gray-900">{toolDescription}</p>
                  </div>
                )}

                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">Input Parameters</label>
                  {Object.keys(formData).length > 0 ? (
                    <div className="space-y-6">
                      {Object.entries(formData).map(([key, value]) => {
                        const prop = selectedTemplate.inputSchema?.properties?.[key];
                        const isStringWithPlaceholders = prop?.type === 'string' && value && extractPlaceholders(value).length > 0;
                        
                        return (
                          <div key={key} className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                            <div className="flex justify-between items-start mb-4">
                              <span className="text-lg font-semibold text-gray-900 capitalize">{key}</span>
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-500">({prop?.type})</span>
                                {isStringWithPlaceholders && (
                                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                                    Dynamic Template String
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {isStringWithPlaceholders ? (
                              <div className="space-y-4">
                                <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                                  <p className="text-sm font-semibold text-blue-700 mb-2">Template String:</p>
                                  <p className="text-sm text-blue-900 font-mono bg-white p-3 rounded-lg border">
                                    {value}
                                  </p>
                                </div>
                                
                                <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
                                  <p className="text-sm font-semibold text-gray-700 mb-2">Detected Placeholders:</p>
                                  <p className="text-sm text-gray-600">{extractPlaceholders(value).join(', ')}</p>
                                </div>
                                
                              </div>
                            ) : (
                              <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
                                <p className="text-sm font-semibold text-gray-700 mb-2">Value:</p>
                                <p className="text-sm text-gray-900 font-mono bg-white p-3 rounded-lg border">
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </p>
                              </div>
                            )}
                          </div>
                        );
                      })}
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

                {/* Generated Input Schema Preview */}
                <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">Generated Input Schema</label>
                  <p className="text-xs text-gray-600 mb-3">
                    This schema will be generated from your template strings with placeholders
                  </p>
                  <pre className="text-xs bg-white p-3 rounded-lg border overflow-x-auto text-gray-800">
                    {JSON.stringify((() => {
                      const properties = {};
                      const required = [];
                      
                      Object.entries(formData).forEach(([key, value]) => {
                        if (typeof value === 'string' && value.includes('{')) {
                          const placeholders = extractPlaceholders(value);
                          placeholders.forEach(placeholder => {
                            if (!properties[placeholder]) {
                              properties[placeholder] = {
                                type: "string",
                                description: `Value for placeholder {${placeholder}} in ${key}`
                              };
                              required.push(placeholder);
                            }
                          });
                        }
                      });
                      
                      return {
                        type: "object",
                        properties,
                        required
                      };
                    })(), null, 2)}
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
              {step < 4 ? (
                <button
                  onClick={handleNext}
                  disabled={loading || (step === 1 && !selectedTemplate)}
                  className="px-6 py-3 bg-gradient-to-r from-brand-600 to-brand-700 text-white text-sm font-semibold rounded-xl hover:from-brand-700 hover:to-brand-800 disabled:opacity-50 transition-all duration-200 flex items-center space-x-2 shadow-lg hover:shadow-xl"
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
