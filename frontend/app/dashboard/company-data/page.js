'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Upload, CheckCircle, AlertCircle, Building, Users, Target, TrendingUp, Lightbulb, Save } from 'lucide-react';
import { companyDataAPI } from '../../services/api';
import { getTenantId } from '../../services/auth';
import { useRouter } from 'next/navigation';
import Sidebar from '../../components/Sidebar';
import PDFUploader from '../../components/PDFUploader';

const CompanyDataPage = () => {
  const router = useRouter();
  
  // Company data state
  const [companyData, setCompanyData] = useState(null);
  const [editedData, setEditedData] = useState({});
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState(null);
  const [updateMessage, setUpdateMessage] = useState(null);
  const [showPDFUploader, setShowPDFUploader] = useState(false);

  // Refs for auto-resizing textareas
  const textareaRefs = useRef({});

  // Fetch company data on component mount
  useEffect(() => {
    fetchCompanyData();
  }, []);

  // Auto-resize textareas when content changes
  useEffect(() => {
    Object.values(textareaRefs.current).forEach(textarea => {
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(textarea.scrollHeight, textarea.offsetHeight) + 'px';
      }
    });
  }, [editedData]);

  const fetchCompanyData = async () => {
    try {
      setLoading(true);
      const response = await companyDataAPI.getCompanyData();
      if (response.success) {
        setCompanyData(response.data);
        setEditedData(response.data);
      } else {
        setError(response.error || 'Failed to fetch company data');
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch company data');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleUpdate = async () => {
    setUpdating(true);
    setUpdateMessage(null);
    
    try {
      const response = await companyDataAPI.updateCompanyData(editedData);
      if (response.success) {
        setCompanyData(editedData);
      }
    } catch (err) {
      setUpdateMessage({ type: 'error', message: err.message || 'Failed to update company data' });
    } finally {
      setUpdating(false);
    }
  };

  const hasChanges = () => {
    if (!companyData || !editedData) return false;
    return Object.keys(editedData).some(key => editedData[key] !== companyData[key]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex">
        <Sidebar currentPage="company-data" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading company data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex">
        <Sidebar currentPage="company-data" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchCompanyData}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex">
      {/* Sidebar */}
      <Sidebar currentPage="company-data" />

      {/* Main Content */}
      <div className="flex-1 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Audy's knowledge of your company</h1>
            <p className="text-gray-600">View and manage your company information and knowledge base</p>
          </div>

          {/* Update Message */}
          {updateMessage && (
            <div className="mb-2 px-3 py-1 text-sm bg-gray-50 text-gray-600 rounded-md border border-gray-100">
              {updateMessage.message}
            </div>
          )}

          <div className="flex gap-8">
            {/* Left Side - Company Information */}
            <div className="flex-1">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                      <Building className="h-5 w-5 mr-2" />
                      Company Information
                    </h2>
                    <button
                      onClick={handleUpdate}
                      disabled={updating || !hasChanges()}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                    >
                      {updating ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Updating...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          Update
                        </>
                      )}
                    </button>
                  </div>
                  
                  {editedData && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div className="flex items-start space-x-3">
                          <TrendingUp className="h-5 w-5 text-blue-500 mt-3 flex-shrink-0" />
                          <div className="flex-1">
                            <label className="block font-medium text-gray-900 mb-1">Industry</label>
                            <textarea
                              ref={(el) => textareaRefs.current['industry'] = el}
                              value={editedData.industry || ''}
                              onChange={(e) => handleFieldChange('industry', e.target.value)}
                              placeholder="Enter industry"
                              className="w-full p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[80px]"
                            />
                          </div>
                        </div>
                        
                        <div className="flex items-start space-x-3">
                          <Users className="h-5 w-5 text-green-500 mt-3 flex-shrink-0" />
                          <div className="flex-1">
                            <label className="block font-medium text-gray-900 mb-1">Target Audience</label>
                            <textarea
                              ref={(el) => textareaRefs.current['target_audience'] = el}
                              value={editedData.target_audience || ''}
                              onChange={(e) => handleFieldChange('target_audience', e.target.value)}
                              placeholder="Describe your target audience"
                              className="w-full p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[80px]"
                            />
                          </div>
                        </div>
                        
                        <div className="flex items-start space-x-3">
                          <Target className="h-5 w-5 text-purple-500 mt-3 flex-shrink-0" />
                          <div className="flex-1">
                            <label className="block font-medium text-gray-900 mb-1">Market Need</label>
                            <textarea
                              ref={(el) => textareaRefs.current['market_need'] = el}
                              value={editedData.market_need || ''}
                              onChange={(e) => handleFieldChange('market_need', e.target.value)}
                              placeholder="Describe the market need you address"
                              className="w-full p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[80px]"
                            />
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex items-start space-x-3">
                          <Lightbulb className="h-5 w-5 text-yellow-500 mt-3 flex-shrink-0" />
                          <div className="flex-1">
                            <label className="block font-medium text-gray-900 mb-1">Core Value Proposition</label>
                            <textarea
                              ref={(el) => textareaRefs.current['core_value_prop'] = el}
                              value={editedData.core_value_prop || ''}
                              onChange={(e) => handleFieldChange('core_value_prop', e.target.value)}
                              placeholder="Describe your core value proposition"
                              className="w-full p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[80px]"
                            />
                          </div>
                        </div>
                        
                        <div className="flex items-start space-x-3">
                          <Building className="h-5 w-5 text-indigo-500 mt-3 flex-shrink-0" />
                          <div className="flex-1">
                            <label className="block font-medium text-gray-900 mb-1">Company Description</label>
                            <textarea
                              ref={(el) => textareaRefs.current['context_description'] = el}
                              value={editedData.context_description || ''}
                              onChange={(e) => handleFieldChange('context_description', e.target.value)}
                              placeholder="Provide a detailed company description"
                              className="w-full p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[100px]"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Side - Actions */}
            <div className="w-64">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                
                <button
                  onClick={() => setShowPDFUploader(true)}
                  className="w-full flex items-center justify-center px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Upload className="h-5 w-5 mr-2" />
                  Upload Documents
                </button>
                
                <p className="text-sm text-gray-500 mt-2">
                  Add PDFs to your knowledge base for better content generation
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* PDF Uploader Modal */}
      <PDFUploader 
        isOpen={showPDFUploader} 
        onClose={() => setShowPDFUploader(false)} 
      />
    </div>
  );
};

export default CompanyDataPage;
