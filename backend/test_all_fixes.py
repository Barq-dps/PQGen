#!/usr/bin/env python3
"""
Test script to verify all the fixes made to the LLM challenge generator
and the implementation of hints for wrong answers in coding challenges.
"""

import sys
import os
import json
import logging
from pprint import pprint

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the modules we want to test
# We'll mock the LLM-related functions
from fallback_hints import (
    generate_fallback_hint_for_multiple_choice,
    generate_fallback_hint_for_debugging,
    generate_fallback_hint_for_coding
)
from code_evaluator import (
    evaluate_coding_solution,
    evaluate_debugging_solution,
    generate_feedback_for_incorrect_solution
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock LLM-generated challenges
def mock_multiple_choice(topic, topic_text, difficulty):
    """Mock multiple choice question generation."""
    return {
        "id": "mock-mc-1",
        "topic": topic,
        "type": "multiple_choice",
        "question": f"What is the primary purpose of {topic}?",
        "options": [
            "To store data in memory",
            "To perform calculations",
            "To organize code into reusable blocks",
            "To handle user input"
        ],
        "correct_index": 2,
        "hint": f"Think about how {topic} helps with code organization and reusability.",
        "difficulty": difficulty
    }

def mock_debugging(topic, topic_text, difficulty, language="python"):
    """Mock debugging challenge generation."""
    code_length = 5 if difficulty == "easy" else (15 if difficulty == "medium" else 25)
    code = f"def example_{topic.lower().replace(' ', '_')}():\n"
    code += "    # This is a function that demonstrates a bug\n"
    for i in range(code_length - 2):
        code += f"    print('Line {i}')\n"
    code += "    return 'buggy result'  # Bug: should return correct result\n"
    
    return {
        "id": "mock-debug-1",
        "topic": topic,
        "type": "debugging",
        "question": f"Fix the bug in this {topic} implementation.",
        "code_stub": code,
        "hint": f"Look at the return value of the function. Is it returning what it should for {topic}?",
        "bug_comment": "The function returns 'buggy result' instead of the correct result.",
        "difficulty": difficulty
    }

def mock_coding(topic, topic_text, difficulty, language="python"):
    """Mock coding challenge generation."""
    code_length = 3 if difficulty == "easy" else (8 if difficulty == "medium" else 15)
    code = f"def solution_{topic.lower().replace(' ', '_')}(input):\n"
    code += "    # Implement your solution here\n"
    for i in range(code_length - 2):
        code += f"    # Line {i}\n"
    code += "    pass\n"
    
    test_cases = []
    for i in range(1 if difficulty == "easy" else (2 if difficulty == "medium" else 3)):
        test_cases.append({
            "input": f"test input {i+1}",
            "expected": f"expected output {i+1}"
        })
    
    return {
        "id": "mock-coding-1",
        "topic": topic,
        "type": "coding",
        "question": f"Implement a function that handles {topic}.",
        "code_stub": code,
        "test_cases": test_cases,
        "hint": f"Think about how to process the input to produce the expected output for {topic}.",
        "difficulty": difficulty
    }

def test_multiple_choice_generation():
    """Test multiple choice question generation with correct answers."""
    print("\n=== Testing Multiple Choice Question Generation ===")
    
    # Test with different difficulty levels
    for difficulty in ["easy", "medium", "hard"]:
        print(f"\nTesting {difficulty} difficulty:")
        
        # Mock topic and content
        topic = "Python Lists"
        topic_text = """
        Python lists are ordered collections of items. They are mutable, which means they can be changed after creation.
        Lists are defined by enclosing items in square brackets []. Items in a list can be of different types.
        Common operations on lists include append(), extend(), insert(), remove(), pop(), clear(), index(), count(), sort(), and reverse().
        """
        
        # Generate a multiple choice question
        question = mock_multiple_choice(topic, topic_text, difficulty)
        
        # Check if the question was generated
        if question:
            print(f"Question: {question['question']}")
            print(f"Options: {question['options']}")
            print(f"Correct Index: {question['correct_index']}")
            print(f"Hint: {question['hint']}")
            
            # Verify correct_index is within bounds
            assert 0 <= question['correct_index'] < len(question['options']), "Correct index out of bounds"
            
            # Verify hint is not empty
            assert question['hint'], "Hint is empty"
            
            print("✅ Multiple choice question generated successfully")
        else:
            print("❌ Failed to generate multiple choice question")
    
    # Test fallback hint generation
    print("\nTesting fallback hint generation for multiple choice:")
    hint = generate_fallback_hint_for_multiple_choice("Python Lists", "medium")
    print(f"Fallback Hint: {hint}")
    assert hint, "Fallback hint is empty"
    print("✅ Fallback hint generated successfully")

def test_difficulty_scaling():
    """Test difficulty scaling across all challenge types."""
    print("\n=== Testing Difficulty Scaling ===")
    
    # Mock topic and content
    topic = "Python Functions"
    topic_text = """
    Python functions are defined using the def keyword, followed by the function name and parameters.
    Functions can return values using the return statement. If no return statement is used, the function returns None.
    Functions can have default parameter values, which are used if no argument is provided for that parameter.
    Python also supports variable-length arguments using *args and **kwargs.
    """
    
    # Test difficulty scaling for multiple choice questions
    print("\nTesting difficulty scaling for multiple choice questions:")
    for difficulty in ["easy", "medium", "hard"]:
        question = mock_multiple_choice(topic, topic_text, difficulty)
        if question:
            print(f"{difficulty.capitalize()} question: {question['question']}")
            print(f"Hint: {question['hint']}")
            print("✅ Generated successfully")
        else:
            print(f"❌ Failed to generate {difficulty} multiple choice question")
    
    # Test difficulty scaling for debugging challenges
    print("\nTesting difficulty scaling for debugging challenges:")
    for difficulty in ["easy", "medium", "hard"]:
        challenge = mock_debugging(topic, topic_text, difficulty)
        if challenge:
            print(f"{difficulty.capitalize()} challenge:")
            print(f"Question: {challenge['question']}")
            code_lines = challenge['code_stub'].count('\n') + 1
            print(f"Code length: {code_lines} lines")
            print(f"Hint: {challenge['hint']}")
            print("✅ Generated successfully")
        else:
            print(f"❌ Failed to generate {difficulty} debugging challenge")
    
    # Test difficulty scaling for coding challenges
    print("\nTesting difficulty scaling for coding challenges:")
    for difficulty in ["easy", "medium", "hard"]:
        challenge = mock_coding(topic, topic_text, difficulty)
        if challenge:
            print(f"{difficulty.capitalize()} challenge:")
            print(f"Question: {challenge['question']}")
            code_lines = challenge['code_stub'].count('\n') + 1
            print(f"Code stub length: {code_lines} lines")
            print(f"Test cases: {len(challenge['test_cases'])}")
            print(f"Hint: {challenge['hint']}")
            print("✅ Generated successfully")
        else:
            print(f"❌ Failed to generate {difficulty} coding challenge")

def test_hint_functionality():
    """Test hint functionality for all challenge types."""
    print("\n=== Testing Hint Functionality ===")
    
    # Mock topic and content
    topic = "Python Dictionaries"
    topic_text = """
    Python dictionaries are unordered collections of key-value pairs. They are mutable and can be changed after creation.
    Dictionaries are defined by enclosing key-value pairs in curly braces {}. Keys must be unique and immutable.
    Common operations on dictionaries include get(), keys(), values(), items(), update(), and pop().
    """
    
    # Test hint functionality for multiple choice questions
    print("\nTesting hint functionality for multiple choice questions:")
    question = mock_multiple_choice(topic, topic_text, "medium")
    if question:
        print(f"Question: {question['question']}")
        print(f"Hint: {question['hint']}")
        assert question['hint'], "Hint is empty"
        print("✅ Hint generated successfully")
    else:
        print("❌ Failed to generate multiple choice question")
    
    # Test hint functionality for debugging challenges
    print("\nTesting hint functionality for debugging challenges:")
    challenge = mock_debugging(topic, topic_text, "medium")
    if challenge:
        print(f"Question: {challenge['question']}")
        print(f"Hint: {challenge['hint']}")
        assert challenge['hint'], "Hint is empty"
        print("✅ Hint generated successfully")
    else:
        print("❌ Failed to generate debugging challenge")
    
    # Test hint functionality for coding challenges
    print("\nTesting hint functionality for coding challenges:")
    challenge = mock_coding(topic, topic_text, "medium")
    if challenge:
        print(f"Question: {challenge['question']}")
        print(f"Hint: {challenge['hint']}")
        assert challenge['hint'], "Hint is empty"
        print("✅ Hint generated successfully")
    else:
        print("❌ Failed to generate coding challenge")
    
    # Test fallback hint generation
    print("\nTesting fallback hint generation:")
    
    mc_hint = generate_fallback_hint_for_multiple_choice(topic, "medium")
    print(f"Multiple choice fallback hint: {mc_hint}")
    assert mc_hint, "Multiple choice fallback hint is empty"
    
    debug_hint = generate_fallback_hint_for_debugging(topic, "medium", "def example():\n    return {}")
    print(f"Debugging fallback hint: {debug_hint}")
    assert debug_hint, "Debugging fallback hint is empty"
    
    coding_hint = generate_fallback_hint_for_coding(topic, "medium", "def solution(input):\n    pass")
    print(f"Coding fallback hint: {coding_hint}")
    assert coding_hint, "Coding fallback hint is empty"
    
    print("✅ All fallback hints generated successfully")

def test_wrong_answer_hints():
    """Test hints for wrong answers in coding challenges."""
    print("\n=== Testing Hints for Wrong Answers in Coding Challenges ===")
    
    # Test coding challenge evaluation with correct solution
    print("\nTesting coding challenge evaluation with correct solution:")
    
    # Define a simple coding challenge
    test_cases = [
        {"input": "5", "expected": "25"},
        {"input": "10", "expected": "100"}
    ]
    
    # Define a correct solution
    correct_solution = """
def solution(input):
    n = int(input)
    return str(n * n)
"""
    
    # Evaluate the solution
    result = evaluate_coding_solution(correct_solution, test_cases)
    print(f"Status: {result['status']}")
    print(f"Feedback: {result['feedback']}")
    
    # Verify the solution is correct
    assert result['status'] == 'correct', "Correct solution marked as incorrect"
    print("✅ Correct solution evaluated successfully")
    
    # Test coding challenge evaluation with incorrect solution
    print("\nTesting coding challenge evaluation with incorrect solution:")
    
    # Define an incorrect solution
    incorrect_solution = """
def solution(input):
    n = int(input)
    return str(n + n)  # Should be n * n
"""
    
    # Define a hint
    hint = "Remember that squaring a number means multiplying it by itself."
    
    # Evaluate the solution
    result = evaluate_coding_solution(incorrect_solution, test_cases, hint)
    print(f"Status: {result['status']}")
    print(f"Feedback: {result['feedback']}")
    
    # Verify the solution is incorrect and the feedback includes the hint
    assert result['status'] == 'incorrect', "Incorrect solution marked as correct"
    assert hint in result['feedback'], "Hint not included in feedback"
    print("✅ Incorrect solution evaluated successfully with hint")
    
    # Test debugging challenge evaluation
    print("\nTesting debugging challenge evaluation:")
    
    # Define a buggy code
    buggy_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers) - 1  # Bug: should not subtract 1
"""
    
    # Define a fixed solution
    fixed_solution = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
"""
    
    # Define a bug comment
    bug_comment = "The function incorrectly subtracts 1 from the average."
    
    # Evaluate the solution
    result = evaluate_debugging_solution(fixed_solution, buggy_code, bug_comment)
    print(f"Status: {result['status']}")
    print(f"Feedback: {result['feedback']}")
    
    # Verify the solution is correct
    assert result['status'] == 'correct', "Correct debugging solution marked as incorrect"
    print("✅ Debugging solution evaluated successfully")
    
    # Test feedback generation for incorrect solutions
    print("\nTesting feedback generation for incorrect solutions:")
    
    # Define test results with errors
    test_results = [
        {
            "input": "5",
            "expected": "25",
            "actual": "10",
            "passed": False,
            "error": None
        }
    ]
    
    # Generate feedback
    feedback = generate_feedback_for_incorrect_solution(incorrect_solution, test_results, hint)
    print(f"Feedback: {feedback}")
    
    # Verify the feedback includes the hint
    assert hint in feedback, "Hint not included in feedback"
    print("✅ Feedback generated successfully with hint")

def main():
    """Run all tests."""
    print("=== Running Tests for LLM Challenge Generator and Coding Hints ===")
    
    # Run the tests
    test_multiple_choice_generation()
    test_difficulty_scaling()
    test_hint_functionality()
    test_wrong_answer_hints()
    
    print("\n=== All Tests Completed Successfully ===")

if __name__ == "__main__":
    main()

def test_multiple_choice_generation():
    """Test multiple choice question generation with correct answers."""
    print("\n=== Testing Multiple Choice Question Generation ===")
    
    # Test with different difficulty levels
    for difficulty in ["easy", "medium", "hard"]:
        print(f"\nTesting {difficulty} difficulty:")
        
        # Mock topic and content
        topic = "Python Lists"
        topic_text = """
        Python lists are ordered collections of items. They are mutable, which means they can be changed after creation.
        Lists are defined by enclosing items in square brackets []. Items in a list can be of different types.
        Common operations on lists include append(), extend(), insert(), remove(), pop(), clear(), index(), count(), sort(), and reverse().
        """
        
        # Generate a multiple choice question
        question = mock_multiple_choice(topic, topic_text, difficulty)
        
        # Check if the question was generated
        if question:
            print(f"Question: {question['question']}")
            print(f"Options: {question['options']}")
            print(f"Correct Index: {question['correct_index']}")
            print(f"Hint: {question['hint']}")
            
            # Verify correct_index is within bounds
            assert 0 <= question['correct_index'] < len(question['options']), "Correct index out of bounds"
            
            # Verify hint is not empty
            assert question['hint'], "Hint is empty"
            
            print("✅ Multiple choice question generated successfully")
        else:
            print("❌ Failed to generate multiple choice question")
    
    # Test fallback hint generation
    print("\nTesting fallback hint generation for multiple choice:")
    hint = generate_fallback_hint_for_multiple_choice("Python Lists", "medium")
    print(f"Fallback Hint: {hint}")
    assert hint, "Fallback hint is empty"
    print("✅ Fallback hint generated successfully")

def test_difficulty_scaling():
    """Test difficulty scaling across all challenge types."""
    print("\n=== Testing Difficulty Scaling ===")
    
    # Mock topic and content
    topic = "Python Functions"
    topic_text = """
    Python functions are defined using the def keyword, followed by the function name and parameters.
    Functions can return values using the return statement. If no return statement is used, the function returns None.
    Functions can have default parameter values, which are used if no argument is provided for that parameter.
    Python also supports variable-length arguments using *args and **kwargs.
    """
    
    # Test difficulty scaling for multiple choice questions
    print("\nTesting difficulty scaling for multiple choice questions:")
    for difficulty in ["easy", "medium", "hard"]:
        question = mock_multiple_choice(topic, topic_text, difficulty)
        if question:
            print(f"{difficulty.capitalize()} question: {question['question']}")
            print(f"Hint: {question['hint']}")
            print("✅ Generated successfully")
        else:
            print(f"❌ Failed to generate {difficulty} multiple choice question")
    
    # Test difficulty scaling for debugging challenges
    print("\nTesting difficulty scaling for debugging challenges:")
    for difficulty in ["easy", "medium", "hard"]:
        challenge = mock_debugging(topic, topic_text, difficulty)
        if challenge:
            print(f"{difficulty.capitalize()} challenge:")
            print(f"Question: {challenge['question']}")
            code_lines = challenge['code_stub'].count('\n') + 1
            print(f"Code length: {code_lines} lines")
            print(f"Hint: {challenge['hint']}")
            print("✅ Generated successfully")
        else:
            print(f"❌ Failed to generate {difficulty} debugging challenge")
    
    # Test difficulty scaling for coding challenges
    print("\nTesting difficulty scaling for coding challenges:")
    for difficulty in ["easy", "medium", "hard"]:
        challenge = mock_coding(topic, topic_text, difficulty)
        if challenge:
            print(f"{difficulty.capitalize()} challenge:")
            print(f"Question: {challenge['question']}")
            code_lines = challenge['code_stub'].count('\n') + 1
            print(f"Code stub length: {code_lines} lines")
            print(f"Test cases: {len(challenge['test_cases'])}")
            print(f"Hint: {challenge['hint']}")
            print("✅ Generated successfully")
        else:
            print(f"❌ Failed to generate {difficulty} coding challenge")

def test_hint_functionality():
    """Test hint functionality for all challenge types."""
    print("\n=== Testing Hint Functionality ===")
    
    # Mock topic and content
    topic = "Python Dictionaries"
    topic_text = """
    Python dictionaries are unordered collections of key-value pairs. They are mutable and can be changed after creation.
    Dictionaries are defined by enclosing key-value pairs in curly braces {}. Keys must be unique and immutable.
    Common operations on dictionaries include get(), keys(), values(), items(), update(), and pop().
    """
    
    # Test hint functionality for multiple choice questions
    print("\nTesting hint functionality for multiple choice questions:")
    question = mock_multiple_choice(topic, topic_text, "medium")
    if question:
        print(f"Question: {question['question']}")
        print(f"Hint: {question['hint']}")
        assert question['hint'], "Hint is empty"
        print("✅ Hint generated successfully")
    else:
        print("❌ Failed to generate multiple choice question")
    
    # Test hint functionality for debugging challenges
    print("\nTesting hint functionality for debugging challenges:")
    challenge = mock_debugging(topic, topic_text, "medium")
    if challenge:
        print(f"Question: {challenge['question']}")
        print(f"Hint: {challenge['hint']}")
        assert challenge['hint'], "Hint is empty"
        print("✅ Hint generated successfully")
    else:
        print("❌ Failed to generate debugging challenge")
    
    # Test hint functionality for coding challenges
    print("\nTesting hint functionality for coding challenges:")
    challenge = mock_coding(topic, topic_text, "medium")
    if challenge:
        print(f"Question: {challenge['question']}")
        print(f"Hint: {challenge['hint']}")
        assert challenge['hint'], "Hint is empty"
        print("✅ Hint generated successfully")
    else:
        print("❌ Failed to generate coding challenge")
    
    # Test fallback hint generation
    print("\nTesting fallback hint generation:")
    
    mc_hint = generate_fallback_hint_for_multiple_choice(topic, "medium")
    print(f"Multiple choice fallback hint: {mc_hint}")
    assert mc_hint, "Multiple choice fallback hint is empty"
    
    debug_hint = generate_fallback_hint_for_debugging(topic, "medium", "def example():\n    return {}")
    print(f"Debugging fallback hint: {debug_hint}")
    assert debug_hint, "Debugging fallback hint is empty"
    
    coding_hint = generate_fallback_hint_for_coding(topic, "medium", "def solution(input):\n    pass")
    print(f"Coding fallback hint: {coding_hint}")
    assert coding_hint, "Coding fallback hint is empty"
    
    print("✅ All fallback hints generated successfully")

def test_wrong_answer_hints():
    """Test hints for wrong answers in coding challenges."""
    print("\n=== Testing Hints for Wrong Answers in Coding Challenges ===")
    
    # Test coding challenge evaluation with correct solution
    print("\nTesting coding challenge evaluation with correct solution:")
    
    # Define a simple coding challenge
    test_cases = [
        {"input": "5", "expected": "25"},
        {"input": "10", "expected": "100"}
    ]
    
    # Define a correct solution
    correct_solution = """
def solution(input):
    n = int(input)
    return str(n * n)
"""
    
    # Evaluate the solution
    result = evaluate_coding_solution(correct_solution, test_cases)
    print(f"Status: {result['status']}")
    print(f"Feedback: {result['feedback']}")
    
    # Verify the solution is correct
    assert result['status'] == 'correct', "Correct solution marked as incorrect"
    print("✅ Correct solution evaluated successfully")
    
    # Test coding challenge evaluation with incorrect solution
    print("\nTesting coding challenge evaluation with incorrect solution:")
    
    # Define an incorrect solution
    incorrect_solution = """
def solution(input):
    n = int(input)
    return str(n + n)  # Should be n * n
"""
    
    # Define a hint
    hint = "Remember that squaring a number means multiplying it by itself."
    
    # Evaluate the solution
    result = evaluate_coding_solution(incorrect_solution, test_cases, hint)
    print(f"Status: {result['status']}")
    print(f"Feedback: {result['feedback']}")
    
    # Verify the solution is incorrect and the feedback includes the hint
    assert result['status'] == 'incorrect', "Incorrect solution marked as correct"
    assert hint in result['feedback'], "Hint not included in feedback"
    print("✅ Incorrect solution evaluated successfully with hint")
    
    # Test debugging challenge evaluation
    print("\nTesting debugging challenge evaluation:")
    
    # Define a buggy code
    buggy_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers) - 1  # Bug: should not subtract 1
"""
    
    # Define a fixed solution
    fixed_solution = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
"""
    
    # Define a bug comment
    bug_comment = "The function incorrectly subtracts 1 from the average."
    
    # Evaluate the solution
    result = evaluate_debugging_solution(fixed_solution, buggy_code, bug_comment)
    print(f"Status: {result['status']}")
    print(f"Feedback: {result['feedback']}")
    
    # Verify the solution is correct
    assert result['status'] == 'correct', "Correct debugging solution marked as incorrect"
    print("✅ Debugging solution evaluated successfully")
    
    # Test feedback generation for incorrect solutions
    print("\nTesting feedback generation for incorrect solutions:")
    
    # Define test results with errors
    test_results = [
        {
            "input": "5",
            "expected": "25",
            "actual": "10",
            "passed": False,
            "error": None
        }
    ]
    
    # Generate feedback
    feedback = generate_feedback_for_incorrect_solution(incorrect_solution, test_results, hint)
    print(f"Feedback: {feedback}")
    
    # Verify the feedback includes the hint
    assert hint in feedback, "Hint not included in feedback"
    print("✅ Feedback generated successfully with hint")

def main():
    """Run all tests."""
    print("=== Running Tests for LLM Challenge Generator and Coding Hints ===")
    
    # Run the tests
    test_multiple_choice_generation()
    test_difficulty_scaling()
    test_hint_functionality()
    test_wrong_answer_hints()
    
    print("\n=== All Tests Completed Successfully ===")

if __name__ == "__main__":
    main()

