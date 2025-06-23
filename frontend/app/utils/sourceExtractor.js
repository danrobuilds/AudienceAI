// Utility functions for extracting source information from generation logs

/**
 * Extract PDF sources from logs
 */
export function extractPDFSources(logs) {
  const pdfSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // First, extract PDF names from various patterns
  const pdfNames = new Set();
  
  // Pattern 1: "Source PDF: filename.pdf"
  const pdfPattern1 = /Source PDF: (.+?)(?:\n|$)/g;
  let match;
  
  while ((match = pdfPattern1.exec(logText)) !== null) {
    const pdfInfo = match[1].trim();
    if (pdfInfo) {
      pdfNames.add(pdfInfo);
    }
  }
  
  // Pattern 2: "Source PDFs used: • filename1.pdf • filename2.pdf"
  const pdfPattern2 = /Source PDFs used:\s*\n?(.+?)(?:\n\n|$)/gs;
  while ((match = pdfPattern2.exec(logText)) !== null) {
    const pdfList = match[1];
    // Extract individual PDF names from bullet list
    const pdfMatches = pdfList.match(/•\s*([^•\n]+)/g);
    if (pdfMatches) {
      pdfMatches.forEach(pdfMatch => {
        const pdfName = pdfMatch.replace(/^•\s*/, '').trim();
        if (pdfName) {
          pdfNames.add(pdfName);
        }
      });
    }
  }
  
  // Now extract PDF URLs from "Document Access URLs" section
  const urlPattern = /Document Access URLs[^:]*:\s*(.+?)(?:\n\n|---|\n\s*\n|$)/gs;
  const urlMatches = urlPattern.exec(logText);
  
  const pdfUrls = new Map();
  if (urlMatches && urlMatches[1]) {
    const urlSection = urlMatches[1];
    // Extract individual PDF URLs: "• filename.pdf: https://..."
    const urlEntries = urlSection.match(/•\s*([^:]+):\s*(https?:\/\/[^\s\n]+)/g);
    if (urlEntries) {
      urlEntries.forEach(entry => {
        const entryMatch = entry.match(/•\s*([^:]+):\s*(https?:\/\/[^\s\n]+)/);
        if (entryMatch) {
          const filename = entryMatch[1].trim();
          const url = entryMatch[2].trim();
          pdfUrls.set(filename, url);
        }
      });
    }
  }
  
  // Combine PDF names with their URLs
  pdfNames.forEach(pdfName => {
    const url = pdfUrls.get(pdfName);
    pdfSources.push({
      filename: pdfName,
      url: url || null
    });
  });
  
  return pdfSources;
}

/**
 * Extract web article sources from logs
 */
export function extractWebSources(logs) {
  const webSources = [];
  const logText = Array.isArray(logs) ? logs.join('\n') : logs;
  
  // Pattern for web search results: "Web Result X: Title: ... URL: ..."
  const webPattern = /Web Result \d+:\s*\n\s*Title: (.+?)\s*\n\s*URL: (.+?)(?:\n|$)/g;
  let match;
  
  while ((match = webPattern.exec(logText)) !== null) {
    const title = match[1].trim();
    const url = match[2].trim();
    
    if (title && url && !webSources.some(source => source.url === url)) {
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
  
  // Pattern for viral post examples: "Viral Post Example X: Content: ..."
  const viralPattern = /Viral Post Example \d+:\s*\n\s*Content: (.+?)\n.*?Similarity Score: ([\d.]+)/gs;
  let match;
  
  while ((match = viralPattern.exec(logText)) !== null) {
    const content = match[1].trim();
    const score = match[2].trim();
    
    if (content && !viralSources.some(source => source.content === content)) {
      // Extract first line or first 100 characters as title
      const title = content.split('\n')[0].substring(0, 100) + (content.length > 100 ? '...' : '');
      
      viralSources.push({
        title: title,
        content: content,
        similarityScore: score
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