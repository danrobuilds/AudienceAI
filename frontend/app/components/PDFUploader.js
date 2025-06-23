import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadsAPI } from '../services/api';

const PDFUploader = ({ isOpen, onClose }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResults, setUploadResults] = useState([]);

  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true,
    maxSize: MAX_FILE_SIZE,
    onDrop: (acceptedFiles, rejectedFiles) => {
      setFiles([...files, ...acceptedFiles]);
      
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const messages = rejectedFiles.map(({ file, errors }) => ({
          message: `File '${file.name}' rejected: ${errors.map(e => e.message).join(', ')}`,
          type: 'error',
          filename: file.name
        }));
        setUploadResults(prev => [...prev, ...messages]);
      }
    }
  });

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setUploadResults([{
        message: 'Please select at least one PDF file to upload.',
        type: 'error',
        filename: 'General'
      }]);
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadResults([]);

    try {
      const results = await uploadsAPI.uploadMultiple(files, (progress) => {
        setUploadProgress(progress);
      });

      // Transform API response to match our UI format
      const transformedResults = results.map(result => ({
        message: result.message,
        type: result.success ? 'success' : 'error',
        filename: result.filename,
        chunksCreated: result.chunks_created
      }));

      setUploadResults(transformedResults);
      
      // Clear files on successful upload
      const hasAnySuccess = results.some(r => r.success);
      if (hasAnySuccess) {
        setFiles([]);
      }

    } catch (error) {
      setUploadResults([{
        message: `Upload failed: ${error.message}`,
        type: 'error',
        filename: 'General'
      }]);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleClose = () => {
    setFiles([]);
    setUploadResults([]);
    setUploadProgress(0);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="border-t border-gray-200 pt-6 mt-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-4">Upload PDF Documents to Knowledge Base</h2>
        
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          {isDragActive ? (
            <p className="text-lg">Drop the PDF files here...</p>
          ) : (
            <div>
              <p className="text-lg mb-2">Drag & drop PDF files here, or click to select</p>
              <p className="text-sm text-gray-500">Maximum 10MB per file</p>
            </div>
          )}
        </div>

        {/* Selected Files */}
        {files.length > 0 && (
          <div className="mt-4">
            <h3 className="font-medium mb-2">Selected Files ({files.length})</h3>
            <div className="space-y-2">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <File className="h-5 w-5 text-red-600 mr-2" />
                    <div>
                      <p className="font-medium">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {uploading && (
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Upload Results */}
        {uploadResults.length > 0 && (
          <div className="mt-4">
            <h3 className="font-medium mb-2">Upload Results:</h3>
            <div className="space-y-2">
              {uploadResults.map((result, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg flex items-start ${
                    result.type === 'success' 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}
                >
                  {result.type === 'success' ? (
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-2 flex-shrink-0" />
                  )}
                  <div>
                    <p className={`font-medium ${
                      result.type === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {result.filename}
                    </p>
                    <p className={`text-sm ${
                      result.type === 'success' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {result.message}
                    </p>
                    {result.chunksCreated && (
                      <p className="text-xs text-green-600 mt-1">
                        Created {result.chunksCreated} text chunks
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 mt-6">
          <button
            onClick={handleUpload}
            disabled={uploading || files.length === 0}
            className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Processing...' : 'Process Uploaded Files'}
          </button>
          <button
            onClick={handleClose}
            className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
          >
            Close Uploader
          </button>
        </div>
      </div>
    </div>
  );
};

export default PDFUploader; 