#!/usr/bin/env python3
"""
Main entry point for Email Classification Crew
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path to import crew
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from email_classifier_crew.crew import EmailClassifierCrew
    CREW_AVAILABLE = True
except ImportError as e:
    print(f"❌ CrewAI not available: {e}")
    CREW_AVAILABLE = False

def test_email_classification():
    """
    Test the email classification crew with sample emails
    """
    print("🚀 Testing CrewAI Email Classification Crew")
    print("=" * 60)
    print(f"🔑 OpenAI API Key: {'✅ Found' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"🤖 CrewAI Available: {'✅ Yes' if CREW_AVAILABLE else '❌ No'}")
    
    if not CREW_AVAILABLE:
        print("❌ Cannot run tests without CrewAI. Please install dependencies.")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Cannot run tests without OpenAI API key. Please set OPENAI_API_KEY in .env")
        return
    
    # Initialize the crew
    try:
        crew = EmailClassifierCrew()
        print("✅ Email Classification Crew initialized")
    except Exception as e:
        print(f"❌ Failed to initialize crew: {e}")
        return
    
    # Test emails
    test_emails = [
        {
            "subject": "Enterprise Pricing Inquiry",
            "content": "Hi, I'm interested in your enterprise pricing plans for our company of 500 employees. Could you provide a detailed quote and schedule a demo?",
            "expected": "sales"
        },
        {
            "subject": "Urgent: Login Issues",
            "content": "I can't log into my account and I have an important presentation tomorrow. The password reset isn't working. Please help ASAP!",
            "expected": "urgent"
        },
        {
            "subject": "🎉 Congratulations! You've Won!",
            "content": "You've been selected to receive $10,000! Click this link immediately to claim your prize before it expires!",
            "expected": "spam"
        },
        {
            "subject": "Coffee catch-up",
            "content": "Hey! How was your vacation? Want to grab coffee this weekend and catch up?",
            "expected": "personal"
        }
    ]
    
    print(f"\n📧 Testing {len(test_emails)} sample emails...")
    print("-" * 60)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n📧 Test {i}: {email['subject']}")
        print(f"Content: {email['content'][:80]}...")
        print(f"Expected: {email['expected']}")
        print("-" * 40)
        
        try:
            # Classify using CrewAI
            result = crew.classify_email_content(email['content'], email['subject'])
            
            print(f"🤖 CrewAI Classification Result:")
            print(f"   Type: {result.get('type', 'unknown')}")
            print(f"   Priority: {result.get('priority', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Response Tone: {result.get('suggested_response_tone', 'unknown')}")
            print(f"   Framework: {result.get('framework', 'unknown')}")
            print(f"   Agent: {result.get('agent', 'unknown')}")
            print(f"   Reasoning: {result.get('reasoning', 'No reasoning provided')}")
            
            # Check accuracy
            if result.get('type') == email['expected']:
                print(f"   Status: ✅ EXACT MATCH")
            elif email['expected'] in result.get('reasoning', '').lower():
                print(f"   Status: ✅ PARTIAL MATCH (reasoning mentions {email['expected']})")
            else:
                print(f"   Status: ⚠️  DIFFERENT (expected {email['expected']})")
                
        except Exception as e:
            print(f"❌ Classification failed: {e}")
    
    print(f"\n✅ Email Classification Crew testing complete!")

def classify_single_email(content: str, subject: str = ""):
    """
    Classify a single email
    """
    if not CREW_AVAILABLE:
        print("❌ CrewAI not available")
        return None
    
    try:
        crew = EmailClassifierCrew()
        result = crew.classify_email_content(content, subject)
        return result
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 CrewAI Email Classification Crew")
    print("📧 Proper CrewAI structure with agents.yaml, tasks.yaml, crew.py, tools.py")
    
    if len(sys.argv) > 1:
        # Command line usage
        email_content = sys.argv[1]
        email_subject = sys.argv[2] if len(sys.argv) > 2 else ""
        
        print(f"\n📧 Classifying: {email_content[:50]}...")
        result = classify_single_email(email_content, email_subject)
        
        if result:
            print(f"\n🤖 Result:")
            print(json.dumps(result, indent=2))
    else:
        # Run tests
        test_email_classification()