Social Places AI Engineer Test
Scenario 2 Evaluation Guide

Author: Branden Reddy
Date: November 2024

This document walks you through my solution for Scenario 2 and shows you how to test each requirement. Same as Scenario 1, I have included both a web interface and command line options for testing.



QUICK START

To test the solution with the web interface:

1. Open a terminal and navigate to the scenario2 folder
2. Install the dependencies: pip install -r requirements.txt
3. Run the web app: streamlit run app.py
4. Open your browser to http://localhost:8501
5. Enter your OpenAI API key in the sidebar
6. Click "Reset Database" in the sidebar to create the sample data
7. Use the tabs to test each feature

The web interface has four tabs: Ask Questions (natural language), Query Builder (direct SQL), Performance Analysis (EXPLAIN output), and Guardrails Demo (test the safety filters).

If you prefer command line testing, run: python demo_auto.py YOUR_API_KEY
This will run through all features automatically and print results to the terminal.



DELIVERABLE CHECKLIST

Below is each requirement from the scenario brief with where to find my solution and how to test it.


1. What provider and model would you use?

My Answer: OpenAI GPT-4o-mini

Where to Find It: README.md under "PROVIDER AND MODEL SELECTION"

Reasoning:
Same model as Scenario 1 for consistency across the application. The structured output support is crucial for getting clean SQL queries without parsing issues. Claude would also work well here, particularly for understanding nuanced questions, but GPT-4o-mini's structured output made the implementation cleaner.


2. Outline steps using various tools

Where to Find It: README.md under "HOW THE TEXT-TO-SQL SYSTEM WORKS"

The system uses a four-step pipeline:
Pre-screening catches competitor mentions before any LLM call
Query generation produces SQL with structured JSON output
Safety validation blocks dangerous SQL operations
Execution with EXPLAIN provides performance insights


3. Examples of tools and reasons

The tools involved are:

OpenAI API with response_format for guaranteed structured output
SQLite for the database (would be PostgreSQL in production)
EXPLAIN QUERY PLAN for performance analysis
Regex patterns for safety validation
Streamlit for the demo interface

Each tool was chosen for specific reasons documented in the README.


4. Prompts used

Where to Find It: query_generator.py lines 55-140

The prompt has three main components:

DATABASE_SCHEMA (lines 66-105): Full schema definition including all tables, columns, relationships, and available values. This gives the model complete context about what data exists.

SYSTEM_PROMPT (lines 107-140): Rules for query generation including only SELECT statements, proper JOINs, guardrail instructions, and examples of good SQL patterns.

User Message Template: Combines the schema with the user's question in a clear format.


5. Handle the example questions

Bottom 5 stores with lowest average rating:
The model generates proper GROUP BY with ORDER BY ASC and LIMIT 5. Test this using the "Bottom 5 Stores" button in the web interface.

5-point overview of service-related issues:
The model joins review_categories table and aggregates by sentiment. Test using the "Service Breakdown" button.

Competitor comparison (must be blocked):
Pre-screening catches brand names like KFC, Nando's, Spur before any LLM call. Test using the "Competitor Query (blocked)" button or the Guardrails Demo tab.


6. Constraints

Read-only database:
Safety validation in query_generator.py (lines 180-200) blocks any non-SELECT SQL. Additional regex catches INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, EXEC, GRANT, REVOKE.

Query timeout 1-2 minutes:
query_executor.py line 27 sets configurable timeout (default 120 seconds). For large datasets this prevents runaway queries from consuming resources.

How to Test: In the Guardrails Demo tab, enter dangerous SQL like "DELETE FROM reviews" and see it get blocked.


7. Evaluation criteria

SQL correctness:
The model consistently generates syntactically correct SQL. The structured output format prevents malformed queries.

Performance (EXPLAIN):
Use the Performance Analysis tab to see query plans and recommendations. The system identifies full table scans and missing index usage.

Ambiguous questions:
Try vague questions like "Show me reviews" in the Ask Questions tab. The system flags ambiguity, provides clarification suggestions, and still returns a best-guess result.

Graceful degradation:
When queries fail or time out, users get clear error messages rather than crashes.

Prompt manipulation:
The pre-screening and safety validation layers provide defense in depth. Even if a user tried to inject malicious instructions, the output validation would catch dangerous SQL.

Guardrails:
Both competitor filtering and SQL safety validation are testable in the Guardrails Demo tab.



FILE OVERVIEW

Here is what each file does:

database_setup.py
Creates SQLite database with Cape Town store locations and sample review data.

query_generator.py
Core text-to-SQL engine with prompt, schema, guardrails, and structured output.

query_executor.py
Executes queries with timeout protection and EXPLAIN analysis.

app.py
Web interface with four demo tabs.

demo_auto.py
Command line demo that runs through all features.

README.md
Full technical documentation.

requirements.txt
Python dependencies (openai, streamlit, pandas).



CAPE TOWN STORES IN THE DATABASE

I used real Cape Town locations for the sample data:

V&A Waterfront
Canal Walk
Cavendish Square
Century City
Stellenbosch
Camps Bay
Sea Point
Claremont
Tyger Valley
Somerset West

Canal Walk and Tyger Valley have slightly worse ratings in the sample data to create testable patterns. You should see these appear in "bottom stores" queries.



COST INFORMATION

Running the full demo costs approximately R0.05 in API usage.

Each query conversion uses about 1200 tokens.

Monthly projections at R0.003 per query:
1000 queries: R3
10000 queries: R30
100000 queries: R300



AI ASSISTANCE DISCLOSURE

I used Claude Code to assist with:

The EXPLAIN plan parsing logic that identifies performance issues from SQLite's output format

The regex patterns for SQL safety validation to ensure proper keyword detection

The core system design, database schema, prompt engineering, and text-to-SQL approach are my own work. I can explain and defend any part of this solution.



QUESTIONS

Happy to walk through any part of the implementation during the interview. The web interface makes it easy to see everything in action, but I can also step through the code if you prefer.
