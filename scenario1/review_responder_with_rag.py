"""
Social Places AI Engineer Test - Scenario 1 (RAG Version)
Review Response Generator with FAQ Integration

Author: Branden Reddy

AI Assistance: Claude Code helped with the embedding similarity
calculation and structuring the FAQ retrieval logic.
"""

import os
import json
import numpy as np
from openai import OpenAI

client = OpenAI()

# Sample FAQ knowledge base
# In production this would come from a database or CMS
FAQ_KNOWLEDGE_BASE = [
    {
        "id": "faq_1",
        "category": "hours",
        "question": "What are your opening hours?",
        "answer": "We are open Monday to Friday from 6 AM to 10 PM, and weekends from 8 AM to 11 PM.",
        "keywords": ["hours", "open", "closing", "time", "schedule", "early", "late"]
    },
    {
        "id": "faq_2",
        "category": "complaints",
        "question": "How do I file a complaint?",
        "answer": "You can file a complaint through our support portal at support.socialplaces.io or call our customer service line at 0800-123-456.",
        "keywords": ["complaint", "issue", "problem", "unhappy", "disappointed", "bad"]
    },
    {
        "id": "faq_3",
        "category": "hygiene",
        "question": "What are your hygiene and food safety standards?",
        "answer": "We maintain strict hygiene protocols with daily health inspections, regular pest control, and all staff are food safety certified. If you experience any hygiene concerns, please contact our quality assurance team immediately.",
        "keywords": ["hygiene", "clean", "dirty", "pest", "cockroach", "insect", "food safety", "health"]
    },
    {
        "id": "faq_4",
        "category": "refunds",
        "question": "What is your refund policy?",
        "answer": "We offer full refunds for unsatisfactory experiences within 30 days. Please bring your receipt or provide your order number.",
        "keywords": ["refund", "money back", "return", "compensation"]
    },
    {
        "id": "faq_5",
        "category": "service",
        "question": "How can I provide feedback on service quality?",
        "answer": "We value your feedback! You can rate your experience through our app, website, or speak directly to a manager on-site.",
        "keywords": ["service", "staff", "waiter", "waitress", "rude", "slow", "communication"]
    },
    {
        "id": "faq_6",
        "category": "loyalty",
        "question": "Do you have a loyalty program?",
        "answer": "Yes! Join our rewards program to earn points on every purchase. Sign up at socialplaces.io/rewards for exclusive discounts.",
        "keywords": ["loyalty", "rewards", "points", "discount", "member", "benefits"]
    }
]


def get_embedding(text, model="text-embedding-3-small"):
    """Get embedding vector for text."""
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


def cosine_similarity(vec1, vec2):
    """Calculate similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def retrieve_relevant_faqs(review_text, top_k=2, similarity_threshold=0.3):
    """
    Find FAQs relevant to the review using semantic search.
    This method uses embeddings which costs a small amount but is more accurate.
    """
    review_embedding = get_embedding(review_text)

    faq_scores = []
    for faq in FAQ_KNOWLEDGE_BASE:
        faq_text = f"{faq['question']} {faq['answer']} {' '.join(faq['keywords'])}"
        faq_embedding = get_embedding(faq_text)
        similarity = cosine_similarity(review_embedding, faq_embedding)
        faq_scores.append({**faq, "similarity_score": similarity})

    faq_scores.sort(key=lambda x: x["similarity_score"], reverse=True)
    return [faq for faq in faq_scores[:top_k] if faq["similarity_score"] >= similarity_threshold]


def retrieve_relevant_faqs_keyword(review_text, top_k=2):
    """
    Find FAQs using simple keyword matching.
    This is free and fast, good for high volume.
    """
    review_lower = review_text.lower()

    faq_scores = []
    for faq in FAQ_KNOWLEDGE_BASE:
        matches = sum(1 for kw in faq["keywords"] if kw.lower() in review_lower)
        if matches > 0:
            faq_scores.append({**faq, "match_count": matches})

    faq_scores.sort(key=lambda x: x["match_count"], reverse=True)
    return faq_scores[:top_k]


# System prompt that includes space for FAQ context
SYSTEM_PROMPT_WITH_RAG = """You are a professional customer review response assistant for {brand_name}.

BRAND VOICE GUIDELINES:
{brand_tone_guidelines}

RELEVANT KNOWLEDGE BASE INFORMATION:
{faq_context}

YOUR TASK:
1. Analyze the sentiment of the review (consider BOTH the rating AND the comment)
2. Detect the appropriate tone context based on how the reviewer wrote
3. Generate a personalized response using the structure provided
4. If relevant FAQ information is provided, naturally incorporate helpful details from it

TONE ADAPTATION RULES:
- Casual: Relaxed language, contractions allowed
- Formal: Professional, no contractions
- Friendly: Enthusiastic, empathetic

SENTIMENT-BASED ACTIONS:
- Negative/Mixed: Include the support_link
- Positive: No support link needed

RESPONSE CONSTRAINTS:
- Salutation: 1 sentence
- Introduction: 1 sentence
- Body: 2-3 sentences (work in FAQ info naturally if relevant)
- Conclusion: 1 sentence
- Closing: 1 sentence

CRITICAL RULES:
- Never use slang or profanity
- Address reviewer by first name
- If rating and comment contradict, trust the comment
- Weave FAQ information in naturally, don't dump it"""


# JSON schema with fields to track RAG usage
RESPONSE_SCHEMA_WITH_RAG = {
    "name": "review_response_with_rag",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "sentiment_analysis": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "mixed"]},
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"}
                },
                "required": ["sentiment", "confidence", "reasoning"],
                "additionalProperties": False
            },
            "detected_tone_context": {"type": "string", "enum": ["casual", "formal", "friendly"]},
            "response": {
                "type": "object",
                "properties": {
                    "salutation": {"type": "string"},
                    "introduction": {"type": "string"},
                    "body": {"type": "string"},
                    "conclusion": {"type": "string"},
                    "closing": {"type": "string"}
                },
                "required": ["salutation", "introduction", "body", "conclusion", "closing"],
                "additionalProperties": False
            },
            "support_link_included": {"type": "boolean"},
            "support_link": {"type": ["string", "null"]},
            "faq_info_used": {"type": "boolean", "description": "Whether FAQ info was used"},
            "faq_categories_referenced": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Which FAQ categories were referenced"
            }
        },
        "required": [
            "sentiment_analysis", "detected_tone_context", "response",
            "support_link_included", "support_link", "faq_info_used", "faq_categories_referenced"
        ],
        "additionalProperties": False
    }
}


def generate_review_response_with_rag(
    reviewer_name,
    rating,
    review_comment,
    brand_name="Social Places",
    brand_tone_guidelines="Professional yet approachable. We value customer feedback.",
    support_url="https://support.socialplaces.io/help",
    use_embeddings=False
):
    """
    Generate a response with RAG-enhanced context from FAQs.
    Set use_embeddings=True for semantic search (more accurate, small cost)
    or False for keyword matching (free, slightly less accurate)
    """

    # Get relevant FAQs
    if use_embeddings:
        relevant_faqs = retrieve_relevant_faqs(review_comment, top_k=2)
    else:
        relevant_faqs = retrieve_relevant_faqs_keyword(review_comment, top_k=2)

    # Format FAQ context for the prompt
    if relevant_faqs:
        faq_context = "The following information from our knowledge base may be relevant:\n"
        for faq in relevant_faqs:
            faq_context += f"\nTopic: {faq['category'].title()}\n"
            faq_context += f"Q: {faq['question']}\n"
            faq_context += f"A: {faq['answer']}\n"
    else:
        faq_context = "No specific FAQ information is relevant to this review."

    system_message = SYSTEM_PROMPT_WITH_RAG.format(
        brand_name=brand_name,
        brand_tone_guidelines=brand_tone_guidelines,
        faq_context=faq_context
    )

    user_message = f"""REVIEW TO RESPOND TO:
- Reviewer Name: {reviewer_name}
- Rating: {rating}/5 stars
- Comment: {review_comment}

AVAILABLE SUPPORT LINK (use only if sentiment is negative/mixed):
{support_url}

Generate a structured response, incorporating relevant FAQ information naturally if applicable."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": RESPONSE_SCHEMA_WITH_RAG
        },
        temperature=0.7,
        max_tokens=600
    )

    result = json.loads(response.choices[0].message.content)

    result["_metadata"] = {
        "model": "gpt-4o-mini",
        "rag_method": "embeddings" if use_embeddings else "keyword",
        "faqs_retrieved": [faq["id"] for faq in relevant_faqs],
        "tokens_used": {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
    }

    return result


def format_rag_response_for_display(result):
    """Format the RAG response for console output."""
    response = result["response"]

    formatted = f"""
{'='*60}
SENTIMENT ANALYSIS:
  Sentiment: {result['sentiment_analysis']['sentiment'].upper()}
  Confidence: {result['sentiment_analysis']['confidence']:.0%}
  Reasoning: {result['sentiment_analysis']['reasoning']}
  Detected Tone: {result['detected_tone_context']}

RAG CONTEXT:
  FAQ Info Used: {result['faq_info_used']}
  Categories Referenced: {', '.join(result['faq_categories_referenced']) if result['faq_categories_referenced'] else 'None'}
  FAQs Retrieved: {', '.join(result['_metadata']['faqs_retrieved'])}

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


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        os.environ["OPENAI_API_KEY"] = sys.argv[1]

    print("\nRAG-ENHANCED REVIEW RESPONSE GENERATOR")
    print("Testing FAQ Integration with cockroach review\n")

    test_review = {
        "reviewer_name": "Alex Stone",
        "rating": 5,
        "review_comment": "There was a cockroach in my soup"
    }

    print(f"Review: \"{test_review['review_comment']}\"")
    print("Expected: Should retrieve hygiene FAQ\n")

    try:
        result = generate_review_response_with_rag(
            reviewer_name=test_review["reviewer_name"],
            rating=test_review["rating"],
            review_comment=test_review["review_comment"],
            use_embeddings=False
        )
        print(format_rag_response_for_display(result))

        with open("result_rag_example.json", "w") as f:
            json.dump(result, f, indent=2)

    except Exception as e:
        print(f"Error: {e}")
