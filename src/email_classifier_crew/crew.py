"""
Email Classification Crew
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from .tools import EmailClassificationTool, ValidationTool

# Load environment variables
load_dotenv()

@CrewBase
class EmailClassifierCrew():
    """Email Classification Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        # Initialize LLM with GPT-4o-mini for cost control
        self.llm = LLM(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1  # Low temperature for consistent classification
        )

    @agent
    def email_classifier(self) -> Agent:
        return Agent(
            role="Email Classification Specialist",
            goal="Accurately classify emails into categories (sales, support, spam, personal, urgent) and determine appropriate priority and response tone",
            backstory="You are an expert email analyst with years of experience in customer service, sales, and support operations. You can quickly identify the intent, urgency, and sentiment of any email. You provide clear reasoning for your classifications and suggest the most appropriate response approach. You always respond with structured JSON format for consistency.",
            llm=self.llm,
            tools=[EmailClassificationTool(), ValidationTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=1
        )

    @task
    def classify_email(self) -> Task:
        return Task(
            description="""Analyze the provided email and classify it into one of these categories:
            - sales: Sales inquiries, pricing questions, product interest, demo requests
            - support: Technical issues, help requests, account problems, bug reports
            - spam: Promotional content, suspicious offers, scams, unwanted marketing
            - personal: Personal messages, casual communication, non-business related
            - urgent: Time-sensitive matters requiring immediate attention regardless of type
            
            Email to classify:
            Subject: {email_subject}
            Content: {email_content}
            
            Analyze the email content, subject line, tone, and context to determine:
            1. The primary category this email belongs to
            2. The priority level (high/medium/low) based on urgency and importance
            3. Your confidence level in this classification (0.0 to 1.0)
            4. Clear reasoning explaining your classification decision
            5. Suggested response tone (professional/friendly/urgent/dismissive)
            
            IMPORTANT: Respond with ONLY a valid JSON object in this exact format:
            {
              "type": "category_name",
              "priority": "high/medium/low",
              "confidence": 0.85,
              "reasoning": "Clear explanation of classification decision",
              "suggested_response_tone": "professional/friendly/urgent/dismissive"
            }""",
            expected_output="A JSON object containing email classification with type, priority, confidence, reasoning, and suggested response tone. Must be valid JSON format only.",
            agent=self.email_classifier()
        )

    @crew
    def crew(self) -> Crew:
        """Create the email classification crew"""
        return Crew(
            agents=[self.email_classifier()],
            tasks=[self.classify_email()],
            process=Process.sequential,
            verbose=True
        )
    
    def classify_email_content(self, email_content: str, email_subject: str = "") -> dict:
        """
        Classify an email using the crew
        """
        try:
            # Execute the crew with email content
            result = self.crew().kickoff(inputs={
                'email_content': email_content,
                'email_subject': email_subject
            })
            
            # Parse the result
            import json
            result_text = result.raw if hasattr(result, 'raw') else str(result)
            
            # Extract JSON from the result
            try:
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    classification = json.loads(json_str)
                    classification["framework"] = "CrewAI + GPT-4o-mini"
                    classification["agent"] = "email_classifier"
                    return classification
                else:
                    return {
                        "type": "error",
                        "priority": "medium",
                        "confidence": 0.0,
                        "reasoning": f"No JSON found in response: {result_text[:200]}",
                        "suggested_response_tone": "professional",
                        "framework": "CrewAI + GPT-4o-mini",
                        "agent": "email_classifier"
                    }
                    
            except json.JSONDecodeError as e:
                return {
                    "type": "error",
                    "priority": "medium", 
                    "confidence": 0.0,
                    "reasoning": f"JSON parse error: {str(e)}. Raw: {result_text[:100]}",
                    "suggested_response_tone": "professional",
                    "framework": "CrewAI + GPT-4o-mini",
                    "agent": "email_classifier"
                }
                
        except Exception as e:
            return {
                "type": "error",
                "priority": "medium",
                "confidence": 0.0,
                "reasoning": f"Crew execution error: {str(e)}",
                "suggested_response_tone": "professional",
                "framework": "CrewAI Error",
                "agent": "email_classifier"
            }