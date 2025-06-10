"""
Code evaluation module for assessing user-submitted code.

This module provides functions to evaluate user-submitted code against test cases
and generate helpful feedback when solutions are incorrect.
"""

import sys
import io
import traceback
import ast
import re
from contextlib import redirect_stdout, redirect_stderr

def evaluate_coding_solution(user_code, test_cases, challenge_hint=None):
    """Evaluate a user-submitted coding solution against test cases.
    
    Args:
        user_code: The user-submitted code as a string
        test_cases: List of test cases, each with 'input' and 'expected' fields
        challenge_hint: The hint provided with the challenge
        
    Returns:
        A dictionary with evaluation results
    """
    results = {
        'status': 'incorrect',
        'feedback': '',
        'test_results': [],
        'error': None
    }
    
    # Check for syntax errors first
    try:
        ast.parse(user_code)
    except SyntaxError as e:
        results['error'] = f"Syntax error: {str(e)}"
        results['feedback'] = f"Your code has a syntax error: {str(e)}. Check line {e.lineno}, column {e.offset}."
        return results
    
    # Extract the function name from the code
    function_name = None
    try:
        tree = ast.parse(user_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_name = node.name
                break
    except:
        pass
    
    if not function_name:
        results['error'] = "Could not find a function definition in your code."
        results['feedback'] = "Make sure your code defines a function."
        return results
    
    # Create a namespace to execute the code
    namespace = {}
    
    # Execute the code to define the function
    try:
        exec(user_code, namespace)
    except Exception as e:
        results['error'] = f"Error defining function: {str(e)}"
        results['feedback'] = f"There was an error in your code: {str(e)}"
        return results
    
    # Get the function object
    if function_name not in namespace:
        results['error'] = f"Function '{function_name}' not found."
        results['feedback'] = f"Could not find the function '{function_name}' in your code."
        return results
    
    function = namespace[function_name]
    
    # Run each test case
    all_passed = True
    for i, test_case in enumerate(test_cases):
        test_input = test_case.get('input')
        expected_output = test_case.get('expected')
        
        test_result = {
            'input': test_input,
            'expected': expected_output,
            'actual': None,
            'passed': False,
            'error': None
        }
        
        # Capture stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Execute the function with the test input
                actual_output = function(test_input)
                
            # Check if there was any output to stdout
            stdout_output = stdout_buffer.getvalue().strip()
            if stdout_output:
                test_result['stdout'] = stdout_output
            
            # Check if the output matches the expected output
            test_result['actual'] = actual_output
            
            # Compare the actual output with the expected output
            if str(actual_output).strip() == str(expected_output).strip():
                test_result['passed'] = True
            else:
                all_passed = False
                
        except Exception as e:
            all_passed = False
            test_result['error'] = str(e)
            test_result['traceback'] = traceback.format_exc()
        
        results['test_results'].append(test_result)
    
    # Set the overall status
    if all_passed:
        results['status'] = 'correct'
        results['feedback'] = "All test cases passed! Great job!"
    else:
        # Generate helpful feedback for incorrect solutions
        results['feedback'] = generate_feedback_for_incorrect_solution(
            user_code, results['test_results'], challenge_hint
        )
    
    return results

def evaluate_debugging_solution(user_code, buggy_code, bug_comment=None):
    """Evaluate a user-submitted debugging solution.
    
    Args:
        user_code: The user-submitted fixed code
        buggy_code: The original buggy code
        bug_comment: Description of the bug
        
    Returns:
        A dictionary with evaluation results
    """
    results = {
        'status': 'incorrect',
        'feedback': '',
        'error': None
    }
    
    # Check for syntax errors first
    try:
        ast.parse(user_code)
    except SyntaxError as e:
        results['error'] = f"Syntax error: {str(e)}"
        results['feedback'] = f"Your code has a syntax error: {str(e)}. Check line {e.lineno}, column {e.offset}."
        return results
    
    # Check if the code has been modified
    if user_code.strip() == buggy_code.strip():
        results['feedback'] = "You haven't made any changes to the code. Try to find and fix the bug."
        return results
    
    # Try to execute the code
    try:
        # Create a namespace to execute the code
        namespace = {}
        
        # Execute the code
        exec(user_code, namespace)
        
        # If we get here, the code executed without errors
        # This is a simple check - in a real system, you would run tests
        results['status'] = 'correct'
        results['feedback'] = "Your solution runs without errors. Good job!"
        
    except Exception as e:
        results['error'] = f"Error executing code: {str(e)}"
        results['feedback'] = f"Your code still has an error: {str(e)}"
    
    return results

def generate_feedback_for_incorrect_solution(user_code, test_results, challenge_hint=None):
    """Generate helpful feedback for incorrect solutions.
    
    Args:
        user_code: The user-submitted code
        test_results: Results of running the test cases
        challenge_hint: The hint provided with the challenge
        
    Returns:
        A string with helpful feedback
    """
    # Start with a general message
    feedback = "Your solution doesn't pass all test cases. "
    
    # Check for common issues
    if any(result.get('error') for result in test_results):
        # There was an error during execution
        error_result = next(result for result in test_results if result.get('error'))
        feedback += f"Your code raised an error: {error_result.get('error')}. "
        
        # Check for specific error types and provide targeted advice
        error_msg = error_result.get('error', '')
        if 'index out of range' in error_msg or 'IndexError' in error_msg:
            feedback += "Check your array indexing. You might be trying to access an element that doesn't exist. "
        elif 'division by zero' in error_msg or 'ZeroDivisionError' in error_msg:
            feedback += "Your code is trying to divide by zero. Make sure to handle this case. "
        elif 'TypeError' in error_msg:
            feedback += "There's a type mismatch in your code. Check that you're using the right data types. "
    else:
        # Code executed but produced incorrect results
        # Find the first failing test case
        failing_test = next((result for result in test_results if not result.get('passed')), None)
        if failing_test:
            feedback += f"For input '{failing_test.get('input')}', your code returned '{failing_test.get('actual')}' but the expected output is '{failing_test.get('expected')}'. "
    
    # Add code-specific feedback
    if 'for' in user_code and 'range' in user_code:
        feedback += "Check your loop ranges. Make sure you're iterating over the correct indices. "
    if 'if' in user_code:
        feedback += "Review your conditional logic. Are all conditions correct? "
    if 'return' in user_code:
        feedback += "Make sure you're returning the correct value. "
    
    # Add the challenge hint if available
    if challenge_hint:
        feedback += f"\n\nHint: {challenge_hint}"
    
    return feedback

