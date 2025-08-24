#!/usr/bin/env python3
"""
COMPASS Qwen Vector Recommendation System Setup
This script sets up the complete vector-based recommendation system using Qwen3-Embedding-8B
"""

import os
import sys
import subprocess
import json
import torch
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 70)
    print("🚀 COMPASS Qwen Vector Recommendation System Setup")
    print("   Using Qwen3-Embedding-0.6B for local embeddings")
    print("=" * 70)
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📋 Checking dependencies...")
    
    required_packages = [
        ('torch', 'PyTorch for model inference'),
        ('transformers', 'Hugging Face transformers'),
        ('numpy', 'Numerical computing'),
        ('scikit-learn', 'Machine learning utilities'),
        ('faiss-cpu', 'Fast similarity search (optional)'),
    ]
    
    missing_packages = []
    available_packages = []
    
    for package, description in required_packages:
        try:
            if package == 'faiss-cpu':
                import faiss
                package_name = 'faiss'
            else:
                package_name = package.replace('-', '_')
            
            __import__(package_name)
            print(f"  ✅ {package} - {description}")
            available_packages.append(package)
        except ImportError:
            print(f"  ❌ {package} - {description} (missing)")
            missing_packages.append(package)
    
    # Special handling for FAISS (optional)
    if 'faiss-cpu' in missing_packages:
        print("  ⚠️  FAISS is optional - will use sklearn for similarity search")
    
    if missing_packages and not all(pkg == 'faiss-cpu' for pkg in missing_packages):
        core_missing = [pkg for pkg in missing_packages if pkg != 'faiss-cpu']
        if core_missing:
            print(f"\n🔧 Installing missing core packages: {' '.join(core_missing)}")
            subprocess.run([sys.executable, "-m", "pip", "install"] + core_missing, check=True)
            print("✅ Core dependencies installed successfully")
    
    print()
    return len(missing_packages) == 0 or all(pkg == 'faiss-cpu' for pkg in missing_packages)

def check_device_capabilities():
    """Check GPU/CPU capabilities"""
    print("🔧 Checking device capabilities...")
    
    device_info = {
        'cuda_available': torch.cuda.is_available(),
        'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        'recommended_device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'recommended_batch_size': 16 if torch.cuda.is_available() else 8
    }
    
    if device_info['cuda_available']:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"  ✅ CUDA available: {gpu_name} ({gpu_memory:.1f}GB)")
        print(f"  📊 Recommended: GPU with batch size {device_info['recommended_batch_size']}")
    else:
        print("  💻 CUDA not available - using CPU")
        print(f"  📊 Recommended: CPU with batch size {device_info['recommended_batch_size']}")
        print("  ⏱️  Note: CPU inference will be slower but still functional")
    
    print()
    return device_info

def check_database():
    """Check if course database is populated"""
    print("📊 Checking course database...")
    
    try:
        # Add backend to Python path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.models.database import SessionLocal, Course
        
        with SessionLocal() as db:
            total_courses = db.query(Course).filter(Course.is_active == True).count()
            departments = db.query(Course.department).distinct().count()
            
        print(f"  📚 Total courses: {total_courses}")
        print(f"  🏫 Departments: {departments}")
        
        if total_courses < 1000:
            print("⚠️  Database seems incomplete (< 1000 courses)")
            print("   Run scraping to populate more courses")
        else:
            print("✅ Course database looks good")
        
        return total_courses > 0
    
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def download_qwen_model():
    """Check if Qwen model needs to be downloaded"""
    print("🤖 Checking Qwen3-Embedding-0.6B model...")
    
    model_name = "Qwen/Qwen3-Embedding-0.6B"
    
    try:
        from transformers import AutoTokenizer, AutoModel
        
        print(f"  📥 Checking model: {model_name}")
        
        # Try to load tokenizer (this will download if needed)
        print("  🔄 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Try to load model metadata (without loading full model)
        print("  🔄 Loading model config...")
        model = AutoModel.from_pretrained(model_name, torch_dtype=torch.float16)
        
        print("  ✅ Qwen3-Embedding-0.6B model is ready")
        return True
        
    except Exception as e:
        print(f"  ❌ Model download/check failed: {e}")
        print("  💡 This might be due to network issues or insufficient disk space")
        print("  💡 The model is ~2GB and will be downloaded to ~/.cache/huggingface/")
        return False
    
    print()

def generate_qwen_embeddings(device_info: dict):
    """Generate course embeddings using Qwen"""
    print("🧠 Generating course embeddings with Qwen3-Embedding-0.6B...")
    
    # Check if embeddings already exist
    embeddings_file = "qwen_course_embeddings.json"
    if os.path.exists(embeddings_file):
        try:
            with open(embeddings_file, 'r') as f:
                data = json.load(f)
                existing_count = len(data.get('embeddings', []))
                print(f"  📁 Found existing embeddings: {existing_count} courses")
                
                response = input("  🤔 Generate new embeddings? (y/n): ").strip().lower()
                if response != 'y':
                    print("  ⏭️  Skipping embedding generation")
                    return True
        except:
            pass
    
    try:
        # Add backend to Python path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.vector_engine.local_embedding_generator import QwenEmbeddingGenerator
        
        print(f"  🚀 Initializing Qwen on {device_info['recommended_device']}")
        generator = QwenEmbeddingGenerator(device=device_info['recommended_device'])
        
        print(f"  📊 Model info:")
        model_info = generator.get_model_info()
        for key, value in model_info.items():
            print(f"     - {key}: {value}")
        
        print("  🚀 Starting embedding generation...")
        print(f"     This will process all courses in batches of {generator.batch_size}")
        
        if device_info['recommended_device'] == 'cpu':
            print("     ⏱️  CPU inference may take 15-30 minutes (0.6B model is faster!)")
        else:
            print("     ⏱️  GPU inference should take 5-10 minutes (0.6B model is faster!)")
        
        stats = generator.process_all_courses(
            save_to_file=embeddings_file,
            resume=True
        )
        
        print(f"  ✅ Generated embeddings for {stats['successful_embeddings']} courses")
        print(f"  ⏱️  Duration: {stats.get('duration_minutes', 0):.1f} minutes")
        print(f"  🔧 Device used: {generator.device}")
        
        return True
    
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False
    
    print()

def test_qwen_vector_system():
    """Test the Qwen vector recommendation system"""
    print("🧪 Testing Qwen vector recommendation system...")
    
    try:
        # Add backend to Python path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.vector_engine.qwen_similarity_search import QwenSimilarityEngine, RecommendationContext
        
        # Initialize engine
        print("  🔄 Initializing similarity search engine...")
        engine = QwenSimilarityEngine()
        
        if engine.embeddings_array is None:
            print("  ❌ No embeddings loaded")
            return False
        
        print(f"  📊 Loaded {len(engine.course_codes)} course embeddings")
        print(f"  🔍 Using {'FAISS' if engine.use_faiss else 'sklearn'} for search")
        
        # Test recommendation
        print("  🧪 Testing student recommendations...")
        context = RecommendationContext(
            student_year=2,
            favorite_courses=["CS135", "MATH135"],
            interests=["algorithms", "software engineering"],
            program="Computer Science",
            gpa=3.5
        )
        
        recommendations = engine.get_recommendations_for_student(context, top_k=5)
        
        print(f"  ✅ Generated {len(recommendations)} test recommendations")
        
        if recommendations:
            print("  📋 Sample recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"    {i}. {rec.course_code}: {rec.title}")
                print(f"       Similarity: {rec.similarity_score:.3f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Vector system test failed: {e}")
        return False
    
    print()

def create_qwen_test_script():
    """Create a test script for Qwen recommendations"""
    print("📝 Creating Qwen test script...")
    
    test_script_content = '''#!/usr/bin/env python3
"""
Test script for COMPASS Qwen3-Embedding-0.6B vector recommendations
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.vector_engine.qwen_similarity_search import QwenSimilarityEngine, RecommendationContext

def test_qwen_recommendations():
    """Test different recommendation scenarios with Qwen"""
    
    print("🚀 COMPASS Qwen Vector Recommendation Test")
    print("=" * 50)
    
    engine = QwenSimilarityEngine()
    
    if engine.embeddings_array is None:
        print("❌ No Qwen embeddings found!")
        print("   Run: python setup_qwen_vector_system.py")
        return
    
    print(f"📊 Loaded {len(engine.course_codes)} course embeddings")
    print(f"🔍 Search engine: {'FAISS' if engine.use_faiss else 'sklearn'}")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Computer Science Student",
            "context": RecommendationContext(
                student_year=2,
                favorite_courses=["CS135", "CS136", "MATH135"],
                interests=["algorithms", "data structures", "software engineering"],
                program="Computer Science",
                gpa=3.7
            )
        },
        {
            "name": "Engineering Student", 
            "context": RecommendationContext(
                student_year=3,
                favorite_courses=["ECE240", "MATH213"],
                interests=["electronics", "signal processing", "embedded systems"],
                program="Electrical Engineering",
                gpa=3.4
            )
        },
        {
            "name": "Math Student",
            "context": RecommendationContext(
                student_year=2,
                favorite_courses=["MATH135", "MATH137"],
                interests=["pure mathematics", "analysis", "algebra"],
                program="Mathematics",
                gpa=3.8
            )
        }
    ]
    
    for scenario in scenarios:
        print(f"\\n🎯 Testing: {scenario['name']}")
        print("=" * 40)
        
        recommendations = engine.get_recommendations_for_student(
            scenario["context"], 
            top_k=5
        )
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec.course_code}: {rec.title}")
            print(f"     Department: {rec.department} | Level: {rec.level}")
            print(f"     Similarity: {rec.similarity_score:.3f}")
            print()
    
    # Test similarity search
    print("\\n🔍 Testing similarity search:")
    print("=" * 40)
    
    test_course = "CS135"
    similar_courses = engine.find_similar_courses(test_course, top_k=5)
    
    print(f"Courses similar to {test_course}:")
    for rec in similar_courses:
        print(f"  • {rec.course_code}: {rec.title} (similarity: {rec.similarity_score:.3f})")
    
    # Test text query
    print("\\n🔤 Testing text query search:")
    print("=" * 40)
    
    query = "machine learning artificial intelligence data science"
    text_results = engine.search_by_text_query(query, top_k=5)
    
    print(f"Courses matching '{query}':")
    for rec in text_results:
        print(f"  • {rec.course_code}: {rec.title} (similarity: {rec.similarity_score:.3f})")

if __name__ == "__main__":
    test_qwen_recommendations()
'''
    
    with open("test_qwen_recommendations.py", "w") as f:
        f.write(test_script_content)
    
    os.chmod("test_qwen_recommendations.py", 0o755)
    print("  ✅ Created test_qwen_recommendations.py")
    print()

def print_next_steps():
    """Print next steps"""
    print("🎉 Qwen Vector System Setup Complete!")
    print()
    print("🔍 Next Steps:")
    print("  1. 📊 Test recommendations: python test_qwen_recommendations.py") 
    print("  2. 🌐 Start the backend: cd backend && uvicorn app.main:app --reload")
    print("  3. 🎨 Test via API: POST /api/v1/recommendations?use_vector=true&mode=advanced")
    print("  4. 🔧 Frontend integration: Update API calls to use vector parameters")
    print()
    print("📋 System Features:")
    print("  - 🧠 Qwen3-Embedding-0.6B for fast, high-quality semantic understanding")
    print("  - 🚀 FAISS for millisecond similarity search (if available)")
    print("  - 📊 K-means clustering for topic discovery")
    print("  - 🎯 Multi-dimensional scoring algorithm")
    print("  - 🔄 Progressive recommendation modes")
    print()
    print("⚡ Performance Notes:")
    print("  - GPU: ~5-10 minutes for embedding generation (0.6B is fast!)")
    print("  - CPU: ~15-30 minutes for embedding generation (0.6B is fast!)")
    print("  - Search: <100ms per query after embeddings are loaded")
    print()
    
def main():
    """Main setup function for Qwen vector system"""
    print_banner()
    
    # Step 1: Check dependencies
    try:
        deps_ok = check_dependencies()
        if not deps_ok:
            print("❌ Critical dependencies missing. Please install them and try again.")
            return
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return
    
    # Step 2: Check device capabilities
    device_info = check_device_capabilities()
    
    # Step 3: Check database
    db_available = check_database()
    if not db_available:
        print("❌ Database not available. Please ensure the database is set up and populated.")
        return
    
    # Step 4: Download/check Qwen model
    model_ready = download_qwen_model()
    if not model_ready:
        print("❌ Qwen model not available. Please check network connection and disk space.")
        return
    
    # Step 5: Generate embeddings
    embeddings_generated = generate_qwen_embeddings(device_info)
    if not embeddings_generated:
        print("⚠️  Embeddings not generated. Vector recommendations will not work.")
        return
    
    # Step 6: Test system
    system_works = test_qwen_vector_system()
    if not system_works:
        print("❌ System test failed")
        return
    
    # Step 7: Create test utilities
    create_qwen_test_script()
    
    # Step 8: Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()