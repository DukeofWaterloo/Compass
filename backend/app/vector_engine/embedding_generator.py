"""
Vector embedding generation for course recommendations
"""

import os
import logging
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models.database import Course, SessionLocal
from app.data_processing.course_cleaner import CourseDataCleaner

logger = logging.getLogger(__name__)

@dataclass
class CourseEmbedding:
    """Course embedding data structure"""
    course_code: str
    department: str
    level: int
    embedding: List[float]
    metadata: Dict
    created_at: str

class CourseEmbeddingGenerator:
    """Generate and manage course embeddings using OpenAI"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
        self.embedding_model = "text-embedding-3-small"  # 1536 dimensions, cost-effective
        self.embedding_dim = 1536
        self.batch_size = 100  # OpenAI batch limit
        self.rate_limit_delay = 0.1  # seconds between requests
        
        # Initialize course cleaner for consistent data
        self.cleaner = CourseDataCleaner()
        
    def create_embedding_text(self, course: Course) -> str:
        """Create optimized text for embedding generation"""
        # Build comprehensive text for semantic understanding
        parts = []
        
        # Course identification
        if course.code and course.title:
            parts.append(f"{course.code}: {course.title}")
        
        # Course description (primary content)
        if course.description:
            parts.append(course.description)
        
        # Academic metadata
        if course.department:
            parts.append(f"Department: {course.department}")
            
        if course.level:
            year_level = course.level // 100
            parts.append(f"Level: {year_level} year course")
        
        # Prerequisites (important for recommendations)
        if course.prerequisites and course.prerequisites.lower() not in ['none', 'n/a']:
            parts.append(f"Prerequisites: {course.prerequisites}")
            
        # Additional context
        if course.credits:
            parts.append(f"Credits: {course.credits}")
            
        if course.terms_offered:
            terms = ', '.join(course.terms_offered) if isinstance(course.terms_offered, list) else course.terms_offered
            parts.append(f"Offered: {terms}")
        
        return " | ".join(parts)
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def process_all_courses(self, save_to_file: str = "course_embeddings.json", resume: bool = True) -> Dict[str, any]:
        """Process all courses and generate embeddings"""
        
        # Load existing embeddings if resuming
        existing_embeddings = {}
        if resume and os.path.exists(save_to_file):
            try:
                with open(save_to_file, 'r') as f:
                    data = json.load(f)
                    existing_embeddings = {item['course_code']: item for item in data.get('embeddings', [])}
                logger.info(f"Loaded {len(existing_embeddings)} existing embeddings")
            except Exception as e:
                logger.warning(f"Could not load existing embeddings: {e}")
        
        with SessionLocal() as db:
            # Get all active courses
            courses = db.query(Course).filter(Course.is_active == True).all()
            logger.info(f"Processing {len(courses)} courses for embeddings")
            
            # Filter out already processed courses if resuming
            if resume:
                courses = [c for c in courses if c.code not in existing_embeddings]
                logger.info(f"Skipping {len(existing_embeddings)} already processed courses")
            
            stats = {
                'total_courses': len(courses),
                'successful_embeddings': 0,
                'failed_embeddings': 0,
                'batches_processed': 0,
                'start_time': time.time(),
                'api_calls': 0
            }
            
            # Process courses in batches
            all_embeddings = list(existing_embeddings.values()) if resume else []
            batch_texts = []
            batch_courses = []
            
            for i, course in enumerate(courses):
                # Create embedding text
                embedding_text = self.create_embedding_text(course)
                batch_texts.append(embedding_text)
                batch_courses.append(course)
                
                # Process batch when full or at end
                if len(batch_texts) >= self.batch_size or i == len(courses) - 1:
                    try:
                        logger.info(f"Processing batch {stats['batches_processed'] + 1}, courses {i - len(batch_texts) + 2}-{i + 1}")
                        
                        # Generate embeddings for batch
                        embeddings = self.generate_batch_embeddings(batch_texts)
                        stats['api_calls'] += 1
                        
                        # Store embeddings
                        for course, embedding in zip(batch_courses, embeddings):
                            course_embedding = CourseEmbedding(
                                course_code=course.code,
                                department=course.department,
                                level=course.level,
                                embedding=embedding,
                                metadata={
                                    'title': course.title,
                                    'credits': course.credits,
                                    'prerequisites': course.prerequisites,
                                    'description_length': len(course.description) if course.description else 0
                                },
                                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
                            )
                            
                            all_embeddings.append(course_embedding.__dict__)
                            stats['successful_embeddings'] += 1
                        
                        stats['batches_processed'] += 1
                        
                        # Rate limiting
                        time.sleep(self.rate_limit_delay)
                        
                        # Save progress periodically
                        if stats['batches_processed'] % 10 == 0:
                            self._save_embeddings(all_embeddings, save_to_file, stats)
                            
                    except Exception as e:
                        logger.error(f"Failed to process batch: {e}")
                        stats['failed_embeddings'] += len(batch_courses)
                        
                        # Continue with next batch
                        continue
                    
                    # Reset batch
                    batch_texts = []
                    batch_courses = []
            
            # Final save
            stats['end_time'] = time.time()
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']) / 60
            
            self._save_embeddings(all_embeddings, save_to_file, stats)
            
            logger.info(f"Embedding generation complete:")
            logger.info(f"  - Total processed: {stats['successful_embeddings']}")
            logger.info(f"  - Failed: {stats['failed_embeddings']}")
            logger.info(f"  - API calls: {stats['api_calls']}")
            logger.info(f"  - Duration: {stats['duration_minutes']:.1f} minutes")
            
            return stats
    
    def _save_embeddings(self, embeddings: List[Dict], filename: str, stats: Dict):
        """Save embeddings to file"""
        try:
            data = {
                'metadata': {
                    'model': self.embedding_model,
                    'dimensions': self.embedding_dim,
                    'total_embeddings': len(embeddings),
                    'generation_stats': stats
                },
                'embeddings': embeddings
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(embeddings)} embeddings to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")
    
    def load_embeddings(self, filename: str = "course_embeddings.json") -> Tuple[np.ndarray, List[str], Dict]:
        """Load embeddings from file for similarity search"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            embeddings = []
            course_codes = []
            metadata = {}
            
            for item in data['embeddings']:
                embeddings.append(item['embedding'])
                course_codes.append(item['course_code'])
                metadata[item['course_code']] = item['metadata']
            
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            logger.info(f"Loaded {len(embeddings)} embeddings with shape {embeddings_array.shape}")
            
            return embeddings_array, course_codes, metadata
            
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            raise

def main():
    """Generate embeddings for all courses"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate course embeddings')
    parser.add_argument('--output', '-o', default='course_embeddings.json', help='Output file')
    parser.add_argument('--resume', '-r', action='store_true', help='Resume from existing file')
    parser.add_argument('--batch-size', '-b', type=int, default=100, help='Batch size')
    
    args = parser.parse_args()
    
    # Ensure OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    generator = CourseEmbeddingGenerator()
    generator.batch_size = args.batch_size
    
    print("🚀 Starting course embedding generation...")
    print(f"   Model: {generator.embedding_model}")
    print(f"   Batch size: {generator.batch_size}")
    print(f"   Output: {args.output}")
    print(f"   Resume: {args.resume}")
    
    try:
        stats = generator.process_all_courses(
            save_to_file=args.output,
            resume=args.resume
        )
        
        print("\n✅ Embedding generation completed!")
        print(f"   Successful: {stats['successful_embeddings']} courses")
        print(f"   Failed: {stats['failed_embeddings']} courses")
        print(f"   Duration: {stats.get('duration_minutes', 0):.1f} minutes")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        logger.exception("Embedding generation failed")

if __name__ == "__main__":
    main()