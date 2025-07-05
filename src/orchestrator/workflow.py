"""
Workflow orchestration engine for end-to-end email processing
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from .models import (
    WorkflowState, WorkflowStep, EmailInput, WorkflowConfig,
    ClassificationResult, StrategyResult, ResponseResult, HumanReviewDecision,
    WorkflowSummary
)
from .acp_client import ACPClient
from .human_review import HumanReviewInterface


class WorkflowOrchestrator:
    """Orchestrates the complete email processing workflow."""
    
    def __init__(self, config: WorkflowConfig = None):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config: Workflow configuration. Uses defaults if not provided.
        """
        self.config = config or WorkflowConfig()
        self.human_review = HumanReviewInterface()
    
    async def process_email(self, email: EmailInput) -> WorkflowState:
        """
        Process an email through the complete workflow.
        
        Args:
            email: Email input to process
            
        Returns:
            Complete workflow state with results
        """
        # Initialize workflow state
        workflow_id = str(uuid.uuid4())
        state = WorkflowState(
            workflow_id=workflow_id,
            current_step=WorkflowStep.INITIALIZED,
            email_input=email,
            config=self.config
        )
        
        print(f"🚀 Starting email processing workflow: {workflow_id}")
        print(f"📧 Email: {email.subject}")
        print("=" * 60)
        
        try:
            # Step 1: Email Classification
            state = await self._classify_email(state)
            if state.current_step == WorkflowStep.FAILED:
                return state
            
            # Step 2: Strategy Planning
            state = await self._plan_strategy(state)
            if state.current_step == WorkflowStep.FAILED:
                return state
            
            # Step 3: Response Generation
            state = await self._generate_response(state)
            if state.current_step == WorkflowStep.FAILED:
                return state
            
            # Step 4: Human Review (if needed)
            state = await self._human_review_step(state)
            if state.current_step == WorkflowStep.FAILED:
                return state
            
            # Step 5: Complete workflow
            state = await self._complete_workflow(state)
            
        except Exception as e:
            print(f"❌ Workflow failed with error: {e}")
            state.current_step = WorkflowStep.FAILED
            state.error_message = str(e)
            state.add_step_history(WorkflowStep.FAILED, {"error": str(e)})
        
        # Set completion time
        state.completed_at = datetime.now()
        
        # Print summary
        self._print_workflow_summary(state)
        
        return state
    
    async def _classify_email(self, state: WorkflowState) -> WorkflowState:
        """Step 1: Classify the email."""
        print("🔍 Step 1: Email Classification")
        print("-" * 30)
        
        state.current_step = WorkflowStep.CLASSIFYING
        state.add_step_history(WorkflowStep.CLASSIFYING)
        
        try:
            async with ACPClient(
                self.config.agent_endpoints,
                self.config.timeout_seconds,
                self.config.max_retries
            ) as client:
                
                classification = await client.classify_email(
                    subject=state.email_input.subject,
                    content=state.email_input.content,
                    sender_name=state.email_input.sender_name,
                    sender_email=state.email_input.sender_email
                )
                
                state.classification_result = classification
                state.current_step = WorkflowStep.CLASSIFIED
                state.add_step_history(WorkflowStep.CLASSIFIED, {
                    "type": classification.type,
                    "priority": classification.priority,
                    "confidence": classification.confidence
                })
                
                print(f"✅ Classification complete:")
                print(f"   Type: {classification.type}")
                print(f"   Priority: {classification.priority}")
                print(f"   Confidence: {classification.confidence:.2f}")
                print(f"   Framework: {classification.framework}")
                print()
                
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            state.current_step = WorkflowStep.FAILED
            state.error_message = f"Classification failed: {str(e)}"
            state.add_step_history(WorkflowStep.FAILED, {"step": "classification", "error": str(e)})
        
        return state
    
    async def _plan_strategy(self, state: WorkflowState) -> WorkflowState:
        """Step 2: Plan response strategy."""
        print("🧠 Step 2: Strategy Planning")
        print("-" * 30)
        
        state.current_step = WorkflowStep.PLANNING_STRATEGY
        state.add_step_history(WorkflowStep.PLANNING_STRATEGY)
        
        try:
            async with ACPClient(
                self.config.agent_endpoints,
                self.config.timeout_seconds,
                self.config.max_retries
            ) as client:
                
                strategy = await client.plan_strategy(state.classification_result)
                
                state.strategy_result = strategy
                state.current_step = WorkflowStep.STRATEGY_PLANNED
                state.add_step_history(WorkflowStep.STRATEGY_PLANNED, {
                    "strategy": strategy.strategy_decision.get("response_strategy"),
                    "approach": strategy.strategy_decision.get("response_approach"),
                    "confidence": strategy.strategy_decision.get("confidence_score")
                })
                
                print(f"✅ Strategy planning complete:")
                print(f"   Strategy: {strategy.strategy_decision.get('response_strategy', 'unknown')}")
                print(f"   Approach: {strategy.strategy_decision.get('response_approach', 'unknown')}")
                print(f"   Confidence: {strategy.strategy_decision.get('confidence_score', 0):.2f}")
                print(f"   Framework: {strategy.framework}")
                
                if strategy.escalation_reason:
                    print(f"   ⚠️ Escalation: {strategy.escalation_reason}")
                print()
                
        except Exception as e:
            print(f"❌ Strategy planning failed: {e}")
            state.current_step = WorkflowStep.FAILED
            state.error_message = f"Strategy planning failed: {str(e)}"
            state.add_step_history(WorkflowStep.FAILED, {"step": "strategy", "error": str(e)})
        
        return state
    
    async def _generate_response(self, state: WorkflowState) -> WorkflowState:
        """Step 3: Generate email response."""
        print("📝 Step 3: Response Generation")
        print("-" * 30)
        
        state.current_step = WorkflowStep.GENERATING_RESPONSE
        state.add_step_history(WorkflowStep.GENERATING_RESPONSE)
        
        try:
            async with ACPClient(
                self.config.agent_endpoints,
                self.config.timeout_seconds,
                self.config.max_retries
            ) as client:
                
                response = await client.generate_response(
                    email_subject=state.email_input.subject,
                    email_content=state.email_input.content,
                    sender_name=state.email_input.sender_name or "",
                    sender_email=state.email_input.sender_email or "",
                    classification=state.classification_result,
                    strategy=state.strategy_result
                )
                
                state.response_result = response
                state.current_step = WorkflowStep.RESPONSE_GENERATED
                state.add_step_history(WorkflowStep.RESPONSE_GENERATED, {
                    "variants_generated": len(response.variants),
                    "recommended_variant": response.recommended_variant,
                    "overall_confidence": response.overall_confidence,
                    "requires_review": response.requires_human_review
                })
                
                print(f"✅ Response generation complete:")
                print(f"   Variants: {len(response.variants)}")
                print(f"   Recommended: Variant {response.recommended_variant + 1}")
                print(f"   Confidence: {response.overall_confidence:.2f}")
                print(f"   Requires Review: {'Yes' if response.requires_human_review else 'No'}")
                print(f"   Framework: {response.framework}")
                
                if response.review_reasons:
                    print(f"   Review Reasons: {', '.join(response.review_reasons)}")
                print()
                
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            state.current_step = WorkflowStep.FAILED
            state.error_message = f"Response generation failed: {str(e)}"
            state.add_step_history(WorkflowStep.FAILED, {"step": "response", "error": str(e)})
        
        return state
    
    async def _human_review_step(self, state: WorkflowState) -> WorkflowState:
        """Step 4: Human review (if needed)."""
        # Check if human review is needed
        if not self._requires_human_review(state):
            print("⚡ Skipping human review (not required)")
            state.current_step = WorkflowStep.APPROVED
            state.add_step_history(WorkflowStep.APPROVED, {"auto_approved": True})
            return state
        
        print("👤 Step 4: Human Review")
        print("-" * 30)
        
        state.current_step = WorkflowStep.HUMAN_REVIEW
        state.add_step_history(WorkflowStep.HUMAN_REVIEW)
        
        try:
            # Present information for review
            review_decision = await self.human_review.request_review(
                email=state.email_input,
                classification=state.classification_result,
                strategy=state.strategy_result,
                response=state.response_result
            )
            
            state.human_review = review_decision
            
            if review_decision.approved:
                state.current_step = WorkflowStep.APPROVED
                state.add_step_history(WorkflowStep.APPROVED, {
                    "selected_variant": review_decision.selected_variant,
                    "has_modifications": bool(review_decision.modifications)
                })
                print("✅ Response approved by human reviewer")
            else:
                state.current_step = WorkflowStep.REJECTED
                state.add_step_history(WorkflowStep.REJECTED, {
                    "feedback": review_decision.feedback
                })
                print("❌ Response rejected by human reviewer")
            
            print()
            
        except Exception as e:
            print(f"❌ Human review failed: {e}")
            state.current_step = WorkflowStep.FAILED
            state.error_message = f"Human review failed: {str(e)}"
            state.add_step_history(WorkflowStep.FAILED, {"step": "human_review", "error": str(e)})
        
        return state
    
    async def _complete_workflow(self, state: WorkflowState) -> WorkflowState:
        """Step 5: Complete the workflow."""
        print("🎯 Step 5: Workflow Completion")
        print("-" * 30)
        
        if state.current_step in [WorkflowStep.APPROVED, WorkflowStep.REJECTED]:
            state.current_step = WorkflowStep.COMPLETED
            state.add_step_history(WorkflowStep.COMPLETED)
            
            # Get final response
            final_response = state.get_final_response()
            if final_response:
                print("✅ Workflow completed successfully!")
                print(f"📧 Final response subject: {final_response.get('subject', 'N/A')}")
                print(f"📄 Response length: {final_response.get('estimated_length', 'unknown')}")
                print(f"🎭 Tone: {final_response.get('tone', 'unknown')}")
            else:
                print("⚠️ Workflow completed but no final response available")
        else:
            print("❌ Workflow could not be completed")
        
        print()
        return state
    
    def _requires_human_review(self, state: WorkflowState) -> bool:
        """Determine if human review is required."""
        if not self.config.enable_human_review:
            return False
        
        # Always require review if response generation says so
        if state.response_result and state.response_result.requires_human_review:
            if self.config.require_review_for_escalation:
                return True
        
        # Check auto-approval conditions
        if (self.config.auto_approve_high_confidence and 
            state.response_result and 
            state.response_result.overall_confidence >= self.config.confidence_threshold):
            return False
        
        # Default to requiring review
        return self.config.enable_human_review
    
    def _print_workflow_summary(self, state: WorkflowState):
        """Print a summary of the completed workflow."""
        print("📊 WORKFLOW SUMMARY")
        print("=" * 60)
        print(f"Workflow ID: {state.workflow_id}")
        print(f"Email Subject: {state.email_input.subject}")
        print(f"Final Status: {state.current_step.value}")
        
        if state.started_at and state.completed_at:
            duration = (state.completed_at - state.started_at).total_seconds()
            print(f"Processing Time: {duration:.1f} seconds")
        
        if state.classification_result:
            print(f"Classification: {state.classification_result.type} ({state.classification_result.priority})")
        
        if state.strategy_result:
            strategy = state.strategy_result.strategy_decision.get("response_strategy", "unknown")
            print(f"Strategy: {strategy}")
        
        if state.response_result:
            print(f"Response Variants: {len(state.response_result.variants)}")
            print(f"Overall Confidence: {state.response_result.overall_confidence:.2f}")
        
        if state.human_review:
            print(f"Human Review: {'Approved' if state.human_review.approved else 'Rejected'}")
        
        if state.error_message:
            print(f"Error: {state.error_message}")
        
        print("=" * 60)
    
    def get_workflow_summary(self, state: WorkflowState) -> WorkflowSummary:
        """Get a concise summary of the workflow."""
        processing_time = 0.0
        if state.started_at and state.completed_at:
            processing_time = (state.completed_at - state.started_at).total_seconds()
        
        return WorkflowSummary(
            workflow_id=state.workflow_id,
            email_subject=state.email_input.subject,
            final_step=state.current_step,
            processing_time_seconds=processing_time,
            classification_type=state.classification_result.type if state.classification_result else None,
            strategy_applied=state.strategy_result.strategy_decision.get("response_strategy") if state.strategy_result else None,
            human_reviewed=state.human_review is not None,
            success=state.current_step == WorkflowStep.COMPLETED,
            error_message=state.error_message
        )