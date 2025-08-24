import axios from 'axios';
import { 
  StudentProfile, 
  Recommendation, 
  Course, 
  UWFlowData, 
  PrerequisiteValidation 
} from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 90000, // 90 seconds for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Health Check
export const checkHealth = async (): Promise<any> => {
  const response = await api.get('/api/v1/health');
  return response.data;
};

// Course API functions
export const getCourses = async (
  department?: string,
  limit: number = 50
): Promise<Course[]> => {
  const params = new URLSearchParams();
  if (department) params.append('department', department);
  params.append('limit', limit.toString());
  
  const response = await api.get(`/api/v1/courses?${params}`);
  return response.data;
};

export const getCourseByCode = async (courseCode: string): Promise<Course> => {
  const response = await api.get(`/api/v1/courses/${courseCode}`);
  return response.data;
};

export const searchCourses = async (query: string, limit: number = 20): Promise<Course[]> => {
  const response = await api.get(`/api/v1/courses/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  return response.data;
};

// Recommendation API functions
export const getRecommendations = async (
  profile: StudentProfile,
  includeMissingPrereqs: boolean = false
): Promise<Recommendation[]> => {
  const response = await api.post('/api/v1/recommendations', profile, {
    params: { include_missing_prereqs: includeMissingPrereqs },
    timeout: 120000 // 2 minutes for AI recommendations
  });
  return response.data;
};

export const explainRecommendation = async (
  courseCode: string,
  profile: StudentProfile
): Promise<any> => {
  const response = await api.post('/api/v1/recommendations/explain', profile, {
    params: { course_code: courseCode }
  });
  return response.data;
};

export const validatePrerequisites = async (
  courseCode: string,
  profile: StudentProfile
): Promise<PrerequisiteValidation> => {
  const response = await api.post('/api/v1/recommendations/validate-prerequisites', profile, {
    params: { course_code: courseCode }
  });
  return response.data;
};

// UWFlow API functions
export const getUWFlowData = async (courseCode: string): Promise<UWFlowData> => {
  const response = await api.get(`/uwflow-data/${courseCode}`);
  return response.data;
};

export const getUWFlowStats = async (): Promise<any> => {
  const response = await api.get('/uwflow-stats');
  return response.data;
};

// Department API functions
export const getDepartments = async (): Promise<string[]> => {
  const response = await api.get('/courses/departments');
  return response.data;
};

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

// Loading wrapper utility
export const withLoading = async <T>(
  apiCall: () => Promise<T>,
  setLoading: (loading: boolean) => void
): Promise<T> => {
  setLoading(true);
  try {
    const result = await apiCall();
    return result;
  } finally {
    setLoading(false);
  }
};