import React, { useState, useEffect, useCallback } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import Notification from '../../components/common/Notification';
import { API_BASE_URL } from '../../../constants/env';

const TemplateToolModal = ({ isOpen, onClose, onSuccess, connector }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Select template, 2: Fill form, 3: Review
  const [notification, setNotification] = useState(null);

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      // Fetch templates from the connector
      const response = await fetch(`${connector.url}`);
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setNotification({
        type: 'error',
        message: 'Failed to load templates. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  }, [connector]);

  useEffect(() => {
    if (isOpen && connector) {
      fetchTemplates();
    }
  }, [isOpen, connector, fetchTemplates]);

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
    if (step === 2) {
      setStep(3);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);

      // Create the tool based on template and form data
      const toolData = {
        connector_id: connector.id,
        template_name: selectedTemplate.name,
        template_params: formData,
        tool_name: `${selectedTemplate.name}_${Date.now()}`, // Generate unique name
        description: selectedTemplate.description
      };

      // Call the API to create the tool
      const response = await fetch(`${API_BASE_URL}/api/tools/from-template`, {
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

      await response.json();
      
      // Show success notification
      setNotification({
        type: 'success',
        message: `Tool "${selectedTemplate.name}" created successfully!`
      });
      
      if (onSuccess) {
        onSuccess();
      }
      
      // Close modal after a short delay
      setTimeout(() => {
        onClose();
      }, 500);
      
    } catch (error) {
      console.error('Error creating tool:', error);
      
      // Show error notification
      setNotification({
        type: 'error',
        message: error.message || 'Failed to create tool. Please try again.'
      });
      
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setTemplates([]);
      setSelectedTemplate(null);
      setFormData({});
      setStep(1);
      setNotification(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Notification Toast */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={4000}
          onClose={() => setNotification(null)}
        />
      )}

      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={handleClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-brand-600 to-blue-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-white">
                  Create Tool from Template
                </h3>
                <p className="text-brand-100 text-sm mt-1">
                  {connector?.name} - Step {step} of 3
                </p>
              </div>
              <button
                onClick={handleClose}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="px-6 py-4 bg-gray-50 border-b">
            <div className="flex items-center">
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= 1 ? 'bg-brand-600 text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  1
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  step >= 1 ? 'text-brand-600' : 'text-gray-500'
                }`}>
                  Select Template
                </span>
              </div>
              <div className="flex-1 h-0.5 bg-gray-300 mx-4">
                <div className={`h-full transition-all duration-300 ${
                  step >= 2 ? 'bg-brand-600' : 'bg-gray-300'
                }`} style={{ width: step >= 2 ? '100%' : '0%' }}></div>
              </div>
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= 2 ? 'bg-brand-600 text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  2
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  step >= 2 ? 'text-brand-600' : 'text-gray-500'
                }`}>
                  Configure
                </span>
              </div>
              <div className="flex-1 h-0.5 bg-gray-300 mx-4">
                <div className={`h-full transition-all duration-300 ${
                  step >= 3 ? 'bg-brand-600' : 'bg-gray-300'
                }`} style={{ width: step >= 3 ? '100%' : '0%' }}></div>
              </div>
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= 3 ? 'bg-brand-600 text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  3
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  step >= 3 ? 'text-brand-600' : 'text-gray-500'
                }`}>
                  Review
                </span>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="px-6 py-6 max-h-96 overflow-y-auto">
            {loading && step === 1 ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-brand-600"></div>
                  <p className="mt-4 text-gray-600">Loading templates...</p>
                </div>
              </div>
            ) : step === 1 ? (
              /* Step 1: Template Selection */
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Choose a Template</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {templates.map((template, index) => (
                    <div
                      key={index}
                      onClick={() => handleTemplateSelect(template)}
                      className="p-4 border border-gray-200 rounded-lg hover:border-brand-300 hover:bg-brand-50 cursor-pointer transition-all duration-200"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className="text-sm font-medium text-gray-900">{template.name}</h5>
                          <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                          {template.params && Object.keys(template.params).length > 0 && (
                            <div className="mt-2">
                              <span className="text-xs text-gray-500">Parameters:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {Object.keys(template.params).map((param) => (
                                  <span
                                    key={param}
                                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
                                  >
                                    {param}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  ))}
                </div>
                {templates.length === 0 && (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No templates available</h3>
                    <p className="text-gray-600">This connector doesn't have any templates defined.</p>
                  </div>
                )}
              </div>
            ) : step === 2 ? (
              /* Step 2: Form Configuration */
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">
                  Configure {selectedTemplate.name}
                </h4>
                <p className="text-sm text-gray-600 mb-6">{selectedTemplate.description}</p>
                
                {selectedTemplate.params && Object.keys(selectedTemplate.params).length > 0 ? (
                  <div className="rjsf-form-wrapper">
                    <Form
                      schema={selectedTemplate.params}
                      validator={validator}
                      formData={formData}
                      onChange={handleFormChange}
                      uiSchema={{
                        'ui:submitButtonOptions': {
                          norender: true
                        }
                      }}
                    >
                      <div></div>
                    </Form>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-600">This template doesn't require any configuration.</p>
                  </div>
                )}
              </div>
            ) : step === 3 ? (
              /* Step 3: Review */
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Review Tool Configuration</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                  <div>
                    <h5 className="text-sm font-medium text-gray-700">Template</h5>
                    <p className="text-sm text-gray-900">{selectedTemplate.name}</p>
                    <p className="text-xs text-gray-600">{selectedTemplate.description}</p>
                  </div>
                  
                  {Object.keys(formData).length > 0 && (
                    <div>
                      <h5 className="text-sm font-medium text-gray-700">Configuration</h5>
                      <div className="mt-2 space-y-2">
                        {Object.entries(formData).map(([key, value]) => (
                          <div key={key} className="flex justify-between text-sm">
                            <span className="text-gray-600">{key}:</span>
                            <span className="text-gray-900 font-medium">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
            <div>
              {step > 1 && (
                <button
                  onClick={handleBack}
                  disabled={loading}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-100 disabled:opacity-50"
                >
                  Back
                </button>
              )}
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleClose}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-100 disabled:opacity-50"
              >
                Cancel
              </button>
              {step < 3 ? (
                <button
                  onClick={handleNext}
                  disabled={loading || (step === 2 && !selectedTemplate)}
                  className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
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
    </>
  );
};

export default TemplateToolModal;
