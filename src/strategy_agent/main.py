"""
Main entry point for testing the strategy agent directly
"""

import json
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_agent.workflow import StrategyPlanner
from strategy_agent.models import EmailClassification


def test_strategy_agent():
    """Test the strategy agent with sample email classifications."""
    print("🧪 Testing LangGraph Strategy Agent")
    print("=" * 50)
    
    # Initialize strategy planner
    try:
        planner = StrategyPlanner()
        print("✅ Strategy planner initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize strategy planner: {e}")
        return
    
    # Test cases with different email classifications
    test_cases = [
        {
            "name": "High Priority Sales Inquiry",
            "classification": EmailClassification(
                type="sales",
                priority="high",
                confidence=0.9,
                reasoning="Enterprise client requesting pricing for 500+ users",
                suggested_response_tone="professional"
            )
        },
        {
            "name": "Medium Priority Support Request",
            "classification": EmailClassification(
                type="support",
                priority="medium",
                confidence=0.8,
                reasoning="User experiencing login issues, not critical",
                suggested_response_tone="friendly"
            )
        },
        {
            "name": "Urgent Issue - Low Confidence",
            "classification": EmailClassification(
                type="urgent",
                priority="high",
                confidence=0.6,
                reasoning="Unclear urgent message, may need human review",
                suggested_response_tone="urgent"
            )
        },
        {
            "name": "Personal Message",
            "classification": EmailClassification(
                type="personal",
                priority="low",
                confidence=0.85,
                reasoning="Personal note from colleague",
                suggested_response_tone="friendly"
            )
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Plan strategy
            recommendation = planner.plan_strategy(test_case['classification'])
            
            # Display results
            print(f"📋 Strategy Decision:")
            print(f"   Strategy: {recommendation.strategy_decision.response_strategy}")
            print(f"   Approach: {recommendation.strategy_decision.response_approach}")
            print(f"   Confidence: {recommendation.strategy_decision.confidence_score:.2f}")
            print(f"   Timing: {recommendation.strategy_decision.estimated_response_time}")
            print(f"   Reasoning: {recommendation.strategy_decision.reasoning}")
            print(f"   Next Steps: {', '.join(recommendation.strategy_decision.next_steps)}")
            
            if recommendation.response_template:
                print(f"📝 Response Template: {recommendation.response_template}")
            
            if recommendation.escalation_reason:
                print(f"🚨 Escalation Reason: {recommendation.escalation_reason}")
            
            print(f"🤖 Framework: {recommendation.framework}")
            
        except Exception as e:
            print(f"❌ Strategy planning failed: {e}")
    
    print("\n✅ Strategy agent testing completed!")


def plan_strategy_from_json(classification_json: str) -> Dict[str, Any]:
    """
    Plan strategy from JSON classification results.
    
    Args:
        classification_json: JSON string with email classification
        
    Returns:
        Strategy recommendation as dictionary
    """
    try:
        # Parse classification
        classification_data = json.loads(classification_json)
        classification = EmailClassification(**classification_data)
        
        # Initialize planner
        planner = StrategyPlanner()
        
        # Plan strategy
        recommendation = planner.plan_strategy(classification)
        
        # Convert to dictionary
        return {
            "strategy_decision": recommendation.strategy_decision.model_dump(),
            "response_template": recommendation.response_template,
            "escalation_reason": recommendation.escalation_reason,
            "priority_override": recommendation.priority_override,
            "framework": recommendation.framework,
            "agent": recommendation.agent
        }
        
    except Exception as e:
        return {
            "error": f"Strategy planning failed: {str(e)}",
            "strategy_decision": {
                "response_strategy": "delayed",
                "response_approach": "standard",
                "confidence_score": 0.5,
                "reasoning": f"Error in strategy planning: {str(e)}",
                "next_steps": ["manual_review"],
                "estimated_response_time": "within_day"
            },
            "framework": "LangGraph + GPT-4o-mini (Error)",
            "agent": "strategy_planner"
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If JSON provided as argument, process it
        classification_json = sys.argv[1]
        result = plan_strategy_from_json(classification_json)
        print(json.dumps(result, indent=2))
    else:
        # Run tests
        test_strategy_agent()