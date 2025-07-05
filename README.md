# Email Classifier POC

Multi-Agent Email Classification and Response Generation System using ACP Protocol.

## Overview

This POC demonstrates ACP (Agent Communication Protocol) capabilities through:
- CrewAI email classification
- LangGraph strategy planning  
- OpenAI response generation
- Human-in-the-loop workflow
- Multi-modal support

## Setup

```bash
poetry install
```

## Running

```bash
# Start email classifier agent
poetry run python src/email_classifier_agent.py

# Test the classifier
poetry run python src/test_email_classifier.py
```

## Architecture

1. **Email Classifier Agent** (CrewAI) - Categorizes emails
2. **Strategy Agent** (LangGraph) - Plans response approach
3. **Response Generator** (OpenAI) - Creates draft responses
4. **Human Approval** - Review and approve steps