/**
 * Extract source information from generation logs
 * @param {string[]} logs - Array of log messages
 * @returns {Object} Sources object with categorized sources
 */
export const extractSourcesFromLogs = (logs) => {
  const sources = {
    pdfs: [],
    news: [],
    posts: [],
    web: []
  };

  // Combine all logs into a single string for pattern matching
  const currentLog = logs.join('\n');

  // Extract PDF sources - look for "Source PDF:" pattern and document URLs
  if (currentLog.includes('Source PDF:')) {
    const pdfMatches = currentLog.match(/Source PDF: ([^\n]+)/g);
    if (pdfMatches) {
      const pdfSources = pdfMatches.map(match => match.replace('Source PDF: ', '').trim());
      sources.pdfs = [...new Set(pdfSources)].map(filename => ({ filename, url: null })); // Initialize with no URLs
    }
  }

  // Extract document access URLs and match them to PDF sources
  if (currentLog.includes('Document Access URLs')) {
    const urlSection = currentLog.match(/Document Access URLs \(valid for [^)]+\):\n([\s\S]*?)(?=\n\n|\n---|\nSource PDFs used:|$)/);
    
    if (urlSection && urlSection[1]) {
      const urlMatches = urlSection[1].match(/• ([^:]+): (https?:\/\/[^\s\n]+)/g);
      
      if (urlMatches) {
        urlMatches.forEach(match => {
          const [, filename, url] = match.match(/• ([^:]+): (https?:\/\/[^\s\n]+)/);
          if (filename && url) {
            // Find the corresponding PDF source and add the URL
            const pdfIndex = sources.pdfs.findIndex(pdf => 
              typeof pdf === 'object' ? pdf.filename === filename.trim() : pdf === filename.trim()
            );
            
            if (pdfIndex !== -1) {
              // Update existing PDF source with URL
              sources.pdfs[pdfIndex] = {
                filename: filename.trim(),
                url: url.trim()
              };
            } else {
              // Add new PDF source with URL if not found
              sources.pdfs.push({
                filename: filename.trim(),
                url: url.trim()
              });
            }
          }
        });
      }
    }
  }

  // Ensure all PDF sources have the correct structure (filename, url)
  sources.pdfs = sources.pdfs.map(pdf => {
    if (typeof pdf === 'string') {
      return { filename: pdf, url: null };
    }
    return pdf;
  });

  // Extract news article sources - look for "Article X:" pattern
  if (currentLog.includes('Article ') && currentLog.includes('Title:')) {
    const articleBlocks = currentLog.match(/Article \d+:\s*\n\s*Title: ([^\n]+)\s*\n\s*Source: ([^\n]+)[\s\S]*?\n\s*URL: (https?:\/\/[^\s\n]+)/gm);
    
    if (articleBlocks) {
      articleBlocks.forEach(block => {
        const titleMatch = block.match(/Title: ([^\n]+)/);
        const sourceMatch = block.match(/Source: ([^\n]+)/);
        const urlMatch = block.match(/URL: (https?:\/\/[^\s\n]+)/);
        
        if (titleMatch && sourceMatch && urlMatch) {
          const title = titleMatch[1].trim();
          const source = sourceMatch[1].trim();
          const url = urlMatch[1].trim();
          
          if (title && title !== 'N/A') {
            sources.news.push({
              title,
              url,
              source
            });
          }
        }
      });
    }
  }

  // Extract web search results - look for "Result X:" pattern (different from news articles)
  if (currentLog.includes('MCP Tool: Searching web') || 
      (currentLog.includes('Result ') && currentLog.includes('Title:') && currentLog.includes('URL:'))) {
    const webBlocks = currentLog.match(/Result \d+:\s*\n\s*Title: ([^\n]+)\s*\n\s*URL: (https?:\/\/[^\s\n]+)/gm);
    
    if (webBlocks) {
      webBlocks.forEach(block => {
        const titleMatch = block.match(/Title: ([^\n]+)/);
        const urlMatch = block.match(/URL: (https?:\/\/[^\s\n]+)/);
        
        if (titleMatch && urlMatch) {
          const title = titleMatch[1].trim();
          const url = urlMatch[1].trim();
          
          if (title && title !== 'N/A' && !url.toLowerCase().includes('newsapi')) {
            sources.web.push({
              title,
              url
            });
          }
        }
      });
    }
  }

  // Extract viral post sources - look for "Viral Post Example X:" pattern
  if (currentLog.includes('Viral Post Example')) {
    const viralBlocks = currentLog.match(/Viral Post Example \d+:[\s\S]*?Source: ([^,\n]+)(?:, Views: ([^,\n]+))?(?:, Reactions: ([^,\n]+))?/gm);
    
    if (viralBlocks) {
      viralBlocks.forEach(block => {
        const sourceMatch = block.match(/Source: ([^,\n]+)/);
        const viewsMatch = block.match(/Views: ([^,\n]+)/);
        const reactionsMatch = block.match(/Reactions: ([^,\n]+)/);
        
        if (sourceMatch) {
          const source = sourceMatch[1].trim();
          const views = viewsMatch ? viewsMatch[1].trim() : 'Unknown';
          const reactions = reactionsMatch ? reactionsMatch[1].trim() : 'Unknown';
          
          if (source && source !== 'N/A' && source !== 'Unknown') {
            sources.posts.push({
              source,
              views,
              reactions
            });
          }
        }
      });
    }
  }

  return sources;
};

/**
 * Check if sources object has any content
 * @param {Object} sources - Sources object
 * @returns {boolean} True if any sources exist
 */
export const hasAnySources = (sources) => {
  return Object.values(sources).some(sourceArray => sourceArray.length > 0);
}; 