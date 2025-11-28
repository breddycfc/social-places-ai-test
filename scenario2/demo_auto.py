"""
Social Places AI Engineer Test - Scenario 2
Automated Demo Script

Author: Branden Reddy

Run this script to see all features in action without the web interface.
Usage: python demo_auto.py YOUR_API_KEY
"""

import os
import sys

# Set API key from command line
if len(sys.argv) > 1:
    os.environ["OPENAI_API_KEY"] = sys.argv[1]
else:
    print("Usage: python demo_auto.py YOUR_API_KEY")
    print("Or set OPENAI_API_KEY environment variable")
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit(1)

from database_setup import create_database, generate_sample_data
from query_generator import generate_sql_query, check_competitor_mention, validate_sql_safety, format_query_result
from query_executor import execute_with_analysis, format_result_as_table, format_explain_output


def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    print_section("SCENARIO 2: TEXT-TO-SQL REPORTING TOOL")
    print("Author: Branden Reddy")
    print("This demo shows all the features of the SQL query system.")

    # Setup database
    print_section("1. DATABASE SETUP")
    print("Creating SQLite database with sample review data...")
    conn = create_database("reviews.db")
    generate_sample_data(conn, num_reviews=5000)
    conn.close()
    print("Database ready with 5000 reviews across 10 Cape Town stores.")

    # Test Question 1: Bottom 5 stores
    print_section("2. TEST: Bottom 5 Stores by Rating")
    question1 = "Which 5 stores have the lowest average rating?"
    print(f"Question: {question1}")

    result1 = generate_sql_query(question1)
    print(f"\n{format_query_result(result1)}")

    if not result1['is_blocked'] and result1['sql_query']:
        exec_result = execute_with_analysis(result1['sql_query'])
        print(f"\nRESULTS:")
        print(format_result_as_table(exec_result))

    # Test Question 2: Service breakdown
    print_section("3. TEST: Service Sentiment Breakdown")
    question2 = "Give me a breakdown of service sentiment across all stores"
    print(f"Question: {question2}")

    result2 = generate_sql_query(question2)
    print(f"\n{format_query_result(result2)}")

    if not result2['is_blocked'] and result2['sql_query']:
        exec_result = execute_with_analysis(result2['sql_query'])
        print(f"\nRESULTS:")
        print(format_result_as_table(exec_result))

    # Test Question 3: Competitor guardrail
    print_section("4. TEST: Competitor Guardrail")
    question3 = "How does Social Places compare to KFC?"
    print(f"Question: {question3}")

    has_competitor, competitor = check_competitor_mention(question3)
    if has_competitor:
        print(f"\nBLOCKED by pre-filter: Competitor brand detected ({competitor})")
        print("The system does not process queries about competitor restaurants.")
    else:
        result3 = generate_sql_query(question3)
        print(f"\n{format_query_result(result3)}")

    # Test Question 4: Ambiguous question
    print_section("5. TEST: Ambiguous Question Handling")
    question4 = "Show me reviews"
    print(f"Question: {question4}")

    result4 = generate_sql_query(question4)
    print(f"\n{format_query_result(result4)}")

    if not result4['is_blocked'] and result4['sql_query']:
        exec_result = execute_with_analysis(result4['sql_query'])
        print(f"\nRESULTS (limited):")
        print(format_result_as_table(exec_result, max_rows=5))

    # Test SQL Safety
    print_section("6. TEST: SQL Safety Guardrails")
    dangerous_queries = [
        "DELETE FROM reviews WHERE id = 1",
        "DROP TABLE reviews",
        "UPDATE reviews SET rating = 5"
    ]

    for sql in dangerous_queries:
        is_safe, reason = validate_sql_safety(sql)
        status = "SAFE" if is_safe else "BLOCKED"
        print(f"{status}: {sql[:40]}...")
        if not is_safe:
            print(f"  Reason: {reason}")

    # Test Performance Analysis
    print_section("7. TEST: EXPLAIN Performance Analysis")
    test_sql = """
    SELECT r.store_name, COUNT(*) as negative_count
    FROM reviews r
    JOIN review_categories rc ON r.id = rc.review_id
    WHERE rc.sentiment = 'Negative'
    GROUP BY r.store_name
    ORDER BY negative_count DESC
    """
    print(f"Analyzing query performance...")

    exec_result = execute_with_analysis(test_sql)
    print(format_explain_output(exec_result))
    print(f"\nActual execution: {exec_result.execution_time_ms}ms for {exec_result.row_count} rows")

    # Summary
    print_section("DEMO COMPLETE")
    print("All Scenario 2 features demonstrated:")
    print("  Text-to-SQL query generation")
    print("  Competitor brand guardrails")
    print("  SQL safety validation")
    print("  Ambiguous question handling")
    print("  EXPLAIN performance analysis")
    print("  Query execution with timeout protection")


if __name__ == "__main__":
    main()
