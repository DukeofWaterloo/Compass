"""
Local embedding generation using Qwen3-Embedding-8B
"""

import os
import logging
import time
import numpy as np
import torch
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from transformers import AutoTokenizer, AutoModel
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

class QwenEmbeddingGenerator:
    """Generate and manage course embeddings using Qwen3-Embedding-8B"""
    
    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-8B", device: str = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = 16 if self.device == "cuda" else 8  # Adjust based on memory
        
        logger.info(f"Initializing Qwen embedding generator on {self.device}")
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            self.model.eval()
            
            # Get embedding dimensions
            with torch.no_grad():
                test_input = self.tokenizer("test", return_tensors="pt", truncation=True, max_length=512)
                if self.device != "cpu":
                    test_input = {k: v.to(self.device) for k, v in test_input.items()}
                test_output = self.model(**test_input)
                self.embedding_dim = test_output.last_hidden_state.mean(dim=1).shape[1]
            
            logger.info(f"Model loaded successfully. Embedding dimensions: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"Failed to load Qwen model: {e}")
            raise
        
        # Initialize course cleaner for consistent data
        self.cleaner = CourseDataCleaner()
        
    def create_embedding_text(self, course: Course) -> str:
        """Create optimized text for embedding generation"""
        # Build comprehensive text for semantic understanding
        parts = []
        
        # Course identification and title
        if course.code and course.title:
            parts.append(f"{course.code}: {course.title}")
        
        # Course description (primary content)
        if course.description:
            parts.append(course.description)
        
        # Academic metadata for better context
        if course.department:
            parts.append(f"Department: {course.department}")
            
        if course.level:
            year_level = course.level // 100
            parts.append(f"Academic Level: {year_level} year course")
        
        # Prerequisites for academic progression understanding
        if course.prerequisites and course.prerequisites.lower() not in ['none', 'n/a']:
            parts.append(f"Prerequisites: {course.prerequisites}")
            
        # Additional academic context
        if course.credits:
            parts.append(f"Credit Hours: {course.credits}")
            
        if course.terms_offered:
            terms = ', '.join(course.terms_offered) if isinstance(course.terms_offered, list) else course.terms_offered
            parts.append(f"Terms Offered: {terms}")
        
        return " | ".join(parts)
    
    def mean_pooling(self, model_output, attention_mask):
        """Apply mean pooling to get sentence embeddings"""
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            embeddings = []
            
            with torch.no_grad():
                # Tokenize batch
                encoded_input = self.tokenizer(
                    texts, 
                    padding=True, 
                    truncation=True, 
                    max_length=512,  # Qwen3 context limit
                    return_tensors='pt'
                )
                
                # Move to device
                if self.device != "cpu":
                    encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
                
                # Generate embeddings
                model_output = self.model(**encoded_input)
                
                # Apply mean pooling
                sentence_embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
                
                # Normalize embeddings for cosine similarity
                sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
                
                # Convert to CPU and list
                embeddings = sentence_embeddings.cpu().numpy().tolist()
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def process_all_courses(self, save_to_file: str = "qwen_course_embeddings.json", resume: bool = True) -> Dict[str, any]:
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
                logger.info(f"Remaining to process: {len(courses)} courses")
            
            if not courses:
                logger.info("No courses to process")
                return {'total_courses': 0, 'successful_embeddings': 0}
            
            stats = {
                'total_courses': len(courses),
                'successful_embeddings': 0,
                'failed_embeddings': 0,
                'batches_processed': 0,
                'start_time': time.time(),
            }
            
            # Process courses in batches
            all_embeddings = list(existing_embeddings.values()) if resume else []
            
            for i in range(0, len(courses), self.batch_size):
                batch_courses = courses[i:i + self.batch_size]
                batch_start = i + 1
                batch_end = min(i + self.batch_size, len(courses))
                
                try:
                    logger.info(f"Processing batch {stats['batches_processed'] + 1}, courses {batch_start}-{batch_end}")
                    
                    # Create embedding texts for batch
                    batch_texts = [self.create_embedding_text(course) for course in batch_courses]
                    
                    # Generate embeddings for batch
                    embeddings = self.generate_batch_embeddings(batch_texts)
                    
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
                                'description_length': len(course.description) if course.description else 0,
                                'model': self.model_name
                            },
                            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
                        )
                        
                        all_embeddings.append(course_embedding.__dict__)
                        stats['successful_embeddings'] += 1
                    
                    stats['batches_processed'] += 1
                    
                    # Save progress periodically
                    if stats['batches_processed'] % 5 == 0:
                        self._save_embeddings(all_embeddings, save_to_file, stats)
                    
                    # Small delay to prevent overheating
                    if self.device == "cpu":
                        time.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Failed to process batch {batch_start}-{batch_end}: {e}")
                    stats['failed_embeddings'] += len(batch_courses)
                    continue
            
            # Final save
            stats['end_time'] = time.time()
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']) / 60
            
            self._save_embeddings(all_embeddings, save_to_file, stats)
            
            logger.info(f"Embedding generation complete:")
            logger.info(f"  - Total processed: {stats['successful_embeddings']}")
            logger.info(f"  - Failed: {stats['failed_embeddings']}")
            logger.info(f"  - Duration: {stats['duration_minutes']:.1f} minutes")
            logger.info(f"  - Device used: {self.device}")
            
            return stats
    
    def _save_embeddings(self, embeddings: List[Dict], filename: str, stats: Dict):
        """Save embeddings to file"""
        try:
            data = {
                'metadata': {
                    'model': self.model_name,
                    'dimensions': self.embedding_dim,
                    'device_used': self.device,
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
    
    def load_embeddings(self, filename: str = "qwen_course_embeddings.json") -> Tuple[np.ndarray, List[str], Dict]:
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

    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'embedding_dimensions': self.embedding_dim,
            'batch_size': self.batch_size,
            'dtype': 'float16' if self.device == "cuda" else 'float32'
        }

def main():
    """Generate embeddings for all courses using Qwen"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate course embeddings with Qwen3-Embedding-8B')
    parser.add_argument('--output', '-o', default='qwen_course_embeddings.json', help='Output file')
    parser.add_argument('--resume', '-r', action='store_true', help='Resume from existing file')
    parser.add_argument('--batch-size', '-b', type=int, help='Batch size (auto-detected by default)')
    parser.add_argument('--device', '-d', choices=['cpu', 'cuda'], help='Device to use (auto-detected by default)')
    
    args = parser.parse_args()
    
    try:
        generator = QwenEmbeddingGenerator(device=args.device)
        
        if args.batch_size:
            generator.batch_size = args.batch_size
        
        print("🚀 Starting Qwen course embedding generation...")
        print(f"   Model: {generator.model_name}")
        print(f"   Device: {generator.device}")
        print(f"   Embedding dims: {generator.embedding_dim}")
        print(f"   Batch size: {generator.batch_size}")
        print(f"   Output: {args.output}")
        print(f"   Resume: {args.resume}")
        
        stats = generator.process_all_courses(
            save_to_file=args.output,
            resume=args.resume
        )
        
        print("\n✅ Embedding generation completed!")
        print(f"   Successful: {stats['successful_embeddings']} courses")
        print(f"   Failed: {stats['failed_embeddings']} courses")
        print(f"   Duration: {stats.get('duration_minutes', 0):.1f} minutes")
        print(f"   Device used: {generator.device}")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        logger.exception("Embedding generation failed")

if __name__ == "__main__":
    main()