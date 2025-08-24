import React, { useState, useRef, useEffect } from 'react';
import { 
  SparklesIcon, 
  UserIcon, 
  AcademicCapIcon, 
  PlusIcon,
  XMarkIcon,
  ChevronDownIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { getRecommendations } from '../utils/api.ts';
import { StudentProfile, Recommendation } from '../types';
import LoadingSpinner from '../components/LoadingSpinner.tsx';
import ErrorMessage from '../components/ErrorMessage.tsx';
import { searchPrograms, isValidProgram } from '../data/programs.ts';

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
  
  // Program dropdown state
  const [programQuery, setProgramQuery] = useState('');
  const [programSuggestions, setProgramSuggestions] = useState<string[]>([]);
  const [showProgramDropdown, setShowProgramDropdown] = useState(false);
  const programInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Program dropdown effects
  useEffect(() => {
    const suggestions = searchPrograms(programQuery);
    setProgramSuggestions(suggestions);
  }, [programQuery]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowProgramDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleProgramInputChange = (value: string) => {
    setProgramQuery(value);
    setProfile(prev => ({ ...prev, program: value }));
    setShowProgramDropdown(value.length > 0);
  };

  const selectProgram = (program: string) => {
    setProgramQuery(program);
    setProfile(prev => ({ ...prev, program }));
    setShowProgramDropdown(false);
    programInputRef.current?.blur();
  };

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
      setError('Please select your program');
      return;
    }
    
    if (!isValidProgram(profile.program)) {
      setError('Please select a valid University of Waterloo program from the dropdown');
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
        setError('Request timed out. AI recommendations usually take 15-30 seconds. The server may be busy - please try again.');
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
              <div className="relative" ref={dropdownRef}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Program *
                </label>
                <div className="relative">
                  <input
                    ref={programInputRef}
                    type="text"
                    value={programQuery}
                    onChange={(e) => handleProgramInputChange(e.target.value)}
                    onFocus={() => setShowProgramDropdown(programQuery.length > 0)}
                    placeholder="Search for your UWaterloo program..."
                    className={`w-full px-4 py-3 pr-10 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      profile.program && !isValidProgram(profile.program) 
                        ? 'border-red-300 bg-red-50' 
                        : 'border-gray-300'
                    }`}
                  />
                  <ChevronDownIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  
                  {profile.program && isValidProgram(profile.program) && (
                    <CheckIcon className="absolute right-8 top-1/2 transform -translate-y-1/2 h-5 w-5 text-green-500" />
                  )}
                </div>

                {/* Program Dropdown */}
                {showProgramDropdown && programSuggestions.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {programSuggestions.map((program, index) => (
                      <button
                        key={index}
                        onClick={() => selectProgram(program)}
                        className="w-full text-left px-4 py-3 hover:bg-blue-50 focus:bg-blue-50 focus:outline-none first:rounded-t-lg last:rounded-b-lg border-b border-gray-100 last:border-b-0"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">{program}</span>
                          {profile.program === program && (
                            <CheckIcon className="h-4 w-4 text-blue-600" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {/* No programs found */}
                {showProgramDropdown && programQuery.length > 2 && programSuggestions.length === 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg p-4 text-gray-500 text-center">
                    No programs found. Try a different search term.
                  </div>
                )}

                {/* Invalid program warning */}
                {profile.program && !isValidProgram(profile.program) && programQuery === profile.program && (
                  <p className="mt-2 text-sm text-red-600">
                    Please select a valid University of Waterloo program from the dropdown.
                  </p>
                )}
              </div>

              {/* Year */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Year
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {[
                    { value: 1, label: '1st Year' },
                    { value: 2, label: '2nd Year' },
                    { value: 3, label: '3rd Year' },
                    { value: 4, label: '4th Year' },
                    { value: 5, label: '5th Year+' }
                  ].map(({ value, label }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setProfile(prev => ({...prev, year: value}))}
                      className={`px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
                        profile.year === value
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
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

              {/* Favourite Courses */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Favourite Courses
                </label>
                <p className="text-sm text-gray-500 mb-3">
                  Add courses you enjoyed to get similar recommendations
                </p>
                <div className="flex space-x-2 mb-3">
                  <input
                    type="text"
                    value={currentCourse}
                    onChange={(e) => setCurrentCourse(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCourse()}
                    placeholder="e.g., CS135, MATH137, ENGL109"
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
                      className="inline-flex items-center px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                    >
                      {course}
                      <button
                        onClick={() => removeCourse(course)}
                        className="ml-2 text-purple-600 hover:text-purple-800"
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
                    <span>AI analyzing your profile (15-30s)...</span>
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
                    <li>• Be specific about your program (e.g., "Computer Science (CS)")</li>
                    <li>• Add your interests (algorithms, AI, web dev, etc.)</li>
                    <li>• List courses you enjoyed to get similar recommendations</li>
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
                        <h3 className="font-bold text-lg text-gray-900">{rec.course.code}</h3>
                        <p className="text-gray-600">{rec.course.title}</p>
                      </div>
                      <div className="text-right">
                        <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                          {Math.round(rec.confidence * 100)}% match
                        </div>
                      </div>
                    </div>
                    <p className="text-gray-700 mb-3">{rec.course.description}</p>
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