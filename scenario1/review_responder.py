"""
Social Places AI Engineer Test - Scenario 1
Automated Review Response Generator

Author: Branden Reddy

AI Assistance: Used Claude Code to help structure the JSON schema
and format the OpenAI API calls.
"""

import os
import json
from openai import OpenAI

client = OpenAI()

# This schema tells GPT-4o-mini exactly what format to return
# Using strict mode guarantees valid JSON every time
RESPONSE_SCHEMA = {
    "name": "review_response",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "sentiment_analysis": {
                "type": "object",
                "properties": {
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative", "mixed"],
                        "description": "Overall sentiment based on both rating and comment"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score between 0 and 1"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation especially if rating and comment contradict"
                    }
                },
                "required": ["sentiment", "confidence", "reasoning"],
                "additionalProperties": False
            },
            "detected_tone_context": {
                "type": "string",
                "enum": ["casual", "formal", "friendly"],
                "description": "Tone to use based on how the reviewer wrote"
            },
            "response": {
                "type": "object",
                "properties": {
                    "salutation": {"type": "string", "description": "Greeting with name"},
                    "introduction": {"type": "string", "description": "Acknowledge feedback"},
                    "body": {"type": "string", "description": "Address specific points"},
                    "conclusion": {"type": "string", "description": "Resolution or thanks"},
                    "closing": {"type": "string", "description": "Sign off"}
                },
                "required": ["salutation", "introduction", "body", "conclusion", "closing"],
                "additionalProperties": False
            },
            "support_link_included": {
                "type": "boolean",
                "description": "Whether support link was added for negative sentiment"
            },
            "support_link": {
                "type": ["string", "null"],
                "description": "The support URL if included"
            }
        },
        "required": ["sentiment_analysis", "detected_tone_context", "response", "support_link_included", "support_link"],
        "additionalProperties": False
    }
}

# System prompt that defines how the AI should behave
SYSTEM_PROMPT = """You are a professional customer review response assistant for {brand_name}.

BRAND VOICE GUIDELINES:
{brand_tone_guidelines}

YOUR TASK:
1. Analyze the sentiment of the review (consider BOTH the rating AND the comment - they may contradict)
2. Detect the appropriate tone context (casual/formal/friendly) based on how the reviewer wrote
3. Generate a personalized response following the exact structure provided

TONE ADAPTATION RULES:
- Casual: Use relaxed language, contractions allowed, warm but not overly formal
- Formal: Professional language, no contractions, respectful and measured
- Friendly: Enthusiastic, empathetic, use of positive affirmations

SENTIMENT-BASED ACTIONS:
- Negative/Mixed sentiment: Include the provided support_link to help resolve issues
- Positive sentiment: Set support_link to null, focus on appreciation

RESPONSE LENGTH CONSTRAINTS:
- Salutation: 1 short sentence (greeting with name)
- Introduction: 1 sentence (acknowledge their feedback)
- Body: 1-2 sentences (address specific points)
- Conclusion: 1 sentence (resolution or appreciation)
- Closing: 1 short sentence (sign-off)

CRITICAL RULES:
- Never use slang, profanity, or overly casual terms (no 'kak', 'awesome sauce', etc.)
- Always address the reviewer by their first name
- If rating and comment contradict (e.g., 5 stars but negative comment), trust the COMMENT for sentiment
- Keep responses professional but warm
- Match the energy: enthusiastic for positive, empathetic for negative"""


def generate_review_response(
    reviewer_name,
    rating,
    review_comment,
    brand_name="Social Places",
    brand_tone_guidelines="Professional yet approachable. We value customer feedback and aim to resolve issues promptly.",
    support_url="https://support.socialplaces.io/help"
):
    """
    Takes a review and generates a structured response.
    Returns a dict with sentiment analysis and the formatted reply.
    """

    system_message = SYSTEM_PROMPT.format(
        brand_name=brand_name,
        brand_tone_guidelines=brand_tone_guidelines
    )

    user_message = f"""REVIEW TO RESPOND TO:
- Reviewer Name: {reviewer_name}
- Rating: {rating}/5 stars
- Comment: {review_comment}

AVAILABLE SUPPORT LINK (use only if sentiment is negative/mixed):
{support_url}

Generate a structured response following the brand voice guidelines."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": RESPONSE_SCHEMA
        },
        temperature=0.7,
        max_tokens=500
    )

    result = json.loads(response.choices[0].message.content)

    # Add token usage info for cost tracking
    result["_metadata"] = {
        "model": "gpt-4o-mini",
        "tokens_used": {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
    }

    return result


def format_response_for_display(result):
    """Formats the structured response for printing to console."""
    response = result["response"]

    formatted = f"""
{'='*60}
SENTIMENT ANALYSIS:
  Sentiment: {result['sentiment_analysis']['sentiment'].upper()}
  Confidence: {result['sentiment_analysis']['confidence']:.0%}
  Reasoning: {result['sentiment_analysis']['reasoning']}
  Detected Tone: {result['detected_tone_context']}

GENERATED RESPONSE:
{'-'*40}
{response['salutation']}

{response['introduction']}

{response['body']}

{response['conclusion']}

{response['closing']}
{'-'*40}

Support Link Included: {result['support_link_included']}
{f"Link: {result['support_link']}" if result['support_link'] else ""}

TOKEN USAGE:
  Prompt tokens: {result['_metadata']['tokens_used']['prompt']}
  Completion tokens: {result['_metadata']['tokens_used']['completion']}
  Total tokens: {result['_metadata']['tokens_used']['total']}
{'='*60}
"""
    return formatted


# The three example reviews from the test scenario
EXAMPLE_REVIEWS = [
    {
        "reviewer_name": "John Smith",
        "rating": 3,
        "review_comment": "The service was decent, but there's room for improvement. Communication was okay, though some aspects could have been clearer. The software delivered met expectations but lacked some polish in certain areas. Overall, an average experience—not bad, but not outstanding either."
    },
    {
        "reviewer_name": "Jane Doe",
        "rating": 5,
        "review_comment": "Amazing response times and great opening times from very early to super late. Finally a store that I can go to after work :)"
    },
    {
        "reviewer_name": "Alex Stone",
        "rating": 5,
        "review_comment": "There was a cockroach in my soup"
    }
]


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SOCIAL PLACES - AUTOMATED REVIEW RESPONSE GENERATOR")
    print("Model: GPT-4o-mini | Scenario 1 Test")
    print("="*60)

    for i, review in enumerate(EXAMPLE_REVIEWS, 1):
        print(f"\n\nREVIEW {i}:")
        print(f"  Reviewer: {review['reviewer_name']}")
        print(f"  Rating: {review['rating']}/5 stars")
        print(f"  Comment: {review['review_comment']}")

        try:
            result = generate_review_response(
                reviewer_name=review["reviewer_name"],
                rating=review["rating"],
                review_comment=review["review_comment"]
            )
            print(format_response_for_display(result))

            with open(f"result_review_{i}.json", "w") as f:
                json.dump(result, f, indent=2)

        except Exception as e:
            print(f"Error processing review: {e}")

    print("\n\nResults saved to JSON files.")
