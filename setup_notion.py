#!/usr/bin/env python3
"""
Quick setup script for LeaseHawk Notion integration
"""
import os

def main():
    print("🦅 LeaseHawk Notion Integration Setup")
    print("=" * 50)
    
    # Check if .env exists
    env_path = "backend/.env"
    if not os.path.exists(env_path):
        print("Creating .env file from template...")
        os.system("cp backend/config.env.template backend/.env")
        print("✅ Created backend/.env")
    else:
        print("✅ .env file already exists")
    
    print("\n📋 Setup Instructions:")
    print("1. Go to https://www.notion.so/my-integrations")
    print("2. Create new integration named 'LeaseHawk'")
    print("3. Copy the Integration Token")
    print("4. Create two databases in Notion:")
    print("   - Prospectuses Database")
    print("   - Properties Database")
    print("5. Share both databases with your LeaseHawk integration")
    print("6. Copy the database IDs from the URLs")
    print("7. Update backend/.env with your tokens and IDs")
    
    print("\n🚀 Quick Start Commands:")
    print("# Install requirements")
    print("cd backend && pip install -r requirements.txt")
    print("")
    print("# Run complete workflow")
    print("python backend/scripts/complete_workflow.py --full")
    print("")
    print("# Start API server")
    print("cd backend && uvicorn app.main:app --reload")
    print("")
    print("# Start Notion watcher (separate terminal)")
    print("cd backend && python -c \"from app.notion_watcher import start_notion_watcher; start_notion_watcher(15)\"")
    
    print("\n📚 API Endpoints:")
    print("POST /sync-from-notion/ - Pull data from Notion")
    print("POST /upload-pdf-to-notion/ - Parse PDF and add to Notion")
    print("POST /push-match-to-notion/ - Update match scores in Notion")
    print("GET /opportunities/ - Get all opportunities with match counts")

if __name__ == "__main__":
    main()