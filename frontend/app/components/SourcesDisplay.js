import React from 'react';
import { FileText, Globe, TrendingUp, ExternalLink, Database, Link } from 'lucide-react';

const SourcesDisplay = ({ sources }) => {
  if (!sources || Object.values(sources).every(arr => arr.length === 0)) {
    return null;
  }

  // Count total sources
  const totalSources = Object.values(sources).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="mt-6 border border-blue-200 rounded-lg p-4 bg-blue-50">
      <h3 className="text-lg font-semibold mb-4 text-blue-900 flex items-center">
        <Database className="mr-2 h-5 w-5" />
        📚 Sources Used ({totalSources} total)
      </h3>
      
      <div className="space-y-4">
        {/* Internal Documents */}
        {sources.pdfs && sources.pdfs.length > 0 && (
          <div className="bg-white rounded-lg border border-blue-200 p-3">
            <h4 className="font-semibold mb-3 text-blue-800 flex items-center">
              <FileText className="mr-2 h-4 w-4" />
              📄 Internal Documents ({sources.pdfs.length})
            </h4>
            <div className="space-y-2">
              {sources.pdfs.map((pdf, index) => (
                <div key={index} className="bg-blue-50 rounded-md p-2 border-l-4 border-blue-400">
                  <div className="font-medium text-gray-800">• {pdf.filename}</div>
                  <div className="text-xs text-gray-600">Company document analyzed for relevant information</div>
                  {pdf.url && (
                    <a 
                      href={pdf.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-700 hover:text-blue-900 text-sm flex items-center mt-1"
                    >
                      <ExternalLink className="mr-1 h-3 w-3" />
                      See PDF 
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Web Articles Used */}
        {sources.webArticles && sources.webArticles.length > 0 && (
          <div className="bg-white rounded-lg border border-green-200 p-3">
            <h4 className="font-semibold mb-3 text-green-800 flex items-center">
              <Link className="mr-2 h-4 w-4" />
              🌐 Web Articles Used ({sources.webArticles.length})
            </h4>
            <div className="space-y-2">
              {sources.webArticles.map((webResult, index) => (
                <div key={`web-${index}`} className="bg-green-50 rounded-md p-2 border-l-4 border-green-400">
                  <div className="font-medium text-gray-800">• {webResult.title}</div>
                  <a 
                    href={webResult.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-green-700 hover:text-green-900 text-sm flex items-center mt-1"
                  >
                    <ExternalLink className="mr-1 h-3 w-3" />
                    {webResult.url}
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Viral Posts Reference */}
        {sources.viralPosts && sources.viralPosts.length > 0 && (
          <div className="bg-white rounded-lg border border-purple-200 p-3">
            <h4 className="font-semibold mb-3 text-purple-800 flex items-center">
              <TrendingUp className="mr-2 h-4 w-4" />
              💼 Viral Posts Referenced ({sources.viralPosts.length})
            </h4>
            <div className="space-y-2">
              {sources.viralPosts.map((post, index) => (
                <div key={index} className="bg-purple-50 rounded-md p-2 border-l-4 border-purple-400">
                  <div className="font-medium text-gray-800">• {post.title}</div>
                  <div className="text-sm text-gray-600">
                    Used as reference for viral content patterns
                    {post.similarityScore && (
                      <span className="ml-2">• 📊 {Math.round(post.similarityScore * 100)}% similarity</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourcesDisplay; 