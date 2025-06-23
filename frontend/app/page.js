'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Loader, Download, ChevronDown, ChevronUp } from 'lucide-react';
import { userQueriesAPI } from './services/api';
import { extractSourcesFromLogs, hasAnySources } from './utils/sourceExtractor';
import SourcesDisplay from './components/SourcesDisplay';
import PDFUploader from './components/PDFUploader';

export default function HomePage() {
  // State management - similar to Streamlit session state
  const [userPrompt, setUserPrompt] = useState("");
  const [generatedPost, setGeneratedPost] = useState("");
  const [generatedImages, setGeneratedImages] = useState([]);
  const [logs, setLogs] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [showPDFUploader, setShowPDFUploader] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  // Ref for the generated post textarea
  const textareaRef = useRef(null);

  // Auto-resize textarea to fit content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      // Set height to scrollHeight to fit content
      textarea.style.height = Math.max(textarea.scrollHeight, 200) + 'px';
    }
  }, [generatedPost]);

  // Handle post generation
  const handleGeneratePost = async () => {
    console.log("🔥 BUTTON CLICKED! handleGeneratePost called");
    console.log("User prompt:", userPrompt);
    
    if (!userPrompt.trim()) {
      console.log("❌ No prompt provided");
      alert("Please enter a prompt for the LinkedIn post.");
      return;
    }

    console.log("✅ Starting generation process");
    setProcessing(true);
    setLogs(["Starting LinkedIn post generation..."]);
    setGeneratedPost("");
    setGeneratedImages([]);

    try {
      console.log("🚀 Starting generation with prompt:", userPrompt);
      
      const response = await userQueriesAPI.generateContent(userPrompt);
      
      console.log("📥 API Response:", response);

      if (response.success && response.content) {
        // Handle the structured response format
        if (typeof response.content === 'object') {
          setGeneratedPost(response.content.post_content || response.content.content || '');
          setGeneratedImages(response.content.generated_images || []);
          
          // Set logs from response if available
          if (response.content.logs && Array.isArray(response.content.logs)) {
            setLogs(prev => [...prev, ...response.content.logs]);
          }
        } else {
          // Fallback for string responses
          setGeneratedPost(response.content);
        }

        // Add completion log
        setLogs(prev => [...prev, "LinkedIn post generation completed successfully!"]);
      } else {
        throw new Error(response.message || "Generation failed");
      }

    } catch (error) {
      console.error("💥 Generation error:", error);
      setLogs(prev => [...prev, `Error: ${error.message}`]);
    } finally {
      console.log("🏁 Generation process finished");
      setProcessing(false);
    }
  };

  // Handle image download
  const handleDownloadImage = (imgInfo, index) => {
    try {
      if (imgInfo.base64_data) {
        // Create download link for base64 data
        const link = document.createElement('a');
        link.href = `data:image/png;base64,${imgInfo.base64_data}`;
        link.download = imgInfo.filename || `generated_image_${index + 1}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error("Error downloading image:", error);
    }
  };

  // Extract sources from logs
  const sources = extractSourcesFromLogs(logs);
  const hasGeneratedContent = generatedPost && !processing;

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <h1 className="text-4xl font-semibold text-gray-900 mb-8">Hi, I'm Audy.</h1>

        {!hasGeneratedContent ? (
          /* Initial centered layout */
          <div className="flex flex-col items-center justify-center min-h-[50vh]">
            <h2 className="text-2xl text-center mb-8 mt-24">What should I work on?</h2>
            
            {/* Input row */}
            <div className="flex items-center gap-4 w-full max-w-4xl mb-8">
              <div className="flex-1">
                <input
                  type="text"
                  value={userPrompt}
                  onChange={(e) => setUserPrompt(e.target.value)}
                  placeholder="e.g., Write a post about the future of AI in ABL..."
                  className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && !processing && handleGeneratePost()}
                />
              </div>
              <button
                onClick={handleGeneratePost}
                disabled={processing}
                className="h-10 px-4 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {processing ? (
                  <div className="flex items-center">
                    <Loader className="animate-spin h-4 w-4 mr-2" />
                    Generating...
                  </div>
                ) : (
                  "Generate Post"
                )}
              </button>
            </div>

            {/* Upload PDFs button */}
            <div className="w-full max-w-4xl">
              <div className="flex">
                <button
                  onClick={() => {
                    console.log("🔥 PDF UPLOAD BUTTON CLICKED!");
                    setShowPDFUploader(true);
                  }}
                  className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
                >
                  Upload PDFs
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Post-generation two-column layout */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column */}
            <div>
              <h2 className="text-xl font-semibold mb-4">What should I work on?</h2>
              
              {/* Text area */}
              <textarea
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="e.g., Write a post about the future of AI in asset-based lending..."
                className="w-full h-20 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />

              {/* Action buttons */}
              <div className="flex gap-4 mt-4">
                <button
                  onClick={handleGeneratePost}
                  disabled={processing}
                  className="flex-1 h-10 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {processing ? (
                    <div className="flex items-center justify-center">
                      <Loader className="animate-spin h-4 w-4 mr-2" />
                      Generating...
                    </div>
                  ) : (
                    "Generate Post"
                  )}
                </button>
                <button
                  onClick={() => {
                    console.log("🔥 PDF UPLOAD BUTTON CLICKED (Two-column layout)!");
                    setShowPDFUploader(true);
                  }}
                  className="flex-1 h-10 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
                >
                  Upload PDFs
                </button>
              </div>

              {/* Sources Display */}
              {logs.length > 0 && !processing && hasAnySources(sources) && (
                <SourcesDisplay sources={sources} />
              )}

              {/* Generation Logs */}
              {logs.length > 0 && !processing && (
                <div className="mt-6">
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="flex items-center text-gray-700 hover:text-gray-900 mb-2"
                  >
                    {showLogs ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
                    View Generation Logs
                  </button>
                  {showLogs && (
                    <div className="bg-gray-50 border border-gray-200 rounded-md p-4 max-h-48 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                        {logs.join('\n')}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Column */}
            <div>
              <textarea
                ref={textareaRef}
                value={generatedPost}
                onChange={(e) => setGeneratedPost(e.target.value)}
                placeholder="Generated post will appear here..."
                className="w-full min-h-[200px] p-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none overflow-hidden"
              />

              {/* Generated Images */}
              {generatedImages.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-4">Generated Images:</h3>
                  <div className="space-y-4">
                    {generatedImages.map((imgInfo, index) => (
                      <div key={index}>
                        {imgInfo.base64_data ? (
                          <div>
                            <img
                              src={`data:image/png;base64,${imgInfo.base64_data}`}
                              alt={`Generated ${index + 1}`}
                              className="w-full rounded-lg shadow-sm"
                            />
                            <div className="mt-2 flex justify-between items-center">
                              <p className="text-sm text-gray-600">
                                {imgInfo.filename} ({imgInfo.size || 'Unknown size'}, {imgInfo.style || 'Unknown style'})
                              </p>
                              <button
                                onClick={() => handleDownloadImage(imgInfo, index)}
                                className="flex items-center px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                              >
                                <Download className="h-3 w-3 mr-1" />
                                Download
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="text-gray-500 text-sm">
                            Image not available: {imgInfo.filename}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* PDF Uploader */}
        <PDFUploader 
          isOpen={showPDFUploader} 
          onClose={() => setShowPDFUploader(false)} 
        />

        {/* Processing Overlay */}
        {processing && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-8 rounded-lg shadow-lg">
              <div className="flex items-center">
                <Loader className="animate-spin h-8 w-8 text-blue-500 mr-4" />
                <div>
                  <h3 className="text-lg font-semibold">Generating LinkedIn post...</h3>
                  <p className="text-gray-600">Please wait while we create your content.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 