import React from 'react';
import { 
  AcademicCapIcon, 
  BeakerIcon, 
  ChartBarIcon,
  UserGroupIcon,
  BoltIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

const AboutPage: React.FC = () => {
  const features = [
    {
      icon: BeakerIcon,
      title: 'AI-Powered Engine',
      description: 'Advanced machine learning algorithms analyze your academic profile and preferences to provide personalized course recommendations.'
    },
    {
      icon: UserGroupIcon,
      title: 'Student Community Data',
      description: 'Access real reviews and ratings from thousands of UWaterloo students who have taken these courses before you.'
    },
    {
      icon: ShieldCheckIcon,
      title: 'Prerequisite Validation',
      description: 'Smart prerequisite checking ensures you never select courses you\'re not eligible for, with suggested preparation paths.'
    },
    {
      icon: ChartBarIcon,
      title: 'Comprehensive Analytics',
      description: 'Detailed difficulty scoring, workload estimation, and usefulness ratings help you make informed decisions.'
    }
  ];

  const techStack = [
    { name: 'Backend', technologies: ['Python', 'FastAPI', 'SQLAlchemy', 'SQLite'] },
    { name: 'AI/ML', technologies: ['OpenRouter', 'DeepSeek', 'Custom Algorithms'] },
    { name: 'Frontend', technologies: ['React', 'TypeScript', 'Tailwind CSS'] },
    { name: 'Data Sources', technologies: ['UWaterloo Calendar', 'UWFlow', 'Course Scraping'] }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <AcademicCapIcon className="mx-auto h-16 w-16 text-blue-600 mb-4" />
            <h1 className="text-4xl font-bold text-gray-900 mb-4">About Compass</h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Your intelligent academic advisor for University of Waterloo course selection
            </p>
          </div>
        </div>
      </div>

      {/* Mission Statement */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-white rounded-xl shadow-lg p-8 mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">Our Mission</h2>
          <p className="text-lg text-gray-700 leading-relaxed text-center max-w-4xl mx-auto">
            Compass was created to solve a common problem faced by UWaterloo students: choosing the right courses 
            for their academic journey. By combining artificial intelligence with real student experiences and 
            academic requirements validation, we help students make informed decisions that align with their goals, 
            interests, and academic standing.
          </p>
        </div>

        {/* Key Features */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">How Compass Works</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="bg-white rounded-xl p-8 shadow-lg">
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

        {/* Data Sources */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Data Sources</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <AcademicCapIcon className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">UWaterloo Calendar</h3>
              <p className="text-gray-600">
                Official course descriptions, prerequisites, and academic requirements from all 119 departments.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <UserGroupIcon className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">UWFlow Community</h3>
              <p className="text-gray-600">
                Student ratings, difficulty scores, workload estimates, and reviews from the UWaterloo community.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <BoltIcon className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Analysis</h3>
              <p className="text-gray-600">
                Advanced algorithms that analyze patterns and provide intelligent recommendations based on your profile.
              </p>
            </div>
          </div>
        </div>

        {/* Technical Stack */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Technology Stack</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {techStack.map((category, index) => (
              <div key={index} className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{category.name}</h3>
                <div className="space-y-2">
                  {category.technologies.map((tech, techIndex) => (
                    <div key={techIndex} className="bg-gray-100 rounded-full px-3 py-1 text-sm text-gray-700">
                      {tech}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl text-white p-8">
          <h2 className="text-3xl font-bold mb-8 text-center">By the Numbers</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold mb-2">119</div>
              <div className="text-blue-100">Departments Covered</div>
            </div>
            <div>
              <div className="text-3xl font-bold mb-2">5000+</div>
              <div className="text-blue-100">Courses Analyzed</div>
            </div>
            <div>
              <div className="text-3xl font-bold mb-2">95%</div>
              <div className="text-blue-100">Data Coverage</div>
            </div>
            <div>
              <div className="text-3xl font-bold mb-2">AI</div>
              <div className="text-blue-100">Powered Engine</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;