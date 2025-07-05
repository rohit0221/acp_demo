#!/usr/bin/env python3
"""
ACP Server wrapper for CrewAI Email Classifier
This creates a proper ACP agent that can be discovered and communicate with other agents
"""

import sys
import os
import json
from collections.abc import Iterator, AsyncIterator
from typing import Any

# Add the parent directory to the path to import crew
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from acp_sdk import Message, MessagePart
    from acp_sdk.server import Context, Server
    ACP_AVAILABLE = True
    print("✅ ACP SDK loaded successfully")
except ImportError as e:
    print(f"❌ ACP SDK not available: {e}")
    ACP_AVAILABLE = False
    # Mock classes for when ACP is not available
    class Message:
        def __init__(self, role="user", parts=None):
            self.role = role
            self.parts = parts or []
    
    class MessagePart:
        def __init__(self, content="", type="text/plain"):
            self.content = content
            self.type = type
    
    class Context:
        pass
    
    class Server:
        def agent(self):
            return lambda f: f
        
        def run(self, host="0.0.0.0", port=8003):
            print(f"❌ Mock server cannot run without ACP SDK")

# Import our CrewAI crew



try:
    from email_classifier_crew.crew import EmailClassifierCrew
    CREW_AVAILABLE = True
    print("✅ CrewAI crew loaded successfully")
except ImportError as e:
    try:
        # Try absolute import
        sys.path.append(os.path.dirname(__file__))
        from email_classifier_crew.crew import EmailClassifierCrew
        CREW_AVAILABLE = True
        print("✅ CrewAI crew loaded successfully")
    except ImportError as e2:
        print(f"❌ CrewAI crew not available: {e2}")
        CREW_AVAILABLE = False

# Initialize ACP server
server = Server() if ACP_AVAILABLE else None

# Initialize CrewAI crew
crew_instance = EmailClassifierCrew() if CREW_AVAILABLE else None

@server.agent(
    name="email-classifier",
    description="Classifies emails using CrewAI and GPT-4o-mini",
    input_content_types=["text/plain", "application/json"],
    output_content_types=["application/json"]
) if ACP_AVAILABLE else lambda f: f
async def email_classifier_agent(input: list, context) -> AsyncIterator:
    """
    ACP Agent that wraps CrewAI Email Classifier
    
    This agent:
    1. Receives ACP messages 
    2. Extracts email content
    3. Uses CrewAI crew with GPT-4o-mini for classification
    4. Returns structured JSON via ACP
    """
    print(f"📧 ACP Email Classifier Agent started. Processing {len(input)} messages...")
    
    if not CREW_AVAILABLE:
        yield MessagePart(
            content=json.dumps({
                "error": "CrewAI crew not available",
                "type": "error",
                "priority": "low",
                "confidence": 0.0,
                "reasoning": "CrewAI email classification crew could not be loaded",
                "suggested_response_tone": "professional"
            }, indent=2),
            type="application/json"
        )
        return
    
    if not input:
        yield MessagePart(
            content=json.dumps({
                "error": "No email content provided", 
                "type": "error",
                "priority": "low",
                "confidence": 0.0,
                "reasoning": "No ACP messages received for classification",
                "suggested_response_tone": "professional"
            }, indent=2),
            type="application/json"
        )
        return
    
    # Extract email content and subject from ACP messages
    email_content = ""
    email_subject = ""
    
    for message in input:
        for part in message.parts:
            if part.type == "text/plain":
                email_content += part.content + "\n"
            elif part.type == "application/json":
                try:
                    data = json.loads(part.content)
                    if "email_subject" in data:
                        email_subject = data["email_subject"]
                    elif "subject" in data:
                        email_subject = data["subject"]
                    if "email_content" in data:
                        email_content += data["email_content"] + "\n"
                    elif "content" in data:
                        email_content += data["content"] + "\n"
                except json.JSONDecodeError:
                    pass
    
    # Extract subject from email if not provided separately
    if not email_subject and email_content:
        lines = email_content.strip().split('\n')
        for line in lines:
            if line.lower().startswith('subject:'):
                email_subject = line[8:].strip()
                break
    
    if not email_content.strip():
        yield MessagePart(
            content=json.dumps({
                "error": "No email content found in messages",
                "type": "error", 
                "priority": "low",
                "confidence": 0.0,
                "reasoning": "ACP messages contained no readable email content",
                "suggested_response_tone": "professional"
            }, indent=2),
            type="application/json"
        )
        return
    
    print(f"📧 Extracted email content: {email_content[:100]}...")
    print(f"📧 Extracted subject: {email_subject}")
    
    try:
        # Use CrewAI crew to classify the email
        print("🤖 Calling CrewAI crew for email classification...")
        result = crew_instance.classify_email_content(email_content.strip(), email_subject)
        
        # Add ACP metadata
        result["acp_agent"] = "email_classifier_agent"
        result["communication_protocol"] = "ACP"
        result["processing_time"] = "completed"
        
        print(f"📧 CrewAI classification complete: {result.get('type', 'unknown')}")
        
        # Return via ACP MessagePart
        yield MessagePart(
            content=json.dumps(result, indent=2),
            type="application/json"
        )
        
    except Exception as e:
        print(f"❌ CrewAI classification error: {e}")
        
        yield MessagePart(
            content=json.dumps({
                "error": f"Classification failed: {str(e)}",
                "type": "error",
                "priority": "medium",
                "confidence": 0.0,
                "reasoning": f"CrewAI crew execution failed: {str(e)}",
                "suggested_response_tone": "professional",
                "acp_agent": "email_classifier_agent",
                "communication_protocol": "ACP"
            }, indent=2),
            type="application/json"
        )

def test_acp_server():
    """Test function to verify ACP server is working"""
    print("🧪 Testing ACP Email Classifier Agent")
    print("=" * 50)
    
    if not ACP_AVAILABLE:
        print("❌ Cannot test: ACP SDK not available")
        return
        
    if not CREW_AVAILABLE:
        print("❌ Cannot test: CrewAI crew not available")  
        return
    
    # Create test message
    test_message = Message(
        role="user",
        parts=[
            MessagePart(
                content="Subject: Pricing Question\n\nHi, I'm interested in your enterprise pricing for 100 users. Can you send me a quote?",
                type="text/plain"
            )
        ]
    )
    
    print("📧 Testing with sample email message...")
    
    # Test the agent function directly
    context = Context()  # Mock context
    results = list(email_classifier_agent([test_message], context))
    
    for result in results:
        if result.type == "application/json":
            classification = json.loads(result.content)
            print(f"🤖 Test Result:")
            print(f"   Type: {classification.get('type', 'unknown')}")
            print(f"   Priority: {classification.get('priority', 'unknown')}")
            print(f"   Confidence: {classification.get('confidence', 0):.2f}")
            print(f"   ACP Agent: {classification.get('acp_agent', 'unknown')}")
            print(f"   Protocol: {classification.get('communication_protocol', 'unknown')}")
        else:
            print(f"❌ Unexpected result type: {result.type}")

if __name__ == "__main__":
    print("🚀 ACP Email Classifier Agent Server")
    print(f"🔧 ACP SDK Available: {'✅ Yes' if ACP_AVAILABLE else '❌ No'}")
    print(f"🤖 CrewAI Available: {'✅ Yes' if CREW_AVAILABLE else '❌ No'}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        test_acp_server()
    else:
        # Server mode
        if ACP_AVAILABLE and server:
            print("📧 Starting ACP server on port 8003...")
            print("📧 Agent manifest: http://localhost:8003/agents")
            print("📧 Use ACP client to send email classification requests")
            server.run(host="0.0.0.0", port=8003)
        else:
            print("❌ Cannot start server: ACP SDK not available")
            print("Running test instead...")
            test_acp_server()