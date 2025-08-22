import React from 'react';
import { SparklesIcon, UserIcon, AcademicCapIcon } from '@heroicons/react/24/outline';

const RecommendationsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <SparklesIcon className="mx-auto h-16 w-16 text-blue-600 mb-4" />
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI Course Recommendations
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Get personalized course suggestions based on your academic profile and interests
          </p>
        </div>

        {/* Coming Soon Content */}
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Intelligent Course Recommendations Coming Soon!
            </h2>
            <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
              We're building an amazing experience that will help you discover your perfect courses. 
              Here's what you can expect:
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="bg-blue-50 p-6 rounded-lg">
              <UserIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Student Profile Setup
              </h3>
              <p className="text-gray-600 text-sm">
                Tell us about your program, year, completed courses, and interests
              </p>
            </div>
            
            <div className="bg-green-50 p-6 rounded-lg">
              <SparklesIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                AI Analysis
              </h3>
              <p className="text-gray-600 text-sm">
                Our AI analyzes your profile against thousands of courses and student data
              </p>
            </div>
            
            <div className="bg-purple-50 p-6 rounded-lg">
              <AcademicCapIcon className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Smart Recommendations
              </h3>
              <p className="text-gray-600 text-sm">
                Get ranked course suggestions with prerequisites, ratings, and reasoning
              </p>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-8 rounded-lg">
            <h3 className="text-xl font-bold mb-4">Coming in Phase 4.2!</h3>
            <p className="mb-6">
              We're working hard to bring you the most intelligent course recommendation system. 
              Our backend is ready with:
            </p>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="text-left">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>AI-powered recommendation engine</span>
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>Prerequisite validation system</span>
                </div>
              </div>
              <div className="text-left">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>UWFlow data integration</span>
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>Comprehensive course database</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendationsPage;