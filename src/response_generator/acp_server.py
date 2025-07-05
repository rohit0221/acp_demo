#!/usr/bin/env python3
"""
ACP Server wrapper for OpenAI Response Generator
This creates a proper ACP agent that can be discovered and communicate with other agents
"""

import sys
import os
import json
from collections.abc import Iterator, AsyncIterator
from typing import Any

# Add the parent directory to the path to import response generator
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
        
        def run(self, host="0.0.0.0", port=8004):
            print(f"❌ Mock server cannot run without ACP SDK")

# Import our OpenAI response generator
try:
    from response_generator.generator import ResponseGenerator
    from response_generator.models import (
        ResponseRequest, EmailContext, StrategyContext, BusinessContext
    )
    RESPONSE_GEN_AVAILABLE = True
    print("✅ OpenAI response generator loaded successfully")
except ImportError as e:
    print(f"❌ OpenAI response generator not available: {e}")
    RESPONSE_GEN_AVAILABLE = False

# Initialize ACP server
server = Server() if ACP_AVAILABLE else None

# Initialize response generator
response_generator = ResponseGenerator() if RESPONSE_GEN_AVAILABLE else None

@server.agent(
    name="response-generator",
    description="Generates email responses using OpenAI GPT-4o-mini",
    input_content_types=["application/json"],
    output_content_types=["application/json"]
) if ACP_AVAILABLE else lambda f: f
async def response_generation_agent(input: list, context) -> AsyncIterator:
    """
    ACP Agent that wraps OpenAI Response Generator
    
    This agent:
    1. Receives ACP messages with email context and strategy recommendations
    2. Extracts email and strategy data
    3. Uses OpenAI GPT-4o-mini to generate email responses
    4. Returns structured response variants via ACP
    """
    print(f"📝 ACP Response Generation Agent started. Processing {len(input)} messages...")
    
    if not RESPONSE_GEN_AVAILABLE:
        yield MessagePart(
            content=json.dumps({
                "error": "OpenAI response generator not available",
                "variants": [],
                "recommended_variant": 0,
                "overall_confidence": 0.0,
                "requires_human_review": True,
                "review_reasons": ["Response generator could not be loaded"],
                "framework": "OpenAI GPT-4o-mini (Error)",
                "agent": "response_generation_agent"
            }, indent=2),
            type="application/json"
        )
        return
    
    if not input:
        yield MessagePart(
            content=json.dumps({
                "error": "No request data provided",
                "variants": [],
                "recommended_variant": 0,
                "overall_confidence": 0.0,
                "requires_human_review": True,
                "review_reasons": ["No ACP messages received for response generation"],
                "framework": "OpenAI GPT-4o-mini (Error)",
                "agent": "response_generation_agent"
            }, indent=2),
            type="application/json"
        )
        return
    
    # Extract request data from ACP messages
    email_context = None
    strategy_context = None
    
    for message in input:
        for part in message.parts:
            if part.type == "application/json":
                try:
                    data = json.loads(part.content)
                    
                    # Check for complete request data
                    if "email_context" in data and "strategy_context" in data:
                        email_context = EmailContext(**data["email_context"])
                        strategy_context = StrategyContext(**data["strategy_context"])
                        break
                    
                    # Check for email classification + strategy recommendation
                    elif "classification" in data and "strategy_decision" in data:
                        # Build email context from embedded data
                        email_context = EmailContext(
                            subject=data.get("subject", "Email"),
                            content=data.get("content", ""),
                            sender_name=data.get("sender_name"),
                            sender_email=data.get("sender_email"),
                            classification=data["classification"]
                        )
                        strategy_context = StrategyContext(
                            strategy_decision=data["strategy_decision"],
                            response_template=data.get("response_template"),
                            escalation_reason=data.get("escalation_reason")
                        )
                        break
                    
                    # Check for strategy recommendation from previous agent
                    elif "strategy_decision" in data:
                        strategy_context = StrategyContext(
                            strategy_decision=data["strategy_decision"],
                            response_template=data.get("response_template"),
                            escalation_reason=data.get("escalation_reason")
                        )
                        # Email context might be in another message
                    
                except json.JSONDecodeError:
                    continue
            elif part.type == "text/plain":
                # Try to parse as JSON if it's text
                try:
                    data = json.loads(part.content)
                    if "email_context" in data and "strategy_context" in data:
                        email_context = EmailContext(**data["email_context"])
                        strategy_context = StrategyContext(**data["strategy_context"])
                        break
                except json.JSONDecodeError:
                    continue
    
    # Validate we have required data
    if not email_context or not strategy_context:
        yield MessagePart(
            content=json.dumps({
                "error": "Incomplete request data - missing email context or strategy context",
                "variants": [],
                "recommended_variant": 0,
                "overall_confidence": 0.0,
                "requires_human_review": True,
                "review_reasons": [
                    f"Missing email context: {email_context is None}",
                    f"Missing strategy context: {strategy_context is None}"
                ],
                "framework": "OpenAI GPT-4o-mini (Error)",
                "agent": "response_generation_agent"
            }, indent=2),
            type="application/json"
        )
        return
    
    print(f"📝 Extracted email: {email_context.subject}")
    print(f"📝 Strategy: {strategy_context.strategy_decision.get('response_strategy', 'unknown')}")
    
    try:
        # Create response request
        request = ResponseRequest(
            email_context=email_context,
            strategy_context=strategy_context,
            response_variants=2  # Generate 2 variants by default
        )
        
        # Generate responses using OpenAI
        print("🤖 Calling OpenAI for response generation...")
        result = response_generator.generate_responses(request)
        
        # Convert to dictionary for JSON serialization
        response_data = {
            "variants": [variant.model_dump() for variant in result.variants],
            "recommended_variant": result.recommended_variant,
            "overall_confidence": result.overall_confidence,
            "requires_human_review": result.requires_human_review,
            "review_reasons": result.review_reasons,
            "metadata": result.metadata,
            "framework": result.framework,
            "agent": result.agent,
            "generated_at": result.generated_at.isoformat(),
            "acp_agent": "response_generation_agent",
            "communication_protocol": "ACP",
            "processing_time": "completed"
        }
        
        print(f"📝 Response generation complete: {len(result.variants)} variants generated")
        print(f"📝 Recommended: Variant {result.recommended_variant + 1}")
        print(f"📝 Requires review: {result.requires_human_review}")
        
        # Return via ACP MessagePart
        yield MessagePart(
            content=json.dumps(response_data, indent=2),
            type="application/json"
        )
        
    except Exception as e:
        print(f"❌ Response generation error: {e}")
        
        yield MessagePart(
            content=json.dumps({
                "error": f"Response generation failed: {str(e)}",
                "variants": [],
                "recommended_variant": 0,
                "overall_confidence": 0.0,
                "requires_human_review": True,
                "review_reasons": [f"OpenAI generation failed: {str(e)}"],
                "framework": "OpenAI GPT-4o-mini (Error)",
                "agent": "response_generation_agent",
                "acp_agent": "response_generation_agent",
                "communication_protocol": "ACP"
            }, indent=2),
            type="application/json"
        )


def test_acp_server():
    """Test function to verify ACP server is working"""
    print("🧪 Testing ACP Response Generation Agent")
    print("=" * 50)
    
    if not ACP_AVAILABLE:
        print("❌ Cannot test: ACP SDK not available")
        return
        
    if not RESPONSE_GEN_AVAILABLE:
        print("❌ Cannot test: OpenAI response generator not available")  
        return
    
    # Create test message with email and strategy context
    test_request = {
        "email_context": {
            "subject": "Pricing Question",
            "content": "Hi, I'm interested in your enterprise pricing for 100 users. Can you send me a quote?",
            "sender_name": "John Smith",
            "sender_email": "john@company.com",
            "classification": {
                "type": "sales",
                "priority": "high",
                "confidence": 0.9,
                "reasoning": "Sales inquiry from potential enterprise client",
                "suggested_response_tone": "professional"
            }
        },
        "strategy_context": {
            "strategy_decision": {
                "response_strategy": "immediate",
                "response_approach": "professional",
                "confidence_score": 0.9,
                "reasoning": "High priority sales inquiry requires immediate attention",
                "next_steps": ["draft_response", "schedule_demo"],
                "estimated_response_time": "immediate"
            },
            "response_template": "Thank you for your inquiry. We will connect you with a sales representative within the next hour."
        }
    }
    
    test_message = Message(
        role="user",
        parts=[
            MessagePart(
                content=json.dumps(test_request),
                type="application/json"
            )
        ]
    )
    
    print("📝 Testing with sample email and strategy context...")
    print(f"   Email: {test_request['email_context']['subject']}")
    print(f"   Strategy: {test_request['strategy_context']['strategy_decision']['response_strategy']}")
    
    # Test the agent function directly
    context = None  # Mock context - not needed for this test
    results = list(response_generation_agent([test_message], context))
    
    for result in results:
        if result.type == "application/json":
            response_result = json.loads(result.content)
            print(f"🤖 Test Result:")
            
            if "error" in response_result:
                print(f"   Error: {response_result['error']}")
            else:
                print(f"   Variants Generated: {len(response_result.get('variants', []))}")
                print(f"   Recommended: Variant {response_result.get('recommended_variant', 0) + 1}")
                print(f"   Confidence: {response_result.get('overall_confidence', 0):.2f}")
                print(f"   Requires Review: {response_result.get('requires_human_review', True)}")
                print(f"   ACP Agent: {response_result.get('acp_agent', 'unknown')}")
                print(f"   Protocol: {response_result.get('communication_protocol', 'unknown')}")
                
                # Show sample response
                variants = response_result.get('variants', [])
                if variants:
                    recommended_idx = response_result.get('recommended_variant', 0)
                    if recommended_idx < len(variants):
                        recommended = variants[recommended_idx]
                        print(f"   Sample Subject: {recommended.get('subject', 'N/A')}")
                        print(f"   Sample Content: {recommended.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ Unexpected result type: {result.type}")


if __name__ == "__main__":
    print("🚀 ACP Response Generation Agent Server")
    print(f"🔧 ACP SDK Available: {'✅ Yes' if ACP_AVAILABLE else '❌ No'}")
    print(f"🤖 OpenAI Available: {'✅ Yes' if RESPONSE_GEN_AVAILABLE else '❌ No'}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        test_acp_server()
    else:
        # Server mode
        if ACP_AVAILABLE and server:
            print("📝 Starting ACP server on port 8004...")
            print("📝 Agent manifest: http://localhost:8004/agents")
            print("📝 Use ACP client to send email context and strategy for response generation")
            server.run(host="0.0.0.0", port=8004)
        else:
            print("❌ Cannot start server: ACP SDK not available")
            print("Running test instead...")
            test_acp_server()