// Student and Profile Types
export interface StudentProfile {
  program: string;
  year: number;
  completed_courses: string[];
  current_courses: string[];
  interests: string[];
  preferred_terms: string[];
}

// Course Types
export interface Course {
  id: number;
  code: string;
  title: string;
  description: string;
  credits: number;
  prerequisites?: string;
  corequisites?: string;
  antirequisites?: string;
  terms_offered: string;
  department: string;
  level: number;
  url?: string;
}

// Recommendation Types
export interface Recommendation {
  course: Course;
  confidence: number;
  reasoning: string;
}

// UWFlow Data Types
export interface UWFlowData {
  course_code: string;
  rating?: number;
  difficulty?: number;
  workload?: number;
  usefulness?: number;
  num_ratings: number;
  review_count: number;
  liked_percentage?: number;
  professor_ratings: any[];
  last_updated?: string;
  data_source: string;
}

// Enhanced Recommendation with UWFlow data
export interface EnhancedRecommendation extends Recommendation {
  uwflow_data?: UWFlowData;
  prerequisite_status?: 'satisfied' | 'missing' | 'unknown';
  missing_prereqs?: string[];
  difficulty_score?: number;
}

// Prerequisite Validation Types
export interface PrerequisiteValidation {
  course_code: string;
  course_title: string;
  prerequisites?: string;
  is_eligible: boolean;
  missing_prerequisites: string[];
  warnings: string[];
  difficulty_score: number;
  difficulty_label: string;
  suggested_prerequisite_path: string[];
  student_year: number;
  student_program: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  error?: string;
}

// Form Types
export interface StudentProfileForm {
  program: string;
  year: string;
  completed_courses: string;
  current_courses: string;
  interests: string;
  preferred_terms: string[];
}

// Course Search Types
export interface CourseSearchFilters {
  department?: string;
  level?: number;
  term?: string;
  credits?: number;
  has_prerequisites?: boolean;
}