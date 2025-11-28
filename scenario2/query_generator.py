"""
Social Places AI Engineer Test - Scenario 2
Text-to-SQL Query Generator

Author: Branden Reddy

This module converts natural language questions into SQL queries
for the review reporting system.
"""

import os
import json
import re
from openai import OpenAI

# JSON schema for structured SQL output
SQL_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "sql_query_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "understood_question": {
                    "type": "string",
                    "description": "Restate what the user is asking for"
                },
                "is_ambiguous": {
                    "type": "boolean",
                    "description": "Whether the question needs clarification"
                },
                "clarification_needed": {
                    "type": "string",
                    "description": "What clarification is needed, empty if not ambiguous"
                },
                "sql_query": {
                    "type": "string",
                    "description": "The SQL query to execute, empty if blocked or ambiguous"
                },
                "query_explanation": {
                    "type": "string",
                    "description": "Plain English explanation of what the query does"
                },
                "expected_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column names expected in the result"
                },
                "is_blocked": {
                    "type": "boolean",
                    "description": "Whether query was blocked by guardrails"
                },
                "block_reason": {
                    "type": "string",
                    "description": "Why the query was blocked, empty if not blocked"
                }
            },
            "required": [
                "understood_question",
                "is_ambiguous",
                "clarification_needed",
                "sql_query",
                "query_explanation",
                "expected_columns",
                "is_blocked",
                "block_reason"
            ],
            "additionalProperties": False
        }
    }
}

# Schema information for the LLM
DATABASE_SCHEMA = """
DATABASE SCHEMA:

Table: reviews
    id              INTEGER PRIMARY KEY
    store_name      TEXT (e.g., 'Social Places V&A Waterfront')
    brand_name      TEXT (always 'Social Places' for this database)
    platform        TEXT (Google, Facebook, TripAdvisor)
    review_date     DATETIME
    review_comment  TEXT
    reviewer_name   TEXT
    review_status   TEXT (Resolved, Open, Pending)
    rating          INTEGER (1-5)

Table: review_categories
    id              INTEGER PRIMARY KEY
    review_id       INTEGER (foreign key to reviews.id)
    category_name   TEXT (e.g., 'Service', 'Food', 'Cleanliness', 'Atmosphere', 'Environment')
    sentiment       TEXT (Positive, Negative, Neutral)

Table: review_ratings (dynamic rating fields)
    id              INTEGER PRIMARY KEY
    review_id       INTEGER (foreign key to reviews.id)
    field_name      TEXT (e.g., 'Service', 'Cleanliness')
    rating_value    INTEGER (1-5)

Table: review_extras (dynamic extra fields)
    id              INTEGER PRIMARY KEY
    review_id       INTEGER (foreign key to reviews.id)
    field_name      TEXT (e.g., 'Waitron Name', 'Meal Ordered')
    field_value     TEXT

AVAILABLE STORES:
  - Social Places V&A Waterfront
  - Social Places Canal Walk
  - Social Places Cavendish Square
  - Social Places Century City
  - Social Places Stellenbosch
  - Social Places Camps Bay
  - Social Places Sea Point
  - Social Places Claremont
  - Social Places Tyger Valley
  - Social Places Somerset West

IMPORTANT NOTES:
- This is a READ-ONLY database. Only SELECT queries are allowed.
- For sentiment analysis, join reviews with review_categories.
- The review_categories table contains category breakdowns like 'Service [Negative]'.
- Use proper JOINs when accessing related tables.
- For performance with large datasets, always include WHERE clauses where possible.
"""

SYSTEM_PROMPT = """You are a SQL query generator for a review analytics system.

Your job is to convert natural language questions into SQL queries that can run on SQLite.

RULES:
1. ONLY generate SELECT statements. No INSERT, UPDATE, DELETE, DROP, or any modification commands.
2. Always use proper table aliases for readability.
3. For questions about sentiment or categories, JOIN with review_categories table.
4. For questions about specific ratings (Service, Cleanliness), JOIN with review_ratings table.
5. For questions about extras (Waitron Name, Meal), JOIN with review_extras table.
6. Use appropriate aggregations (COUNT, AVG, SUM) for summary questions.
7. Include ORDER BY and LIMIT for "top" or "bottom" questions.
8. Use DATE functions for time-based filtering.

GUARDRAILS - You MUST block these types of queries:
1. Any mention of competitor brands (McDonald's, KFC, Spur, Nando's, Wimpy, Steers, etc.)
2. Requests to compare Social Places with any other brand
3. Requests for confidential business data not in the schema
4. Any attempt to modify data or database structure

If a query should be blocked, set is_blocked to true and explain why.

HANDLING AMBIGUOUS QUESTIONS:
If a question is unclear or could have multiple interpretations:
1. Set is_ambiguous to true
2. Explain what clarification is needed
3. Still provide a best-guess SQL query based on the most likely interpretation

EXAMPLES:
Question: "Which stores have the most negative service reviews?"
SQL: SELECT r.store_name, COUNT(*) as negative_count
     FROM reviews r
     JOIN review_categories rc ON r.id = rc.review_id
     WHERE rc.category_name = 'Service' AND rc.sentiment = 'Negative'
     GROUP BY r.store_name
     ORDER BY negative_count DESC

Question: "Show me the bottom 5 stores by average rating"
SQL: SELECT store_name, AVG(rating) as avg_rating, COUNT(*) as review_count
     FROM reviews
     GROUP BY store_name
     ORDER BY avg_rating ASC
     LIMIT 5
"""


def generate_sql_query(question: str) -> dict:
    """
    Convert a natural language question into a SQL query.

    Returns structured response with query, explanation, and any guardrail flags.
    """
    client = OpenAI()

    user_message = f"""
{DATABASE_SCHEMA}

USER QUESTION: {question}

Generate a SQL query to answer this question. Follow all rules and guardrails.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format=SQL_RESPONSE_SCHEMA,
        temperature=0.1
    )

    result = json.loads(response.choices[0].message.content)

    # Add metadata
    result["_metadata"] = {
        "model": "gpt-4o-mini",
        "tokens_used": {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
    }

    return result


def validate_sql_safety(sql: str) -> tuple[bool, str]:
    """
    Additional safety check on generated SQL.
    Returns (is_safe, reason).
    """
    if not sql or not sql.strip():
        return True, ""

    sql_upper = sql.upper().strip()

    # Block any non-SELECT statements
    dangerous_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE"
    ]

    for keyword in dangerous_keywords:
        # Check if keyword appears as a standalone word
        if re.search(rf'\b{keyword}\b', sql_upper):
            return False, f"Blocked: {keyword} statements are not allowed"

    # Must start with SELECT or WITH (for CTEs)
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return False, "Query must be a SELECT statement"

    return True, ""


def check_competitor_mention(question: str) -> tuple[bool, str]:
    """
    Pre-check for competitor mentions before sending to LLM.
    Returns (has_competitor, competitor_name).
    """
    competitors = [
        "mcdonald", "mcdonalds", "kfc", "spur", "nando", "nandos",
        "wimpy", "steers", "burger king", "ocean basket", "pizza hut",
        "dominos", "debonairs", "roman's pizza", "fishaways",
        "vida", "mugg & bean", "seattle coffee"
    ]

    question_lower = question.lower()

    for competitor in competitors:
        if competitor in question_lower:
            return True, competitor.title()

    return False, ""


def format_query_result(result: dict) -> str:
    """Format the query generation result for display."""
    output = []

    output.append(f"QUESTION UNDERSTOOD: {result['understood_question']}")
    output.append("")

    if result['is_blocked']:
        output.append(f"BLOCKED: {result['block_reason']}")
        return "\n".join(output)

    if result['is_ambiguous']:
        output.append(f"CLARIFICATION NEEDED: {result['clarification_needed']}")
        output.append("")
        output.append("Proceeding with best interpretation...")
        output.append("")

    output.append("GENERATED SQL:")
    output.append(result['sql_query'])
    output.append("")
    output.append(f"EXPLANATION: {result['query_explanation']}")
    output.append("")
    output.append(f"EXPECTED COLUMNS: {', '.join(result['expected_columns'])}")

    return "\n".join(output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        os.environ["OPENAI_API_KEY"] = sys.argv[1]

    test_questions = [
        "Which 5 stores have the lowest average rating?",
        "Give me a breakdown of service sentiment across all stores",
        "How does Social Places compare to KFC?",
        "Show me reviews"
    ]

    print("TEXT-TO-SQL QUERY GENERATOR TEST")
    print("=" * 50)

    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 40)

        # Pre-check for competitors
        has_competitor, competitor = check_competitor_mention(question)
        if has_competitor:
            print(f"BLOCKED: Cannot process queries about competitor brands ({competitor})")
            continue

        try:
            result = generate_sql_query(question)
            print(format_query_result(result))
        except Exception as e:
            print(f"Error: {e}")
