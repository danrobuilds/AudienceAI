'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User, Lock, LogIn, AlertCircle, Loader } from 'lucide-react';
import { getTenantId, setTenantId, isAuthenticated, isValidUUID, refreshAuthTimestamp } from '../services/auth';
import { authAPI } from '../services/api';

export default function SignInPage() {
  const router = useRouter();
  const [tenantId, setTenantIdState] = useState('');
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [error, setError] = useState('');
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Check if user is already authenticated on page load
  useEffect(() => {
    const checkExistingAuth = () => {
      if (isAuthenticated()) {
        // User is already authenticated, redirect to dashboard
        refreshAuthTimestamp();
        router.push('/dashboard');
        return;
      }
      setCheckingAuth(false);
    };

    checkExistingAuth();
  }, [router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!tenantId.trim()) {
      setError('Please enter your tenant ID');
      return;
    }

    if (!isValidUUID(tenantId.trim())) {
      setError('Please enter a valid UUID format');
      return;
    }

    setIsSigningIn(true);
    
    try {
      // Call the backend signin endpoint to validate tenant ID
      const data = await authAPI.signin(tenantId.trim());

      // If successful, store tenant_id in sessionStorage and redirect
      if (data.success) {
        setTenantId(tenantId.trim());
        router.push('/dashboard');
      } else {
        setError('Authentication failed. Please try again.');
      }
    } catch (error) {
      console.error('Sign in error:', error);
      
      // Handle different error status codes from axios
      if (error.response) {
        const status = error.response.status;
        const errorData = error.response.data;
        
        if (status === 401) {
          setError('Invalid tenant ID. Please check your credentials.');
        } else if (status === 400) {
          setError('Invalid tenant ID format. Please enter a valid UUID.');
        } else {
          setError(errorData?.detail || 'Authentication failed. Please try again.');
        }
      } else if (error.request) {
        setError('Network error. Please check your connection and try again.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsSigningIn(false);
    }
  };

  // Show loading while checking existing authentication
  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex items-center">
          <Loader className="animate-spin h-8 w-8 text-blue-500 mr-4" />
          <span className="text-gray-600">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-8">
      <div className="max-w-md w-full">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
            <User className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">Welcome to AudienceAI</h1>
          <p className="text-gray-600">Enter your tenant ID to access your workspace</p>
        </div>

        {/* Sign In Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="tenantId" className="block text-sm font-medium text-gray-700 mb-2">
              Tenant ID
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                id="tenantId"
                value={tenantId}
                onChange={(e) => {
                  setTenantIdState(e.target.value);
                  if (error) setError(''); // Clear error when user types
                }}
                placeholder="Enter your tenant ID"
                className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:border-transparent ${
                  error 
                    ? 'border-red-300 focus:ring-red-500' 
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                disabled={isSigningIn}
              />
            </div>
            {error && (
              <div className="mt-2 flex items-center text-sm text-red-600">
                <AlertCircle className="h-4 w-4 mr-1 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isSigningIn || !tenantId.trim()}
            className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSigningIn ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing In...
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4 mr-2" />
                Sign In
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            Need help? Contact your administrator for your tenant ID.
          </p>
        </div>
      </div>
    </div>
  );
} 