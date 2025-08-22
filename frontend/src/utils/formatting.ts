// Utility functions for formatting data in the UI

export const formatCourseCode = (code: string): string => {
  // Ensure consistent formatting: "CS135" -> "CS 135"
  const match = code.match(/^([A-Z]+)(\d+[A-Z]?)$/);
  if (match) {
    return `${match[1]} ${match[2]}`;
  }
  return code;
};

export const formatCredits = (credits: number): string => {
  if (credits === 0.5) return '0.5 unit';
  if (credits === 1) return '1 unit';
  return `${credits} units`;
};

export const formatRating = (rating?: number): string => {
  if (!rating) return 'N/A';
  return `${rating.toFixed(1)}/5.0`;
};

export const formatPercentage = (percentage?: number): string => {
  if (percentage === undefined || percentage === null) return 'N/A';
  return `${Math.round(percentage)}%`;
};

export const formatDifficulty = (difficulty?: number): { label: string; color: string } => {
  if (!difficulty) return { label: 'Unknown', color: 'gray' };
  
  if (difficulty <= 2) {
    return { label: 'Easy', color: 'green' };
  } else if (difficulty <= 3.5) {
    return { label: 'Medium', color: 'yellow' };
  } else {
    return { label: 'Hard', color: 'red' };
  }
};

export const formatWorkload = (workload?: number): { label: string; color: string } => {
  if (!workload) return { label: 'Unknown', color: 'gray' };
  
  if (workload <= 2) {
    return { label: 'Light', color: 'green' };
  } else if (workload <= 3.5) {
    return { label: 'Moderate', color: 'yellow' };
  } else {
    return { label: 'Heavy', color: 'red' };
  }
};

export const formatConfidence = (confidence: number): { label: string; color: string } => {
  if (confidence >= 0.8) {
    return { label: 'High', color: 'green' };
  } else if (confidence >= 0.6) {
    return { label: 'Medium', color: 'yellow' };
  } else {
    return { label: 'Low', color: 'red' };
  }
};

export const formatTerm = (term: string): string => {
  const termMap: { [key: string]: string } = {
    'F': 'Fall',
    'W': 'Winter',
    'S': 'Spring',
    'Fall': 'Fall',
    'Winter': 'Winter',
    'Spring': 'Spring'
  };
  return termMap[term] || term;
};

export const formatPrerequisites = (prerequisites?: string): string => {
  if (!prerequisites || prerequisites.toLowerCase() === 'none') {
    return 'None';
  }
  return prerequisites;
};

export const formatCourseLevel = (level: number): string => {
  if (level < 200) return 'Introductory';
  if (level < 300) return 'Intermediate';
  if (level < 400) return 'Advanced';
  return 'Graduate';
};

export const formatStudentYear = (year: number): string => {
  const yearMap: { [key: number]: string } = {
    1: '1st Year',
    2: '2nd Year', 
    3: '3rd Year',
    4: '4th Year',
    5: '5th+ Year'
  };
  return yearMap[year] || `Year ${year}`;
};

export const formatDepartmentName = (code: string): string => {
  const deptMap: { [key: string]: string } = {
    'CS': 'Computer Science',
    'ECE': 'Electrical & Computer Engineering',
    'MATH': 'Mathematics',
    'STAT': 'Statistics',
    'ENVS': 'Environment & Resource Studies',
    'BET': 'Business, Entrepreneurship & Technology',
    'FINE': 'Fine Arts',
    'MUSIC': 'Music',
    'ENGL': 'English',
    'PHIL': 'Philosophy',
    'HIST': 'History',
    'PSCI': 'Political Science',
    'ECON': 'Economics',
    'PSYCH': 'Psychology',
    'BIOL': 'Biology',
    'CHEM': 'Chemistry',
    'PHYS': 'Physics',
    'EARTH': 'Earth Sciences',
    'GEOG': 'Geography'
  };
  return deptMap[code] || code;
};

export const formatReviewCount = (count: number): string => {
  if (count === 0) return 'No reviews';
  if (count === 1) return '1 review';
  return `${count} reviews`;
};

export const formatRatingCount = (count: number): string => {
  if (count === 0) return 'No ratings';
  if (count === 1) return '1 rating';
  if (count < 1000) return `${count} ratings`;
  return `${(count / 1000).toFixed(1)}k ratings`;
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
};

export const highlightSearchTerm = (text: string, searchTerm: string): string => {
  if (!searchTerm) return text;
  
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
};