"""
Tools for Email Classification Crew
"""

from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json

class EmailInput(BaseModel):
    """Input schema for email classification tool"""
    email_content: str = Field(..., description="The email content to classify")
    email_subject: str = Field(default="", description="The email subject line")

class EmailClassificationTool(BaseTool):
    name: str = "Email Classification Tool"
    description: str = "Tool for extracting and validating email content for classification"

    def _run(self, email_content: str, email_subject: str = "") -> str:
        """
        Process and validate email content for classification
        """
        if not email_content or not email_content.strip():
            return json.dumps({
                "error": "Email content is empty or invalid",
                "type": "error",
                "priority": "low",
                "confidence": 0.0,
                "reasoning": "No email content provided for classification",
                "suggested_response_tone": "professional"
            })
        
        # Clean and prepare email content
        cleaned_content = email_content.strip()
        cleaned_subject = email_subject.strip() if email_subject else ""
        
        # Return the cleaned email data for the agent to analyze
        return f"Subject: {cleaned_subject}\nContent: {cleaned_content}"

class ValidationTool(BaseTool):
    name: str = "JSON Validation Tool"
    description: str = "Tool for validating JSON output format"
    
    def _run(self, json_output: str) -> str:
        """
        Validate that the output is proper JSON format
        """
        try:
            parsed = json.loads(json_output)
            required_fields = ['type', 'priority', 'confidence', 'reasoning', 'suggested_response_tone']
            
            for field in required_fields:
                if field not in parsed:
                    return f"Missing required field: {field}"
            
            # Validate field values
            valid_types = ['sales', 'support', 'spam', 'personal', 'urgent']
            valid_priorities = ['high', 'medium', 'low']
            valid_tones = ['professional', 'friendly', 'urgent', 'dismissive']
            
            if parsed['type'] not in valid_types:
                return f"Invalid type. Must be one of: {', '.join(valid_types)}"
            
            if parsed['priority'] not in valid_priorities:
                return f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            
            if parsed['suggested_response_tone'] not in valid_tones:
                return f"Invalid tone. Must be one of: {', '.join(valid_tones)}"
            
            if not isinstance(parsed['confidence'], (int, float)) or not 0 <= parsed['confidence'] <= 1:
                return "Confidence must be a number between 0 and 1"
            
            return "Valid JSON format"
            
        except json.JSONDecodeError:
            return "Invalid JSON format"