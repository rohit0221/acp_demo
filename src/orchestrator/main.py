"""
Main entry point for the email processing orchestrator
"""

import asyncio
import json
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.workflow import WorkflowOrchestrator
from orchestrator.models import EmailInput, WorkflowConfig
from orchestrator.human_review import HumanReviewInterface


async def main():
    """Main function to run the email processing orchestrator."""
    print("🚀 ACP Email Processing Orchestrator")
    print("=" * 60)
    
    # Check if agents are running
    await check_agent_connectivity()
    
    # Run test workflows
    await run_test_workflows()


async def check_agent_connectivity():
    """Check connectivity to all ACP agents."""
    print("🔍 Checking agent connectivity...")
    
    from orchestrator.acp_client import ACPClient
    
    config = WorkflowConfig()
    
    try:
        async with ACPClient(config.agent_endpoints) as client:
            connectivity = await client.test_connectivity()
            
            for agent_name, is_connected in connectivity.items():
                status = "✅ Connected" if is_connected else "❌ Disconnected"
                endpoint = config.agent_endpoints[agent_name]
                print(f"  {agent_name.capitalize()} Agent ({endpoint}): {status}")
            
            all_connected = all(connectivity.values())
            if not all_connected:
                print("\n⚠️ Warning: Not all agents are connected. Some workflows may fail.")
            else:
                print("\n✅ All agents are connected and ready!")
                
    except Exception as e:
        print(f"❌ Error checking connectivity: {e}")
    
    print()


async def run_test_workflows():
    """Run test workflows with sample emails."""
    print("🧪 Running test workflows...")
    print()
    
    # Create orchestrator with mock review for automated testing
    config = WorkflowConfig(
        enable_human_review=True,
        auto_approve_high_confidence=False,
        confidence_threshold=0.8
    )
    
    orchestrator = WorkflowOrchestrator(config)
    # Use real interactive review for human input
    orchestrator.human_review = HumanReviewInterface()
    
    # Test cases
    test_emails = [
        {
            "name": "High Priority Sales Inquiry",
            "email": EmailInput(
                subject="Enterprise Pricing Inquiry - Urgent",
                content="Hi, I'm the CTO at TechCorp and we need to make a decision by Friday. We're interested in your platform for our team of 500+ developers. Could you send me pricing information and schedule a demo this week? This is time-sensitive as we're evaluating multiple vendors.",
                sender_name="John Smith",
                sender_email="john.smith@techcorp.com",
                metadata={"company": "TechCorp", "urgency": "high"}
            )
        },
        {
            "name": "Support Issue - Login Problems",
            "email": EmailInput(
                subject="Cannot access my account",
                content="I've been trying to log into my account for the past hour but keep getting an error message 'Invalid credentials' even though I'm sure my password is correct. I need to access my project files before the deadline tomorrow. Can you help me reset my password or troubleshoot this issue?",
                sender_name="Sarah Wilson",
                sender_email="sarah.wilson@example.com",
                metadata={"account_type": "premium", "last_login": "2024-01-14"}
            )
        },
        {
            "name": "Customer Complaint",
            "email": EmailInput(
                subject="Extremely disappointed with service - requesting refund",
                content="This is completely unacceptable. Your software crashed during our important client presentation yesterday and caused us significant embarrassment. We lost a major deal because of this. I want to speak to a manager immediately about compensation for this incident and I'm considering canceling our subscription.",
                sender_name="Michael Johnson",
                sender_email="mjohnson@business.com",
                metadata={"subscription": "enterprise", "incident_date": "2024-01-15"}
            )
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_emails, 1):
        print(f"📧 Test Case {i}: {test_case['name']}")
        print("=" * 40)
        
        try:
            # Process the email
            workflow_state = await orchestrator.process_email(test_case['email'])
            
            # Display final response
            orchestrator.human_review.display_final_response(workflow_state)
            
            # Store results
            summary = orchestrator.get_workflow_summary(workflow_state)
            results.append(summary)
            
        except Exception as e:
            print(f"❌ Test case failed: {e}")
            print()
        
        print("\n" + "=" * 60 + "\n")
    
    # Print overall summary
    print_test_summary(results)


def print_test_summary(results: List):
    """Print summary of all test results."""
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.success)
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    
    if total_tests > 0:
        print(f"Success Rate: {(successful_tests / total_tests * 100):.1f}%")
    else:
        print("Success Rate: N/A (no tests completed)")
    print()
    
    if results:
        avg_time = sum(r.processing_time_seconds for r in results) / len(results)
        print(f"Average Processing Time: {avg_time:.1f} seconds")
        
        # Classification types
        classification_types = [r.classification_type for r in results if r.classification_type]
        if classification_types:
            print(f"Classification Types: {', '.join(set(classification_types))}")
        
        # Strategies applied
        strategies = [r.strategy_applied for r in results if r.strategy_applied]
        if strategies:
            print(f"Strategies Applied: {', '.join(set(strategies))}")
        
        # Human review stats
        human_reviewed = sum(1 for r in results if r.human_reviewed)
        print(f"Human Reviewed: {human_reviewed}/{total_tests}")
    
    print("=" * 60)


async def process_single_email():
    """Process a single email from command line input."""
    if len(sys.argv) < 3:
        print("Usage: python -m orchestrator.main single <subject> <content> [sender_name] [sender_email]")
        return
    
    subject = sys.argv[2]
    content = sys.argv[3]
    sender_name = sys.argv[4] if len(sys.argv) > 4 else None
    sender_email = sys.argv[5] if len(sys.argv) > 5 else None
    
    email = EmailInput(
        subject=subject,
        content=content,
        sender_name=sender_name,
        sender_email=sender_email
    )
    
    # Create orchestrator
    config = WorkflowConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    # Process email
    print("🚀 Processing single email...")
    workflow_state = await orchestrator.process_email(email)
    
    # Display results
    orchestrator.human_review.display_final_response(workflow_state)
    
    # Print summary
    summary = orchestrator.get_workflow_summary(workflow_state)
    print(f"\nWorkflow completed in {summary.processing_time_seconds:.1f} seconds")
    print(f"Success: {summary.success}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        # Process single email
        asyncio.run(process_single_email())
    else:
        # Run full test suite
        asyncio.run(main())