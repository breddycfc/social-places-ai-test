"""
Social Places AI Engineer Test - Scenario 2
Query Executor with Performance Analysis
Author: Branden Reddy
"""

import sqlite3
import time
from dataclasses import dataclass


@dataclass
class QueryResult:
    success: bool
    data: list
    columns: list
    row_count: int
    execution_time_ms: float
    error_message: str = ""
    explain_plan: list = None
    performance_notes: list = None


def execute_query(sql: str, db_path: str = "reviews.db", timeout_seconds: int = 120) -> QueryResult:
    try:
        conn = sqlite3.connect(db_path, timeout=timeout_seconds)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        start_time = time.time()
        cursor.execute(sql)
        rows = cursor.fetchall()
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000

        columns = [description[0] for description in cursor.description] if cursor.description else []
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
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
        plan = cursor.fetchall()

        conn.close()

        notes = analyze_query_plan(plan, sql)

        return plan, notes

    except Exception as e:
        return [], [f"Could not analyze query: {str(e)}"]


def analyze_query_plan(plan: list, sql: str) -> list:
    notes = []
    plan_text = " ".join([str(row) for row in plan]).upper()

    if "SCAN TABLE" in plan_text and "USING INDEX" not in plan_text:
        notes.append("Full table scan detected. Consider adding WHERE clauses or using indexed columns.")

    if "USING COVERING INDEX" in plan_text:
        notes.append("Query uses covering index efficiently.")

    if "TEMP" in plan_text or "TEMPORARY" in plan_text:
        notes.append("Query creates temporary tables. May be slow on large datasets.")

    if "ORDER BY" in sql.upper() and "USING INDEX" not in plan_text:
        notes.append("Sorting without index. Consider indexing the ORDER BY column.")

    scan_count = plan_text.count("SCAN TABLE")
    if scan_count > 1:
        notes.append(f"Multiple table scans detected ({scan_count}). Ensure proper indexes on join columns.")

    if not notes:
        notes.append("Query plan looks efficient.")

    return notes


def execute_with_analysis(sql: str, db_path: str = "reviews.db", timeout_seconds: int = 120) -> QueryResult:
    explain_plan, performance_notes = get_explain_plan(sql, db_path)

    result = execute_query(sql, db_path, timeout_seconds)

    result.explain_plan = explain_plan
    result.performance_notes = performance_notes

    if result.success:
        if result.execution_time_ms > 5000:
            result.performance_notes.append(f"Query took {result.execution_time_ms:.0f}ms. Consider optimization for production.")
        elif result.execution_time_ms > 1000:
            result.performance_notes.append(f"Query took {result.execution_time_ms:.0f}ms. Acceptable but monitor on larger datasets.")

    return result


def format_result_as_table(result: QueryResult, max_rows: int = 20) -> str:
    if not result.success:
        return f"ERROR: {result.error_message}"

    if not result.data:
        return "No results found."

    output = []

    output.append(" | ".join(result.columns))
    output.append("-" * len(output[0]))

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
