"""
Social Places AI Engineer Test - Scenario 2
Query Executor with Performance Analysis

Author: Branden Reddy

This module executes SQL queries and provides performance analysis using EXPLAIN.
"""

import sqlite3
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Container for query execution results."""
    success: bool
    data: list
    columns: list
    row_count: int
    execution_time_ms: float
    error_message: str = ""
    explain_plan: list = None
    performance_notes: list = None


def execute_query(
    sql: str,
    db_path: str = "reviews.db",
    timeout_seconds: int = 120
) -> QueryResult:
    """
    Execute a SQL query with timeout protection.

    Timeout default is 2 minutes as per requirements for large datasets.
    """
    try:
        conn = sqlite3.connect(db_path, timeout=timeout_seconds)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Time the execution
        start_time = time.time()
        cursor.execute(sql)
        rows = cursor.fetchall()
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to ms

        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []

        # Convert rows to list of dicts
        data = [dict(row) for row in rows]

        conn.close()

        return QueryResult(
            success=True,
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time_ms=round(execution_time, 2)
        )

    except sqlite3.OperationalError as e:
        if "timeout" in str(e).lower():
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                execution_time_ms=timeout_seconds * 1000,
                error_message=f"Query timed out after {timeout_seconds} seconds"
            )
        return QueryResult(
            success=False,
            data=[],
            columns=[],
            row_count=0,
            execution_time_ms=0,
            error_message=str(e)
        )

    except Exception as e:
        return QueryResult(
            success=False,
            data=[],
            columns=[],
            row_count=0,
            execution_time_ms=0,
            error_message=str(e)
        )


def get_explain_plan(sql: str, db_path: str = "reviews.db") -> tuple[list, list]:
    """
    Get the EXPLAIN QUERY PLAN for a SQL statement.
    Returns (explain_output, performance_notes).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get EXPLAIN QUERY PLAN
        cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
        plan = cursor.fetchall()

        conn.close()

        # Parse the plan for performance notes
        notes = analyze_query_plan(plan, sql)

        return plan, notes

    except Exception as e:
        return [], [f"Could not analyze query: {str(e)}"]


def analyze_query_plan(plan: list, sql: str) -> list:
    """
    Analyze the query plan and provide performance recommendations.
    """
    notes = []
    plan_text = " ".join([str(row) for row in plan]).upper()

    # Check for table scans (no index usage)
    if "SCAN TABLE" in plan_text and "USING INDEX" not in plan_text:
        notes.append("Full table scan detected. Consider adding WHERE clauses or using indexed columns.")

    # Check for covering index usage (good)
    if "USING COVERING INDEX" in plan_text:
        notes.append("Query uses covering index efficiently.")

    # Check for temporary tables (can be slow)
    if "TEMP" in plan_text or "TEMPORARY" in plan_text:
        notes.append("Query creates temporary tables. May be slow on large datasets.")

    # Check for sorting without index
    if "ORDER BY" in sql.upper() and "USING INDEX" not in plan_text:
        notes.append("Sorting without index. Consider indexing the ORDER BY column.")

    # Check for multiple table scans
    scan_count = plan_text.count("SCAN TABLE")
    if scan_count > 1:
        notes.append(f"Multiple table scans detected ({scan_count}). Ensure proper indexes on join columns.")

    # If query looks good
    if not notes:
        notes.append("Query plan looks efficient.")

    return notes


def execute_with_analysis(
    sql: str,
    db_path: str = "reviews.db",
    timeout_seconds: int = 120
) -> QueryResult:
    """
    Execute query and include EXPLAIN analysis in the result.
    """
    # First get the explain plan
    explain_plan, performance_notes = get_explain_plan(sql, db_path)

    # Then execute the actual query
    result = execute_query(sql, db_path, timeout_seconds)

    # Add the analysis to the result
    result.explain_plan = explain_plan
    result.performance_notes = performance_notes

    # Add timing-based notes
    if result.success:
        if result.execution_time_ms > 5000:
            result.performance_notes.append(f"Query took {result.execution_time_ms:.0f}ms. Consider optimization for production.")
        elif result.execution_time_ms > 1000:
            result.performance_notes.append(f"Query took {result.execution_time_ms:.0f}ms. Acceptable but monitor on larger datasets.")

    return result


def format_result_as_table(result: QueryResult, max_rows: int = 20) -> str:
    """Format query results as a readable text table."""
    if not result.success:
        return f"ERROR: {result.error_message}"

    if not result.data:
        return "No results found."

    output = []

    # Header
    output.append(" | ".join(result.columns))
    output.append("-" * len(output[0]))

    # Data rows (limited)
    for row in result.data[:max_rows]:
        values = [str(row.get(col, ""))[:30] for col in result.columns]
        output.append(" | ".join(values))

    if result.row_count > max_rows:
        output.append(f"... and {result.row_count - max_rows} more rows")

    output.append("")
    output.append(f"Total rows: {result.row_count}")
    output.append(f"Execution time: {result.execution_time_ms}ms")

    return "\n".join(output)


def format_explain_output(result: QueryResult) -> str:
    """Format the EXPLAIN analysis for display."""
    output = []

    output.append("QUERY PLAN:")
    if result.explain_plan:
        for row in result.explain_plan:
            output.append(f"  {row}")
    else:
        output.append("  No plan available")

    output.append("")
    output.append("PERFORMANCE NOTES:")
    if result.performance_notes:
        for note in result.performance_notes:
            output.append(f"  {note}")

    return "\n".join(output)


if __name__ == "__main__":
    # Test with sample queries
    test_queries = [
        "SELECT store_name, COUNT(*) as count FROM reviews GROUP BY store_name ORDER BY count DESC LIMIT 5",
        "SELECT AVG(rating) as avg_rating FROM reviews WHERE store_name = 'Social Places Canal Walk'",
        "SELECT * FROM reviews LIMIT 3"
    ]

    print("QUERY EXECUTOR TEST")
    print("=" * 50)

    for sql in test_queries:
        print(f"\nSQL: {sql[:60]}...")
        print("-" * 40)

        result = execute_with_analysis(sql)

        print(format_result_as_table(result))
        print()
        print(format_explain_output(result))
