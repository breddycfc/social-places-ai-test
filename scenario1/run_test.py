"""
Test runner for basic review responses.
Author: Branden Reddy
"""
import os
import sys
import json

os.environ["OPENAI_API_KEY"] = sys.argv[1] if len(sys.argv) > 1 else os.getenv("OPENAI_API_KEY", "")

if not os.environ.get("OPENAI_API_KEY"):
    print("Usage: python run_test.py YOUR_API_KEY")
    sys.exit(1)

from review_responder import EXAMPLE_REVIEWS, generate_review_response, format_response_for_display

print("\nSOCIAL PLACES - REVIEW RESPONSE TEST")
print("=" * 50)

for i, review in enumerate(EXAMPLE_REVIEWS, 1):
    print(f"\nREVIEW {i}:")
    print(f"  Reviewer: {review['reviewer_name']}")
    print(f"  Rating: {review['rating']}/5")
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
        print(f"Error: {e}")

print("\nResults saved to JSON files.")
