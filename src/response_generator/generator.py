"""
OpenAI-powered email response generator
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from openai import OpenAI
from pydantic import ValidationError

from .models import (
    ResponseRequest, ResponseGeneration, ResponseVariant, 
    EmailContext, StrategyContext, BusinessContext
)

# Load environment variables
load_dotenv()


class ResponseGenerator:
    """OpenAI-powered email response generator."""
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        """Initialize the response generator with OpenAI client."""
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Use default business context if none provided
        self.business_context = business_context or BusinessContext()
        
        # Response generation settings
        self.model = "gpt-4o-mini"
        self.temperature = 0.7  # Balanced creativity for natural responses
        self.max_tokens = 1000  # Sufficient for email responses
    
    def generate_responses(self, request: ResponseRequest) -> ResponseGeneration:
        """
        Generate email responses based on request context.
        
        Args:
            request: Complete request with email and strategy context
            
        Returns:
            ResponseGeneration with multiple variants and recommendations
        """
        try:
            # Extract key information
            email_ctx = request.email_context
            strategy_ctx = request.strategy_context
            
            # Generate response variants
            variants = []
            for i in range(request.response_variants):
                variant = self._generate_single_response(
                    email_ctx, strategy_ctx, variant_number=i+1
                )
                if variant:
                    variants.append(variant)
            
            if not variants:
                # Fallback if generation fails
                return self._create_fallback_response(request)
            
            # Determine recommended variant and review requirements
            recommended_idx, requires_review, review_reasons = self._analyze_responses(
                variants, email_ctx, strategy_ctx
            )
            
            # Calculate overall confidence
            overall_confidence = sum(v.confidence_score for v in variants) / len(variants)
            
            return ResponseGeneration(
                variants=variants,
                recommended_variant=recommended_idx,
                overall_confidence=overall_confidence,
                requires_human_review=requires_review,
                review_reasons=review_reasons,
                metadata={
                    "generation_method": "openai_gpt4o_mini",
                    "variants_requested": request.response_variants,
                    "variants_generated": len(variants),
                    "strategy_applied": strategy_ctx.strategy_decision.get("response_strategy"),
                    "tone_applied": strategy_ctx.strategy_decision.get("response_approach")
                }
            )
            
        except Exception as e:
            # Return fallback response on error
            return self._create_error_response(request, str(e))
    
    def _generate_single_response(
        self, 
        email_ctx: EmailContext, 
        strategy_ctx: StrategyContext,
        variant_number: int = 1
    ) -> Optional[ResponseVariant]:
        """Generate a single response variant."""
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(strategy_ctx)
            
            # Build user prompt with context
            user_prompt = self._build_user_prompt(email_ctx, strategy_ctx, variant_number)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            return self._parse_openai_response(response_text, email_ctx, strategy_ctx)
            
        except Exception as e:
            print(f"❌ Error generating response variant {variant_number}: {e}")
            return None
    
    def _build_system_prompt(self, strategy_ctx: StrategyContext) -> str:
        """Build system prompt based on strategy context."""
        strategy = strategy_ctx.strategy_decision.get("response_strategy", "delayed")
        approach = strategy_ctx.strategy_decision.get("response_approach", "standard")
        
        base_prompt = f"""You are an expert email response generator for {self.business_context.company_name}. 

Your task is to generate professional email responses based on the strategy recommendations provided.

Key Guidelines:
- Follow the recommended response strategy: {strategy}
- Use the recommended approach/tone: {approach}
- Maintain {self.business_context.brand_voice} brand voice
- Be helpful, clear, and actionable
- Address the original email's main points
- Keep responses concise but complete

Business Context:
- Company: {self.business_context.company_name}
- Business Hours: {self.business_context.business_hours}
- Brand Voice: {self.business_context.brand_voice}

Response Format:
Generate a JSON response with:
- "subject": Email subject line
- "content": Email body content  
- "key_points": List of key points addressed
- "confidence": Confidence score (0.0-1.0)
- "reasoning": Why this approach was chosen
"""

        # Add strategy-specific guidance
        if strategy == "immediate":
            base_prompt += "\n- Acknowledge urgency and provide immediate next steps"
        elif strategy == "delayed":
            base_prompt += "\n- Set appropriate expectations for response timing"
        elif strategy == "escalate":
            base_prompt += "\n- Acknowledge issue and explain escalation process"
        elif strategy == "auto_reply":
            base_prompt += "\n- Provide automated acknowledgment with clear next steps"
        
        return base_prompt
    
    def _build_user_prompt(
        self, 
        email_ctx: EmailContext, 
        strategy_ctx: StrategyContext,
        variant_number: int
    ) -> str:
        """Build user prompt with email context."""
        classification = email_ctx.classification
        
        prompt = f"""Please generate email response variant #{variant_number}.

Original Email:
Subject: {email_ctx.subject}
From: {email_ctx.sender_name or email_ctx.sender_email or 'Customer'}
Content: {email_ctx.content}

Email Classification:
- Type: {classification.get('type', 'unknown')}
- Priority: {classification.get('priority', 'medium')}
- Confidence: {classification.get('confidence', 0.5):.2f}
- Reasoning: {classification.get('reasoning', 'No reasoning provided')}

Strategy Recommendation:
- Strategy: {strategy_ctx.strategy_decision.get('response_strategy', 'delayed')}
- Approach: {strategy_ctx.strategy_decision.get('response_approach', 'standard')}
- Confidence: {strategy_ctx.strategy_decision.get('confidence_score', 0.5):.2f}
- Reasoning: {strategy_ctx.strategy_decision.get('reasoning', 'No reasoning provided')}
"""

        if strategy_ctx.response_template:
            prompt += f"\nSuggested Template: {strategy_ctx.response_template}"
        
        if variant_number > 1:
            prompt += f"\n\nFor variant #{variant_number}, try a slightly different approach while maintaining the same strategy and tone."
        
        prompt += "\n\nGenerate appropriate email response as JSON with the specified format."
        
        return prompt
    
    def _parse_openai_response(
        self, 
        response_text: str, 
        email_ctx: EmailContext, 
        strategy_ctx: StrategyContext
    ) -> ResponseVariant:
        """Parse OpenAI response into ResponseVariant."""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Extract required fields
                subject = parsed.get('subject', f"Re: {email_ctx.subject}")
                content = parsed.get('content', response_text)
                key_points = parsed.get('key_points', [])
                confidence = float(parsed.get('confidence', 0.7))
                reasoning = parsed.get('reasoning', 'Generated response based on strategy')
                
            else:
                # Fallback if no JSON found
                subject = f"Re: {email_ctx.subject}"
                content = response_text
                key_points = ["Original email content"]
                confidence = 0.6
                reasoning = "Generated response without structured parsing"
            
            # Determine tone and length
            tone = strategy_ctx.strategy_decision.get('response_approach', 'standard')
            if tone not in ["professional", "friendly", "urgent", "standard"]:
                tone = "standard"
            
            length = self._estimate_response_length(content)
            
            return ResponseVariant(
                subject=subject,
                content=content,
                tone=tone,
                confidence_score=confidence,
                reasoning=reasoning,
                estimated_length=length,
                key_points_addressed=key_points
            )
            
        except Exception as e:
            print(f"❌ Error parsing OpenAI response: {e}")
            # Return fallback variant
            return ResponseVariant(
                subject=f"Re: {email_ctx.subject}",
                content=response_text,
                tone="standard",
                confidence_score=0.5,
                reasoning=f"Fallback parsing due to error: {str(e)}",
                estimated_length="medium",
                key_points_addressed=["Original email"]
            )
    
    def _estimate_response_length(self, content: str) -> str:
        """Estimate response length category."""
        word_count = len(content.split())
        if word_count < 50:
            return "brief"
        elif word_count < 150:
            return "medium"
        else:
            return "detailed"
    
    def _analyze_responses(
        self, 
        variants: List[ResponseVariant], 
        email_ctx: EmailContext, 
        strategy_ctx: StrategyContext
    ) -> tuple[int, bool, List[str]]:
        """Analyze generated responses and determine recommendations."""
        if not variants:
            return 0, True, ["No responses generated"]
        
        # Find best variant (highest confidence)
        best_idx = max(range(len(variants)), key=lambda i: variants[i].confidence_score)
        
        # Determine if human review is needed
        requires_review = False
        review_reasons = []
        
        classification = email_ctx.classification
        strategy = strategy_ctx.strategy_decision
        
        # Check confidence thresholds
        max_confidence = max(v.confidence_score for v in variants)
        if max_confidence < 0.7:
            requires_review = True
            review_reasons.append("Low confidence in generated responses")
        
        # Check for escalation strategy
        if strategy.get("response_strategy") == "escalate":
            requires_review = True
            review_reasons.append("Strategy requires escalation to human")
        
        # Check for high priority with low classification confidence
        if (classification.get("priority") == "high" and 
            classification.get("confidence", 0) < 0.8):
            requires_review = True
            review_reasons.append("High priority email with uncertain classification")
        
        # Check for urgent emails
        if classification.get("type") == "urgent":
            requires_review = True
            review_reasons.append("Urgent email requires human oversight")
        
        # Check for sensitive content indicators
        sensitive_keywords = ["complaint", "legal", "lawsuit", "refund", "cancel", "angry"]
        email_content_lower = email_ctx.content.lower()
        if any(keyword in email_content_lower for keyword in sensitive_keywords):
            requires_review = True
            review_reasons.append("Email contains potentially sensitive content")
        
        return best_idx, requires_review, review_reasons
    
    def _create_fallback_response(self, request: ResponseRequest) -> ResponseGeneration:
        """Create fallback response when generation fails."""
        fallback_variant = ResponseVariant(
            subject=f"Re: {request.email_context.subject}",
            content=f"Thank you for your email. We have received your message and will respond within {self.business_context.business_hours}.\n\nBest regards,\nCustomer Service Team",
            tone="professional",
            confidence_score=0.5,
            reasoning="Fallback response due to generation failure",
            estimated_length="brief",
            key_points_addressed=["Acknowledgment"]
        )
        
        return ResponseGeneration(
            variants=[fallback_variant],
            recommended_variant=0,
            overall_confidence=0.5,
            requires_human_review=True,
            review_reasons=["Response generation failed, using fallback"],
            metadata={"generation_method": "fallback"}
        )
    
    def _create_error_response(self, request: ResponseRequest, error: str) -> ResponseGeneration:
        """Create error response when generation fails completely."""
        error_variant = ResponseVariant(
            subject=f"Re: {request.email_context.subject}",
            content="Thank you for your email. We are currently experiencing technical difficulties and will respond as soon as possible.",
            tone="professional",
            confidence_score=0.3,
            reasoning=f"Error response due to: {error}",
            estimated_length="brief",
            key_points_addressed=["Error acknowledgment"]
        )
        
        return ResponseGeneration(
            variants=[error_variant],
            recommended_variant=0,
            overall_confidence=0.3,
            requires_human_review=True,
            review_reasons=[f"Generation error: {error}"],
            metadata={"generation_method": "error", "error": error}
        )