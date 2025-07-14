import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

// Source extraction functions (moved from sourceExtractor.js)

/**
 * Extract PDF sources from logs
 */
function extractPDFSources(logs) {
  const pdfSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Match “Document Title: …” then any lines of content up to “Document URL: …”
  const segmentPattern = 
    /Document Title:\s*(.+?)\s*\nDocument Content:\s*([\s\S]+?)\s*\nDocument URL:\s*([^\s\n]+)/g;
  let match;
  
  while ((match = segmentPattern.exec(logText)) !== null) {
    const [, filename, rawContent, url] = match;
    // collapse newlines in the snippet to a single space
    const content = rawContent.trim().replace(/\s+/g, ' ');
    
    if (!pdfSources.some(src => src.url === url)) {
      pdfSources.push({
        filename: filename.trim(),
        content,
        url: url.trim() !== 'None' ? url.trim() : null
      });
    }
  }
  
  return pdfSources;
}

/**
 * Extract web article sources from logs produced by format_output_for_log("web_search")
 */
function extractWebSources(logs) {
  const webSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Match “Web Title: …” then “Web Content: …” then “WebURL: …”
  const resultPattern = 
    /Web Title:\s*(.+?)\s*\nWeb Content:\s*([\s\S]+?)\s*\nWebURL:\s*([^\s\n]+)/g;
  let match;
  
  while ((match = resultPattern.exec(logText)) !== null) {
    const [, title, rawContent, url] = match;
    const content = rawContent.trim().replace(/\s+/g, ' ');
    
    if (!webSources.some(src => src.url === url)) {
      webSources.push({
        title: title.trim(),
        content,
        url: url.trim()
      });
    }
  }
  
  return webSources;
}

/**
 * Extract viral post sources from logs produced by format_output_for_log("search_linkedin_posts")
 */
function extractViralPostSources(logs) {
  const viralSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Match “Post Content: …” then “Similarity Score: …”
  const postPattern = 
    /Post Content:\s*(.+?)\s*\nSimilarity Score:\s*([\d.]+)/g;
  let match;
  
  while ((match = postPattern.exec(logText)) !== null) {
    const [, rawContent, similarityScore] = match;
    const content = rawContent.trim().replace(/\s+/g, ' ');
    
    if (!viralSources.some(src => src.content === content)) {
      viralSources.push({
        title: content.slice(0, 100) + (content.length > 100 ? '...' : ''),
        content,
        similarityScore: similarityScore.trim()
      });
    }
  }
  
  return viralSources;
}

/**
 * Extract all sources from logs
 */
function extractSourcesFromLogs(logs) {
  if (!logs || logs.length === 0) {
    return {
      pdfs: [],
      webArticles: [],
      viralPosts: []
    };
  }

  return {
    pdfs: extractPDFSources(logs),
    webArticles: extractWebSources(logs),
    viralPosts: extractViralPostSources(logs)
  };
}

// Main Sources Display Component
const SourcesDisplay = ({ sources, logs }) => {
  const [expanded, setExpanded] = useState(true);
  
  // If logs are provided, extract sources from them
  const extractedSources = logs ? extractSourcesFromLogs(logs) : sources;
  
  if (!extractedSources || Object.values(extractedSources).every(arr => arr.length === 0)) {
    return null;
  }

  const totalSources = Object.values(extractedSources).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-100">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="text-sm font-medium text-gray-700">
          📚 Sources ({totalSources})
        </span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      
      {expanded && (
        <div className="mt-3 space-y-2">
          {extractedSources.pdfs && extractedSources.pdfs.map((pdf, index) => (
            <div key={index} className="text-xs text-gray-600 bg-white p-2 rounded border-l-2 border-blue-300">
              <div className="flex items-center justify-between">
                <span>📄 {pdf.filename}</span>
                <div className="flex items-center gap-2">
                  {pdf.similarityScore && (
                    <span className="text-blue-600">
                      {Math.round(pdf.similarityScore * 100)}%
                    </span>
                  )}
                  {pdf.url && (
                    <a 
                      href={pdf.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
          {extractedSources.webArticles && extractedSources.webArticles.map((article, index) => (
            <div key={index} className="text-xs text-gray-600 bg-white p-2 rounded border-l-2 border-green-300">
              <div className="flex items-center justify-between">
                <span>🌐 {article.title}</span>
                {article.url && (
                  <a 
                    href={article.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-green-600 hover:text-green-800 ml-2"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
          {extractedSources.viralPosts && extractedSources.viralPosts.map((post, index) => (
            <div key={index} className="text-xs text-gray-600 bg-white p-2 rounded border-l-2 border-purple-300">
              <div className="flex items-center justify-between">
                <span>💼 {post.title}</span>
                <div className="flex items-center gap-2 ml-2">
                  {post.similarityScore && (
                    <span className="text-purple-600">
                      {Math.round(post.similarityScore * 100)}%
                    </span>
                  )}
                </div>
              </div>
              {post.targetAudience && (
                <div className="text-xs text-gray-500 mt-1">
                  <strong>Target:</strong> {post.targetAudience.substring(0, 50)}...
                </div>
              )}
              {post.mediaDescription && (
                <div className="text-xs text-gray-500 mt-1">
                  <strong>Media:</strong> {post.mediaDescription.substring(0, 50)}...
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SourcesDisplay; 