"""
Data models for strategy agent
"""

from typing import TypedDict, Annotated, Literal, Optional, List
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langchain_core.utils.function_calling import convert_to_openai_tool


def add_messages(left: list[AnyMessage], right: Optional[AnyMessage | list[AnyMessage]]) -> list[AnyMessage]:
    """Add message(s) to the conversation."""
    if right is None:
        return left
    if isinstance(right, list):
        return left + right
    return left + [right]


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the workflow state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class EmailClassification(BaseModel):
    """Email classification results from CrewAI agent."""
    type: Literal["sales", "support", "spam", "personal", "urgent"]
    priority: Literal["high", "medium", "low"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    suggested_response_tone: Literal["professional", "friendly", "urgent", "dismissive"]
    framework: Optional[str] = None
    agent: Optional[str] = None


class StrategyDecision(BaseModel):
    """Strategy planning decision output."""
    response_strategy: Literal["immediate", "delayed", "escalate", "auto_reply"] = Field(
        description="The recommended response strategy based on email classification"
    )
    response_approach: Literal["formal", "friendly", "urgent", "standard"] = Field(
        description="The tone and approach for the response"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, 
        description="Confidence level in the strategy decision"
    )
    reasoning: str = Field(
        description="Clear explanation of why this strategy was chosen"
    )
    next_steps: List[str] = Field(
        description="Recommended next actions to take"
    )
    estimated_response_time: Literal["immediate", "within_hour", "within_day", "when_available"] = Field(
        description="Expected time frame for response"
    )


class StrategyRecommendation(BaseModel):
    """Final strategy recommendation with detailed guidance."""
    strategy_decision: StrategyDecision
    response_template: Optional[str] = Field(
        default=None,
        description="Template or structure for the response"
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Reason for escalation if strategy is 'escalate'"
    )
    priority_override: Optional[bool] = Field(
        default=None,
        description="Whether to override the original priority level"
    )
    framework: str = Field(default="LangGraph + GPT-4o-mini")
    agent: str = Field(default="strategy_planner")


class StrategyState(TypedDict):
    """State for the strategy planning workflow."""
    messages: Annotated[list[AnyMessage], add_messages]
    classification_results: EmailClassification
    strategy_decision: Optional[StrategyDecision]
    strategy_recommendation: Optional[StrategyRecommendation]
    dialog_state: Annotated[list[str], update_dialog_stack]
    current_step: str