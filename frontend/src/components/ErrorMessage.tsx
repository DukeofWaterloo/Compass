import React from 'react';
import { ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface ErrorMessageProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning';
  onRetry?: () => void;
  className?: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title,
  message,
  type = 'error',
  onRetry,
  className = ''
}) => {
  const isError = type === 'error';
  
  return (
    <div className={`rounded-lg p-4 ${className} ${
      isError 
        ? 'bg-red-50 border border-red-200' 
        : 'bg-yellow-50 border border-yellow-200'
    }`}>
      <div className="flex">
        <div className="flex-shrink-0">
          {isError ? (
            <XCircleIcon className="h-5 w-5 text-red-400" />
          ) : (
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
          )}
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={`text-sm font-medium ${
              isError ? 'text-red-800' : 'text-yellow-800'
            }`}>
              {title}
            </h3>
          )}
          <div className={`${title ? 'mt-2' : ''} text-sm ${
            isError ? 'text-red-700' : 'text-yellow-700'
          }`}>
            <p>{message}</p>
          </div>
          {onRetry && (
            <div className="mt-4">
              <button
                onClick={onRetry}
                className={`text-sm font-medium ${
                  isError 
                    ? 'text-red-800 hover:text-red-900' 
                    : 'text-yellow-800 hover:text-yellow-900'
                } underline`}
              >
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;