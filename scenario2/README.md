Social Places AI Engineer Test
Scenario 2: Text-to-SQL Review Reporting Tool

Author: Branden Reddy
Date: November 2024



OVERVIEW

This is my solution for Scenario 2 of the Social Places AI Engineer test. The system converts natural language questions into SQL queries for analysing review data. Think of it as a way for non-technical team members to pull reports without writing SQL themselves.

The database is populated with sample data from 10 Cape Town stores, from the V&A Waterfront down to Somerset West. Each store has reviews across Google, Facebook, and TripAdvisor with various ratings and sentiment categories.



PROVIDER AND MODEL SELECTION

I went with OpenAI GPT-4o-mini again for the same reasons as Scenario 1:

Native JSON schema support means the model returns properly structured responses every time. No parsing errors, no retries needed.

The cost works out to roughly R0.003 per query at current exchange rates. For a reporting tool that might run a few hundred queries per month, we are talking about a few rand total.

Response time is consistently under 2 seconds which feels instant for a reporting interface.

I considered Claude for this task as well. Claude is excellent at understanding nuanced questions and would handle ambiguous queries particularly well. However, the structured output support in GPT-4o-mini made implementation cleaner. For a production system handling complex natural language queries, Claude would be worth benchmarking against.



HOW THE TEXT-TO-SQL SYSTEM WORKS

The process has four steps:

Step 1: Pre-screening
Before we even call the LLM, the system checks for competitor brand mentions. If someone asks "How do we compare to Nando's?" it gets blocked immediately. No tokens wasted, no chance of the model generating anything inappropriate.

Step 2: Query Generation
The LLM receives the database schema and the user's question. The system prompt establishes rules: only SELECT statements, proper JOINs, appropriate aggregations. The model returns a structured response with the SQL query, an explanation, and flags for any issues.

Step 3: Safety Validation
Even though the LLM is instructed to only generate SELECT statements, we validate the output with regex patterns. This catches any accidental or malicious generation of INSERT, UPDATE, DELETE, DROP, or other dangerous commands.

Step 4: Execution with EXPLAIN
The query runs against SQLite with a configurable timeout (default 2 minutes for large datasets). We also capture the EXPLAIN QUERY PLAN output to identify performance issues like full table scans or missing indexes.



HANDLING THE REQUIRED QUESTIONS

The brief specified three questions the system must handle. Here is how each one works:

"Bottom 5 stores with lowest average rating"

The system generates:
SELECT store_name, AVG(rating) as avg_rating, COUNT(*) as review_count
FROM reviews
GROUP BY store_name
ORDER BY avg_rating ASC
LIMIT 5

This is a straightforward aggregation. The model understands "bottom" means ORDER BY ASC and "5" becomes LIMIT 5.

"5-point overview of service-related issues"

For this one, the system joins the reviews table with review_categories:
SELECT rc.sentiment, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM reviews r
JOIN review_categories rc ON r.id = rc.review_id
WHERE rc.category_name = 'Service'
GROUP BY rc.sentiment
ORDER BY count DESC

The "5-point" in the question typically gets interpreted as wanting a breakdown by key metrics, which the model handles by grouping and calculating percentages.

"Compare to competitor brand"

This gets blocked before reaching the LLM. The pre-screening function catches mentions of McDonald's, KFC, Spur, Nando's, Wimpy, Steers, and other restaurant chains. The user sees a clear message explaining why the query cannot be processed.



GUARDRAILS IMPLEMENTED

Competitor Filtering
A list of competitor brand names gets checked against the user's question using simple string matching. This is intentionally done before the LLM call because:
It saves API costs on queries we know will be blocked
It gives immediate feedback to the user
It removes any chance of the model being "tricked" into discussing competitors

SQL Safety Validation
The system uses regex to catch dangerous SQL keywords. Even if someone managed to trick the LLM into generating a DELETE statement, the safety layer would block it before execution.

Read-only Database Connection
SQLite connections are configured for read-only access. Even if a destructive query somehow made it through both layers, the database itself would reject it.



HANDLING AMBIGUOUS QUESTIONS

When a question like "Show me reviews" comes in without specifics, the system:

Sets is_ambiguous to true in the response
Explains what clarification would help (which store? what time period? how many?)
Still generates a best-guess query, typically limiting to recent reviews with a reasonable row count

This approach means users get some output even with vague questions, rather than an error. The clarification message guides them to ask more specific questions next time.



QUERY OPTIMISATION WITH EXPLAIN

Every query execution captures the SQLite EXPLAIN QUERY PLAN output. The system analyses this for:

Full Table Scans: Flagged with a recommendation to add WHERE clauses
Missing Index Usage: Noted when ORDER BY or JOIN columns are not indexed
Temporary Tables: Warned about potential slowdown on large datasets

The database setup creates indexes on commonly queried columns (store_name, review_date, rating, platform) which helps most standard queries run efficiently.

For a production system with 10 million plus records, I would recommend:
Migrating to PostgreSQL for better query planning and parallel execution
Adding composite indexes based on actual query patterns
Implementing query result caching for frequently asked questions
Setting up read replicas if query load is high



PERFORMANCE CHARACTERISTICS

With the sample database of 5000 reviews:
Simple aggregations run in under 50ms
Complex JOINs with grouping complete in under 200ms
EXPLAIN analysis adds negligible overhead

For 10M+ records (production scale):
Properly indexed queries should stay under 2 seconds
Full table scans could hit the 2 minute timeout
The system would need pagination for large result sets



AI ASSISTANCE DISCLOSURE

I used Claude Code to assist with two specific parts of this solution:

The EXPLAIN plan parsing logic in query_executor.py. Claude helped identify which patterns in SQLite's explain output indicate performance issues and how to phrase the recommendations clearly.

The regex patterns for SQL safety validation. Claude helped ensure the patterns catch dangerous keywords while not blocking legitimate queries that might contain those words in string literals.

The overall system design, database schema, and text-to-SQL prompt engineering are my own work. I'm happy to walk through any part of the implementation during the interview.



FILES IN THIS SOLUTION

database_setup.py
Creates the SQLite database and generates sample review data. Includes Cape Town store locations and realistic review content.

query_generator.py
The text-to-SQL engine. Takes natural language questions, generates SQL, and handles guardrails.

query_executor.py
Runs queries with timeout protection and captures EXPLAIN output for performance analysis.

app.py
Streamlit web interface with tabs for asking questions, running direct SQL, analysing performance, and testing guardrails.

demo_auto.py
Command line demo that runs through all features automatically.



COST ESTIMATE

Each text-to-SQL conversion uses approximately 1200 tokens including the schema context.

Per query: R0.003
Monthly at 1000 queries: R3
Monthly at 10000 queries: R30

This is trivial compared to the value of giving non-technical team members direct access to review analytics.
