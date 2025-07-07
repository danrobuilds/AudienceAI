import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

// Source extraction functions (moved from sourceExtractor.js)

/**
 * Extract PDF sources from logs
 */
function extractPDFSources(logs) {
  const pdfSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Extract PDF sources from "Segment X:" pattern
  const segmentPattern = /Segment \d+:\s*\n\s*File: (.+?\.pdf)\s*\n\s*Similarity: [\d.]+\s*\n\s*Document URL: (.+?)\s*\n/g;
  let match;
  
  while ((match = segmentPattern.exec(logText)) !== null) {
    const filename = match[1].trim();
    const url = match[2].trim();
    
    // Only add if we haven't seen this filename before
    if (!pdfSources.some(source => source.filename === filename)) {
      pdfSources.push({
        filename: filename,
        url: url
      });
    }
  }
  
  return pdfSources;
}

/**
 * Extract web article sources from logs
 */
function extractWebSources(logs) {
  const webSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Extract web sources from "Result X:" pattern
  const resultPattern = /Result \d+:\s*\n\s*Title: (.+?)\s*\n\s*URL: (.+?)\s*\n/g;
  let match;
  
  while ((match = resultPattern.exec(logText)) !== null) {
    const title = match[1].trim();
    const url = match[2].trim();
    
    // Only add if we haven't seen this URL before
    if (!webSources.some(source => source.url === url)) {
      webSources.push({
        title: title,
        url: url
      });
    }
  }
  
  return webSources;
}

/**
 * Extract viral post sources from logs
 */
function extractViralPostSources(logs) {
  const viralSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Extract viral posts from "Example X:" pattern
  // Updated pattern to match the actual log format without Interactions field
  const examplePattern = /Example \d+:\s*\n\s*Similarity: ([\d.]+)\s*\n\s*Content: (.+?)(?=\n\nExample|\nLinkedin viral content creation complete|$)/gs;
  let match;
  
  while ((match = examplePattern.exec(logText)) !== null) {
    const similarityScore = match[1].trim();
    const content = match[2].trim();
    
    console.log('SourcesDisplay: Extracted viral post:', { similarityScore, content: content.substring(0, 100) });
    
    // Only add if we haven't seen this content before
    if (!viralSources.some(source => source.content === content)) {
      // Use first 100 characters as title
      const title = content.substring(0, 100) + (content.length > 100 ? '...' : '');
      
      viralSources.push({
        title: title,
        content: content,
        similarityScore: similarityScore,
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
                {pdf.url && (
                  <a 
                    href={pdf.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 ml-2"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SourcesDisplay; 