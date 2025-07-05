"""
Data models for orchestrator workflow
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class WorkflowStep(str, Enum):
    """Workflow step enumeration."""
    INITIALIZED = "initialized"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"
    PLANNING_STRATEGY = "planning_strategy"
    STRATEGY_PLANNED = "strategy_planned"
    GENERATING_RESPONSE = "generating_response"
    RESPONSE_GENERATED = "response_generated"
    HUMAN_REVIEW = "human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailInput(BaseModel):
    """Input email for processing."""
    subject: str = Field(description="Email subject line")
    content: str = Field(description="Email body content")
    sender_name: Optional[str] = Field(default=None, description="Sender's name")
    sender_email: Optional[str] = Field(default=None, description="Sender's email address")
    attachments: List[str] = Field(default_factory=list, description="File paths to attachments")
    received_at: datetime = Field(default_factory=datetime.now, description="When email was received")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional email metadata")


class ClassificationResult(BaseModel):
    """Email classification results."""
    type: str = Field(description="Email type (sales, support, etc.)")
    priority: str = Field(description="Priority level (high, medium, low)")
    confidence: float = Field(description="Classification confidence score")
    reasoning: str = Field(description="Reasoning for classification")
    suggested_response_tone: str = Field(description="Suggested response tone")
    framework: str = Field(description="Framework used for classification")
    agent: str = Field(description="Agent that performed classification")


class StrategyResult(BaseModel):
    """Strategy planning results."""
    strategy_decision: Dict[str, Any] = Field(description="Strategy decision details")
    response_template: Optional[str] = Field(default=None, description="Response template if provided")
    escalation_reason: Optional[str] = Field(default=None, description="Escalation reason if applicable")
    priority_override: Optional[bool] = Field(default=None, description="Priority override flag")
    framework: str = Field(description="Framework used for strategy")
    agent: str = Field(description="Agent that performed strategy planning")


class ResponseResult(BaseModel):
    """Response generation results."""
    variants: List[Dict[str, Any]] = Field(description="Generated response variants")
    recommended_variant: int = Field(description="Index of recommended variant")
    overall_confidence: float = Field(description="Overall confidence in responses")
    requires_human_review: bool = Field(description="Whether human review is required")
    review_reasons: List[str] = Field(description="Reasons for human review")
    framework: str = Field(description="Framework used for response generation")
    agent: str = Field(description="Agent that performed response generation")


class HumanReviewDecision(BaseModel):
    """Human review decision."""
    approved: bool = Field(description="Whether the response was approved")
    selected_variant: Optional[int] = Field(description="Selected response variant index")
    modifications: Optional[str] = Field(description="Modifications requested")
    feedback: Optional[str] = Field(description="Feedback from reviewer")
    reviewer: str = Field(default="human", description="Who performed the review")
    reviewed_at: datetime = Field(default_factory=datetime.now, description="When review was completed")


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""
    enable_human_review: bool = Field(default=True, description="Enable human review step")
    auto_approve_high_confidence: bool = Field(default=False, description="Auto-approve high confidence responses")
    confidence_threshold: float = Field(default=0.8, description="Confidence threshold for auto-approval")
    require_review_for_escalation: bool = Field(default=True, description="Always require review for escalations")
    agent_endpoints: Dict[str, str] = Field(
        default_factory=lambda: {
            "classifier": "http://localhost:8003",
            "strategy": "http://localhost:8002", 
            "response": "http://localhost:8004"
        },
        description="Agent endpoint URLs"
    )
    timeout_seconds: int = Field(default=30, description="Timeout for agent requests")
    max_retries: int = Field(default=3, description="Maximum retries for failed requests")


class WorkflowState(BaseModel):
    """Complete workflow state tracking."""
    workflow_id: str = Field(description="Unique workflow identifier")
    current_step: WorkflowStep = Field(description="Current workflow step")
    email_input: EmailInput = Field(description="Original email input")
    classification_result: Optional[ClassificationResult] = Field(default=None, description="Classification results")
    strategy_result: Optional[StrategyResult] = Field(default=None, description="Strategy planning results")
    response_result: Optional[ResponseResult] = Field(default=None, description="Response generation results")
    human_review: Optional[HumanReviewDecision] = Field(default=None, description="Human review decision")
    config: WorkflowConfig = Field(description="Workflow configuration")
    
    # Tracking fields
    started_at: datetime = Field(default_factory=datetime.now, description="Workflow start time")
    completed_at: Optional[datetime] = Field(default=None, description="Workflow completion time")
    error_message: Optional[str] = Field(default=None, description="Error message if workflow failed")
    step_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of workflow steps and timings"
    )
    
    def add_step_history(self, step: WorkflowStep, details: Dict[str, Any] = None):
        """Add step to history."""
        entry = {
            "step": step.value,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.step_history.append(entry)
    
    def get_final_response(self) -> Optional[Dict[str, Any]]:
        """Get the final approved response."""
        if not self.response_result or not self.response_result.variants:
            return None
        
        # Determine which variant to use
        variant_index = 0  # Default to first variant
        
        if self.human_review and self.human_review.selected_variant is not None:
            variant_index = self.human_review.selected_variant
        elif self.response_result.recommended_variant is not None:
            variant_index = self.response_result.recommended_variant
        
        # Ensure index is valid
        if 0 <= variant_index < len(self.response_result.variants):
            variant = self.response_result.variants[variant_index]
            
            # Apply any human modifications
            if self.human_review and self.human_review.modifications:
                variant = variant.copy()
                variant["content"] = self.human_review.modifications
                variant["modified_by_human"] = True
            
            return variant
        
        return None


class WorkflowSummary(BaseModel):
    """Summary of completed workflow."""
    workflow_id: str
    email_subject: str
    final_step: WorkflowStep
    processing_time_seconds: float
    classification_type: Optional[str] = None
    strategy_applied: Optional[str] = None
    human_reviewed: bool = False
    success: bool = False
    error_message: Optional[str] = None