"""
Social Places Review Reporting Tool - Web Interface
Author: Branden Reddy
"""

import streamlit as st
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Review Reporting Tool",
    page_icon="📊",
    layout="wide"
)

st.title("Social Places - Review Reporting Tool")
st.markdown("Scenario 2: Natural Language SQL Query System")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("API Key set")

    st.markdown("---")
    st.markdown("**Model:** GPT-4o-mini")
    st.markdown("**Database:** SQLite (5000 reviews)")
    st.markdown("**Timeout:** 2 minutes max")

    # Database setup button
    st.markdown("---")
    if st.button("Reset Database"):
        from database_setup import create_database, generate_sample_data
        conn = create_database("reviews.db")
        generate_sample_data(conn, num_reviews=5000)
        conn.close()
        st.success("Database reset with 5000 reviews")

# Check if database exists
db_exists = os.path.exists("reviews.db")
if not db_exists:
    st.warning("Database not found. Click 'Reset Database' in the sidebar to create it.")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Ask Questions", "Query Builder", "Performance Analysis", "Guardrails Demo"])

# Tab 1: Natural Language Questions
with tab1:
    st.header("Ask Questions About Reviews")
    st.markdown("Type your question in plain English and get SQL results.")

    question = st.text_area(
        "Your Question",
        value="Which 5 stores have the lowest average rating?",
        height=100
    )

    # Example questions
    st.markdown("**Example Questions:**")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Bottom 5 Stores"):
            question = "Which 5 stores have the lowest average rating?"
            st.session_state.question = question
        if st.button("Service Breakdown"):
            question = "Give me a 5-point breakdown of service-related negative reviews"
            st.session_state.question = question

    with col2:
        if st.button("Platform Stats"):
            question = "What's the average rating by platform?"
            st.session_state.question = question
        if st.button("Competitor Query (blocked)"):
            question = "How does Social Places compare to KFC?"
            st.session_state.question = question

    if st.button("Run Query", type="primary"):
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar")
        elif not db_exists:
            st.error("Please create the database first using 'Reset Database' in the sidebar")
        else:
            try:
                from query_generator import generate_sql_query, check_competitor_mention, validate_sql_safety
                from query_executor import execute_with_analysis, format_result_as_table

                # Pre-check for competitors
                has_competitor, competitor = check_competitor_mention(question)

                if has_competitor:
                    st.error(f"BLOCKED: Cannot process queries about competitor brands ({competitor})")
                    st.info("This guardrail prevents queries that mention other restaurant brands.")
                else:
                    with st.spinner("Generating SQL query..."):
                        result = generate_sql_query(question)

                    # Show interpretation
                    st.subheader("Query Interpretation")
                    st.info(f"**Understood:** {result['understood_question']}")

                    if result['is_blocked']:
                        st.error(f"**Blocked:** {result['block_reason']}")
                    else:
                        if result['is_ambiguous']:
                            st.warning(f"**Clarification:** {result['clarification_needed']}")
                            st.markdown("Proceeding with best interpretation...")

                        # Show generated SQL
                        st.subheader("Generated SQL")
                        st.code(result['sql_query'], language="sql")
                        st.markdown(f"**Explanation:** {result['query_explanation']}")

                        # Validate SQL safety
                        is_safe, reason = validate_sql_safety(result['sql_query'])

                        if not is_safe:
                            st.error(f"Safety check failed: {reason}")
                        else:
                            # Execute the query
                            with st.spinner("Executing query..."):
                                exec_result = execute_with_analysis(result['sql_query'])

                            st.subheader("Results")

                            if exec_result.success:
                                # Show as dataframe if we have results
                                if exec_result.data:
                                    import pandas as pd
                                    df = pd.DataFrame(exec_result.data)
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    st.info("Query returned no results")

                                st.markdown(f"**Rows returned:** {exec_result.row_count}")
                                st.markdown(f"**Execution time:** {exec_result.execution_time_ms}ms")
                            else:
                                st.error(f"Query failed: {exec_result.error_message}")

                        # Token usage
                        st.markdown("---")
                        tokens = result["_metadata"]["tokens_used"]
                        st.caption(f"Tokens used: {tokens['total']} (Prompt: {tokens['prompt']}, Completion: {tokens['completion']})")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 2: Query Builder
with tab2:
    st.header("Direct SQL Query")
    st.markdown("Write and execute SQL queries directly. Only SELECT statements allowed.")

    custom_sql = st.text_area(
        "SQL Query",
        value="SELECT store_name, AVG(rating) as avg_rating, COUNT(*) as review_count\nFROM reviews\nGROUP BY store_name\nORDER BY avg_rating ASC\nLIMIT 10",
        height=150
    )

    if st.button("Execute SQL", type="primary"):
        if not db_exists:
            st.error("Please create the database first")
        else:
            try:
                from query_generator import validate_sql_safety
                from query_executor import execute_with_analysis

                # Safety check
                is_safe, reason = validate_sql_safety(custom_sql)

                if not is_safe:
                    st.error(f"Query blocked: {reason}")
                else:
                    with st.spinner("Executing..."):
                        result = execute_with_analysis(custom_sql)

                    if result.success:
                        if result.data:
                            import pandas as pd
                            df = pd.DataFrame(result.data)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No results")

                        st.markdown(f"**Execution time:** {result.execution_time_ms}ms")
                    else:
                        st.error(f"Error: {result.error_message}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 3: Performance Analysis
with tab3:
    st.header("Query Performance Analysis")
    st.markdown("See EXPLAIN output and performance recommendations for your queries.")

    perf_sql = st.text_area(
        "SQL Query to Analyze",
        value="SELECT r.store_name, COUNT(*) as negative_count\nFROM reviews r\nJOIN review_categories rc ON r.id = rc.review_id\nWHERE rc.sentiment = 'Negative'\nGROUP BY r.store_name\nORDER BY negative_count DESC",
        height=150
    )

    if st.button("Analyze Performance", type="primary"):
        if not db_exists:
            st.error("Please create the database first")
        else:
            try:
                from query_executor import execute_with_analysis

                with st.spinner("Analyzing..."):
                    result = execute_with_analysis(perf_sql)

                st.subheader("EXPLAIN Query Plan")
                if result.explain_plan:
                    for row in result.explain_plan:
                        st.code(str(row))
                else:
                    st.info("No plan available")

                st.subheader("Performance Notes")
                if result.performance_notes:
                    for note in result.performance_notes:
                        if "efficient" in note.lower() or "good" in note.lower():
                            st.success(note)
                        elif "scan" in note.lower() or "slow" in note.lower():
                            st.warning(note)
                        else:
                            st.info(note)

                if result.success:
                    st.markdown(f"**Actual execution time:** {result.execution_time_ms}ms")
                    st.markdown(f"**Rows returned:** {result.row_count}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 4: Guardrails Demo
with tab4:
    st.header("Guardrails Demonstration")
    st.markdown("This system blocks queries about competitor brands and dangerous SQL operations.")

    st.subheader("Competitor Brand Filter")
    competitor_test = st.text_input(
        "Test a question",
        value="How does Social Places compare to Nando's?"
    )

    if st.button("Check Competitor Filter"):
        from query_generator import check_competitor_mention

        has_competitor, competitor = check_competitor_mention(competitor_test)

        if has_competitor:
            st.error(f"BLOCKED - Competitor detected: {competitor}")
            st.info("The system blocks any queries that mention competitor restaurant brands.")
        else:
            st.success("PASSED - No competitor brands detected")

    st.markdown("---")
    st.subheader("SQL Safety Filter")

    sql_test = st.text_input(
        "Test SQL statement",
        value="DELETE FROM reviews WHERE id = 1"
    )

    if st.button("Check SQL Safety"):
        from query_generator import validate_sql_safety

        is_safe, reason = validate_sql_safety(sql_test)

        if is_safe:
            st.success("PASSED - Query is safe to execute")
        else:
            st.error(f"BLOCKED - {reason}")

    st.markdown("---")
    st.markdown("**Blocked Keywords:**")
    st.code("INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, EXEC, GRANT, REVOKE")

    st.markdown("**Blocked Competitors:**")
    st.code("McDonald's, KFC, Spur, Nando's, Wimpy, Steers, Burger King, Ocean Basket, Pizza Hut, Domino's, etc.")

# Footer
st.markdown("---")
st.markdown("**Author:** Branden Reddy | **AI Assistance:** Claude Code helped with EXPLAIN plan parsing")
