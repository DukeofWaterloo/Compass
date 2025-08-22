import React from 'react';
import { useParams } from 'react-router-dom';
import { AcademicCapIcon } from '@heroicons/react/24/outline';

const CoursePage: React.FC = () => {
  const { courseCode } = useParams<{ courseCode: string }>();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-xl shadow-lg p-8 text-center">
          <AcademicCapIcon className="mx-auto h-16 w-16 text-blue-600 mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Course Details: {courseCode}
          </h1>
          <p className="text-gray-600 mb-8">
            This page will show detailed information about {courseCode}, including:
          </p>
          <div className="grid md:grid-cols-2 gap-4 text-left max-w-2xl mx-auto">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">Course Information</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Course description</li>
                <li>• Prerequisites & corequisites</li>
                <li>• Credits and terms offered</li>
              </ul>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">Student Feedback</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• UWFlow ratings</li>
                <li>• Difficulty and workload</li>
                <li>• Student reviews</li>
              </ul>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-8">
            Coming soon in Phase 4.4!
          </p>
        </div>
      </div>
    </div>
  );
};

export default CoursePage;