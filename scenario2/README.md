Social Places AI Engineer Test
Scenario 2: Text-to-SQL Review Reporting Tool

Author: Branden Reddy
Date: November 2024



OVERVIEW

This is my solution for Scenario 2 of the Social Places AI Engineer test. The system converts natural language questions into SQL queries for analysing review data. Think of it as a way for non-technical team members to pull reports without writing SQL themselves.

The database is populated with sample data from 10 Cape Town stores, from the V&A Waterfront down to Somerset West. Each store has reviews across Google, Facebook, and TripAdvisor with various ratings and sentiment categories.



PROVIDER AND MODEL SELECTION

I went with OpenAI GPT-4o-mini again for the same reasons as Scenario 1.

Native JSON schema support means the model returns properly structured responses every time. No parsing errors, no retries needed.

The cost works out to roughly R0.003 per query at current exchange rates. For a reporting tool that might run a few hundred queries per month, we are talking about a few rand total.

Response time is consistently under 2 seconds which feels instant for a reporting interface.

I considered Claude for this task as well. Claude is excellent at understanding nuanced questions and would handle ambiguous queries particularly well. However, the structured output support in GPT-4o-mini made implementation cleaner. For a production system handling complex natural language queries, Claude would be worth benchmarking against.



HOW THE TEXT-TO-SQL SYSTEM WORKS

The process has four steps.

Pre-screening happens first. Before we even call the LLM, the system checks for competitor brand mentions. If someone asks "How do we compare to Nando's?" it gets blocked immediately. No tokens wasted, no chance of the model generating anything inappropriate.

Query generation comes next. The LLM receives the database schema and the user's question. The system prompt establishes rules: only SELECT statements, proper JOINs, appropriate aggregations. The model returns a structured response with the SQL query, an explanation, and flags for any issues.

Safety validation follows. Even though the LLM is instructed to only generate SELECT statements, we validate the output with regex patterns. This catches any accidental or malicious generation of INSERT, UPDATE, DELETE, DROP, or other dangerous commands.

Finally, execution with EXPLAIN runs the query against SQLite with a configurable timeout (default 2 minutes for large datasets). We also capture the EXPLAIN QUERY PLAN output to identify performance issues like full table scans or missing indexes.



HANDLING THE REQUIRED QUESTIONS

The brief specified three questions the system must handle.

For "Bottom 5 stores with lowest average rating" the system generates a query that groups by store name, calculates the average rating, orders ascending, and limits to 5. The model understands "bottom" means ORDER BY ASC.

For "5-point overview of service-related issues" the system joins the reviews table with review_categories, filters for Service, and groups by sentiment. This gives a breakdown of positive, negative, and neutral service feedback.

For "Compare to competitor brand" the query gets blocked before reaching the LLM. The pre-screening function catches mentions of McDonald's, KFC, Spur, Nando's, Wimpy, Steers, and other restaurant chains. The user sees a clear message explaining why the query cannot be processed.



GUARDRAILS IMPLEMENTED

Competitor filtering uses a list of competitor brand names checked against the user's question using simple string matching. This is intentionally done before the LLM call because it saves API costs on queries we know will be blocked, gives immediate feedback to the user, and removes any chance of the model being "tricked" into discussing competitors.

SQL safety validation uses regex to catch dangerous SQL keywords. Even if someone managed to trick the LLM into generating a DELETE statement, the safety layer would block it before execution.

Read-only database connection is configured in SQLite. Even if a destructive query somehow made it through both layers, the database itself would reject it.



HANDLING AMBIGUOUS QUESTIONS

When a question like "Show me reviews" comes in without specifics, the system sets is_ambiguous to true in the response, explains what clarification would help (which store? what time period? how many?), and still generates a best-guess query, typically limiting to recent reviews with a reasonable row count.

This approach means users get some output even with vague questions, rather than an error. The clarification message guides them to ask more specific questions next time.



QUERY OPTIMISATION WITH EXPLAIN

Every query execution captures the SQLite EXPLAIN QUERY PLAN output. The system analyses this for full table scans (flagged with a recommendation to add WHERE clauses), missing index usage (noted when ORDER BY or JOIN columns are not indexed), and temporary tables (warned about potential slowdown on large datasets).

The database setup creates indexes on commonly queried columns like store_name, review_date, rating, and platform, which helps most standard queries run efficiently.

For a production system with 10 million plus records, I would recommend migrating to PostgreSQL for better query planning and parallel execution, adding composite indexes based on actual query patterns, implementing query result caching for frequently asked questions, and setting up read replicas if query load is high.



PERFORMANCE CHARACTERISTICS

With the sample database of 5000 reviews, simple aggregations run in under 50ms, complex JOINs with grouping complete in under 200ms, and EXPLAIN analysis adds negligible overhead.

For 10M+ records at production scale, properly indexed queries should stay under 2 seconds, full table scans could hit the 2 minute timeout, and the system would need pagination for large result sets.



AI ASSISTANCE DISCLOSURE

I used Claude Code to assist with two specific parts of this solution.

The EXPLAIN plan parsing logic in query_executor.py. Claude helped identify which patterns in SQLite's explain output indicate performance issues and how to phrase the recommendations clearly.

The regex patterns for SQL safety validation. Claude helped ensure the patterns catch dangerous keywords while not blocking legitimate queries that might contain those words in string literals.

The overall system design, database schema, and text-to-SQL prompt engineering are my own work. Happy to walk through any part of the implementation during the interview.



FILES IN THIS SOLUTION

database_setup.py creates the SQLite database and generates sample review data. Includes Cape Town store locations and realistic review content.

query_generator.py is the text-to-SQL engine. Takes natural language questions, generates SQL, and handles guardrails.

query_executor.py runs queries with timeout protection and captures EXPLAIN output for performance analysis.

app.py is the Streamlit web interface with tabs for asking questions, running direct SQL, analysing performance, and testing guardrails.

demo_auto.py is the command line demo that runs through all features automatically.



COST ESTIMATE

Each text-to-SQL conversion uses approximately 1200 tokens including the schema context.

Per query costs about R0.003. Monthly at 1000 queries would be R3. Monthly at 10000 queries would be R30.

This is trivial compared to the value of giving non-technical team members direct access to review analytics.
