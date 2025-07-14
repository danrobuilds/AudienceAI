import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, LogOut, Building, Home } from 'lucide-react';
import { clearTenantId } from '../services/auth';

const Sidebar = ({ currentPage = 'dashboard' }) => {
  const router = useRouter();
  const [generations, setGenerations] = useState([]);
  const [currentGenerationId, setCurrentGenerationId] = useState(null);

  // Modality options for sidebar
  const modalityOptions = [
    { id: 'linkedin', label: 'LinkedIn', emoji: '💼' },
    { id: 'blog', label: 'Blog', emoji: '📝' },
    { id: 'twitter', label: 'Twitter', emoji: '🐦' },
    { id: 'instagram', label: 'Instagram', emoji: '📸' },
  ];

  // Load generations from localStorage
  useEffect(() => {
    const savedGenerations = localStorage.getItem('audienceai_generations');
    if (savedGenerations) {
      try {
        const parsedGenerations = JSON.parse(savedGenerations);
        setGenerations(parsedGenerations);
      } catch (error) {
        console.error('Error loading generations:', error);
      }
    }

    // Get current generation ID from URL if on dashboard
    if (currentPage === 'dashboard') {
      const urlParams = new URLSearchParams(window.location.search);
      const generationId = urlParams.get('id');
      if (generationId) {
        setCurrentGenerationId(generationId);
      }
    }
  }, [currentPage]);

  const handleNavigate = (page) => {
    if (page === 'dashboard') {
      router.push('/dashboard');
    } else if (page === 'company-data') {
      router.push('/dashboard/company-data');
    }
  };

  const handleNewGeneration = () => {
    router.push('/dashboard');
  };

  const handleSelectGeneration = (generationId) => {
    router.push(`/dashboard?id=${generationId}`);
  };

  const handleSignOut = () => {
    clearTenantId();
    localStorage.removeItem('audienceai_generations');
    router.push('/signin');
  };

  return (
    <div className="w-20 flex flex-col items-center py-4 space-y-3 border-r border-gray-100">
      {/* Navigation Options */}
      <div className="flex flex-col space-y-2">
        {/* Company Data */}
        <button
          onClick={() => handleNavigate('company-data')}
          className={`w-16 h-16 rounded-lg flex items-center justify-center transition-colors shadow-sm ${
            currentPage === 'company-data'
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          title="Company Data"
        >
          <Building className="h-6 w-6" />
        </button>

        {/* Dashboard */}
        <button
          onClick={() => handleNavigate('dashboard')}
          className={`w-16 h-16 rounded-lg flex items-center justify-center transition-colors shadow-sm ${
            currentPage === 'dashboard'
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          title="Content Dashboard"
        >
          <Home className="h-6 w-6" />
        </button>
      </div>

      {/* Separator */}
      <div className="w-12 h-px bg-gray-200 my-2"></div>

      {/* Dashboard-specific actions */}
      {currentPage === 'dashboard' && (
        <>
          {/* New Generation Button */}
          <button
            onClick={handleNewGeneration}
            className="w-16 h-16 bg-blue-500 text-white rounded-lg flex items-center justify-center hover:bg-blue-600 transition-colors shadow-md"
            title="New Generation"
          >
            <Plus className="h-6 w-6" />
          </button>
          
          {/* Generation History */}
          <div className="flex flex-col space-y-2 max-h-[calc(100vh-400px)] overflow-y-auto">
            {generations.slice(0, 10).map((generation) => (
              <button
                key={generation.id}
                onClick={() => handleSelectGeneration(generation.id)}
                className={`w-16 h-16 rounded-lg flex flex-col items-center justify-center p-1 transition-colors shadow-sm ${
                  generation.id === currentGenerationId
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title={generation.userPrompt}
              >
                <span className="text-lg mb-1">
                  {modalityOptions.find(m => m.id === generation.selectedModality)?.emoji}
                </span>
                <span className="text-[10px] text-center leading-tight w-full px-1 overflow-hidden">
                  {generation.userPrompt.split(' ').slice(0, 2).join(' ')}
                  {generation.userPrompt.split(' ').length > 2 && '...'}
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {/* Sign Out Button */}
      <div className="mt-auto">
        <button
          onClick={handleSignOut}
          className="w-16 h-16 bg-red-100 text-red-600 rounded-lg flex items-center justify-center hover:bg-red-200 transition-colors shadow-sm"
          title="Sign Out"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 