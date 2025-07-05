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
            config=self.agents_config['email_classifier'],
            llm=self.llm,
            tools=[EmailClassificationTool(), ValidationTool()],
            verbose=True
        )

    @task
    def classify_email(self) -> Task:
        return Task(
            config=self.tasks_config['classify_email'],
            agent=self.email_classifier()
        )

    @crew
    def crew(self) -> Crew:
        """Create the email classification crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
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