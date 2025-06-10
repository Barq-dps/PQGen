"""
Fallback hint generator for different challenge types.

This module provides functions to generate fallback hints when the LLM doesn't provide one.
"""

import random

def generate_fallback_hint_for_multiple_choice(topic: str, difficulty: str) -> str:
    """Generate a fallback hint for multiple choice questions.
    
    Args:
        topic: The topic of the question
        difficulty: The difficulty level
        
    Returns:
        A hint string
    """
    easy_hints = [
        f"Think about the basic definition of {topic}.",
        f"Consider what {topic} is primarily used for.",
        f"Remember the fundamental concepts of {topic}.",
        f"Focus on the most common use case for {topic}.",
        f"Recall the basic properties of {topic}."
    ]
    
    medium_hints = [
        f"Consider the key characteristics of {topic} and how they apply in different contexts.",
        f"Think about the advantages and limitations of {topic}.",
        f"Analyze how {topic} compares to related concepts.",
        f"Consider both the theoretical and practical aspects of {topic}.",
        f"Look for the option that best aligns with standard {topic} principles."
    ]
    
    hard_hints = [
        f"Analyze the advanced applications of {topic} and their implications.",
        f"Consider edge cases and exceptions in how {topic} is implemented.",
        f"Think about optimization considerations related to {topic}.",
        f"Evaluate each option against best practices for {topic}.",
        f"Consider the subtle distinctions between similar concepts related to {topic}."
    ]
    
    if difficulty.lower() == "easy":
        return random.choice(easy_hints)
    elif difficulty.lower() == "hard":
        return random.choice(hard_hints)
    else:  # medium or default
        return random.choice(medium_hints)


def generate_fallback_hint_for_debugging(topic: str, difficulty: str, code: str) -> str:
    """Generate a fallback hint for debugging challenges.
    
    Args:
        topic: The topic of the challenge
        difficulty: The difficulty level
        code: The buggy code
        
    Returns:
        A hint string
    """
    easy_hints = [
        f"Check for syntax errors in the {topic} implementation.",
        f"Look for missing or incorrect variable declarations.",
        f"Check if there are any typos in function or variable names.",
        f"Verify that all parentheses, brackets, and braces are properly matched.",
        f"Make sure all required imports or dependencies are included."
    ]
    
    medium_hints = [
        f"Look for logical errors in how {topic} is being implemented.",
        f"Check the control flow and make sure conditions are evaluated correctly.",
        f"Verify that the algorithm handles edge cases properly.",
        f"Check for off-by-one errors in loops or indexing.",
        f"Examine how data is being transformed or processed at each step."
    ]
    
    hard_hints = [
        f"Consider edge cases and error handling in this {topic} implementation.",
        f"Look for subtle issues with concurrency or resource management.",
        f"Check for performance bottlenecks or inefficient algorithms.",
        f"Verify that the code handles all possible input scenarios correctly.",
        f"Examine how different components interact with each other."
    ]
    
    # Add code-specific hints based on simple analysis
    code_specific_hints = []
    
    if "for" in code and "range" in code:
        code_specific_hints.append("Check the loop range boundaries.")
    if "if" in code:
        code_specific_hints.append("Verify the conditional logic in the if statements.")
    if "return" in code:
        code_specific_hints.append("Make sure the return statement is returning the correct value.")
    if "=" in code:
        code_specific_hints.append("Check the assignment operations for potential issues.")
    if "import" in code:
        code_specific_hints.append("Verify that all necessary modules are imported correctly.")
    
    # Combine general and code-specific hints
    all_hints = []
    if difficulty.lower() == "easy":
        all_hints = easy_hints
    elif difficulty.lower() == "hard":
        all_hints = hard_hints
    else:  # medium or default
        all_hints = medium_hints
    
    if code_specific_hints:
        all_hints.extend(code_specific_hints)
    
    return random.choice(all_hints)


def generate_fallback_hint_for_coding(topic: str, difficulty: str, code_stub: str) -> str:
    """Generate a fallback hint for coding challenges.
    
    Args:
        topic: The topic of the challenge
        difficulty: The difficulty level
        code_stub: The code stub
        
    Returns:
        A hint string
    """
    easy_hints = [
        f"Start by understanding the basic operations needed for {topic}.",
        f"Break down the problem into simple steps.",
        f"Think about the input and output requirements carefully.",
        f"Consider using built-in functions or methods related to {topic}.",
        f"Start with a simple approach before optimizing."
    ]
    
    medium_hints = [
        f"Break down the problem into smaller steps involving {topic}.",
        f"Consider the time and space complexity of your solution.",
        f"Think about edge cases that might affect your implementation.",
        f"Consider using appropriate data structures for efficient operations.",
        f"Look for patterns in the problem that can simplify your solution."
    ]
    
    hard_hints = [
        f"Consider optimization techniques specific to {topic}.",
        f"Think about the algorithmic complexity and how to minimize it.",
        f"Consider multiple approaches and their trade-offs.",
        f"Break the problem into subproblems that can be solved independently.",
        f"Think about how to handle edge cases and error conditions efficiently."
    ]
    
    # Add code-specific hints based on simple analysis
    code_specific_hints = []
    
    if "def" in code_stub and "(" in code_stub and ")" in code_stub:
        function_signature = code_stub.split("\n")[0]
        if "," in function_signature:
            code_specific_hints.append("Pay attention to how you use the multiple parameters in your solution.")
        else:
            code_specific_hints.append("Consider what operations you need to perform on the input parameter.")
    
    if "return" in code_stub:
        code_specific_hints.append("Make sure your return value matches the expected output format.")
    
    if "#" in code_stub:
        code_specific_hints.append("The comments in the code stub provide important clues about the implementation.")
    
    # Combine general and code-specific hints
    all_hints = []
    if difficulty.lower() == "easy":
        all_hints = easy_hints
    elif difficulty.lower() == "hard":
        all_hints = hard_hints
    else:  # medium or default
        all_hints = medium_hints
    
    if code_specific_hints:
        all_hints.extend(code_specific_hints)
    
    return random.choice(all_hints)

