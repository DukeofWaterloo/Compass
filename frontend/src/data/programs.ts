/**
 * Official University of Waterloo Programs
 * Validated list for course recommendations
 */

export const UWATERLOO_PROGRAMS = [
  "Accounting and Financial Management (AFM)",
  "Actuarial Science (ACTSCI)",
  "Anthropology (ANTH)",
  "Applied Mathematics (AMATH)",
  "Architectural Engineering (AE)",
  "Architecture (ARCH)",
  "Bachelor of Arts (BA)",
  "Bachelor of Science (BSc)",
  "Biochemistry (BIOCHEM)",
  "Biological and Medical Physics (BIOMED PHYS)",
  "Biology (BIOL)",
  "Biomedical Engineering (BME)",
  "Biomedical Sciences (BIOMED)",
  "Biostatistics (BIOSTAT)",
  "Business Administration (Laurier) and Computer Science (Waterloo) Double Degree (BBA/BCS)",
  "Business Administration (Laurier) and Mathematics (Waterloo) Double Degree (BBA/BMath)",
  "Chemical Engineering (ChE)",
  "Chemistry (CHEM)",
  "Civil Engineering (CE)",
  "Classical Studies (CLAS)",
  "Climate and Environmental Change (CEC)",
  "Combinatorics and Optimization (C&O)",
  "Communication Studies (COMM)",
  "Computational Mathematics (COMP MATH)",
  "Computer Engineering (CE)",
  "Computer Science (CS)",
  "Computing and Financial Management (CFM)",
  "Data Science (DS)",
  "Earth Sciences (EARTH)",
  "Economics (ECON)",
  "Electrical Engineering (EE)",
  "English (ENGL)",
  "Environment and Business (ENVB)",
  "Environment, Resources and Sustainability (ERS)",
  "Environmental Engineering (EnvE)",
  "Environmental Sciences (ENVS)",
  "Fine Arts (FA)",
  "French (FR)",
  "Gender and Social Justice (GSJ)",
  "Geography and Aviation (GEOG/AVIA)",
  "Geography and Environmental Management (GEM)",
  "Geological Engineering (GEOE)",
  "Geomatics (GEOM)",
  "Global Business and Digital Arts (GBDA)",
  "Health Sciences (HS)",
  "History (HIST)",
  "Honours Arts (HA)",
  "Honours Arts and Business (HAB)",
  "Honours Science (HSci)",
  "Information Technology Management (ITM)",
  "Kinesiology (KIN)",
  "Legal Studies (LS)",
  "Liberal Studies (LS)",
  "Life Sciences (LIFE SCI)",
  "Management Engineering (MSCI)",
  "Materials and Nanosciences (MNS)",
  "Mathematical Economics (MATH ECON)",
  "Mathematical Finance (MATHFIN)",
  "Mathematical Optimization (MATH OPT)",
  "Mathematical Physics (MATH PHYS)",
  "Mathematical Studies (MATH STUD)",
  "Mathematics (MATH)",
  "Mathematics/Business Administration (MATH/BBA)",
  "Mathematics/Chartered Professional Accountancy (MATH/CPA)",
  "Mathematics/Financial Analysis and Risk Management (FARM)",
  "Mathematics/Teaching (MATH/TEACH)",
  "Mechanical Engineering (ME)",
  "Mechatronics Engineering (TRON)",
  "Medical Sciences (Waterloo) and Doctor of Medicine (St. George's University) (MedSci/MD)",
  "Medicinal Chemistry (MED CHEM)",
  "Medieval Studies (MEDVL)",
  "Music (MUSIC)",
  "Nanotechnology Engineering (NANO)",
  "Optometry (OPTOM)",
  "Peace and Conflict Studies (PACS)",
  "Pharmacy (PHARM)",
  "Philosophy (PHIL)",
  "Physical Sciences (PHYS SCI)",
  "Physics (PHYS)",
  "Physics and Astronomy (PHYS/ASTR)",
  "Planning (PLAN)",
  "Political Science (PSCI)",
  "Psychology – Bachelor of Arts (PSYCH BA)",
  "Psychology – Bachelor of Science (PSYCH BSc)",
  "Public Health (PH)",
  "Pure Mathematics (PMATH)",
  "Recreation and Leisure Studies (RLS)",
  "Recreation, Leadership and Health (RLH)",
  "Religion, Culture, and Spirituality (RCS)",
  "Science and Aviation (SCI/AVIA)",
  "Science and Business (SCI/BUS)",
  "Science and Financial Management (SFM)",
  "Sexualities, Relationships, and Families (SRF)",
  "Social Development Studies (SDS)",
  "Social Work (SW)",
  "Sociology (SOC)",
  "Software Engineering (SE)",
  "Sport and Recreation Management (SRM)",
  "Statistics (STAT)",
  "Sustainability and Financial Management (SUSM)",
  "Systems Design Engineering (SYDE)",
  "Teaching (TEACH)",
  "Theatre and Performance (TP)",
  "Therapeutic Recreation (TR)"
] as const;

export type UWProgram = typeof UWATERLOO_PROGRAMS[number];

/**
 * Get program suggestions based on search input - supports both full names and shortforms
 */
export const searchPrograms = (query: string): string[] => {
  if (!query || query.length < 1) return [];
  
  const searchTerm = query.toLowerCase().trim();
  const suggestions: string[] = [];
  
  // First, look for exact shortform matches (higher priority)
  UWATERLOO_PROGRAMS.forEach(program => {
    if (program.includes('(')) {
      // Extract shortform from parentheses  
      const shortformMatch = program.match(/\(([^)]+)\)$/);
      if (shortformMatch) {
        const shortform = shortformMatch[1].toLowerCase();
        if (searchTerm === shortform || shortform.split('/').includes(searchTerm)) {
          suggestions.push(program);
        }
      }
    }
  });
  
  // Then look for partial matches in full program names
  UWATERLOO_PROGRAMS.forEach(program => {
    if (!suggestions.includes(program) && program.toLowerCase().includes(searchTerm)) {
      suggestions.push(program);
    }
  });
  
  // Finally, look for word-boundary matches (e.g., "eng" matches "Engineering")
  if (suggestions.length < 8 && searchTerm.length >= 2) {
    UWATERLOO_PROGRAMS.forEach(program => {
      if (!suggestions.includes(program)) {
        const words = program.toLowerCase().split(/\s+/);
        for (const word of words) {
          if (word.startsWith(searchTerm)) {
            suggestions.push(program);
            break;
          }
        }
      }
    });
  }
  
  return suggestions.slice(0, 8); // Limit to 8 suggestions
};

/**
 * Check if a program name is valid
 */
export const isValidProgram = (program: string): boolean => {
  return UWATERLOO_PROGRAMS.includes(program as UWProgram);
};