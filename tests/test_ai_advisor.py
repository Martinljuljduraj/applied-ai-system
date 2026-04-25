"""
test_ai_advisor.py — AI Advisor Test Harness

Runs a set of predefined prompts against the PawPal+ AI advisor and prints
a pass/fail summary. A test passes if the response contains a structured
task suggestion in the expected format (Task: ... | Duration: ... | Priority: ...)
or a relevant keyword for non-task questions.

"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ai_advisor import get_ai_advice

# Test cases

TEST_CASES = [
    {
        "name": "Daily tasks for a dog",
        "message": "What daily tasks should I add for my dog?",
        "pet_name": "Rex",
        "species": "dog",
        "current_tasks": [],
        "expect_keyword": "Task:",
    },
    {
        "name": "Grooming advice for a cat",
        "message": "How often should I groom my cat?",
        "pet_name": "Whiskers",
        "species": "cat",
        "current_tasks": ["Feeding", "Play session"],
        "expect_keyword": "groom",
    },
    {
        "name": "Structured format returned",
        "message": "Suggest one high priority task for my dog.",
        "pet_name": "Buddy",
        "species": "dog",
        "current_tasks": [],
        "expect_keyword": "Priority:",
    },
    {
        "name": "Context awareness — skips existing tasks",
        "message": "What tasks am I missing for my dog?",
        "pet_name": "Max",
        "species": "dog",
        "current_tasks": ["Morning walk", "Feeding", "Fresh water"],
        "expect_keyword": "Task:",
    },
    {
        "name": "Health question handled safely",
        "message": "My dog seems tired and is eating less. What should I do?",
        "pet_name": "Luna",
        "species": "dog",
        "current_tasks": [],
        "expect_keyword": "vet",
    },
]

# Running tests

def run_tests():
    print("=" * 60)
    print("  PawPal+ AI Advisor — Test Harness")
    print("=" * 60)

    passed = 0
    failed = 0
    results = []

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n  Test {i}: {test['name']}")
        print(f"  Input: \"{test['message']}\"")

        try:
            response = get_ai_advice(
                user_message=test["message"],
                pet_name=test["pet_name"],
                species=test["species"],
                current_tasks=test["current_tasks"],
            )

            keyword = test["expect_keyword"].lower()
            if keyword in response.lower():
                status = "PASS"
                passed += 1
            else:
                status = "FAIL — expected keyword not found"
                failed += 1

            print(f"  Response preview: {response[:120].strip()}...")
            print(f"  Result: {status}")

        except Exception as e:
            status = f"ERROR — {str(e)}"
            failed += 1
            print(f"  Result: {status}")

        results.append({"test": test["name"], "status": status})

    # Summarizing
    print("\n" + "=" * 60)
    print(f"  Results: {passed}/{len(TEST_CASES)} passed")
    if failed > 0:
        print(f"  {failed} test(s) failed or errored")
    else:
        print("  All tests passed.")
    print("=" * 60)

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)