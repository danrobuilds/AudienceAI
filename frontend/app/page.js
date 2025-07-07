'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Users, Zap, Shield, Sparkles, Brain } from 'lucide-react';

export default function LandingPage() {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push('/signin');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">
      {/* Navigation */}
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">Audy AI</span>
        </div>
        <button
          onClick={handleGetStarted}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Meet Audy, your 
            <span className="text-blue-600"> AI-Powered</span> Marketing Assistant
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Supercharge your marketing team with end-to-end AI agents that deeply understand your business, 
            industry, and product, and generate content optimized for your audience.
          </p>
          <button
            onClick={handleGetStarted}
            className="inline-flex items-center px-8 py-4 bg-blue-600 text-white text-lg font-medium rounded-xl hover:bg-blue-700 transition-colors shadow-lg"
          >
            Get Started
            <ArrowRight className="ml-2 h-5 w-5" />
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Versatile</h3>
            <p className="text-gray-600">
              Create optimized content for LinkedIn, Twitter, and Instagram with platform-specific strategies.
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Zap className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Multi-Agent</h3>
            <p className="text-gray-600">
              Deep research agents learn your industry, monitor current trends, and are trained to create hyper-optimized content
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">End-to-End</h3>
            <p className="text-gray-600">
              Audy functions like an autonomous marketing team that learns and gets better as it works with you.
            </p>
          </div>
        </div>

        
      </div>
    </div>
  );
} 