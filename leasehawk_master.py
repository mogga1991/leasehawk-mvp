#!/usr/bin/env python3
"""
LeaseHawk Master Command - Your Secret Weapon
The complete LeaseHawk system in one command
"""
import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """Print LeaseHawk banner"""
    print("""
🦅 ═══════════════════════════════════════════════════════════════
   LEASEHAWK - GOVERNMENT LEASE INTELLIGENCE PLATFORM
   Your Secret Weapon for GSA Opportunities
═══════════════════════════════════════════════════════════════
""")

def run_setup():
    """Initial setup and installation"""
    print("🔧 SETTING UP LEASEHAWK...")
    
    # Install requirements
    print("📦 Installing dependencies...")
    subprocess.run(["pip", "install", "-r", "backend/requirements.txt"], cwd=".")
    
    # Setup directories
    os.makedirs("data/prospectuses", exist_ok=True)
    os.makedirs("data/outreach", exist_ok=True)
    os.makedirs("data/exports", exist_ok=True)
    
    # Check .env file
    if not os.path.exists("backend/.env"):
        print("📝 Creating .env file...")
        subprocess.run(["cp", "backend/config.env.template", "backend/.env"])
        print("⚠️  Please update backend/.env with your API keys and Notion tokens")
    
    print("✅ Setup complete!")

def run_daily_intelligence():
    """Run the daily intelligence brief"""
    print("🧠 RUNNING DAILY INTELLIGENCE BRIEF...")
    subprocess.run(["python", "backend/scripts/daily_brief.py", "--full"], cwd=".")

def load_all_opportunities():
    """Load all GSA opportunities"""
    print("📥 LOADING ALL GSA OPPORTUNITIES...")
    subprocess.run(["python", "backend/scripts/load_all_gsa.py"], cwd=".")

def hunt_properties():
    """Hunt for matching properties"""
    print("🏢 HUNTING FOR MATCHING PROPERTIES...")
    subprocess.run(["python", "backend/scripts/property_hunter.py", "--all"], cwd=".")

def generate_outreach():
    """Generate outreach campaigns"""
    print("📧 GENERATING OUTREACH CAMPAIGNS...")
    subprocess.run(["python", "backend/scripts/outreach_generator.py", "--all-high-value"], cwd=".")

def analyze_deals():
    """Analyze deal values"""
    print("💰 ANALYZING DEAL VALUES...")
    subprocess.run(["python", "backend/scripts/deal_calculator.py", "--portfolio"], cwd=".")

def get_winning_strategy():
    """Get winning strategy"""
    print("🏆 GENERATING WINNING STRATEGY...")
    subprocess.run(["python", "backend/scripts/win_strategy.py"], cwd=".")

def start_api_server():
    """Start the API server"""
    print("🚀 STARTING API SERVER...")
    print("Access at: http://localhost:8000")
    subprocess.run(["uvicorn", "app.main:app", "--reload"], cwd="backend")

def start_notion_watcher():
    """Start Notion watcher"""
    print("👁️  STARTING NOTION WATCHER...")
    subprocess.run([
        "python", "-c", 
        "from app.notion_watcher import start_notion_watcher; start_notion_watcher(15)"
    ], cwd="backend")

def show_quick_wins():
    """Show the specific high-value opportunities"""
    print("""
💰 YOUR IMMEDIATE OPPORTUNITIES:

🎯 Franklin County VA Medical Center (POH-09-VA25)
   📍 Location: Franklin County, OH  
   💵 Annual Value: $4,230,000
   🏆 Your Potential Fee: $84,600 (2% finder + 1% success)
   📊 Size: 85,000 sq ft
   ⏰ Timeline: 9x expansion - URGENT NEED
   🎲 Win Factor: VA medical = specialized requirements = less competition

🎯 Salt Lake City VA Medical Center (PUT-24-VA25)  
   📍 Location: Salt Lake City, UT
   💵 Annual Value: $7,760,000
   🏆 Your Potential Fee: $155,200 (2% finder + 1% success)
   📊 Size: 95,000 sq ft
   ⏰ Timeline: New facility requirement
   🎲 Win Factor: Western market + medical specs = easier win

💎 TOTAL IMMEDIATE POTENTIAL: $239,800

🚀 48-HOUR ACTION PLAN:
   Hour 1-8:   Property hunt (LoopNet, CoStar searches)
   Hour 9-16:  Owner outreach (emails + cold calls)  
   Hour 17-24: Prepare compliance packages
   Hour 25-48: Close first property owner agreement

📞 YOUR SUCCESS FORMULA:
   1. "The government needs X sq ft in your area"
   2. "Worth $X million per year"
   3. "Your property is a perfect match"
   4. "Let's discuss positioning to win"
""")

def main():
    """Main command interface"""
    
    print_banner()
    
    if len(sys.argv) < 2:
        print("""
🎯 LEASEHAWK COMMANDS:

QUICK START:
   setup           🔧 Initial setup and installation
   daily           🧠 Run daily intelligence brief  
   quick-wins      💰 Show immediate high-value opportunities

FULL WORKFLOW:
   load            📥 Load all GSA prospectuses
   hunt            🏢 Hunt for matching properties
   outreach        📧 Generate outreach campaigns
   deals           💰 Analyze deal values
   strategy        🏆 Get winning strategy

SERVICES:
   api             🚀 Start API server
   notion          👁️  Start Notion watcher
   
EXAMPLES:
   python leasehawk_master.py daily       # Daily brief
   python leasehawk_master.py quick-wins  # Show opportunities
   python leasehawk_master.py setup       # First time setup
""")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "setup":
            run_setup()
        elif command == "daily":
            run_daily_intelligence()
        elif command == "quick-wins":
            show_quick_wins()
        elif command == "load":
            load_all_opportunities()
        elif command == "hunt":
            hunt_properties()
        elif command == "outreach":
            generate_outreach()
        elif command == "deals":
            analyze_deals()
        elif command == "strategy":
            get_winning_strategy()
        elif command == "api":
            start_api_server()
        elif command == "notion":
            start_notion_watcher()
        else:
            print(f"❌ Unknown command: {command}")
            print("Run without arguments to see available commands")
    
    except KeyboardInterrupt:
        print("\n👋 LeaseHawk stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()