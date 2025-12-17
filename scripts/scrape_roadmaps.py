"""
سكريبت لعمل Scraping من roadmap.sh وحفظ البيانات في Supabase
"""

import requests
from bs4 import BeautifulSoup
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time

# تحميل المتغيرات
load_dotenv()

# الاتصال بـ Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# قائمة الـ Roadmaps الشهيرة من roadmap.sh
ROADMAPS = [
    {"slug": "frontend", "title": "Frontend Developer", "category": "Web Development"},
    {"slug": "backend", "title": "Backend Developer", "category": "Web Development"},
    {"slug": "devops", "title": "DevOps Engineer", "category": "DevOps"},
    {"slug": "full-stack", "title": "Full Stack Developer", "category": "Web Development"},
    {"slug": "android", "title": "Android Developer", "category": "Mobile Development"},
    {"slug": "react", "title": "React Developer", "category": "Frontend"},
    {"slug": "python", "title": "Python Developer", "category": "Programming"},
    {"slug": "java", "title": "Java Developer", "category": "Programming"},
    {"slug": "nodejs", "title": "Node.js Developer", "category": "Backend"},
    {"slug": "javascript", "title": "JavaScript Developer", "category": "Programming"},
    {"slug": "golang", "title": "Go Developer", "category": "Programming"},
    {"slug": "sql", "title": "SQL", "category": "Database"},
    {"slug": "postgresql-dba", "title": "PostgreSQL DBA", "category": "Database"},
    {"slug": "mongodb", "title": "MongoDB", "category": "Database"},
    {"slug": "cyber-security", "title": "Cyber Security", "category": "Security"},
    {"slug": "ux-design", "title": "UX Design", "category": "Design"},
    {"slug": "ai-data-scientist", "title": "AI & Data Scientist", "category": "AI/ML"},
    {"slug": "mlops", "title": "MLOps", "category": "AI/ML"},
    {"slug": "blockchain", "title": "Blockchain", "category": "Web3"},
    {"slug": "qa", "title": "QA Engineer", "category": "Testing"},
    {"slug": "software-architect", "title": "Software Architect", "category": "Architecture"},
    {"slug": "game-developer", "title": "Game Developer", "category": "Gaming"},
    {"slug": "flutter", "title": "Flutter Developer", "category": "Mobile Development"},
    {"slug": "react-native", "title": "React Native", "category": "Mobile Development"},
    {"slug": "docker", "title": "Docker", "category": "DevOps"},
    {"slug": "kubernetes", "title": "Kubernetes", "category": "DevOps"},
]

def scrape_roadmap_details(slug):
    """
    محاولة الحصول على تفاصيل Roadmap من roadmap.sh
    """
    url = f"https://roadmap.sh/{slug}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # محاولة استخراج الوصف
            description = ""
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            return {
                "url": url,
                "description": description or f"Step by step guide to becoming a {slug.replace('-', ' ').title()}"
            }
    except Exception as e:
        print(f"Error scraping {slug}: {e}")
    
    return {
        "url": f"https://roadmap.sh/{slug}",
        "description": f"Step by step guide to becoming a {slug.replace('-', ' ').title()}"
    }

def insert_roadmaps():
    """
    إدخال الـ Roadmaps في Supabase
    """
    print("Starting Scraping and saving Roadmaps...")
    
    for roadmap in ROADMAPS:
        print(f"\nProcessing: {roadmap['title']}...")
        
        # الحصول على التفاصيل
        details = scrape_roadmap_details(roadmap['slug'])
        
        # البيانات للحفظ
        data = {
            "title": roadmap['title'],
            "slug": roadmap['slug'],
            "description": details['description'],
            "url": details['url'],
            "category": roadmap['category'],
            "skills": json.dumps([])  # يمكن إضافة المهارات لاحقاً
        }
        
        try:
            # محاولة الإدخال
            result = supabase.table("roadmaps").upsert(
                data,
                on_conflict="slug"
            ).execute()
            
            print(f"Saved: {roadmap['title']}")
        except Exception as e:
            print(f"Error saving {roadmap['title']}: {e}")
        
        # تأخير بسيط لتجنب الحظر
        time.sleep(1)
    
    print("\nScraping completed successfully!")

def verify_data():
    """
    التحقق من البيانات المحفوظة
    """
    print("\nVerifying data...")
    
    try:
        result = supabase.table("roadmaps").select("*").execute()
        print(f"Total Roadmaps saved: {len(result.data)}")
        
        # عرض أول 5
        print("\nFirst 5 Roadmaps:")
        for roadmap in result.data[:5]:
            print(f"  - {roadmap['title']} ({roadmap['category']})")
    except Exception as e:
        print(f"Error verifying: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Roadmap.sh Scraper - Professor Code")
    print("=" * 60)
    
    # تنفيذ Scraping
    insert_roadmaps()
    
    # التحقق
    verify_data()
    
    print("\nDone! You can now use the chatbot.")
