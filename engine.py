import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
from db_utils import get_schema_representation

# Load variables from .env
load_dotenv()

# 1. Define Strict Output Schema using Pydantic
class EngineOutput(BaseModel):
    needs_clarification: bool = Field(
        description="True if query has ambiguities, missing filters, or open metrics (gross vs net). False if query is completely unambiguous."
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question clarifying the user's intent. Null if needs_clarification is False."
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="3-4 choices for the user to pick from. Null if needs_clarification is False."
    )
    sql_query: Optional[str] = Field(
        default=None,
        description="Valid PostgreSQL query. Provided ONLY if needs_clarification is False."
    )
    reasoning: str = Field(
        description="Explanation of why clarification is needed OR how the SQL query was built."
    )

# 2. Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = """
You are an expert PostgreSQL Data Analyst with a strict Clarification Engine.
Your job is to translate user requests into executable PostgreSQL queries.

DATABASE SCHEMA:
{schema}

RULES:
1. AMBIGUITY DETECTION:
   - If a query contains vague terms ("best", "sales"), unstated calculations (gross vs net), or unspecified status filters, DO NOT GUESS.
   - Set `needs_clarification = True`, ask a single question, and supply multiple-choice options.
2. SQL GENERATION:
   - Set `needs_clarification = False` and populate `sql_query` only when the request is completely clear or after clarification has been supplied.
   - Return only executable SQL in the sql_query field.
"""

def process_user_request(user_query: str, conversation_history: Optional[List[dict]] = None) -> EngineOutput:
    schema_str = get_schema_representation()
    system_instruction = SYSTEM_PROMPT_TEMPLATE.format(schema=schema_str)

    contents = []
    if conversation_history:
        for msg in conversation_history:
            contents.append(f"{msg['role'].upper()}: {msg['content']}")
            
    contents.append(f"USER: {user_query}")

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="\n".join(contents),
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=EngineOutput,
            temperature=0.1
        )
    )

    # Convert the JSON string response into our Pydantic Python object
    return EngineOutput.model_validate_json(response.text)

# Test block to verify the AI logic
if __name__ == "__main__":
    print("Testing an ambiguous query...")
    test_query = "What are our total sales?"
    result = process_user_request(test_query)
    
    print(f"\nUser asked: '{test_query}'")
    print(f"Needs Clarification: {result.needs_clarification}")
    if result.needs_clarification:
        print(f"Question: {result.clarification_question}")
        print(f"Options: {result.options}")
    else:
        print(f"SQL Generated: {result.sql_query}")