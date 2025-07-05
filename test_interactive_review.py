#!/usr/bin/env python3
"""
Test the interactive human review interface
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator.workflow import WorkflowOrchestrator
from src.orchestrator.models import EmailInput, WorkflowConfig
from src.orchestrator.human_review import HumanReviewInterface


async def test_interactive_review():
    """Test the interactive human review with a single email."""
    print("🧪 Testing Interactive Human Review")
    print("=" * 50)
    
    # Create orchestrator with interactive review
    config = WorkflowConfig(
        enable_human_review=True,
        auto_approve_high_confidence=False,
        confidence_threshold=0.8
    )
    
    orchestrator = WorkflowOrchestrator(config)
    orchestrator.human_review = HumanReviewInterface()
    
    # Create a test email
    test_email = EmailInput(
        subject="Test Email - Interactive Review",
        content="This is a test email to demonstrate the interactive human review process. Please review and provide feedback on the generated response.",
        sender_name="Test User",
        sender_email="test@example.com"
    )
    
    print("📧 Processing test email with interactive human review...")
    print(f"Subject: {test_email.subject}")
    print(f"From: {test_email.sender_name}")
    print()
    
    try:
        # Process the email
        result = await orchestrator.process_email(test_email)
        
        print("✅ Email processing completed!")
        print(f"Final status: {result.current_step}")
        print(f"Workflow ID: {result.workflow_id}")
        
        if result.human_review:
            print(f"Human decision: {'Approved' if result.human_review.approved else 'Rejected'}")
            if result.human_review.feedback:
                print(f"Feedback: {result.human_review.feedback}")
        
    except KeyboardInterrupt:
        print("\n❌ Interactive review cancelled by user")
    except Exception as e:
        print(f"❌ Error during email processing: {e}")


if __name__ == "__main__":
    asyncio.run(test_interactive_review())