// Utility functions for extracting source information from generation logs

/**
 * Extract PDF sources from logs
 */
export function extractPDFSources(logs) {
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
export function extractWebSources(logs) {
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
export function extractViralPostSources(logs) {
  const viralSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Extract viral posts from "Example X:" pattern
  const examplePattern = /Example \d+:\s*\n\s*Similarity: ([\d.]+)\s*\n\s*Interactions: \d+\s*\n\s*Content: Content: (.+?)(?=\n\nExample|\n\nCalling|\n\nViral|$)/gs;
  let match;
  
  while ((match = examplePattern.exec(logText)) !== null) {
    const similarityScore = match[1].trim();
    const content = match[2].trim();
    
    // Only add if we haven't seen this content before
    if (!viralSources.some(source => source.content === content)) {
      // Use first 100 characters as title
      const title = content.substring(0, 100) + (content.length > 100 ? '...' : '');
      
      viralSources.push({
        title: title,
        content: content,
        similarityScore: similarityScore
      });
    }
  }
  
  return viralSources;
}

/**
 * Extract all sources from logs
 */
export function extractSourcesFromLogs(logs) {
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

/**
 * Check if there are any sources in the extracted sources object
 */
export function hasAnySources(sources) {
  if (!sources) return false;
  
  return (
    (sources.pdfs && sources.pdfs.length > 0) ||
    (sources.webArticles && sources.webArticles.length > 0) ||
    (sources.viralPosts && sources.viralPosts.length > 0)
  );
}

/**
 * Get total count of all sources
 */
export function getTotalSourceCount(sources) {
  if (!sources) return 0;
  
  return (
    (sources.pdfs ? sources.pdfs.length : 0) +
    (sources.webArticles ? sources.webArticles.length : 0) +
    (sources.viralPosts ? sources.viralPosts.length : 0)
  );
} 