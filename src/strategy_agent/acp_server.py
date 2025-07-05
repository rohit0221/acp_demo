#!/usr/bin/env python3
"""
ACP Server wrapper for LangGraph Strategy Agent
This creates a proper ACP agent that can be discovered and communicate with other agents
"""

import sys
import os
import json
from collections.abc import Iterator
from typing import Any

# Add the parent directory to the path to import strategy agent
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
        
        def run(self, host="0.0.0.0", port=8002):
            print(f"❌ Mock server cannot run without ACP SDK")

# Import our LangGraph strategy agent
try:
    from strategy_agent.workflow import StrategyPlanner
    from strategy_agent.models import EmailClassification
    STRATEGY_AVAILABLE = True
    print("✅ LangGraph strategy agent loaded successfully")
except ImportError as e:
    print(f"❌ LangGraph strategy agent not available: {e}")
    STRATEGY_AVAILABLE = False

# Initialize ACP server
server = Server() if ACP_AVAILABLE else None

# Initialize strategy planner
strategy_planner = StrategyPlanner() if STRATEGY_AVAILABLE else None

@server.agent() if ACP_AVAILABLE else lambda f: f
def strategy_planning_agent(input: list, context) -> Iterator:
    """
    ACP Agent that wraps LangGraph Strategy Planning Agent
    
    This agent:
    1. Receives ACP messages with email classification results
    2. Extracts classification data
    3. Uses LangGraph workflow with GPT-4o-mini for strategy planning
    4. Returns structured strategy recommendations via ACP
    """
    print(f"🧠 ACP Strategy Planning Agent started. Processing {len(input)} messages...")
    
    if not STRATEGY_AVAILABLE:
        yield MessagePart(
            content=json.dumps({
                "error": "LangGraph strategy agent not available",
                "strategy_decision": {
                    "response_strategy": "delayed",
                    "response_approach": "standard",
                    "confidence_score": 0.5,
                    "reasoning": "LangGraph strategy planning agent could not be loaded",
                    "next_steps": ["manual_review"],
                    "estimated_response_time": "within_day"
                },
                "framework": "LangGraph + GPT-4o-mini (Error)",
                "agent": "strategy_planning_agent"
            }, indent=2),
            type="application/json"
        )
        return
    
    if not input:
        yield MessagePart(
            content=json.dumps({
                "error": "No classification results provided",
                "strategy_decision": {
                    "response_strategy": "delayed",
                    "response_approach": "standard",
                    "confidence_score": 0.5,
                    "reasoning": "No ACP messages received for strategy planning",
                    "next_steps": ["manual_review"],
                    "estimated_response_time": "within_day"
                },
                "framework": "LangGraph + GPT-4o-mini (Error)",
                "agent": "strategy_planning_agent"
            }, indent=2),
            type="application/json"
        )
        return
    
    # Extract classification results from ACP messages
    classification_data = None
    
    for message in input:
        for part in message.parts:
            if part.type == "application/json":
                try:
                    data = json.loads(part.content)
                    
                    # Check if this looks like email classification data
                    if "type" in data and "priority" in data and "confidence" in data:
                        classification_data = data
                        break
                        
                except json.JSONDecodeError:
                    continue
            elif part.type == "text/plain":
                # Try to parse as JSON if it's text
                try:
                    data = json.loads(part.content)
                    if "type" in data and "priority" in data and "confidence" in data:
                        classification_data = data
                        break
                except json.JSONDecodeError:
                    continue
    
    if not classification_data:
        yield MessagePart(
            content=json.dumps({
                "error": "No valid email classification data found in messages",
                "strategy_decision": {
                    "response_strategy": "delayed",
                    "response_approach": "standard",
                    "confidence_score": 0.5,
                    "reasoning": "ACP messages did not contain valid email classification data",
                    "next_steps": ["manual_review"],
                    "estimated_response_time": "within_day"
                },
                "framework": "LangGraph + GPT-4o-mini (Error)",
                "agent": "strategy_planning_agent"
            }, indent=2),
            type="application/json"
        )
        return
    
    print(f"🧠 Extracted classification data: {classification_data.get('type', 'unknown')} - {classification_data.get('priority', 'unknown')}")
    
    try:
        # Convert to EmailClassification model
        classification = EmailClassification(**classification_data)
        
        # Use LangGraph workflow to plan strategy
        print("🤖 Calling LangGraph workflow for strategy planning...")
        recommendation = strategy_planner.plan_strategy(classification)
        
        # Convert to dictionary for JSON serialization
        result = {
            "strategy_decision": recommendation.strategy_decision.model_dump(),
            "response_template": recommendation.response_template,
            "escalation_reason": recommendation.escalation_reason,
            "priority_override": recommendation.priority_override,
            "framework": recommendation.framework,
            "agent": recommendation.agent,
            "acp_agent": "strategy_planning_agent",
            "communication_protocol": "ACP",
            "processing_time": "completed"
        }
        
        print(f"🧠 Strategy planning complete: {result['strategy_decision']['response_strategy']}")
        
        # Return via ACP MessagePart
        yield MessagePart(
            content=json.dumps(result, indent=2),
            type="application/json"
        )
        
    except Exception as e:
        print(f"❌ Strategy planning error: {e}")
        
        yield MessagePart(
            content=json.dumps({
                "error": f"Strategy planning failed: {str(e)}",
                "strategy_decision": {
                    "response_strategy": "delayed",
                    "response_approach": "standard",
                    "confidence_score": 0.5,
                    "reasoning": f"LangGraph workflow execution failed: {str(e)}",
                    "next_steps": ["manual_review"],
                    "estimated_response_time": "within_day"
                },
                "framework": "LangGraph + GPT-4o-mini (Error)",
                "agent": "strategy_planning_agent",
                "acp_agent": "strategy_planning_agent",
                "communication_protocol": "ACP"
            }, indent=2),
            type="application/json"
        )


def test_acp_server():
    """Test function to verify ACP server is working"""
    print("🧪 Testing ACP Strategy Planning Agent")
    print("=" * 50)
    
    if not ACP_AVAILABLE:
        print("❌ Cannot test: ACP SDK not available")
        return
        
    if not STRATEGY_AVAILABLE:
        print("❌ Cannot test: LangGraph strategy agent not available")  
        return
    
    # Create test message with email classification
    test_classification = {
        "type": "sales",
        "priority": "high",
        "confidence": 0.9,
        "reasoning": "Enterprise client requesting pricing for 500+ users",
        "suggested_response_tone": "professional",
        "framework": "CrewAI + GPT-4o-mini",
        "agent": "email_classifier"
    }
    
    test_message = Message(
        role="user",
        parts=[
            MessagePart(
                content=json.dumps(test_classification),
                type="application/json"
            )
        ]
    )
    
    print("🧠 Testing with sample email classification...")
    print(f"   Classification: {test_classification['type']} - {test_classification['priority']}")
    
    # Test the agent function directly
    context = None  # Mock context - not needed for this test
    results = list(strategy_planning_agent([test_message], context))
    
    for result in results:
        if result.type == "application/json":
            strategy_result = json.loads(result.content)
            print(f"🤖 Test Result:")
            
            if "error" in strategy_result:
                print(f"   Error: {strategy_result['error']}")
            else:
                decision = strategy_result.get('strategy_decision', {})
                print(f"   Strategy: {decision.get('response_strategy', 'unknown')}")
                print(f"   Approach: {decision.get('response_approach', 'unknown')}")
                print(f"   Confidence: {decision.get('confidence_score', 0):.2f}")
                print(f"   Timing: {decision.get('estimated_response_time', 'unknown')}")
                print(f"   ACP Agent: {strategy_result.get('acp_agent', 'unknown')}")
                print(f"   Protocol: {strategy_result.get('communication_protocol', 'unknown')}")
        else:
            print(f"❌ Unexpected result type: {result.type}")


if __name__ == "__main__":
    print("🚀 ACP Strategy Planning Agent Server")
    print(f"🔧 ACP SDK Available: {'✅ Yes' if ACP_AVAILABLE else '❌ No'}")
    print(f"🤖 LangGraph Available: {'✅ Yes' if STRATEGY_AVAILABLE else '❌ No'}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        test_acp_server()
    else:
        # Server mode
        if ACP_AVAILABLE and server:
            print("🧠 Starting ACP server on port 8002...")
            print("🧠 Agent manifest: http://localhost:8002/agents")
            print("🧠 Use ACP client to send email classification for strategy planning")
            server.run(host="0.0.0.0", port=8002)
        else:
            print("❌ Cannot start server: ACP SDK not available")
            print("Running test instead...")
            test_acp_server()