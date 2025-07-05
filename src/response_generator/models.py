"""
Data models for response generator
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class EmailContext(BaseModel):
    """Original email context and classification."""
    subject: str = Field(description="Original email subject")
    content: str = Field(description="Original email content")
    sender_name: Optional[str] = Field(default=None, description="Sender's name if available")
    sender_email: Optional[str] = Field(default=None, description="Sender's email address")
    classification: Dict[str, Any] = Field(description="Email classification results from CrewAI")


class StrategyContext(BaseModel):
    """Strategy recommendations from LangGraph agent."""
    strategy_decision: Dict[str, Any] = Field(description="Strategy decision from LangGraph")
    response_template: Optional[str] = Field(default=None, description="Suggested response template")
    escalation_reason: Optional[str] = Field(default=None, description="Escalation reason if applicable")
    priority_override: Optional[bool] = Field(default=None, description="Priority override flag")


class ResponseRequest(BaseModel):
    """Complete request for response generation."""
    email_context: EmailContext
    strategy_context: StrategyContext
    business_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional business context (company info, policies, etc.)"
    )
    response_variants: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of response variants to generate"
    )


class ResponseVariant(BaseModel):
    """A single generated response variant."""
    subject: str = Field(description="Response email subject")
    content: str = Field(description="Response email content")
    tone: Literal["professional", "friendly", "urgent", "standard"] = Field(
        description="Detected/applied tone"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in response quality"
    )
    reasoning: str = Field(description="Why this response approach was chosen")
    estimated_length: Literal["brief", "medium", "detailed"] = Field(
        description="Response length category"
    )
    key_points_addressed: List[str] = Field(
        description="Key points from original email that are addressed"
    )


class ResponseGeneration(BaseModel):
    """Complete response generation output."""
    variants: List[ResponseVariant] = Field(description="Generated response variants")
    recommended_variant: int = Field(
        ge=0,
        description="Index of recommended variant (0-based)"
    )
    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence in response generation"
    )
    requires_human_review: bool = Field(
        description="Whether human review is recommended"
    )
    review_reasons: List[str] = Field(
        default_factory=list,
        description="Specific reasons why human review is needed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about generation process"
    )
    framework: str = Field(default="OpenAI GPT-4o-mini")
    agent: str = Field(default="response_generator")
    generated_at: datetime = Field(default_factory=datetime.now)


class BusinessContext(BaseModel):
    """Business context for response generation."""
    company_name: str = Field(default="Your Company")
    company_domain: Optional[str] = Field(default=None)
    support_email: Optional[str] = Field(default=None)
    sales_email: Optional[str] = Field(default=None)
    business_hours: Optional[str] = Field(default="9 AM - 5 PM, Monday - Friday")
    response_policies: Dict[str, str] = Field(
        default_factory=lambda: {
            "sales": "Respond promptly to sales inquiries with helpful information",
            "support": "Provide clear troubleshooting steps and escalation paths",
            "urgent": "Acknowledge immediately and provide timeline for resolution",
            "personal": "Respond courteously while maintaining professional boundaries"
        }
    )
    brand_voice: Literal["professional", "friendly", "casual", "formal"] = Field(
        default="professional"
    )
    signature_template: str = Field(
        default="Best regards,\n[Agent Name]\n{company_name}"
    )