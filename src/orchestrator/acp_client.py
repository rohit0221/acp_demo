"""
ACP client for communicating with email processing agents
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import ClassificationResult, StrategyResult, ResponseResult


class ACPClient:
    """Client for communicating with ACP agents."""
    
    def __init__(self, agent_endpoints: Dict[str, str], timeout: int = 30, max_retries: int = 3):
        """
        Initialize ACP client.
        
        Args:
            agent_endpoints: Dictionary mapping agent names to their URLs
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.agent_endpoints = agent_endpoints
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, agent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to an ACP agent.
        
        Args:
            agent_name: Name of the agent (classifier, strategy, response)
            data: Data to send to the agent
            
        Returns:
            Response data from the agent
            
        Raises:
            Exception: If request fails after all retries
        """
        if agent_name not in self.agent_endpoints:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        url = f"{self.agent_endpoints[agent_name]}/runs"
        
        # Map agent names to actual agent function names
        agent_function_names = {
            "classifier": "email_classifier_agent",
            "strategy": "strategy_planning_agent", 
            "response": "response_generation_agent"
        }
        
        agent_function_name = agent_function_names.get(agent_name, agent_name)
        
        # Prepare ACP request format
        acp_request = {
            "agent_name": agent_function_name,
            "input": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "content": json.dumps(data),
                            "type": "application/json"
                        }
                    ]
                }
            ],
            "mode": "sync"
        }
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 Calling {agent_name} agent (attempt {attempt + 1}/{self.max_retries})...")
                
                async with self.session.post(url, json=acp_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract response from ACP /runs format
                        if "output" in result and result["output"]:
                            message = result["output"][0]
                            if "parts" in message and message["parts"]:
                                part = message["parts"][0]
                                if part.get("type") == "application/json":
                                    return json.loads(part["content"])
                                else:
                                    return {"raw_content": part["content"]}
                        
                        # Fallback for different response formats
                        if "messages" in result and result["messages"]:
                            message = result["messages"][0]
                            if "parts" in message and message["parts"]:
                                part = message["parts"][0]
                                if part.get("type") == "application/json":
                                    return json.loads(part["content"])
                                else:
                                    return {"raw_content": part["content"]}
                        
                        return result
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}"
                        )
                        
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️ Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Request failed after {self.max_retries} attempts: {e}")
        
        raise Exception(f"Failed to communicate with {agent_name} agent: {last_error}")
    
    async def classify_email(self, subject: str, content: str, sender_name: str = None, sender_email: str = None) -> ClassificationResult:
        """
        Classify an email using the classification agent.
        
        Args:
            subject: Email subject
            content: Email content
            sender_name: Sender's name (optional)
            sender_email: Sender's email (optional)
            
        Returns:
            ClassificationResult with classification details
        """
        # Prepare email content for classification
        email_text = f"Subject: {subject}\n\n{content}"
        if sender_name:
            email_text = f"From: {sender_name}\n{email_text}"
        
        request_data = {
            "email_content": email_text,
            "email_subject": subject,
            "sender_name": sender_name,
            "sender_email": sender_email
        }
        
        try:
            response = await self._make_request("classifier", request_data)
            
            # Handle errors in response
            if "error" in response:
                raise Exception(f"Classification failed: {response['error']}")
            
            # Extract classification data
            return ClassificationResult(
                type=response.get("type", "unknown"),
                priority=response.get("priority", "medium"),
                confidence=float(response.get("confidence", 0.5)),
                reasoning=response.get("reasoning", "No reasoning provided"),
                suggested_response_tone=response.get("suggested_response_tone", "professional"),
                framework=response.get("framework", "CrewAI"),
                agent=response.get("agent", "email_classifier")
            )
            
        except Exception as e:
            print(f"❌ Email classification failed: {e}")
            # Return fallback classification
            return ClassificationResult(
                type="unknown",
                priority="medium",
                confidence=0.3,
                reasoning=f"Classification failed: {str(e)}",
                suggested_response_tone="professional",
                framework="Error",
                agent="email_classifier"
            )
    
    async def plan_strategy(self, classification: ClassificationResult) -> StrategyResult:
        """
        Plan response strategy using the strategy agent.
        
        Args:
            classification: Email classification results
            
        Returns:
            StrategyResult with strategy recommendations
        """
        request_data = classification.model_dump()
        
        try:
            response = await self._make_request("strategy", request_data)
            
            # Handle errors in response
            if "error" in response:
                raise Exception(f"Strategy planning failed: {response['error']}")
            
            return StrategyResult(
                strategy_decision=response.get("strategy_decision", {}),
                response_template=response.get("response_template"),
                escalation_reason=response.get("escalation_reason"),
                priority_override=response.get("priority_override"),
                framework=response.get("framework", "LangGraph"),
                agent=response.get("agent", "strategy_planner")
            )
            
        except Exception as e:
            print(f"❌ Strategy planning failed: {e}")
            # Return fallback strategy
            return StrategyResult(
                strategy_decision={
                    "response_strategy": "delayed",
                    "response_approach": "standard",
                    "confidence_score": 0.3,
                    "reasoning": f"Strategy planning failed: {str(e)}",
                    "next_steps": ["manual_review"],
                    "estimated_response_time": "within_day"
                },
                framework="Error",
                agent="strategy_planner"
            )
    
    async def generate_response(
        self, 
        email_subject: str,
        email_content: str,
        sender_name: str,
        sender_email: str,
        classification: ClassificationResult, 
        strategy: StrategyResult
    ) -> ResponseResult:
        """
        Generate email response using the response generation agent.
        
        Args:
            email_subject: Original email subject
            email_content: Original email content
            sender_name: Sender's name
            sender_email: Sender's email
            classification: Email classification results
            strategy: Strategy planning results
            
        Returns:
            ResponseResult with generated responses
        """
        request_data = {
            "email_context": {
                "subject": email_subject,
                "content": email_content,
                "sender_name": sender_name,
                "sender_email": sender_email,
                "classification": classification.model_dump()
            },
            "strategy_context": strategy.model_dump()
        }
        
        try:
            response = await self._make_request("response", request_data)
            
            # Handle errors in response
            if "error" in response:
                raise Exception(f"Response generation failed: {response['error']}")
            
            return ResponseResult(
                variants=response.get("variants", []),
                recommended_variant=response.get("recommended_variant", 0),
                overall_confidence=float(response.get("overall_confidence", 0.5)),
                requires_human_review=response.get("requires_human_review", True),
                review_reasons=response.get("review_reasons", []),
                framework=response.get("framework", "OpenAI"),
                agent=response.get("agent", "response_generator")
            )
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            # Return fallback response
            return ResponseResult(
                variants=[{
                    "subject": f"Re: {email_subject}",
                    "content": "Thank you for your email. We have received your message and will respond as soon as possible.",
                    "tone": "professional",
                    "confidence_score": 0.3,
                    "reasoning": f"Response generation failed: {str(e)}",
                    "estimated_length": "brief",
                    "key_points_addressed": ["acknowledgment"]
                }],
                recommended_variant=0,
                overall_confidence=0.3,
                requires_human_review=True,
                review_reasons=[f"Generation error: {str(e)}"],
                framework="Error",
                agent="response_generator"
            )
    
    async def test_connectivity(self) -> Dict[str, bool]:
        """
        Test connectivity to all configured agents.
        
        Returns:
            Dictionary mapping agent names to their connectivity status
        """
        results = {}
        
        for agent_name, endpoint in self.agent_endpoints.items():
            try:
                # Try to get the agent manifest
                async with self.session.get(f"{endpoint}/agents") as response:
                    results[agent_name] = response.status == 200
            except Exception:
                results[agent_name] = False
        
        return results