"""
Main entry point for testing the response generator directly
"""

import json
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from response_generator.generator import ResponseGenerator
from response_generator.models import (
    ResponseRequest, EmailContext, StrategyContext, BusinessContext
)


def test_response_generator():
    """Test the response generator with sample data."""
    print("🧪 Testing OpenAI Response Generator")
    print("=" * 50)
    
    # Initialize response generator
    try:
        business_ctx = BusinessContext(
            company_name="ACP Demo Corp",
            support_email="support@acpdemo.com",
            business_hours="9 AM - 6 PM, Monday - Friday",
            brand_voice="professional"
        )
        generator = ResponseGenerator(business_context=business_ctx)
        print("✅ Response generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize response generator: {e}")
        return
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "High Priority Sales Inquiry",
            "email_context": EmailContext(
                subject="Enterprise Pricing Inquiry",
                content="Hi, I'm the CTO at TechCorp and we're interested in your platform for our team of 500+ developers. Could you send me pricing information and schedule a demo?",
                sender_name="John Smith",
                sender_email="john.smith@techcorp.com",
                classification={
                    "type": "sales",
                    "priority": "high",
                    "confidence": 0.9,
                    "reasoning": "Enterprise client requesting pricing for 500+ users",
                    "suggested_response_tone": "professional"
                }
            ),
            "strategy_context": StrategyContext(
                strategy_decision={
                    "response_strategy": "immediate",
                    "response_approach": "professional",
                    "confidence_score": 0.9,
                    "reasoning": "High priority sales inquiry requires immediate attention",
                    "next_steps": ["draft_response", "schedule_demo"],
                    "estimated_response_time": "immediate"
                },
                response_template="Thank you for your inquiry. We will connect you with a sales representative within the next hour."
            )
        },
        {
            "name": "Support Issue - Login Problems",
            "email_context": EmailContext(
                subject="Cannot access my account",
                content="I've been trying to log into my account for the past hour but keep getting an error message. I need to access my project before the deadline tomorrow. Please help!",
                sender_name="Sarah Wilson",
                sender_email="sarah.wilson@example.com",
                classification={
                    "type": "support",
                    "priority": "medium",
                    "confidence": 0.8,
                    "reasoning": "User experiencing login issues, not critical but time-sensitive",
                    "suggested_response_tone": "friendly"
                }
            ),
            "strategy_context": StrategyContext(
                strategy_decision={
                    "response_strategy": "immediate",
                    "response_approach": "friendly",
                    "confidence_score": 0.8,
                    "reasoning": "Time-sensitive support issue needs quick resolution",
                    "next_steps": ["provide_troubleshooting", "escalate_if_needed"],
                    "estimated_response_time": "within_hour"
                }
            )
        },
        {
            "name": "Escalation Required - Complaint",
            "email_context": EmailContext(
                subject="Extremely disappointed with service",
                content="This is completely unacceptable. Your software crashed during our client presentation and caused us significant embarrassment. I want to speak to a manager immediately about compensation for this incident.",
                sender_name="Michael Johnson",
                sender_email="mjohnson@business.com",
                classification={
                    "type": "support",
                    "priority": "high",
                    "confidence": 0.7,
                    "reasoning": "Customer complaint with strong negative sentiment",
                    "suggested_response_tone": "professional"
                }
            ),
            "strategy_context": StrategyContext(
                strategy_decision={
                    "response_strategy": "escalate",
                    "response_approach": "professional",
                    "confidence_score": 0.8,
                    "reasoning": "Serious complaint requires human escalation",
                    "next_steps": ["escalate_to_manager", "immediate_response"],
                    "estimated_response_time": "immediate"
                },
                escalation_reason="Serious customer complaint requires management attention"
            )
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Create request
            request = ResponseRequest(
                email_context=test_case['email_context'],
                strategy_context=test_case['strategy_context'],
                response_variants=2
            )
            
            # Generate responses
            print("🤖 Generating email responses...")
            result = generator.generate_responses(request)
            
            # Display results
            print(f"📊 Generation Summary:")
            print(f"   Variants Generated: {len(result.variants)}")
            print(f"   Recommended: Variant {result.recommended_variant + 1}")
            print(f"   Overall Confidence: {result.overall_confidence:.2f}")
            print(f"   Requires Review: {'Yes' if result.requires_human_review else 'No'}")
            
            if result.review_reasons:
                print(f"   Review Reasons: {', '.join(result.review_reasons)}")
            
            # Show recommended response
            if result.variants:
                recommended = result.variants[result.recommended_variant]
                print(f"\n📝 Recommended Response (Variant {result.recommended_variant + 1}):")
                print(f"   Subject: {recommended.subject}")
                print(f"   Tone: {recommended.tone}")
                print(f"   Length: {recommended.estimated_length}")
                print(f"   Confidence: {recommended.confidence_score:.2f}")
                print(f"   Content Preview: {recommended.content[:150]}...")
                print(f"   Key Points: {', '.join(recommended.key_points_addressed)}")
            
            print(f"🤖 Framework: {result.framework}")
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
    
    print("\n✅ Response generator testing completed!")


def generate_response_from_json(request_json: str) -> Dict[str, Any]:
    """
    Generate response from JSON request.
    
    Args:
        request_json: JSON string with complete request data
        
    Returns:
        Response generation results as dictionary
    """
    try:
        # Parse request
        request_data = json.loads(request_json)
        request = ResponseRequest(**request_data)
        
        # Initialize generator
        generator = ResponseGenerator()
        
        # Generate responses
        result = generator.generate_responses(request)
        
        # Convert to dictionary
        return {
            "variants": [variant.model_dump() for variant in result.variants],
            "recommended_variant": result.recommended_variant,
            "overall_confidence": result.overall_confidence,
            "requires_human_review": result.requires_human_review,
            "review_reasons": result.review_reasons,
            "metadata": result.metadata,
            "framework": result.framework,
            "agent": result.agent,
            "generated_at": result.generated_at.isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Response generation failed: {str(e)}",
            "variants": [],
            "recommended_variant": 0,
            "overall_confidence": 0.0,
            "requires_human_review": True,
            "review_reasons": [f"Generation error: {str(e)}"],
            "framework": "OpenAI GPT-4o-mini (Error)",
            "agent": "response_generator"
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If JSON provided as argument, process it
        request_json = sys.argv[1]
        result = generate_response_from_json(request_json)
        print(json.dumps(result, indent=2))
    else:
        # Run tests
        test_response_generator()