"""
سكريبت للتحقق من بيانات Roadmaps في Supabase
"""

from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

# جلب جميع الـ Roadmaps
result = supabase.table("roadmaps").select("*").execute()

print("=" * 60)
print("Roadmaps in Database:")
print("=" * 60)

for roadmap in result.data:
    print(f"\nTitle: {roadmap['title']}")
    print(f"Slug: {roadmap['slug']}")
    print(f"Category: {roadmap.get('category', 'N/A')}")
    print(f"Description: {roadmap.get('description', 'N/A')[:100]}...")
    print("-" * 40)

print(f"\nTotal: {len(result.data)} roadmaps")
