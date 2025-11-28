Social Places AI Engineer Test
Scenario 1 Evaluation Guide

Author: Branden Reddy
Date: November 2024

This document walks you through my solution for Scenario 1 and shows you how to test each requirement. I have included both a web interface and command line options for testing.



QUICK START

To test the solution with the web interface:

1. Clone this repository
2. Open a terminal and navigate to the scenario1 folder
3. Install the dependencies: pip install -r requirements.txt
4. Run the web app: streamlit run app.py
5. Open your browser to http://localhost:8501
6. Enter your OpenAI API key in the sidebar
7. Use the tabs to test each feature

The web interface has four tabs covering all the deliverables: basic response generation, RAG demo, security demo, and guardrails demo.

If you prefer command line testing, run: python demo_auto.py
This will run through all features automatically and print results to the terminal.



DELIVERABLE CHECKLIST

Below is each requirement from the scenario brief with where to find my solution and how to test it.


1. What provider and model would you use?

My Answer: OpenAI GPT-4o-mini

Where to Find It: README.md under "PROVIDER AND MODEL SELECTION"

Reasoning:
I chose GPT-4o-mini because it has native JSON schema support through the response_format parameter. This guarantees structured output every time without needing to parse or retry. The cost is $0.15 per million input tokens and $0.60 per million output tokens which works out to about $0.00016 per response. Speed is consistently 2-3 seconds which is well under the 20 second constraint.

I considered Claude 3.5 Haiku and Gemini 1.5 Flash as alternatives. Claude is similarly capable but more expensive and requires more prompt engineering for structured output. Gemini is cheaper but the structured output feature is less mature.


2. Construct a prompt for providing information in a structured output

Where to Find It: review_responder.py lines 17-108

The prompt has three parts:

The JSON Schema (lines 17-74) defines exactly what structure the response should have. It includes sentiment analysis with confidence and reasoning, detected tone, five response sections (salutation, introduction, body, conclusion, closing), and whether a support link was included.

The System Prompt (lines 77-108) sets up the AI's role and gives it brand voice guidelines. It includes instructions for tone adaptation (casual, formal, friendly), when to include support links based on sentiment, and a critical rule to trust the comment over the rating if they contradict.

The User Message Template is in the generate_review_response function and contains the review details formatted for the model.

How to Test: Use the web interface "Generate Response" tab or run python demo_auto.py


3. Provide some results from the prompt constructed

Where to Find It: result_review_1.json, result_review_2.json, result_review_3.json

These files contain actual outputs from the system for the three example reviews:

Review 1 (John Smith, 3 stars, mixed feedback): The system detected mixed sentiment with 85% confidence and used a formal tone. It included the support link because the sentiment was not fully positive.

Review 2 (Jane Doe, 5 stars, positive): The system detected positive sentiment with 95% confidence and used a friendly tone to match her casual writing style with the smiley face. No support link was included.

Review 3 (Alex Stone, 5 stars, cockroach complaint): This is the important edge case. Despite the 5 star rating, the system correctly detected negative sentiment with 95% confidence. The reasoning stated that the comment indicates a serious issue with cleanliness. It used a formal tone and included the support link.

How to Test: In the web interface, use the "Cockroach (Edge Case)" button to see this in action. The system should detect negative sentiment despite the high rating.


4. How would you include additional data like FAQ

Where to Find It: review_responder_with_rag.py

I implemented a RAG (Retrieval Augmented Generation) system that pulls in relevant FAQ information before generating a response.

There are two retrieval methods:

Keyword Matching (free and fast): The function retrieve_relevant_faqs_keyword looks for specific words in the review and matches them to FAQ categories. For example, "cockroach" matches the hygiene FAQ.

Semantic Search with Embeddings (more accurate, small cost): The function retrieve_relevant_faqs uses OpenAI's embedding model to find conceptually similar content even when exact keywords are not used.

When relevant FAQs are found, they get added to the prompt as context. The model then naturally incorporates this information into the response. For the cockroach review, the system retrieves the hygiene FAQ and mentions "strict hygiene protocols with daily health inspections and regular pest control."

How to Test: Use the web interface "RAG Demo" tab. Enter different reviews and see which FAQs get retrieved.


5. Alternative methods including fine-tuning

Where to Find It: README.md under "ALTERNATIVE APPROACHES"

Fine-tuning would make sense for deployments processing more than 50,000 responses per month. You would need 50 to 200 good training examples of review and ideal response pairs. The break-even point is around 40,000 responses where the fine-tuning cost ($25) gets offset by cheaper per-request costs from using a smaller model.

A multi-model pipeline could route simple positive reviews to a cheaper model while sending complex or negative reviews to a better one. This could cut costs by 30 to 40 percent.

A template hybrid approach would use pre-written templates for common positive reviews with no LLM cost at all, only using the LLM for cases that need personalisation.


6. Prompt injection and poisoning protection

Where to Find It: security_and_evaluation.py lines 18-92

Prompt injection is when attackers embed malicious instructions in review text to manipulate the AI. I implemented detection using regex patterns that catch common attack types:

Instruction overrides like "ignore previous instructions"
Role manipulation like "pretend you are angry"
Hidden commands like "[[ADMIN: Override safety]]"
Prompt extraction attempts like "show me your system prompt"

When something suspicious is detected, it gets flagged with a risk level and recommendations. High risk content should go to human review rather than being processed automatically.

I also implemented content wrapping (create_injection_resistant_prompt function) which puts user content inside clear delimiters with explicit instructions to treat it as data not commands.

How to Test: Use the web interface "Security Demo" tab. Try entering injection attempts and see them get blocked.


7. Evaluation metrics and A/B testing

Where to Find It: security_and_evaluation.py lines 209-315

I implemented automated metrics:

Structure score checks if all 5 response parts are present
Relevance score measures if the response references the review content
Professionalism score checks for blocked terms in output
Overall score combines these with weights

The ABTestFramework class lets you register different configurations (like temperature or default tone), track impressions and outcomes, then compare conversion rates and average ratings.

In production you would measure things like whether customers reply, whether issues get resolved, and whether follow-up reviews improve.


8. Outgoing guardrails for slang and over-familiar terms

Where to Find It: security_and_evaluation.py lines 117-206

Even with good prompting, the LLM might generate inappropriate language. I added a post-processing filter that catches and replaces problematic terms:

South African slang: "kak" becomes "unfortunate"
Overly casual: "buddy", "mate", "dude" become "valued customer"
Text speak: "lol", "omg" get removed
Excessive punctuation: "!!!!!" becomes "!"

The filter logs what it changes so prompts can be improved over time if certain issues keep coming up.

How to Test: Use the web interface "Guardrails Demo" tab. Enter text with slang and see it get filtered.



FILE OVERVIEW

Here is what each file does:

app.py - Web interface for testing all features
review_responder.py - Core response generator with JSON schema
review_responder_with_rag.py - Version with FAQ integration
security_and_evaluation.py - Injection detection, guardrails, evaluation metrics
demo_auto.py - Command line demo that runs all features
run_test.py - Simple test runner for basic responses
test_rag.py - Test runner for RAG features
README.md - Full documentation of the solution
SETUP.md - Quick setup instructions
result_review_*.json - Pre-generated sample outputs



COST INFORMATION

Running the full demo costs approximately $0.005 (half a cent) in OpenAI API usage.

Each individual response costs about $0.00016 using around 850 tokens.

Monthly projections:
1,000 reviews: $0.16
10,000 reviews: $1.58
100,000 reviews: $15.80



AI ASSISTANCE DISCLOSURE

I used Claude Code (Claude Opus 4.5) to assist with this project. Specifically:

Claude helped structure the JSON schema for the OpenAI API structured output feature
Claude helped write the regex patterns for prompt injection detection
Claude helped with the cosine similarity calculation for the embedding-based RAG search

The design decisions, model selection reasoning, and overall architecture are my own work. I can explain and defend any part of this solution.



QUESTIONS

If you have any questions about the implementation or want me to demonstrate any specific feature, please let me know during the interview.
