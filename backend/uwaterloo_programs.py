"""
University of Waterloo Programs - Validation List
"""

UWATERLOO_PROGRAMS = [
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
]

def is_valid_program(program: str) -> bool:
    """Check if a program name is valid"""
    return program in UWATERLOO_PROGRAMS

def get_program_suggestions(query: str) -> list:
    """Get program suggestions based on search query - supports both full names and shortforms"""
    if not query or len(query) < 1:
        return []
    
    query_lower = query.lower().strip()
    suggestions = []
    
    # First, look for exact shortform matches (higher priority)
    for program in UWATERLOO_PROGRAMS:
        if '(' in program:
            # Extract shortform from parentheses
            shortform = program[program.rfind('(')+1:program.rfind(')')].lower()
            if query_lower == shortform or query_lower in shortform.split('/'):
                suggestions.append(program)
    
    # Then look for partial matches in full program names
    for program in UWATERLOO_PROGRAMS:
        if program not in suggestions and query_lower in program.lower():
            suggestions.append(program)
    
    # Finally, look for word-boundary matches (e.g., "eng" matches "Engineering")
    if len(suggestions) < 8:
        for program in UWATERLOO_PROGRAMS:
            if program not in suggestions:
                words = program.lower().split()
                for word in words:
                    if word.startswith(query_lower) and len(query_lower) >= 2:
                        suggestions.append(program)
                        break
    
    return suggestions[:8]  # Limit to 8 suggestions