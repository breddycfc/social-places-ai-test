Setup Instructions

Prerequisites:
Python 3.10 or higher
OpenAI API key from platform.openai.com

Installation:

1. Clone this repository

2. Install dependencies by running: pip install -r requirements.txt

3. Set your API key
   On Windows run: set OPENAI_API_KEY=your-key
   On Mac or Linux run: export OPENAI_API_KEY=your-key

4. Run the demo with: python demo_auto.py


What the demo shows:

The demo runs through all the features. It generates responses for the 3 example reviews, shows the RAG FAQ integration, demonstrates the prompt injection detection, and shows the slang filter working.


Cost:

Running the full demo costs about half a cent in API usage.


Sample outputs:

If you want to see what the system produces without using API credits, the result_review_1.json, result_review_2.json, and result_review_3.json files contain actual outputs.
