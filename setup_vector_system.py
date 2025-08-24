#!/usr/bin/env python3
"""
COMPASS Vector Recommendation System Setup
This script sets up the complete vector-based recommendation system
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🚀 COMPASS Vector Recommendation System Setup")
    print("=" * 60)
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📋 Checking dependencies...")
    
    required_packages = [
        'openai', 'numpy', 'scikit-learn', 'faiss-cpu', 
        'sentence-transformers', 'neo4j'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n🔧 Installing missing packages: {' '.join(missing_packages)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
        print("✅ Dependencies installed successfully")
    
    print()

def check_openai_key():
    """Check if OpenAI API key is configured"""
    print("🔑 Checking OpenAI API configuration...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("\n📝 To set up OpenAI API:")
        print("   1. Get API key from: https://platform.openai.com/api-keys")
        print("   2. Set environment variable:")
        print("      export OPENAI_API_KEY='your-key-here'")
        print("   3. Add to your ~/.bashrc or ~/.zshrc for persistence")
        print("\n⚠️  Vector embeddings will not work without API key")
        return False
    else:
        # Test API key with a simple request
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Test with a minimal embedding
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            print("✅ OpenAI API key is valid")
            return True
        except Exception as e:
            print(f"❌ OpenAI API key test failed: {e}")
            return False
    
    print()

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
    
    print()

def generate_embeddings():
    """Generate course embeddings"""
    print("🧠 Generating course embeddings...")
    
    # Check if embeddings already exist
    embeddings_file = "course_embeddings.json"
    if os.path.exists(embeddings_file):
        try:
            with open(embeddings_file, 'r') as f:
                data = json.load(f)
                existing_count = len(data.get('embeddings', []))
                print(f"  📁 Found existing embeddings: {existing_count} courses")
                
                response = input("  🤔 Generate new embeddings? (y/n): ")
                if response.lower() != 'y':
                    print("  ⏭️  Skipping embedding generation")
                    return True
        except:
            pass
    
    try:
        # Add backend to Python path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.vector_engine.embedding_generator import CourseEmbeddingGenerator
        
        generator = CourseEmbeddingGenerator()
        print("  🚀 Starting embedding generation (this may take 10-20 minutes)...")
        
        stats = generator.process_all_courses(
            save_to_file=embeddings_file,
            resume=True
        )
        
        print(f"  ✅ Generated embeddings for {stats['successful_embeddings']} courses")
        print(f"  ⏱️  Duration: {stats.get('duration_minutes', 0):.1f} minutes")
        print(f"  💰 API calls: {stats.get('api_calls', 0)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False
    
    print()

def test_vector_system():
    """Test the vector recommendation system"""
    print("🧪 Testing vector recommendation system...")
    
    try:
        # Add backend to Python path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.vector_engine.recommendation_engine import (
            MultiDimensionalRecommendationEngine, 
            RecommendationMode, 
            RecommendationContext
        )
        
        # Initialize engine
        engine = MultiDimensionalRecommendationEngine()
        
        # Test recommendation
        context = RecommendationContext(
            student_year=2,
            favorite_courses=["CS135", "MATH135"],
            interests=["algorithms", "software engineering"],
            program="Computer Science",
            gpa=3.5
        )
        
        recommendations = engine.generate_recommendations(
            context=context,
            mode=RecommendationMode.ADVANCED,
            top_k=5
        )
        
        print(f"  ✅ Generated {len(recommendations)} test recommendations")
        
        if recommendations:
            print("  📋 Sample recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"    {i}. {rec.course.code}: {rec.course.title}")
                print(f"       Score: {rec.overall_score:.3f}, Confidence: {rec.confidence:.3f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Vector system test failed: {e}")
        return False
    
    print()

def create_test_script():
    """Create a test script for manual testing"""
    print("📝 Creating test script...")
    
    test_script_content = '''#!/usr/bin/env python3
"""
Test script for COMPASS vector recommendations
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.vector_engine.recommendation_engine import (
    MultiDimensionalRecommendationEngine, 
    RecommendationMode, 
    RecommendationContext
)

def test_recommendations():
    """Test different recommendation scenarios"""
    
    engine = MultiDimensionalRecommendationEngine()
    
    # Test scenarios
    scenarios = [
        {
            "name": "CS Student",
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
                interests=["electronics", "signal processing"],
                program="Electrical Engineering",
                gpa=3.4
            )
        }
    ]
    
    for scenario in scenarios:
        print(f"\\n🎯 Testing: {scenario['name']}")
        print("=" * 50)
        
        for mode in [RecommendationMode.BASIC, RecommendationMode.ADVANCED]:
            print(f"\\n📊 {mode.value.upper()} Mode:")
            
            recommendations = engine.generate_recommendations(
                context=scenario["context"],
                mode=mode,
                top_k=3
            )
            
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec.course.code}: {rec.course.title}")
                print(f"     Score: {rec.overall_score:.3f} | Confidence: {rec.confidence:.3f}")
                print(f"     {rec.reasoning}")

if __name__ == "__main__":
    print("🚀 COMPASS Vector Recommendation Test")
    test_recommendations()
'''
    
    with open("test_vector_recommendations.py", "w") as f:
        f.write(test_script_content)
    
    os.chmod("test_vector_recommendations.py", 0o755)
    print("  ✅ Created test_vector_recommendations.py")
    print()

def print_next_steps():
    """Print next steps"""
    print("🎉 Setup Complete!")
    print()
    print("🔍 Next Steps:")
    print("  1. 📊 Test recommendations: python test_vector_recommendations.py")
    print("  2. 🌐 Start the backend: cd backend && uvicorn app.main:app --reload")
    print("  3. 🎨 Test via API: POST /api/v1/recommendations?use_vector=true&mode=advanced")
    print("  4. 🔧 Frontend integration: Update API calls to use vector parameters")
    print()
    print("📋 Available Recommendation Modes:")
    print("  - basic: Simple similarity-based recommendations")
    print("  - advanced: Multi-dimensional scoring with progression analysis")
    print("  - super_advanced: Maximum serendipity and discovery features")
    print()
    print("🔗 API Parameters:")
    print("  - use_vector=true: Enable vector recommendations")
    print("  - mode=[basic|advanced|super_advanced]: Set recommendation mode")
    print()
    
def main():
    """Main setup function"""
    print_banner()
    
    # Step 1: Check dependencies
    try:
        check_dependencies()
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return
    
    # Step 2: Check OpenAI API key
    openai_available = check_openai_key()
    
    # Step 3: Check database
    db_available = check_database()
    
    if not db_available:
        print("❌ Database not available. Please ensure the database is set up and populated.")
        return
    
    # Step 4: Generate embeddings (only if OpenAI is available)
    if openai_available:
        embeddings_generated = generate_embeddings()
        if not embeddings_generated:
            print("⚠️  Embeddings not generated. Vector recommendations will not work.")
            return
    else:
        print("⚠️  Skipping embedding generation (OpenAI API key not available)")
        return
    
    # Step 5: Test system
    system_works = test_vector_system()
    if not system_works:
        print("❌ System test failed")
        return
    
    # Step 6: Create test utilities
    create_test_script()
    
    # Step 7: Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()