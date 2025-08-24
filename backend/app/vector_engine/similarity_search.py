"""
Vector similarity search engine for course recommendations
"""

import logging
import numpy as np
import json
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import faiss
from sqlalchemy.orm import Session
from app.models.database import Course, SessionLocal
from app.vector_engine.embedding_generator import CourseEmbeddingGenerator

logger = logging.getLogger(__name__)

@dataclass
class SimilarityResult:
    """Result from similarity search"""
    course_code: str
    similarity_score: float
    department: str
    level: int
    title: str
    metadata: Dict

@dataclass
class RecommendationContext:
    """Context for generating recommendations"""
    student_year: int
    favorite_courses: List[str]
    interests: List[str]
    program: str
    gpa: Optional[float] = None

class VectorSimilarityEngine:
    """High-performance similarity search for course recommendations"""
    
    def __init__(self, embeddings_file: str = "course_embeddings.json"):
        self.embeddings_file = embeddings_file
        self.embeddings_array = None
        self.course_codes = None
        self.metadata = None
        self.faiss_index = None
        self.topic_clusters = None
        self.embedding_generator = CourseEmbeddingGenerator()
        
        # Load embeddings if file exists
        try:
            self.load_embeddings()
        except Exception as e:
            logger.warning(f"Could not load embeddings: {e}")
    
    def load_embeddings(self) -> bool:
        """Load embeddings and build FAISS index"""
        try:
            self.embeddings_array, self.course_codes, self.metadata = self.embedding_generator.load_embeddings(self.embeddings_file)
            
            # Build FAISS index for fast similarity search
            self.build_faiss_index()
            
            # Generate topic clusters
            self.generate_topic_clusters()
            
            logger.info(f"Loaded {len(self.course_codes)} course embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            return False
    
    def build_faiss_index(self):
        """Build FAISS index for fast similarity search"""
        if self.embeddings_array is None:
            raise ValueError("Embeddings not loaded")
        
        # Normalize embeddings for cosine similarity
        normalized_embeddings = self.embeddings_array / np.linalg.norm(self.embeddings_array, axis=1, keepdims=True)
        
        # Build FAISS index (Inner Product = Cosine similarity for normalized vectors)
        dimension = normalized_embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        self.faiss_index.add(normalized_embeddings)
        
        logger.info(f"Built FAISS index with {self.faiss_index.ntotal} vectors")
    
    def generate_topic_clusters(self, n_clusters: int = 50):
        """Generate topic clusters using K-means"""
        if self.embeddings_array is None:
            return
        
        try:
            # Use K-means to cluster courses by topic
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(self.embeddings_array)
            
            # Group courses by cluster
            self.topic_clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in self.topic_clusters:
                    self.topic_clusters[label] = []
                self.topic_clusters[label].append(self.course_codes[i])
            
            logger.info(f"Generated {n_clusters} topic clusters")
            
        except Exception as e:
            logger.error(f"Failed to generate topic clusters: {e}")
    
    def find_similar_courses(self, query_course_code: str, top_k: int = 20, exclude_same_course: bool = True) -> List[SimilarityResult]:
        """Find courses similar to a given course"""
        if self.faiss_index is None:
            raise ValueError("FAISS index not built")
        
        try:
            # Find query course index
            query_idx = self.course_codes.index(query_course_code)
            query_embedding = self.embeddings_array[query_idx:query_idx+1]
            
            # Normalize query embedding
            normalized_query = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search similar courses
            similarities, indices = self.faiss_index.search(normalized_query, top_k + (1 if exclude_same_course else 0))
            
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                course_code = self.course_codes[idx]
                
                # Skip the query course itself if requested
                if exclude_same_course and course_code == query_course_code:
                    continue
                
                # Get course metadata from database
                course_info = self._get_course_info(course_code)
                if course_info:
                    result = SimilarityResult(
                        course_code=course_code,
                        similarity_score=float(similarity),
                        department=course_info['department'],
                        level=course_info['level'],
                        title=course_info['title'],
                        metadata=self.metadata.get(course_code, {})
                    )
                    results.append(result)
                
                if len(results) >= top_k:
                    break
            
            return results
            
        except ValueError as e:
            logger.error(f"Course {query_course_code} not found in embeddings")
            return []
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def find_similar_to_multiple_courses(self, course_codes: List[str], weights: Optional[List[float]] = None, top_k: int = 20) -> List[SimilarityResult]:
        """Find courses similar to multiple courses (weighted average)"""
        if not course_codes:
            return []
        
        if self.faiss_index is None:
            raise ValueError("FAISS index not built")
        
        try:
            # Get embeddings for all input courses
            query_embeddings = []
            valid_weights = []
            
            for i, course_code in enumerate(course_codes):
                try:
                    course_idx = self.course_codes.index(course_code)
                    query_embeddings.append(self.embeddings_array[course_idx])
                    valid_weights.append(weights[i] if weights else 1.0)
                except ValueError:
                    logger.warning(f"Course {course_code} not found in embeddings")
                    continue
            
            if not query_embeddings:
                return []
            
            # Create weighted average embedding
            query_embeddings = np.array(query_embeddings)
            valid_weights = np.array(valid_weights)
            
            weighted_embedding = np.average(query_embeddings, axis=0, weights=valid_weights)
            weighted_embedding = weighted_embedding.reshape(1, -1)
            
            # Normalize query embedding
            normalized_query = weighted_embedding / np.linalg.norm(weighted_embedding, axis=1, keepdims=True)
            
            # Search similar courses
            similarities, indices = self.faiss_index.search(normalized_query, top_k * 2)  # Get more to filter out input courses
            
            results = []
            excluded_courses = set(course_codes)
            
            for similarity, idx in zip(similarities[0], indices[0]):
                course_code = self.course_codes[idx]
                
                # Skip input courses
                if course_code in excluded_courses:
                    continue
                
                # Get course metadata
                course_info = self._get_course_info(course_code)
                if course_info:
                    result = SimilarityResult(
                        course_code=course_code,
                        similarity_score=float(similarity),
                        department=course_info['department'],
                        level=course_info['level'],
                        title=course_info['title'],
                        metadata=self.metadata.get(course_code, {})
                    )
                    results.append(result)
                
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-course similarity search failed: {e}")
            return []
    
    def search_by_text_query(self, query_text: str, top_k: int = 20) -> List[SimilarityResult]:
        """Find courses similar to a text query"""
        if self.faiss_index is None:
            raise ValueError("FAISS index not built")
        
        try:
            # Generate embedding for query text
            query_embedding = self.embedding_generator.generate_single_embedding(query_text)
            query_embedding = np.array(query_embedding).reshape(1, -1)
            
            # Normalize query embedding
            normalized_query = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search similar courses
            similarities, indices = self.faiss_index.search(normalized_query, top_k)
            
            results = []
            for similarity, idx in zip(similarities[0], indices[0]):
                course_code = self.course_codes[idx]
                
                # Get course metadata
                course_info = self._get_course_info(course_code)
                if course_info:
                    result = SimilarityResult(
                        course_code=course_code,
                        similarity_score=float(similarity),
                        department=course_info['department'],
                        level=course_info['level'],
                        title=course_info['title'],
                        metadata=self.metadata.get(course_code, {})
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Text query search failed: {e}")
            return []
    
    def get_recommendations_for_student(self, context: RecommendationContext, top_k: int = 10) -> List[SimilarityResult]:
        """Generate comprehensive recommendations for a student"""
        all_results = []
        
        # 1. Find courses similar to favorite courses
        if context.favorite_courses:
            favorite_results = self.find_similar_to_multiple_courses(
                context.favorite_courses,
                top_k=top_k * 2  # Get more for filtering
            )
            all_results.extend([(r, 0.4, "favorite_similarity") for r in favorite_results])
        
        # 2. Find courses matching interests
        if context.interests:
            interest_query = " ".join(context.interests)
            interest_results = self.search_by_text_query(
                interest_query,
                top_k=top_k * 2
            )
            all_results.extend([(r, 0.3, "interest_match") for r in interest_results])
        
        # 3. Add program-appropriate level filtering and department diversity
        filtered_results = self._filter_and_score_results(all_results, context)
        
        # 4. Sort by combined score and return top results
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        return [result for result, score, reason in filtered_results[:top_k]]
    
    def _filter_and_score_results(self, results: List[Tuple[SimilarityResult, float, str]], context: RecommendationContext) -> List[Tuple[SimilarityResult, float, str]]:
        """Filter and score results based on student context"""
        scored_results = []
        seen_courses = set()
        department_counts = {}
        
        target_level_min = max(100, context.student_year * 100)  # Minimum appropriate level
        target_level_max = min(500, (context.student_year + 2) * 100)  # Maximum appropriate level
        
        for result, base_score, reason in results:
            if result.course_code in seen_courses:
                continue
            seen_courses.add(result.course_code)
            
            # Level appropriateness score
            level_score = 1.0
            if result.level < target_level_min:
                level_score = 0.3  # Too easy
            elif result.level > target_level_max:
                level_score = 0.7  # Challenging but acceptable
            
            # Department diversity bonus/penalty
            dept_count = department_counts.get(result.department, 0)
            diversity_score = max(0.5, 1.0 - (dept_count * 0.2))  # Diminishing returns for same department
            
            # Combine scores
            final_score = base_score * level_score * diversity_score * result.similarity_score
            
            scored_results.append((result, final_score, reason))
            department_counts[result.department] = dept_count + 1
        
        return scored_results
    
    def _get_course_info(self, course_code: str) -> Optional[Dict]:
        """Get course info from database"""
        try:
            with SessionLocal() as db:
                course = db.query(Course).filter(Course.code == course_code, Course.is_active == True).first()
                if course:
                    return {
                        'department': course.department,
                        'level': course.level,
                        'title': course.title,
                        'description': course.description,
                        'credits': course.credits,
                        'prerequisites': course.prerequisites
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get course info for {course_code}: {e}")
            return None
    
    def get_cluster_summary(self) -> Dict[int, Dict]:
        """Get summary of topic clusters"""
        if not self.topic_clusters:
            return {}
        
        summary = {}
        with SessionLocal() as db:
            for cluster_id, course_codes in self.topic_clusters.items():
                # Get sample courses from cluster
                sample_courses = course_codes[:5]
                cluster_info = {
                    'size': len(course_codes),
                    'sample_courses': [],
                    'departments': set(),
                    'levels': set()
                }
                
                for code in sample_courses:
                    course = db.query(Course).filter(Course.code == code).first()
                    if course:
                        cluster_info['sample_courses'].append({
                            'code': course.code,
                            'title': course.title,
                            'department': course.department
                        })
                        cluster_info['departments'].add(course.department)
                        cluster_info['levels'].add(course.level // 100)
                
                cluster_info['departments'] = list(cluster_info['departments'])
                cluster_info['levels'] = list(cluster_info['levels'])
                summary[cluster_id] = cluster_info
        
        return summary

def main():
    """Test the similarity search engine"""
    engine = VectorSimilarityEngine()
    
    if not engine.embeddings_array is not None:
        print("❌ No embeddings loaded. Generate embeddings first!")
        return
    
    print("🔍 Testing similarity search engine...")
    
    # Test 1: Find courses similar to CS135
    print("\n1. Courses similar to CS135:")
    similar = engine.find_similar_courses("CS135", top_k=5)
    for result in similar:
        print(f"   {result.course_code}: {result.title} (similarity: {result.similarity_score:.3f})")
    
    # Test 2: Search by text query
    print("\n2. Courses matching 'machine learning artificial intelligence':")
    text_results = engine.search_by_text_query("machine learning artificial intelligence", top_k=5)
    for result in text_results:
        print(f"   {result.course_code}: {result.title} (similarity: {result.similarity_score:.3f})")
    
    # Test 3: Student recommendations
    print("\n3. Recommendations for CS student:")
    context = RecommendationContext(
        student_year=2,
        favorite_courses=["CS135", "MATH135"],
        interests=["algorithms", "data structures"],
        program="Computer Science"
    )
    recommendations = engine.get_recommendations_for_student(context, top_k=5)
    for result in recommendations:
        print(f"   {result.course_code}: {result.title} (score: {result.similarity_score:.3f})")

if __name__ == "__main__":
    main()