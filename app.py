import streamlit as st
import pandas as pd
from engine import process_user_request
from db_utils import validate_and_execute_sql

st.set_page_config(page_title="Text-to-SQL + Clarification Engine", layout="wide")
st.title("Text-to-SQL with Clarification Engine")

# Initialize Session State to remember the conversation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clarification_state" not in st.session_state:
    st.session_state.clarification_state = None

# Render the Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message:
            st.code(message["sql"], language="sql")
        if "data" in message and message["data"] is not None:
            st.dataframe(pd.DataFrame(message["data"]))

def handle_user_input(prompt_text: str):
    # 1. Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    # 2. Process via your Clarification Engine
    with st.spinner("Analyzing request and database schema..."):
        history_for_engine = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        response = process_user_request(prompt_text, history_for_engine)

    # 3. Handle the Engine's Decision
    with st.chat_message("assistant"):
        if response.needs_clarification:
            # Engine hit an ambiguity (e.g., Gross vs Net)
            st.session_state.clarification_state = response
            st.markdown(f"**Clarification Needed:** {response.clarification_question}")
            st.caption(f"Reasoning: {response.reasoning}")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.clarification_question
            })
            st.rerun() # Refresh to show the buttons
        else:
            # Engine is confident and wrote SQL
            st.session_state.clarification_state = None
            st.markdown("Generated SQL Query:")
            st.code(response.sql_query, language="sql")
            
            # Execute the SQL safely against PostgreSQL
            exec_result = validate_and_execute_sql(response.sql_query)
            
            if exec_result["status"] == "success":
                st.markdown("**Query Results:**")
                st.dataframe(pd.DataFrame(exec_result["data"]))
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Query executed successfully.",
                    "sql": response.sql_query,
                    "data": exec_result["data"]
                })
            else:
                st.error(f"Execution Error: {exec_result['message']}")

# Render Interactive Option Buttons if Clarification is Needed
if st.session_state.clarification_state:
    clarify_obj = st.session_state.clarification_state
    st.info("Select an option to clarify your query:")
    cols = st.columns(len(clarify_obj.options))
    
    # Create a dynamic button for every option Gemini generated
    for idx, option in enumerate(clarify_obj.options):
        if cols[idx].button(option, key=f"opt_{idx}"):
            handle_user_input(f"Selected preference: {option}")

# The main chat input bar at the bottom
user_prompt = st.chat_input("Ask a question about your database...")
if user_prompt:
    handle_user_input(user_prompt)