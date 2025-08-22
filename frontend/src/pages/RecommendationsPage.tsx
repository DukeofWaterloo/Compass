import React, { useState } from 'react';
import { 
  SparklesIcon, 
  UserIcon, 
  AcademicCapIcon, 
  PlusIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { getRecommendations } from '../utils/api.ts';
import { StudentProfile, Recommendation } from '../types';
import LoadingSpinner from '../components/LoadingSpinner.tsx';
import ErrorMessage from '../components/ErrorMessage.tsx';

const RecommendationsPage: React.FC = () => {
  const [profile, setProfile] = useState<StudentProfile>({
    program: '',
    year: 1,
    interests: [],
    completed_courses: [],
    gpa: undefined
  });
  
  const [currentInterest, setCurrentInterest] = useState('');
  const [currentCourse, setCurrentCourse] = useState('');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addInterest = () => {
    if (currentInterest.trim() && !profile.interests.includes(currentInterest.trim())) {
      setProfile(prev => ({
        ...prev,
        interests: [...prev.interests, currentInterest.trim()]
      }));
      setCurrentInterest('');
    }
  };

  const removeInterest = (interest: string) => {
    setProfile(prev => ({
      ...prev,
      interests: prev.interests.filter(i => i !== interest)
    }));
  };

  const addCourse = () => {
    if (currentCourse.trim() && !profile.completed_courses.includes(currentCourse.trim().toUpperCase())) {
      setProfile(prev => ({
        ...prev,
        completed_courses: [...prev.completed_courses, currentCourse.trim().toUpperCase()]
      }));
      setCurrentCourse('');
    }
  };

  const removeCourse = (course: string) => {
    setProfile(prev => ({
      ...prev,
      completed_courses: prev.completed_courses.filter(c => c !== course)
    }));
  };

  const handleGetRecommendations = async () => {
    if (!profile.program.trim()) {
      setError('Please enter your program');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const result = await getRecommendations(profile);
      setRecommendations(result);
      setError(null);
    } catch (err: any) {
      console.error('Recommendations error:', err);
      
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The AI is working hard but taking longer than usual. Please try again.');
      } else if (err.response?.status === 404) {
        setError('No relevant courses found for your profile. Try adjusting your program or year.');
      } else if (err.response?.status >= 500) {
        setError('Server error. The AI engine might be busy. Please try again in a moment.');
      } else {
        setError(`Failed to get recommendations: ${err.response?.data?.detail || err.message || 'Please try again.'}`);
      }
    } finally {
      setLoading(false);
    }
  };

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

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Profile Input Form */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-3 mb-6">
              <UserIcon className="h-6 w-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Your Profile</h2>
            </div>

            <div className="space-y-6">
              {/* Program */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Program *
                </label>
                <input
                  type="text"
                  value={profile.program}
                  onChange={(e) => setProfile(prev => ({...prev, program: e.target.value}))}
                  placeholder="e.g., Computer Science, Software Engineering"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Year */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Year
                </label>
                <select
                  value={profile.year}
                  onChange={(e) => setProfile(prev => ({...prev, year: parseInt(e.target.value)}))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={1}>1st Year</option>
                  <option value={2}>2nd Year</option>
                  <option value={3}>3rd Year</option>
                  <option value={4}>4th Year</option>
                  <option value={5}>5th Year+</option>
                </select>
              </div>

              {/* GPA */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GPA (Optional)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="4.0"
                  value={profile.gpa || ''}
                  onChange={(e) => setProfile(prev => ({
                    ...prev, 
                    gpa: e.target.value ? parseFloat(e.target.value) : undefined
                  }))}
                  placeholder="3.5"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Interests */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Interests
                </label>
                <div className="flex space-x-2 mb-3">
                  <input
                    type="text"
                    value={currentInterest}
                    onChange={(e) => setCurrentInterest(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addInterest()}
                    placeholder="e.g., algorithms, web development"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={addInterest}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="h-5 w-5" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {profile.interests.map((interest, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {interest}
                      <button
                        onClick={() => removeInterest(interest)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Completed Courses */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Completed Courses
                </label>
                <div className="flex space-x-2 mb-3">
                  <input
                    type="text"
                    value={currentCourse}
                    onChange={(e) => setCurrentCourse(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCourse()}
                    placeholder="e.g., CS135, MATH137"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={addCourse}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="h-5 w-5" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {profile.completed_courses.map((course, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                    >
                      {course}
                      <button
                        onClick={() => removeCourse(course)}
                        className="ml-2 text-green-600 hover:text-green-800"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={handleGetRecommendations}
                disabled={loading || !profile.program.trim()}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <LoadingSpinner size="sm" />
                    <span>Getting Recommendations...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <SparklesIcon className="h-5 w-5" />
                    <span>Get AI Recommendations</span>
                  </div>
                )}
              </button>
            </div>
          </div>

          {/* Recommendations Results */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-3 mb-6">
              <AcademicCapIcon className="h-6 w-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900">Recommendations</h2>
            </div>

            {error && (
              <ErrorMessage message={error} />
            )}

            {recommendations.length === 0 && !loading && !error && (
              <div className="text-center py-12">
                <SparklesIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-500 mb-4">
                  Fill out your profile and click "Get AI Recommendations" to see personalized course suggestions
                </p>
                <div className="bg-blue-50 p-4 rounded-lg text-left">
                  <h4 className="font-semibold text-blue-900 mb-2">Tips for better recommendations:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Be specific about your program (e.g., "Computer Science", not just "CS")</li>
                    <li>• Add your interests (algorithms, AI, web dev, etc.)</li>
                    <li>• List completed courses to avoid duplicates</li>
                    <li>• Include your GPA for difficulty-appropriate suggestions</li>
                  </ul>
                </div>
              </div>
            )}

            {recommendations.length > 0 && (
              <div className="space-y-4">
                {recommendations.map((rec, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-bold text-lg text-gray-900">{rec.course_code}</h3>
                        <p className="text-gray-600">{rec.title}</p>
                      </div>
                      <div className="text-right">
                        <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                          {Math.round(rec.confidence_score * 100)}% match
                        </div>
                      </div>
                    </div>
                    <p className="text-gray-700 mb-3">{rec.description}</p>
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-3 rounded-lg">
                      <p className="font-medium text-gray-900 mb-1">Why recommended:</p>
                      <p className="text-gray-700 text-sm">{rec.reasoning}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendationsPage;