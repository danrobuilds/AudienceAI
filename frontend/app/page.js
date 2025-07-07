'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Users, Zap, Shield, Sparkles } from 'lucide-react';

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
          <span className="text-2xl font-bold text-gray-900">AudienceAI</span>
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
            Create Viral Content with
            <span className="text-blue-600"> AI-Powered</span> Intelligence
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Transform your social media presence with AI that understands your brand, 
            analyzes trending content, and generates posts that actually engage your audience.
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
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Multi-Platform</h3>
            <p className="text-gray-600">
              Create optimized content for LinkedIn, Twitter, Instagram, and TikTok with platform-specific strategies.
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Zap className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Lightning Fast</h3>
            <p className="text-gray-600">
              Generate high-quality posts in seconds using advanced AI that learns from viral content patterns.
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Shield className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Secure & Private</h3>
            <p className="text-gray-600">
              Your content and data are protected with enterprise-grade security and multi-tenant isolation.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-20 p-8 bg-blue-600 rounded-2xl text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to Go Viral?</h2>
          <p className="text-xl mb-6 opacity-90">
            Join thousands of creators and brands using AudienceAI to amplify their social media presence.
          </p>
          <button
            onClick={handleGetStarted}
            className="inline-flex items-center px-8 py-4 bg-white text-blue-600 text-lg font-medium rounded-xl hover:bg-gray-100 transition-colors"
          >
            Start Creating Now
            <ArrowRight className="ml-2 h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
} 