"""Demo run - Test AI agents without database"""

import asyncio
import os
import sys

# Setup demo environment
os.environ['TIGER_SERVICE_ID'] = 'demo-service'
os.environ['TIGER_DB_HOST'] = 'localhost'
os.environ['TIGER_DB_PORT'] = '5432'
os.environ['TIGER_DB_NAME'] = 'demo'
os.environ['TIGER_DB_USER'] = 'demo'
os.environ['TIGER_DB_PASSWORD'] = 'demo'

from app.agents import SecurityAgent, PerformanceAgent, QualityAgent

# Sample code to review
SAMPLE_CODE = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user[0]
        return True
    return False

def process_file(filename):
    with open('/uploads/' + filename, 'r') as f:
        data = f.read()
    return data
"""

async def run_demo():
    print("=" * 80)
    print("🚀 AI CODE REVIEW SWARM - DEMO MODE")
    print("=" * 80)
    print()
    print("📝 Sample Code:")
    print("-" * 80)
    print(SAMPLE_CODE)
    print("-" * 80)
    print()
    print("🤖 Initializing AI Agents...")
    print()
    
    # Initialize agents
    security = SecurityAgent()
    performance = PerformanceAgent()
    quality = QualityAgent()
    
    print("✅ Security Agent: Ready")
    print("✅ Performance Agent: Ready")
    print("✅ Quality Agent: Ready")
    print()
    
    # Check AI status
    if security.gemini_model:
        print("🧠 AI Model: Gemini Pro (ACTIVE)")
    elif security.openai_client:
        print("🧠 AI Model: OpenAI GPT-4")
    elif security.anthropic_client:
        print("🧠 AI Model: Anthropic Claude")
    else:
        print("⚠️  No AI model configured - please add API keys to .env")
        return
    
    print()
    print("🔍 Starting code review...")
    print("=" * 80)
    print()
    
    # Run agents in parallel
    results = await asyncio.gather(
        security.analyze_code(SAMPLE_CODE, "python"),
        performance.analyze_code(SAMPLE_CODE, "python"),
        quality.analyze_code(SAMPLE_CODE, "python"),
        return_exceptions=True
    )
    
    # Display results
    agent_names = ["🔒 SECURITY AGENT", "⚡ PERFORMANCE AGENT", "✨ QUALITY AGENT"]
    
    for i, (name, result) in enumerate(zip(agent_names, results)):
        print(f"\n{name}")
        print("=" * 80)
        
        if isinstance(result, Exception):
            print(f"❌ Error: {result}")
            continue
        
        print(f"⏱️  Execution Time: {result.execution_time:.2f}s")
        print(f"📊 Status: {result.status.value}")
        print(f"🔍 Issues Found: {len(result.issues)}")
        print()
        
        if result.issues:
            print("Issues:")
            print("-" * 80)
            for j, issue in enumerate(result.issues[:3], 1):  # Show top 3
                print(f"\n{j}. [{issue.severity.upper()}] {issue.title}")
                print(f"   Line: {issue.line_number}")
                print(f"   Category: {issue.category}")
                print(f"   Description: {issue.description}")
                if issue.suggestion:
                    print(f"   Fix: {issue.suggestion}")
        
        print()
        print("Summary:")
        print(result.summary)
        print()
    
    print("=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    print()
    print("📚 Next Steps:")
    print("1. Setup Tiger Cloud: tiger auth login")
    print("2. Create service: tiger service create --name code-review-swarm")
    print("3. Get credentials: tiger db connection-string")
    print("4. Update .env file")
    print("5. Run full application: python app/main.py")
    print()
    print("📖 Read CHECKLIST.md for complete guide!")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
