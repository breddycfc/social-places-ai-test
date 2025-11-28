"""
Test script for RAG/FAQ integration.
Author: Branden Reddy
"""
import os
import sys

os.environ["OPENAI_API_KEY"] = sys.argv[1] if len(sys.argv) > 1 else ""

from review_responder_with_rag import (
    generate_review_response_with_rag,
    format_rag_response_for_display,
    retrieve_relevant_faqs_keyword
)

print("\nRAG FAQ INTEGRATION TEST")
print("=" * 50)

TEST_REVIEWS = [
    {
        "reviewer_name": "Alex Stone",
        "rating": 5,
        "review_comment": "There was a cockroach in my soup",
        "expected_faq": "hygiene"
    },
    {
        "reviewer_name": "Jane Doe",
        "rating": 5,
        "review_comment": "Amazing response times and great opening times from very early to super late.",
        "expected_faq": "hours"
    },
    {
        "reviewer_name": "John Smith",
        "rating": 2,
        "review_comment": "The waiter was incredibly rude and the service was slow",
        "expected_faq": "service"
    }
]

for i, review in enumerate(TEST_REVIEWS, 1):
    print(f"\nTEST {i}: Expecting {review['expected_faq'].upper()} FAQ")
    print(f"Review: \"{review['review_comment']}\"")

    faqs = retrieve_relevant_faqs_keyword(review['review_comment'])
    print(f"\nFAQs found:")
    for faq in faqs:
        print(f"  {faq['category']}: {faq['question'][:40]}...")

    try:
        result = generate_review_response_with_rag(
            reviewer_name=review["reviewer_name"],
            rating=review["rating"],
            review_comment=review["review_comment"],
            use_embeddings=False
        )
        print(format_rag_response_for_display(result))

    except Exception as e:
        print(f"Error: {e}")

print("\nRAG TEST COMPLETE")
