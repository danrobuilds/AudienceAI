'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader, ImageIcon, Plus, Trash2, ChevronDown, ChevronUp, ExternalLink, LogOut } from 'lucide-react';
import { userQueriesAPI } from '../services/api';
import PDFUploader from '../components/PDFUploader';
import SourcesDisplay from '../components/SourcesDisplay';
import Sidebar from '../components/Sidebar';
import { getTenantId } from '../services/auth';

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentGenerationId = searchParams.get('id');
  
  // State management
  const [userPrompt, setUserPrompt] = useState("");
  const [followupPrompt, setFollowupPrompt] = useState("");
  const [processing, setProcessing] = useState(false);
  const [showPDFUploader, setShowPDFUploader] = useState(false);
  const [selectedModality, setSelectedModality] = useState("linkedin");
  const [generateImage, setGenerateImage] = useState(false);
  const [generations, setGenerations] = useState([]);
  const [currentGeneration, setCurrentGeneration] = useState(null);
  const [logsExpanded, setLogsExpanded] = useState(false);
  const [processingSteps, setProcessingSteps] = useState([]);
  const [isInitialGeneration, setIsInitialGeneration] = useState(false);
  const textareaRef = useRef(null);
  const userPromptRef = useRef(null);
  const followupPromptRef = useRef(null);
  const justCreatedGenerationId = useRef(null);

  // Modality options
  const modalityOptions = [
    { id: 'linkedin', label: 'LinkedIn', emoji: '💼' },
    { id: 'blog', label: 'Blog', emoji: '📝' },
    { id: 'twitter', label: 'Twitter', emoji: '🐦' },
    { id: 'instagram', label: 'Instagram', emoji: '📸' },
  ];

  // Helper function to save generations to localStorage without images (max 5 entries)
  const saveGenerationsToStorage = (generationsArray) => {
    const generationsForStorage = generationsArray
      .slice(0, 5) // Keep only the 5 most recent generations
      .map(gen => ({
        ...gen,
        generatedImages: [] // Don't store images in localStorage to avoid size limits
      }));
    localStorage.setItem('audienceai_generations', JSON.stringify(generationsForStorage));
  };

  // Simulate processing steps for better UX
  const simulateProcessingSteps = (isFollowup = false) => {
    const steps = isFollowup ? [
      'Analyzing your modification request...',
      'Updating content strategy...',
      'Refining the content...',
      'Finalizing changes...'
    ] : [
      'Understanding your request...',
      'Researching relevant information...',
      'Crafting content optimized for your audience...',
      'Writing final output...'
    ];
    
    setProcessingSteps([]);
    
    steps.forEach((step, index) => {
      setTimeout(() => {
        setProcessingSteps(prev => [...prev, { text: step, completed: false }]);
      }, index * 10000);
    });
  };

  // Load generations from localStorage and handle URL changes
  useEffect(() => {
    const savedGenerations = localStorage.getItem('audienceai_generations');
    if (savedGenerations) {
      try {
        const parsedGenerations = JSON.parse(savedGenerations);
        setGenerations(parsedGenerations);
        
        if (currentGenerationId) {
          const current = parsedGenerations.find(g => g.id === currentGenerationId);
          if (current) {
            // Don't override if we just created this generation (it has images in memory)
            if (justCreatedGenerationId.current !== currentGenerationId) {
              setCurrentGeneration(current);
            }
          }
        } else {
          // If no generation ID in URL, clear current generation (new generation view)
          setCurrentGeneration(null);
          justCreatedGenerationId.current = null;
        }
      } catch (error) {
        console.error('Error loading generations:', error);
      }
    } else if (!currentGenerationId) {
      // If no saved generations and no current generation ID, ensure we're in new generation view
      setCurrentGeneration(null);
    }
  }, [currentGenerationId]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea && currentGeneration?.generatedPost) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.max(textarea.scrollHeight, 200) + 'px';
    }
  }, [currentGeneration?.generatedPost]);

  // Auto-resize user prompt textarea
  useEffect(() => {
    const textarea = userPromptRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.max(textarea.scrollHeight, 48) + 'px'; // min height of 48px (h-12)
    }
  }, [userPrompt]);

  // Auto-resize follow-up prompt textarea
  useEffect(() => {
    const textarea = followupPromptRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.max(textarea.scrollHeight, 48) + 'px'; // min height of 48px (h-12)
    }
  }, [followupPrompt]);

  // Handle post generation
  const handleGeneratePost = async () => {
    if (!userPrompt.trim()) {
      alert("Please enter a prompt for the post.");
      return;
    }

    setProcessing(true);
    setIsInitialGeneration(true);
    simulateProcessingSteps(false);

    // Create a pending generation immediately and switch to content view
    const generationId = Date.now().toString();
    const pendingGeneration = {
      id: generationId,
      userPrompt: userPrompt,
      selectedModality: selectedModality,
      generatedPost: '',
      generatedImages: [],
      logs: [],
      timestamp: new Date().toISOString(),
      isLoading: true
    };

    setCurrentGeneration(pendingGeneration);
    router.push(`/dashboard?id=${generationId}`, undefined, { shallow: true });

    try {
      const response = await userQueriesAPI.generateContent(userPrompt, selectedModality, generateImage);
      
      if (response.success && response.content) {
        let post_content = '';
        let generated_images = [];
        let logs = [];
        
        if (typeof response.content === 'object') {
          post_content = response.content.post_content || response.content.content || '';
          generated_images = response.content.generated_images || [];
          logs = response.content.logs || [];
          
          // Debug: Confirm images are being parsed
          if (generated_images.length > 0) {
            console.log(`✅ Parsed ${generated_images.length} generated images`);
          }
        } else {
          post_content = response.content;
        }
        
        const completedGeneration = {
          id: generationId,
          userPrompt: userPrompt,
          selectedModality: selectedModality,
          generatedPost: post_content,
          generatedImages: generated_images,
          logs: logs,
          timestamp: new Date().toISOString(),
          isLoading: false
        };

        const updatedGenerations = [completedGeneration, ...generations].slice(0, 5);
        setGenerations(updatedGenerations);
        saveGenerationsToStorage(updatedGenerations);

        // Track this generation as just created (has images in memory)
        justCreatedGenerationId.current = generationId;

        // Update current generation
        setCurrentGeneration(completedGeneration);
        
        // Reset form
        setUserPrompt("");
      }
    } catch (error) {
      console.error("Generation error:", error);
      // Handle error - could show error state in the content view
    } finally {
      setProcessing(false);
      setIsInitialGeneration(false);
      setProcessingSteps([]);
    }
  };

  const handleDeleteGeneration = (generationId) => {
    const updatedGenerations = generations.filter(g => g.id !== generationId);
    setGenerations(updatedGenerations);
    saveGenerationsToStorage(updatedGenerations);
    
    if (generationId === currentGenerationId) {
      setCurrentGeneration(null);
      router.push('/dashboard', undefined, { shallow: true });
    }
  };

  const handlePostChange = (e) => {
    const newContent = e.target.value;
    const updatedGeneration = { ...currentGeneration, generatedPost: newContent };
    setCurrentGeneration(updatedGeneration);
    
    const updatedGenerations = generations.map(g => 
      g.id === currentGeneration.id ? updatedGeneration : g
    );
    setGenerations(updatedGenerations);
    saveGenerationsToStorage(updatedGenerations);
  };

  const handleFollowup = async () => {
    if (!currentGeneration || !followupPrompt.trim()) return;
    setProcessing(true);
    simulateProcessingSteps(true);
    
    try {
      // Prepare existing content for the followup API
      const existingContent = {
        post_content: currentGeneration.generatedPost,
        modality: currentGeneration.selectedModality,
        image_description: currentGeneration.imageDescription || ""
      };
      
      const response = await userQueriesAPI.followupQuery(
        followupPrompt,
        existingContent,
        currentGeneration.selectedModality
      );
      
      if (response.success && response.content) {
        let post_content = '';
        let generated_images = [];
        let logs = [];
        
        if (typeof response.content === 'object') {
          post_content = response.content.post_content || response.content.content || '';
          generated_images = response.content.generated_images || [];
          logs = response.content.logs || [];
        } else {
          post_content = response.content;
        }
        
        const updatedGeneration = {
          ...currentGeneration,
          generatedPost: post_content,
          generatedImages: generated_images,
          logs: logs,
          timestamp: new Date().toISOString()
        };
        
        // Track this generation as just updated (has images in memory)
        justCreatedGenerationId.current = currentGeneration.id;
        
        setCurrentGeneration(updatedGeneration);
        
        const updatedGenerations = generations.map(g => 
          g.id === currentGeneration.id ? updatedGeneration : g
        );
        setGenerations(updatedGenerations);
        saveGenerationsToStorage(updatedGenerations);
        
        // Clear the follow-up prompt
        setFollowupPrompt("");
      }
    } catch (error) {
      console.error('Follow-up error:', error);
    } finally {
      setProcessing(false);
      setProcessingSteps([]);
    }
  };

  // Handle generation selection from the main content area (not sidebar)
  const handleSelectGeneration = (generationId) => {
    const generation = generations.find(g => g.id === generationId);
    // Clear the "just created" flag when manually navigating
    justCreatedGenerationId.current = null;
    setCurrentGeneration(generation);
    router.push(`/dashboard?id=${generationId}`, undefined, { shallow: true });
  };

  // Handle key press for user prompt
  const handleUserPromptKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !processing) {
      e.preventDefault();
      handleGeneratePost();
    }
  };

  // Handle key press for follow-up prompt
  const handleFollowupPromptKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !processing) {
      e.preventDefault();
      handleFollowup();
    }
  };

  return (
    <div className="min-h-screen bg-white flex">
      {/* Sidebar */}
      <Sidebar currentPage="dashboard" />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {currentGeneration ? (
          /* Generated Post View */
          <div className="flex-1 flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-semibold text-gray-900">
                    {currentGeneration.isLoading ? 'Creating Content...' : 'Content Created'}
                  </h1>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6">
              <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-5 gap-8">
                {/* Left Column - Details */}
                <div className="lg:col-span-2 space-y-6">
                  <div>
                    <h2 className="text-lg font-semibold mb-4">Details</h2>
                    
                    <div className="">
                      <div>
                        <textarea
                          value={currentGeneration.userPrompt}
                          readOnly
                          className="w-full rounded-lg text-gray-700 resize-none focus:outline-none"
                        />
                      </div>

                      <div className="flex items-center space-x-4">
                        <div className="flex items-center">
                          <span className="inline-flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                            {modalityOptions.find(m => m.id === currentGeneration.selectedModality)?.emoji}
                            {modalityOptions.find(m => m.id === currentGeneration.selectedModality)?.label}
                          </span>
                        </div>
                        <div className="flex items-center">
                          <label className="text-sm font-medium text-gray-700 mr-2">Created:</label>
                          <span className="text-sm text-gray-600">
                            {new Date(currentGeneration.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* Spacer to push platform info to align with bottom of content */}
                      <div className="flex-1"></div>
                      <div className="space-y-4"></div>
                      
                      {/* Modify Content Section */}
                      {!currentGeneration.isLoading && (
                        <div className="mt-8">
                          <div className="flex items-start gap-2">
                            <textarea
                              ref={followupPromptRef}
                              value={followupPrompt}
                              onChange={(e) => setFollowupPrompt(e.target.value)}
                              onKeyPress={handleFollowupPromptKeyPress}
                              placeholder="Ask me to modify this content..."
                              className="flex-1 min-h-[48px] max-h-[120px] px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                              rows="1"
                              disabled={processing}
                            />
                            <button
                              onClick={handleFollowup}
                              disabled={processing || !followupPrompt.trim()}
                              className="h-12 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm whitespace-nowrap"
                            >
                              {processing ? (
                                <div className="flex items-center">
                                  <Loader className="animate-spin h-4 w-4 mr-2" />
                                  Updating...
                                </div>
                              ) : (
                                'Update'
                              )}
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Inline Loading Indicators */}
                      {processing && processingSteps.length > 0 && (
                        <div className="border border-blue-200 rounded-lg p-4 bg-blue-50 mt-8">
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-sm font-medium text-blue-900">
                              {isInitialGeneration ? 'Creating your content...' : 'Updating your content...'}
                            </span>
                          </div>
                          <div className="space-y-2">
                            {processingSteps.map((step, index) => (
                              <div key={index} className="flex items-center gap-2">
                                <div className="flex-shrink-0">
                                  {step.completed ? (
                                    <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                                      <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                      </svg>
                                    </div>
                                  ) : (
                                    <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                                      <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                                    </div>
                                  )}
                                </div>
                                <p className="text-xs text-blue-800">{step.text}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  

                  {/* Platform, Created, Logs, and Sources - positioned at bottom */}
                  <div className="space-y-4">

                    {/* Logs Dropdown */}
                    {currentGeneration.logs && currentGeneration.logs.length > 0 && (
                      <div>
                        <button
                          onClick={() => setLogsExpanded(!logsExpanded)}
                          className="flex items-center justify-between w-full text-left text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 p-3 rounded-lg transition-colors"
                        >
                          <span>Logs</span>
                          {logsExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </button>
                        {logsExpanded && (
                          <div className="mt-2 p-3 bg-gray-50 rounded-lg max-h-60 overflow-y-auto">
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                              {Array.isArray(currentGeneration.logs) ? currentGeneration.logs.join('\n') : currentGeneration.logs}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Sources Display */}
                    {currentGeneration.logs && currentGeneration.logs.length > 0 && (
                      <SourcesDisplay logs={currentGeneration.logs} />
                    )}
                  </div>
                </div>

                {/* Right Column - Generated Content */}
                <div className="lg:col-span-3">
                  <h2 className="text-lg font-semibold mb-4">Content</h2>
                  
                  {currentGeneration.isLoading ? (
                    <div className="w-full min-h-[400px] border border-gray-200 rounded-lg p-4 bg-gray-50 flex items-center justify-center">
                      <div className="text-center">
                        <Loader className="animate-spin h-8 w-8 text-blue-500 mx-auto mb-4" />
                        <p className="text-gray-600">Your content is being written...</p>
                      </div>
                    </div>
                  ) : (
                    <textarea
                      ref={textareaRef}
                      value={currentGeneration.generatedPost}
                      onChange={handlePostChange}
                      placeholder="Generated post content..."
                      className="w-full min-h-[400px] p-4 resize-none focus:outline-none"
                    />
                  )}

                  {/* Generated Images */}
                  {currentGeneration.generatedImages && currentGeneration.generatedImages.length > 0 && (
                    <div className="mt-6">
                      <h3 className="text-lg font-semibold mb-4">Generated Images ({currentGeneration.generatedImages.length})</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {currentGeneration.generatedImages.map((image, index) => (
                          <div 
                            key={index} 
                            className="relative group cursor-pointer"
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = `data:image/png;base64,${image.base64_data}`;
                              link.download = image.filename || `generated_image_${index + 1}.png`;
                              link.click();
                            }}
                          >
                            <img
                              src={`data:image/png;base64,${image.base64_data}`}
                              alt={`Generated image ${index + 1}`}
                              className="w-full h-auto rounded-lg shadow-md hover:shadow-lg transition-shadow"
                            />
                            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
                              <span className="text-white text-sm font-medium">Download</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* New Generation View */
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="max-w-2xl w-full">
              <h1 className="text-4xl font-semibold text-gray-900 mb-2">Hi, I'm Audy.</h1>
              <h2 className="text-2xl text-gray-600 mb-4">What should I work on?</h2>
              
              {/* Input */}
              <div className="flex items-start gap-4 mb-6">
                <div className="flex-1">
                  <textarea
                    ref={userPromptRef}
                    value={userPrompt}
                    onChange={(e) => setUserPrompt(e.target.value)}
                    onKeyPress={handleUserPromptKeyPress}
                    placeholder="e.g., Write a post about the future of AI in my industry..."
                    className="w-full min-h-[48px] max-h-[200px] px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none overflow-y-auto"
                    rows="1"
                  />
                </div>
                <button
                  onClick={handleGeneratePost}
                  disabled={processing || !userPrompt.trim()}
                  className="h-12 px-6 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {processing ? (
                    <div className="flex items-center">
                      <Loader className="animate-spin h-4 w-4 mr-2" />
                      Working...
                    </div>
                  ) : (
                    "Create"
                  )}
                </button>
              </div>

              {/* Platform Selection */}
              <div className="mb-6">
                <div className="flex items-center gap-4 mb-2">
                  <span className="text-sm font-medium text-gray-700">Platform:</span>
                  <div className="flex gap-2">
                    {modalityOptions.map((option) => (
                      <button
                        key={option.id}
                        onClick={() => setSelectedModality(option.id)}
                        className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                          selectedModality === option.id
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        <span className="mr-1">{option.emoji}</span>
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Image Generation Toggle */}
              <div className="mb-8">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setGenerateImage(!generateImage)}
                    className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-full transition-colors ${
                      generateImage
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <ImageIcon className="h-4 w-4" />
                    Generate Image
                  </button>
                  <span className="text-xs text-gray-500">
                    {generateImage ? 'Image will be generated' : 'Text only'}
                  </span>
                </div>
              </div>

              {/* Recent Generations */}
              {generations.length > 0 && (
                <div className="mt-12">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Previous Content</h3>
                  <div className="space-y-2">
                    {generations.slice(0, 5).map((generation) => (
                      <div
                        key={generation.id}
                        className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                        onClick={() => handleSelectGeneration(generation.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">
                              {modalityOptions.find(m => m.id === generation.selectedModality)?.emoji}
                            </span>
                            <span className="text-sm text-gray-700 truncate">
                              {generation.userPrompt.substring(0, 60)}...
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">
                              {new Date(generation.timestamp).toLocaleDateString()}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteGeneration(generation.id);
                              }}
                              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* PDF Uploader */}
      <PDFUploader 
        isOpen={showPDFUploader} 
        onClose={() => setShowPDFUploader(false)} 
      />
    </div>
  );
}

// Loading component for Suspense fallback
function DashboardLoading() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="flex items-center">
        <Loader className="animate-spin h-8 w-8 text-blue-500 mr-4" />
        <div>
          <h3 className="text-lg font-semibold">Loading Dashboard...</h3>
          <p className="text-gray-600">Please wait while we prepare your content.</p>
        </div>
      </div>
    </div>
  );
}

// Main component wrapped in Suspense
export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardLoading />}>
      <DashboardContent />
    </Suspense>
  );
} 