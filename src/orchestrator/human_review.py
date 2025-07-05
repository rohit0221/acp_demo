"""
Human-in-the-loop review interface for email responses
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
    EmailInput, ClassificationResult, StrategyResult, ResponseResult, 
    HumanReviewDecision
)


class HumanReviewInterface:
    """Interface for human review of email responses."""
    
    def __init__(self):
        """Initialize the human review interface."""
        pass
    
    async def request_review(
        self,
        email: EmailInput,
        classification: ClassificationResult,
        strategy: StrategyResult,
        response: ResponseResult
    ) -> HumanReviewDecision:
        """
        Request human review of the generated response.
        
        Args:
            email: Original email input
            classification: Email classification results
            strategy: Strategy planning results
            response: Response generation results
            
        Returns:
            HumanReviewDecision with approval/rejection and feedback
        """
        print("👤 HUMAN REVIEW REQUIRED")
        print("=" * 50)
        
        # Display original email
        self._display_original_email(email)
        
        # Display analysis results
        self._display_analysis_results(classification, strategy)
        
        # Display generated responses
        selected_variant = self._display_response_options(response)
        
        # Get human decision
        decision = self._get_human_decision(response, selected_variant)
        
        return decision
    
    def _display_original_email(self, email: EmailInput):
        """Display the original email for review."""
        print("📧 ORIGINAL EMAIL")
        print("-" * 20)
        print(f"From: {email.sender_name or email.sender_email or 'Unknown'}")
        print(f"Subject: {email.subject}")
        print(f"Received: {email.received_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Content:")
        print(email.content)
        print()
    
    def _display_analysis_results(self, classification: ClassificationResult, strategy: StrategyResult):
        """Display classification and strategy analysis."""
        print("🔍 ANALYSIS RESULTS")
        print("-" * 20)
        
        # Classification
        print(f"Classification: {classification.type} ({classification.priority} priority)")
        print(f"Confidence: {classification.confidence:.2f}")
        print(f"Reasoning: {classification.reasoning}")
        print(f"Suggested Tone: {classification.suggested_response_tone}")
        print()
        
        # Strategy
        strategy_decision = strategy.strategy_decision
        print(f"Strategy: {strategy_decision.get('response_strategy', 'unknown')}")
        print(f"Approach: {strategy_decision.get('response_approach', 'unknown')}")
        print(f"Confidence: {strategy_decision.get('confidence_score', 0):.2f}")
        print(f"Timing: {strategy_decision.get('estimated_response_time', 'unknown')}")
        print(f"Reasoning: {strategy_decision.get('reasoning', 'No reasoning provided')}")
        
        if strategy.escalation_reason:
            print(f"⚠️ Escalation: {strategy.escalation_reason}")
        
        print()
    
    def _display_response_options(self, response: ResponseResult) -> int:
        """Display response options and get user selection."""
        print("📝 GENERATED RESPONSE OPTIONS")
        print("-" * 30)
        
        if not response.variants:
            print("❌ No response variants generated")
            return 0
        
        # Display all variants
        for i, variant in enumerate(response.variants):
            print(f"Option {i + 1}:")
            print(f"  Subject: {variant.get('subject', 'N/A')}")
            print(f"  Tone: {variant.get('tone', 'unknown')}")
            print(f"  Length: {variant.get('estimated_length', 'unknown')}")
            print(f"  Confidence: {variant.get('confidence_score', 0):.2f}")
            print(f"  Content:")
            content = variant.get('content', '')
            # Truncate long content for display
            if len(content) > 200:
                print(f"    {content[:200]}...")
            else:
                print(f"    {content}")
            print()
        
        # Show recommended option
        recommended = response.recommended_variant
        print(f"🎯 Recommended: Option {recommended + 1}")
        
        # Show review requirements
        if response.requires_human_review:
            print("⚠️ Human review required:")
            for reason in response.review_reasons:
                print(f"  - {reason}")
        
        print()
        return recommended
    
    def _get_human_decision(self, response: ResponseResult, recommended_variant: int) -> HumanReviewDecision:
        """Get human decision on the responses."""
        print("🤔 REVIEW DECISION")
        print("-" * 20)
        
        # Real interactive human input
        print("Please review the generated response options above.")
        print(f"Recommended option: {recommended_variant + 1}")
        print()
        
        # Get approval decision
        while True:
            decision = input("Do you approve this response? (y/n/q for quit): ").lower().strip()
            if decision in ['y', 'yes']:
                approved = True
                break
            elif decision in ['n', 'no']:
                approved = False
                break
            elif decision in ['q', 'quit']:
                print("Exiting review process...")
                return HumanReviewDecision(
                    approved=False,
                    feedback="Review process cancelled by user",
                    reviewer="human-reviewer"
                )
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'q' to quit")
        
        # If approved, check if they want to select a different variant
        selected_variant = recommended_variant
        if approved and len(response.variants) > 1:
            while True:
                variant_choice = input(f"Which variant do you want to use? (1-{len(response.variants)}, or press Enter for recommended): ").strip()
                if not variant_choice:  # User pressed Enter
                    break
                try:
                    variant_num = int(variant_choice)
                    if 1 <= variant_num <= len(response.variants):
                        selected_variant = variant_num - 1
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(response.variants)}")
                except ValueError:
                    print("Please enter a valid number or press Enter for recommended")
        
        # Get feedback
        feedback = input("Any feedback or comments (optional): ").strip()
        if not feedback:
            feedback = "Approved by human reviewer" if approved else "Rejected by human reviewer"
        
        # Get modifications if approved
        modifications = None
        if approved:
            modify = input("Do you want to modify the response content? (y/n): ").lower().strip()
            if modify in ['y', 'yes']:
                print("Enter your modified response (press Enter twice when done):")
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                modifications = "\n".join(lines[:-1])  # Remove the last empty line
        
        print("✅ Response approved by human reviewer" if approved else "❌ Response rejected by human reviewer")
        
        return HumanReviewDecision(
            approved=approved,
            selected_variant=selected_variant,
            modifications=modifications,
            feedback=feedback,
            reviewer="human-reviewer"
        )
    
    def _suggest_modifications(self, response: ResponseResult, variant_index: int) -> str:
        """Suggest modifications to improve the response."""
        if not response.variants or variant_index >= len(response.variants):
            return "No modifications suggested"
        
        variant = response.variants[variant_index]
        original_content = variant.get('content', '')
        
        # Simple modification: add more professional closing
        if "Best regards" not in original_content and "Sincerely" not in original_content:
            modified_content = original_content.rstrip()
            modified_content += "\n\nBest regards,\nCustomer Service Team\nACP Demo Corp"
            return modified_content
        
        return original_content
    
    def display_final_response(self, workflow_state, show_metadata: bool = True):
        """Display the final approved response."""
        final_response = workflow_state.get_final_response()
        
        if not final_response:
            print("❌ No final response available")
            return
        
        print("🎯 FINAL APPROVED RESPONSE")
        print("=" * 50)
        print(f"Subject: {final_response.get('subject', 'N/A')}")
        print()
        print("Content:")
        print(final_response.get('content', 'No content available'))
        print()
        
        if show_metadata:
            print("📊 METADATA")
            print("-" * 20)
            print(f"Tone: {final_response.get('tone', 'unknown')}")
            print(f"Length: {final_response.get('estimated_length', 'unknown')}")
            print(f"Confidence: {final_response.get('confidence_score', 0):.2f}")
            
            if final_response.get('modified_by_human'):
                print("✏️ Modified by human reviewer")
            
            key_points = final_response.get('key_points_addressed', [])
            if key_points:
                print(f"Key Points: {', '.join(key_points)}")
            
            print()


class MockInteractiveReview(HumanReviewInterface):
    """Mock interactive review for testing purposes."""
    
    def __init__(self, auto_approve: bool = False, always_modify: bool = False):
        """
        Initialize mock review interface.
        
        Args:
            auto_approve: Whether to auto-approve all responses
            always_modify: Whether to always suggest modifications
        """
        super().__init__()
        self.auto_approve = auto_approve
        self.always_modify = always_modify
    
    def _get_human_decision(self, response: ResponseResult, recommended_variant: int) -> HumanReviewDecision:
        """Mock human decision for testing."""
        if self.auto_approve:
            modifications = None
            if self.always_modify:
                modifications = self._suggest_modifications(response, recommended_variant)
            
            return HumanReviewDecision(
                approved=True,
                selected_variant=recommended_variant,
                modifications=modifications,
                feedback="Mock auto-approval for testing",
                reviewer="mock-reviewer"
            )
        
        # Use parent class logic for realistic decisions
        return super()._get_human_decision(response, recommended_variant)