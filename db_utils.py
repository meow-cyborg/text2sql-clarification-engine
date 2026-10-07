import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

def get_db_connection():
    """Establishes a connection to the database."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def get_schema_representation() -> str:
    """Extracts table names, column names, and data types from PostgreSQL."""
    query = """
    SELECT c.table_name, c.column_name, c.data_type
    FROM information_schema.columns c
    WHERE c.table_schema = 'public'
    ORDER BY c.table_name, c.ordinal_position;
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    schema_dict = {}
    for table_name, column_name, data_type in rows:
        if table_name not in schema_dict:
            schema_dict[table_name] = []
        schema_dict[table_name].append(f"{column_name} ({data_type})")

    formatted_schema = ""
    for table, cols in schema_dict.items():
        formatted_schema += f"Table: {table}\n  Columns: {', '.join(cols)}\n\n"
    return formatted_schema

def validate_and_execute_sql(sql_query: str):
    """Guards against destructive statements and executes valid SELECT queries."""
    clean_sql = sql_query.strip().rstrip(";")
    forbidden_keywords = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    
    if any(keyword in clean_sql.upper().split() for keyword in forbidden_keywords):
        return {"status": "error", "message": "Security Violation: Only read-only SELECT queries are permitted."}

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(clean_sql)
        results = cur.fetchall()
        cur.close()
        conn.close()
        return {"status": "success", "data": [dict(r) for r in results]}
    except Exception as e:
        cur.close()
        conn.close()
        return {"status": "error", "message": str(e)}

# Test block to verify extraction works
if __name__ == "__main__":
    print("Extracted Database Schema:\n")
    print(get_schema_representation())