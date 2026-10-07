import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv
from db_utils import get_schema_representation

load_dotenv()

# 1. Define Strict Output Schema
class EngineOutput(BaseModel):
    needs_clarification: bool = Field(
        description="True if query has ambiguities, missing filters, or open metrics. False if clear."
    )
    clarification_question: Optional[str] = Field(default=None)
    options: Optional[List[str]] = Field(default=None)
    sql_query: Optional[str] = Field(default=None)
    reasoning: str = Field(description="Explanation of logic.")

# 2. Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = """
You are an expert PostgreSQL Data Analyst with a strict Clarification Engine.
Your job is to translate user requests into executable PostgreSQL queries.

DATABASE SCHEMA:
{schema}

CRITICAL RULES:
1. AMBIGUITY DETECTION: If a request is vague, set needs_clarification=True, write a clarification_question, and provide 3-4 options.
2. SQL GENERATION: Set needs_clarification=False and populate sql_query ONLY when the request is unambiguous.

You MUST return your output as a valid JSON object matching this structure:
{{
  "needs_clarification": boolean,
  "clarification_question": string or null,
  "options": [array of strings] or null,
  "sql_query": string or null,
  "reasoning": string
}}
"""

# 3. Process Request (No @retry decorator needed for Groq)
def process_user_request(user_query: str, conversation_history: Optional[List[dict]] = None) -> EngineOutput:
    schema_str = get_schema_representation()
    system_instruction = SYSTEM_PROMPT_TEMPLATE.format(schema=schema_str)

    messages = [{"role": "system", "content": system_instruction}]
    
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": user_query})

    # Call Groq's API with OpenAI GPT-OSS 20B
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",  
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1
    )
    

    # Parse the returned JSON string into the Pydantic object
    return EngineOutput.model_validate_json(response.choices[0].message.content)