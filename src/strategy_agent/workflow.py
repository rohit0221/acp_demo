"""
LangGraph workflow for email strategy planning
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .models import StrategyState, StrategyDecision, StrategyRecommendation, EmailClassification

# Load environment variables
load_dotenv()


class StrategyPlanner:
    """LangGraph-based strategy planning agent for email responses."""
    
    def __init__(self):
        """Initialize the strategy planner with OpenAI GPT-4o-mini."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent decision making
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create structured output for strategy decisions
        self.strategy_planner = self.llm.with_structured_output(StrategyDecision)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for strategy planning."""
        workflow = StateGraph(StrategyState)
        
        # Add nodes
        workflow.add_node("strategy_planner", self._strategy_planning_node)
        workflow.add_node("immediate_handler", self._immediate_response_node)
        workflow.add_node("delayed_handler", self._delayed_response_node)
        workflow.add_node("escalation_handler", self._escalation_node)
        workflow.add_node("auto_reply_handler", self._auto_reply_node)
        
        # Set entry point
        workflow.set_entry_point("strategy_planner")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "strategy_planner",
            self._route_strategy,
            {
                "immediate": "immediate_handler",
                "delayed": "delayed_handler",
                "escalate": "escalation_handler",
                "auto_reply": "auto_reply_handler",
                "end": END
            }
        )
        
        # All strategy handlers end the workflow
        workflow.add_edge("immediate_handler", END)
        workflow.add_edge("delayed_handler", END)
        workflow.add_edge("escalation_handler", END)
        workflow.add_edge("auto_reply_handler", END)
        
        return workflow
    
    def _strategy_planning_node(self, state: StrategyState) -> Dict[str, Any]:
        """Main strategy planning node that analyzes email classification."""
        classification = state["classification_results"]
        
        # Create system prompt for strategy planning
        system_prompt = """You are an expert email strategy planner. Your job is to analyze email classification results and determine the optimal response strategy.

Consider these factors:
1. Email type and priority level
2. Confidence in classification
3. Business impact and urgency
4. Appropriate response tone and timing
5. Resource allocation and escalation needs

Choose the most appropriate strategy and provide clear reasoning."""
        
        # Create human message with classification results
        human_message = f"""
Please analyze this email classification and determine the optimal response strategy:

Email Classification:
- Type: {classification.type}
- Priority: {classification.priority}
- Confidence: {classification.confidence:.2f}
- Reasoning: {classification.reasoning}
- Suggested tone: {classification.suggested_response_tone}

Determine the best response strategy, approach, and next steps.
"""
        
        # Get strategy decision from LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        try:
            strategy_decision = self.strategy_planner.invoke(messages)
            
            return {
                "strategy_decision": strategy_decision,
                "dialog_state": "strategy_planned",
                "current_step": "routing"
            }
        except Exception as e:
            # Fallback strategy decision
            fallback_decision = StrategyDecision(
                response_strategy="delayed",
                response_approach="standard",
                confidence_score=0.5,
                reasoning=f"Strategy planning failed: {str(e)}. Using fallback strategy.",
                next_steps=["manual_review", "standard_processing"],
                estimated_response_time="within_day"
            )
            
            return {
                "strategy_decision": fallback_decision,
                "dialog_state": "strategy_planned",
                "current_step": "routing"
            }
    
    def _route_strategy(self, state: StrategyState) -> str:
        """Route to appropriate strategy handler based on decision."""
        if not state.get("strategy_decision"):
            return "end"
        
        strategy = state["strategy_decision"].response_strategy
        
        # Route based on strategy decision
        if strategy == "immediate":
            return "immediate"
        elif strategy == "delayed":
            return "delayed"
        elif strategy == "escalate":
            return "escalate"
        elif strategy == "auto_reply":
            return "auto_reply"
        else:
            return "end"
    
    def _immediate_response_node(self, state: StrategyState) -> Dict[str, Any]:
        """Handle immediate response strategy."""
        decision = state["strategy_decision"]
        classification = state["classification_results"]
        
        recommendation = StrategyRecommendation(
            strategy_decision=decision,
            response_template=self._get_immediate_template(classification.type),
            priority_override=True,
            framework="LangGraph + GPT-4o-mini",
            agent="strategy_planner"
        )
        
        return {
            "strategy_recommendation": recommendation,
            "dialog_state": "pop",
            "current_step": "completed"
        }
    
    def _delayed_response_node(self, state: StrategyState) -> Dict[str, Any]:
        """Handle delayed response strategy."""
        decision = state["strategy_decision"]
        classification = state["classification_results"]
        
        recommendation = StrategyRecommendation(
            strategy_decision=decision,
            response_template=self._get_delayed_template(classification.type),
            framework="LangGraph + GPT-4o-mini",
            agent="strategy_planner"
        )
        
        return {
            "strategy_recommendation": recommendation,
            "dialog_state": "pop",
            "current_step": "completed"
        }
    
    def _escalation_node(self, state: StrategyState) -> Dict[str, Any]:
        """Handle escalation strategy."""
        decision = state["strategy_decision"]
        classification = state["classification_results"]
        
        escalation_reason = self._determine_escalation_reason(classification)
        
        recommendation = StrategyRecommendation(
            strategy_decision=decision,
            escalation_reason=escalation_reason,
            priority_override=True,
            framework="LangGraph + GPT-4o-mini",
            agent="strategy_planner"
        )
        
        return {
            "strategy_recommendation": recommendation,
            "dialog_state": "pop",
            "current_step": "completed"
        }
    
    def _auto_reply_node(self, state: StrategyState) -> Dict[str, Any]:
        """Handle auto-reply strategy."""
        decision = state["strategy_decision"]
        classification = state["classification_results"]
        
        recommendation = StrategyRecommendation(
            strategy_decision=decision,
            response_template=self._get_auto_reply_template(classification.type),
            framework="LangGraph + GPT-4o-mini",
            agent="strategy_planner"
        )
        
        return {
            "strategy_recommendation": recommendation,
            "dialog_state": "pop",
            "current_step": "completed"
        }
    
    def _get_immediate_template(self, email_type: str) -> str:
        """Get response template for immediate responses."""
        templates = {
            "sales": "Thank you for your inquiry. We will connect you with a sales representative within the next hour.",
            "support": "We have received your support request and are investigating. You can expect an update within 2 hours.",
            "urgent": "Your urgent request has been prioritized. We are addressing this immediately and will update you shortly.",
            "personal": "Thank you for your message. We will respond personally as soon as possible.",
            "spam": "This message has been flagged and will be reviewed."
        }
        return templates.get(email_type, "Thank you for your message. We will respond promptly.")
    
    def _get_delayed_template(self, email_type: str) -> str:
        """Get response template for delayed responses."""
        templates = {
            "sales": "Thank you for your interest. A sales representative will contact you within 1-2 business days.",
            "support": "Your support request has been received. We will respond within 24 hours.",
            "personal": "Thank you for your message. We will respond within 2-3 business days.",
            "urgent": "Your message has been received and will be addressed within 24 hours.",
            "spam": "This message will be reviewed and handled appropriately."
        }
        return templates.get(email_type, "Thank you for your message. We will respond within 2-3 business days.")
    
    def _get_auto_reply_template(self, email_type: str) -> str:
        """Get response template for auto-replies."""
        templates = {
            "sales": "Thank you for your inquiry. We have received your message and will respond shortly.",
            "support": "Your support request has been received. Reference number: [AUTO-GENERATED]",
            "personal": "Thank you for your message. This is an automated acknowledgment.",
            "urgent": "Your urgent message has been received and flagged for immediate attention.",
            "spam": "This message has been received and will be processed."
        }
        return templates.get(email_type, "Thank you for your message. This is an automated acknowledgment.")
    
    def _determine_escalation_reason(self, classification: EmailClassification) -> str:
        """Determine why escalation is needed."""
        if classification.priority == "high" and classification.confidence < 0.7:
            return "High priority email with low classification confidence requires human review"
        elif classification.type == "urgent":
            return "Urgent email requires immediate human attention"
        elif classification.type == "support" and classification.priority == "high":
            return "High priority support issue may require specialized expertise"
        else:
            return "Email complexity or sensitivity requires human review"
    
    def plan_strategy(self, classification_results: EmailClassification) -> StrategyRecommendation:
        """
        Plan email response strategy based on classification results.
        
        Args:
            classification_results: Email classification from CrewAI agent
            
        Returns:
            StrategyRecommendation with detailed guidance
        """
        # Initialize state
        initial_state = StrategyState(
            messages=[],
            classification_results=classification_results,
            strategy_decision=None,
            strategy_recommendation=None,
            dialog_state=["start"],
            current_step="planning"
        )
        
        # Run the workflow
        result = self.app.invoke(initial_state)
        
        # Return the strategy recommendation
        return result.get("strategy_recommendation", self._get_fallback_recommendation(classification_results))
    
    def _get_fallback_recommendation(self, classification: EmailClassification) -> StrategyRecommendation:
        """Get fallback recommendation if workflow fails."""
        fallback_decision = StrategyDecision(
            response_strategy="delayed",
            response_approach="standard",
            confidence_score=0.5,
            reasoning="Workflow failed, using fallback strategy for safety",
            next_steps=["manual_review", "standard_processing"],
            estimated_response_time="within_day"
        )
        
        return StrategyRecommendation(
            strategy_decision=fallback_decision,
            response_template="Thank you for your message. We will respond within 2-3 business days.",
            framework="LangGraph + GPT-4o-mini (Fallback)",
            agent="strategy_planner"
        )