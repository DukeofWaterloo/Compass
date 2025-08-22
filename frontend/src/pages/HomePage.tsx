import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  AcademicCapIcon, 
  BoltIcon, 
  CheckCircleIcon,
  ChartBarIcon,
  UserGroupIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { checkHealth, getUWFlowStats } from '../utils/api.ts';

const HomePage: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<'loading' | 'online' | 'offline'>('loading');
  const [uwflowStats, setUwflowStats] = useState<any>(null);

  useEffect(() => {
    // Check API health
    checkHealth()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));

    // Get UWFlow stats
    getUWFlowStats()
      .then(setUwflowStats)
      .catch(console.error);
  }, []);

  const features = [
    {
      icon: SparklesIcon,
      title: 'AI-Powered Recommendations',
      description: 'Get personalized course suggestions based on your program, interests, and academic history using advanced AI.'
    },
    {
      icon: CheckCircleIcon,
      title: 'Prerequisite Validation',
      description: 'Never worry about course eligibility again. We automatically check prerequisites and suggest preparation paths.'
    },
    {
      icon: UserGroupIcon,
      title: 'Real Student Reviews',
      description: 'Access crowd-sourced ratings, difficulty scores, and workload information from thousands of UWaterloo students.'
    },
    {
      icon: ChartBarIcon,
      title: 'Smart Course Analysis',
      description: 'Advanced difficulty scoring and workload estimation help you balance your academic schedule effectively.'
    }
  ];

  const stats = [
    { label: 'Departments Covered', value: '119', icon: AcademicCapIcon },
    { label: 'Course Database', value: '5000+', icon: BoltIcon },
    { label: 'Student Reviews', value: uwflowStats?.courses_with_ratings || '1000+', icon: UserGroupIcon },
    { label: 'Data Coverage', value: uwflowStats?.data_coverage ? `${uwflowStats.data_coverage}%` : '95%', icon: ChartBarIcon }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Find Your Perfect
              <span className="block text-yellow-300">UWaterloo Course</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
              AI-powered course recommendations with real student feedback and intelligent prerequisite validation
            </p>
            
            {/* API Status */}
            <div className="flex items-center justify-center mb-8">
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
                apiStatus === 'online' 
                  ? 'bg-green-500 bg-opacity-20 text-green-100' 
                  : apiStatus === 'offline'
                  ? 'bg-red-500 bg-opacity-20 text-red-100'
                  : 'bg-yellow-500 bg-opacity-20 text-yellow-100'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  apiStatus === 'online' ? 'bg-green-400' : 
                  apiStatus === 'offline' ? 'bg-red-400' : 'bg-yellow-400'
                }`}></div>
                <span className="text-sm font-medium">
                  {apiStatus === 'online' ? 'System Online' : 
                   apiStatus === 'offline' ? 'System Offline' : 'Checking Status...'}
                </span>
              </div>
            </div>

            <Link
              to="/recommendations"
              className="inline-flex items-center space-x-2 bg-yellow-400 text-blue-900 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-yellow-300 transition-colors duration-200 shadow-lg"
            >
              <AcademicCapIcon className="h-6 w-6" />
              <span>Get Course Recommendations</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="text-center">
                  <div className="flex justify-center mb-4">
                    <Icon className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-2">{stat.value}</div>
                  <div className="text-gray-600">{stat.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose Compass?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              We combine cutting-edge AI with real student experiences to help you make the best academic decisions
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow duration-200"
                >
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <Icon className="h-8 w-8 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-3">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Find Your Next Course?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of UWaterloo students who use Compass to make informed academic decisions
          </p>
          <Link
            to="/recommendations"
            className="inline-flex items-center space-x-2 bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-50 transition-colors duration-200 shadow-lg"
          >
            <span>Start Your Academic Journey</span>
            <AcademicCapIcon className="h-6 w-6" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;