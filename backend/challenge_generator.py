import re
import uuid
import time
import random
from typing import List, Dict, Any

# Import fallback hint generator
from fallback_hints import (
    generate_fallback_hint_for_multiple_choice,
    generate_fallback_hint_for_debugging,
    generate_fallback_hint_for_fib
)

import logging
logger = logging.getLogger(__name__)


def generate_fallback_challenges(topics: List[str], difficulty: str = "medium") -> List[Dict[str, Any]]:
    """Generate exactly 2 challenges of each type using static templates for specific topics"""
    
    logger.info(f"Generating fallback challenges for topics: {topics}")
    
    # Use provided topics instead of extracting from content
    if not topics:
        logger.warning("No topics provided for fallback challenge generation")
        return []
    
    challenges = []
    challenge_types = ['multiple-choice', 'fill-in-the-blank', 'debugging']
    
    # Generate exactly 1 challenge of each type
    for challenge_type in challenge_types:
        for i in range(1):  # Generate 1 of each type
            try:
                # Use different topics for variety
                topic_index = (len(challenges)) % len(topics)
                topic = topics[topic_index]
                
                challenge = generate_static_challenge(challenge_type, difficulty, topic, i)
                if challenge:
                    challenge['generated_by'] = 'static'  # Mark as static/fallback
                    challenges.append(challenge)
                    logger.info(f"Generated static {challenge_type} challenge #{i+1}: {topic}")
            except Exception as e:
                logger.error(f"Error generating static {challenge_type} challenge: {e}")
    
    logger.info(f"Generated {len(challenges)} fallback challenges")
    return challenges


def extract_basic_topics(content: str) -> List[str]:
    """Extract meaningful programming topics from content"""
    
    # Enhanced programming keywords and their corresponding topics
    topic_keywords = {
        'Sorting Algorithms': ['sort', 'bubble', 'quick', 'merge', 'heap', 'insertion'],
        'Search Algorithms': ['search', 'binary', 'linear', 'find', 'lookup'],
        'Data Structures': ['list', 'array', 'dict', 'set', 'tuple', 'stack', 'queue', 'tree', 'graph'],
        'Object-Oriented Programming': ['class', 'object', 'inheritance', 'polymorphism', 'encapsulation'],
        'Functions and Methods': ['def ', 'function', 'method', 'return', 'parameter', 'argument'],
        'Control Flow': ['for ', 'while ', 'if ', 'else', 'elif', 'loop', 'iteration', 'condition'],
        'String Processing': ['string', 'str(', 'text', 'character', 'substring', 'split', 'join'],
        'File Operations': ['file', 'open(', 'read(', 'write(', 'close', 'with open'],
        'Error Handling': ['try:', 'except', 'error', 'exception', 'finally', 'raise'],
        'Variables and Types': ['variable', 'int', 'float', 'bool', 'assignment', 'declare'],
        'List Operations': ['append', 'extend', 'insert', 'remove', 'pop', 'index', 'slice'],
        'Dictionary Operations': ['keys()', 'values()', 'items()', 'get()', 'update'],
        'Mathematical Operations': ['math', 'calculation', 'arithmetic', 'sum', 'average', 'max', 'min'],
        'Recursion': ['recursive', 'recursion', 'base case', 'recursive call'],
        'Algorithm Complexity': ['complexity', 'big o', 'time', 'space', 'efficiency', 'optimization']
    }
    
    found_topics = []
    content_lower = content.lower()
    
    # Find topics based on keywords
    for topic, keywords in topic_keywords.items():
        for keyword in keywords:
            if keyword.lower() in content_lower:
                found_topics.append(topic)
                break
    
    # Extract specific function names and convert to meaningful topics
    function_matches = re.findall(r'\bdef\s+(\w+)', content, re.IGNORECASE)
    for func in function_matches[:3]:  # Limit to first 3 functions
        if len(func) > 3 and not func.startswith('__'):  # Only meaningful function names
            # Convert function name to topic
            func_clean = func.replace('_', ' ').title()
            topic_name = f"{func_clean} Implementation"
            found_topics.append(topic_name)
    
    # Extract class names and convert to topics
    class_matches = re.findall(r'\bclass\s+(\w+)', content, re.IGNORECASE)
    for cls in class_matches[:2]:  # Limit to first 2 classes
        if len(cls) > 3:  # Only meaningful class names
            topic_name = f"{cls} Class Design"
            found_topics.append(topic_name)
    
    # Look for algorithm names in comments
    algorithm_patterns = [
        r'(?:implement|algorithm|solve)[\s:]+(\w+(?:\s+\w+)?)',
        r'(\w+\s+sort)',
        r'(\w+\s+search)',
        r'(\w+\s+tree)',
        r'(\w+\s+algorithm)'
    ]
    
    for pattern in algorithm_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches[:2]:
            if len(match) > 3:
                topic_name = match.title()
                found_topics.append(topic_name)
    
    # Remove duplicates while preserving order
    unique_topics = []
    for topic in found_topics:
        if topic not in unique_topics:
            unique_topics.append(topic)
    
    # If no specific topics found, use meaningful generic ones
    if not unique_topics:
        unique_topics = [
            "Python Programming Fundamentals",
            "Algorithm Implementation", 
            "Data Structure Operations",
            "Problem Solving Techniques",
            "Code Logic and Control Flow",
            "Programming Best Practices"
        ]
    
    # Ensure we have at least 6 topics for variety
    while len(unique_topics) < 6:
        additional_topics = [
            "Advanced Programming Concepts",
            "Code Optimization", 
            "Software Design Patterns",
            "Computational Thinking",
            "Programming Methodology",
            "Code Analysis and Testing",
            "Memory Management",
            "Performance Optimization"
        ]
        for topic in additional_topics:
            if topic not in unique_topics:
                unique_topics.append(topic)
                if len(unique_topics) >= 6:
                    break
    
    logger.info(f"Extracted {len(unique_topics)} topics: {unique_topics[:6]}")
    return unique_topics


def generate_static_challenge(challenge_type: str, difficulty: str, topic: str, index: int) -> Dict[str, Any]:
    """Generate a static challenge based on templates"""
    
    if challenge_type == 'multiple-choice':
        return generate_static_mcq(difficulty, topic, index)
    elif challenge_type == 'fill-in-the-blank':
        return generate_static_fill_in_blank(difficulty, topic, index)
    elif challenge_type == 'debugging':
        return generate_static_debugging(difficulty, topic, index)
    
    return None


def generate_static_mcq(difficulty: str, topic: str, index: int) -> Dict[str, Any]:
    """Generate static multiple choice questions"""
    
    mcq_templates = {
        'easy': [
            {
                'question': f'What is the primary purpose of {topic} in programming?',
                'options': [
                    f'To implement {topic.lower()} functionality effectively',
                    'To handle user input exclusively',
                    'To manage memory allocation only',
                    'To create graphical user interfaces'
                ],
                'correct_answer': 0,
                'explanation': f'{topic} is primarily used for implementing specific programming functionality and solving computational problems.'
            },
            {
                'question': f'Which of the following best describes {topic}?',
                'options': [
                    'It only works with integer data types',
                    f'It provides essential operations for {topic.lower()}',
                    'It requires external libraries to function',
                    'It cannot be used within functions'
                ],
                'correct_answer': 1,
                'explanation': f'{topic} provides essential operations and techniques for solving programming problems.'
            }
        ],
        'medium': [
            {
                'question': f'When implementing {topic}, what is the most critical consideration?',
                'options': [
                    'Using the shortest variable names possible',
                    'Avoiding all comments in the code',
                    f'Ensuring efficiency and correctness of {topic.lower()} operations',
                    'Using only global variables'
                ],
                'correct_answer': 2,
                'explanation': f'Efficiency and correctness are crucial when implementing {topic} to ensure optimal performance and reliable results.'
            },
            {
                'question': f'What is the typical time complexity consideration for {topic}?',
                'options': [
                    'Always O(1) constant time',
                    'Always O(n²) quadratic time',
                    f'Depends on the specific {topic.lower()} implementation approach',
                    'Time complexity is never relevant'
                ],
                'correct_answer': 2,
                'explanation': f'Time complexity for {topic} varies based on the specific implementation approach and algorithm chosen.'
            }
        ],
        'hard': [
            {
                'question': f'In advanced {topic} implementations, which optimization strategy is most effective?',
                'options': [
                    'Using only global variables for all data',
                    f'Applying algorithmic optimizations and design patterns specific to {topic.lower()}',
                    'Avoiding all function calls to reduce overhead',
                    'Using only built-in functions without custom logic'
                ],
                'correct_answer': 1,
                'explanation': f'Algorithmic optimizations and appropriate design patterns specific to {topic} provide the most effective performance improvements.'
            },
            {
                'question': f'What is the most challenging aspect of {topic} in large-scale systems?',
                'options': [
                    'Understanding basic syntax requirements',
                    'Choosing appropriate variable names',
                    f'Managing complexity, scalability, and edge cases in {topic.lower()}',
                    'Formatting print statements correctly'
                ],
                'correct_answer': 2,
                'explanation': f'Managing complexity, ensuring scalability, and handling edge cases are the most challenging aspects of {topic} in large-scale systems.'
            }
        ]
    }
    
    template = mcq_templates[difficulty][index % 2]
    
    return {
        'id': str(uuid.uuid4()),
        'type': 'multiple-choice',
        'topic': topic,
        'question': template['question'],
        'options': template['options'],
        'correct_answer': template['correct_answer'],
        'explanation': template['explanation'],
        'difficulty': difficulty,
        'generated_by': 'static'
    }


def generate_static_fill_in_blank(difficulty: str, topic: str, index: int) -> Dict[str, Any]:
    """Generate static fill-in-the-blank challenges"""
    
    # Create meaningful function names based on topic
    topic_clean = topic.lower().replace(' ', '_').replace('-', '_')
    function_base = topic_clean.split('_')[0] if '_' in topic_clean else topic_clean[:10]
    
    fill_blank_templates = {
        'easy': [
            {
                'question': f'Complete the basic {topic} function:',
                'code_template': f'def {function_base}_example(data):\n    if data is __BLANK_1__:\n        return __BLANK_2__\n    result = len(__BLANK_3__)\n    return result',
                'blanks': [
                    {
                        'id': 'BLANK_1',
                        'correct_answers': ['None', 'none', 'null'],
                        'hint': 'What value represents "nothing" in Python?',
                        'explanation': 'None is Python\'s null value'
                    },
                    {
                        'id': 'BLANK_2', 
                        'correct_answers': ['0', 'zero', '[]', 'None'],
                        'hint': 'What should you return for empty/null data?',
                        'explanation': 'Return 0 or an empty value for null input'
                    },
                    {
                        'id': 'BLANK_3',
                        'correct_answers': ['data', 'data '],
                        'hint': 'What variable contains the input?',
                        'explanation': 'Use the data parameter passed to the function'
                    }
                ],
                'explanation': f'This demonstrates basic {topic} concepts with null checking and data processing.'
            },
            {
                'question': f'Fill in the {topic} loop structure:',
                'code_template': f'def process_{function_base}(items):\n    result = []\n    for item __BLANK_1__ items:\n        if item __BLANK_2__ 0:\n            result.__BLANK_3__(item)\n    return result',
                'blanks': [
                    {
                        'id': 'BLANK_1',
                        'correct_answers': ['in', 'in '],
                        'hint': 'How do you iterate through a collection in Python?',
                        'explanation': 'Use "in" to iterate through items in a collection'
                    },
                    {
                        'id': 'BLANK_2',
                        'correct_answers': ['>', '>=', '!='],
                        'hint': 'What comparison checks if a number is positive?',
                        'explanation': 'Use > to check if a number is greater than zero'
                    },
                    {
                        'id': 'BLANK_3',
                        'correct_answers': ['append', 'add'],
                        'hint': 'How do you add an item to a list?',
                        'explanation': 'Use append() to add items to a list'
                    }
                ],
                'explanation': f'This shows basic {topic} iteration and filtering patterns.'
            }
        ],
        'medium': [
            {
                'question': f'Complete the {topic} algorithm:',
                'code_template': f'def {function_base}_search(arr, target):\n    left, right = 0, len(arr) - __BLANK_1__\n    while left __BLANK_2__ right:\n        mid = (left + right) // __BLANK_3__\n        if arr[mid] == target:\n            return __BLANK_4__\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return __BLANK_5__',
                'blanks': [
                    {
                        'id': 'BLANK_1',
                        'correct_answers': ['1'],
                        'hint': 'Array indices start at 0, so the last index is...?',
                        'explanation': 'Last index is length - 1'
                    },
                    {
                        'id': 'BLANK_2',
                        'correct_answers': ['<=', '≤'],
                        'hint': 'When should the search continue?',
                        'explanation': 'Continue while left is less than or equal to right'
                    },
                    {
                        'id': 'BLANK_3',
                        'correct_answers': ['2'],
                        'hint': 'How do you find the middle point?',
                        'explanation': 'Divide by 2 to find the midpoint'
                    },
                    {
                        'id': 'BLANK_4',
                        'correct_answers': ['mid', 'mid '],
                        'hint': 'What should you return when target is found?',
                        'explanation': 'Return the index where target was found'
                    },
                    {
                        'id': 'BLANK_5',
                        'correct_answers': ['-1', 'None'],
                        'hint': 'What indicates the target was not found?',
                        'explanation': 'Return -1 or None when target is not found'
                    }
                ],
                'explanation': f'This implements a binary search algorithm, a key {topic} concept.'
            },
            {
                'question': f'Complete the {topic} data structure:',
                'code_template': f'class {function_base.title()}Stack:\n    def __init__(self):\n        self.__BLANK_1__ = []\n    \n    def push(self, item):\n        self.____.__BLANK_2__(item)\n    \n    def pop(self):\n        if self.is_empty():\n            return __BLANK_3__\n        return self.____.__BLANK_4__()\n    \n    def is_empty(self):\n        return len(self.____) == __BLANK_5__',
                'blanks': [
                    {
                        'id': 'BLANK_1',
                        'correct_answers': ['items', 'data', 'stack'],
                        'hint': 'What should store the stack elements?',
                        'explanation': 'Use a list to store stack items'
                    },
                    {
                        'id': 'BLANK_2',
                        'correct_answers': ['append', 'add'],
                        'hint': 'How do you add to the end of a list?',
                        'explanation': 'Use append() to add items to the end'
                    },
                    {
                        'id': 'BLANK_3',
                        'correct_answers': ['None', 'null'],
                        'hint': 'What should you return from an empty stack?',
                        'explanation': 'Return None for empty stack operations'
                    },
                    {
                        'id': 'BLANK_4',
                        'correct_answers': ['pop', 'pop()'],
                        'hint': 'How do you remove the last item from a list?',
                        'explanation': 'Use pop() to remove and return the last item'
                    },
                    {
                        'id': 'BLANK_5',
                        'correct_answers': ['0', 'zero'],
                        'hint': 'What length indicates an empty collection?',
                        'explanation': 'Length of 0 means the collection is empty'
                    }
                ],
                'explanation': f'This implements a stack data structure, fundamental to {topic}.'
            }
        ],
        'hard': [
            {
                'question': f'Complete the advanced {topic} implementation:',
                'code_template': f'def {function_base}_advanced(data, key=None):\n    if not data:\n        return __BLANK_1__\n    \n    if key is None:\n        key = lambda x: __BLANK_2__\n    \n    sorted_data = __BLANK_3__(data, key=key)\n    result = {{}}\n    \n    for item in sorted_data:\n        group_key = key(item)\n        if group_key not in result:\n            result[group_key] = __BLANK_4__\n        result[group_key].__BLANK_5__(item)\n    \n    return result',
                'blanks': [
                    {
                        'id': 'BLANK_1',
                        'correct_answers': ['{}', 'dict()', 'None'],
                        'hint': 'What should you return for empty input?',
                        'explanation': 'Return an empty dict or None for empty input'
                    },
                    {
                        'id': 'BLANK_2',
                        'correct_answers': ['x', 'item', 'str(x)'],
                        'hint': 'What is the default key function?',
                        'explanation': 'Default key function returns the item itself'
                    },
                    {
                        'id': 'BLANK_3',
                        'correct_answers': ['sorted', 'sort'],
                        'hint': 'How do you sort a collection?',
                        'explanation': 'Use sorted() to sort a collection'
                    },
                    {
                        'id': 'BLANK_4',
                        'correct_answers': ['[]', 'list()'],
                        'hint': 'What should initialize each group?',
                        'explanation': 'Initialize each group with an empty list'
                    },
                    {
                        'id': 'BLANK_5',
                        'correct_answers': ['append', 'add'],
                        'hint': 'How do you add items to a group?',
                        'explanation': 'Use append() to add items to the group list'
                    }
                ],
                'explanation': f'This demonstrates advanced {topic} with grouping and sorting.'
            },
            {
                'question': f'Complete the {topic} optimization:',
                'code_template': f'def {function_base}_optimized(data, cache=None):\n    if cache is __BLANK_1__:\n        cache = {{}}\n    \n    cache_key = __BLANK_2__(data)\n    if cache_key __BLANK_3__ cache:\n        return cache[cache_key]\n    \n    # Complex computation here\n    result = sum(x**2 for x in data if x __BLANK_4__ 0)\n    \n    cache[cache_key] = result\n    return __BLANK_5__',
                'blanks': [
                    {
                        'id': 'BLANK_1',
                        'correct_answers': ['None', 'none'],
                        'hint': 'How do you check if cache was not provided?',
                        'explanation': 'Check if cache is None'
                    },
                    {
                        'id': 'BLANK_2',
                        'correct_answers': ['tuple', 'str', 'hash'],
                        'hint': 'How do you create a hashable key from data?',
                        'explanation': 'Convert data to tuple or string for hashing'
                    },
                    {
                        'id': 'BLANK_3',
                        'correct_answers': ['in', 'in '],
                        'hint': 'How do you check if a key exists in a dict?',
                        'explanation': 'Use "in" to check key existence'
                    },
                    {
                        'id': 'BLANK_4',
                        'correct_answers': ['>', '>=', '!='],
                        'hint': 'What condition filters positive numbers?',
                        'explanation': 'Use > to check for positive numbers'
                    },
                    {
                        'id': 'BLANK_5',
                        'correct_answers': ['result', 'cache[cache_key]'],
                        'hint': 'What should the function return?',
                        'explanation': 'Return the computed result'
                    }
                ],
                'explanation': f'This shows {topic} optimization using memoization.'
            }
        ]
    }
    
    template = fill_blank_templates[difficulty][index % 2]
    
    return {
        'id': str(uuid.uuid4()),
        'type': 'fill-in-the-blank',
        'topic': topic,
        'question': template['question'],
        'code_template': template['code_template'],
        'blanks': template['blanks'],
        'hint': f'Focus on {topic} fundamentals and common programming patterns.',
        'explanation': template['explanation'],
        'difficulty': difficulty,
        'generated_by': 'static'
    }


def generate_static_debugging(difficulty: str, topic: str, index: int) -> Dict[str, Any]:
    """Generate static debugging challenges"""
    
    # Create meaningful function names based on topic
    topic_clean = topic.lower().replace(' ', '_').replace('-', '_')
    function_base = topic_clean.split('_')[0] if '_' in topic_clean else topic_clean[:10]
    
    debugging_templates = {
        'easy': [
            {
                'question': f'The following code is supposed to implement a basic {topic} operation, but it contains bugs. Find and fix all the errors.',
                'buggy_code': f'def buggy_{function_base}(data):\n    # This function should implement {topic}\n    result = data\n    if result = None:  # Bug: assignment instead of comparison\n        return "No data provided"\n    \n    # Bug: calling non-existent method\n    processed = result.process_data()\n    return processed',
                'explanation': f'The bugs are: 1) Using assignment (=) instead of comparison (==) in the if statement, and 2) calling a non-existent method process_data() on the result. Fix by using == for comparison and implementing proper {topic} processing.'
            },
            {
                'question': f'This {topic} function has logical errors that prevent it from working correctly. Identify and correct them.',
                'buggy_code': f'def process_{function_base}(items):\n    # Process items using {topic} principles\n    total = 0\n    for item in items\n        total += item  # Bug: missing colon\n    \n    # Bug: incorrect return logic\n    if total > 0\n        return total\n    else\n        return "Error"  # Should return 0, not string',
                'explanation': f'The bugs are: 1) Missing colon after the for loop statement, 2) Missing colon after the if statement, and 3) Returning a string "Error" instead of 0 for empty/zero cases. Fix by adding colons and returning consistent data types.'
            }
        ],
        'medium': [
            {
                'question': f'This {topic} implementation has subtle bugs that affect its correctness. Debug and fix the issues.',
                'buggy_code': f'def advanced_{function_base}(data, threshold=10):\n    # Advanced {topic} processing with threshold\n    results = []\n    \n    for i in range(len(data)):\n        if data[i] >= threshold:  # Bug: should be >\n            processed = data[i] * 2\n            results.append(processed)\n    \n    # Bug: modifying list during iteration\n    for item in results:\n        if item > 50:\n            results.remove(item)\n    \n    return results',
                'explanation': f'The bugs are: 1) Using >= instead of > for threshold comparison (off-by-one error), and 2) Modifying the list while iterating over it, which can skip elements. Fix by using correct comparison and creating a new list or iterating backwards.'
            },
            {
                'question': f'This {topic} function has performance and logic issues. Find and resolve the problems.',
                'buggy_code': f'def optimized_{function_base}(data_list):\n    # Optimized {topic} processing\n    result = []\n    \n    for i in range(len(data_list)):\n        for j in range(len(data_list)):  # Bug: unnecessary nested loop\n            if i == j:\n                # Bug: inefficient string concatenation\n                result += str(data_list[i])\n    \n    # Bug: returning wrong data type\n    return result',
                'explanation': f'The bugs are: 1) Unnecessary nested loop creating O(n²) complexity, 2) Inefficient string concatenation using +=, and 3) Returning a list of characters instead of a proper result. Fix by removing nested loop, using proper string methods, and returning appropriate data type.'
            }
        ],
        'hard': [
            {
                'question': f'This complex {topic} implementation has multiple subtle bugs including race conditions and edge cases. Debug thoroughly.',
                'buggy_code': f'import threading\n\ndef complex_{function_base}(data, workers=4):\n    # Complex {topic} with threading\n    results = []\n    lock = threading.Lock()\n    \n    def worker(chunk):\n        local_results = []\n        for item in chunk:\n            # Bug: race condition - accessing shared resource\n            if len(results) < 100:  # Bug: checking shared state without lock\n                processed = item ** 2\n                local_results.append(processed)\n        \n        # Bug: potential race condition\n        results.extend(local_results)\n    \n    # Bug: incorrect chunk calculation\n    chunk_size = len(data) // workers\n    threads = []\n    \n    for i in range(workers):\n        start = i * chunk_size\n        end = start + chunk_size  # Bug: last chunk may miss elements\n        chunk = data[start:end]\n        \n        thread = threading.Thread(target=worker, args=(chunk,))\n        threads.append(thread)\n        thread.start()\n    \n    # Bug: not joining threads properly\n    for thread in threads:\n        thread.join()\n    \n    return results',
                'explanation': f'The bugs are: 1) Race condition when checking len(results) without lock, 2) Race condition when extending results list, 3) Incorrect chunk calculation that may miss last elements, and 4) Not using lock when modifying shared results. Fix by proper locking, correct chunking, and thread-safe operations.'
            },
            {
                'question': f'This enterprise-level {topic} system has architectural flaws and edge case bugs. Identify and fix all issues.',
                'buggy_code': f'class Enterprise{topic.replace(" ", "").replace("-", "")}System:\n    def __init__(self):\n        self.cache = {{}}\n        self.stats = {{"processed": 0, "errors": 0}}\n    \n    def process_batch(self, batch_data, cache_enabled=True):\n        # Enterprise {topic} batch processing\n        if not batch_data:  # Bug: should handle None differently\n            return []\n        \n        results = []\n        \n        for data in batch_data:\n            try:\n                # Bug: cache key collision potential\n                cache_key = str(data)\n                \n                if cache_enabled and cache_key in self.cache:\n                    result = self.cache[cache_key]\n                else:\n                    result = self._process_single(data)\n                    # Bug: unbounded cache growth\n                    if cache_enabled:\n                        self.cache[cache_key] = result\n                \n                results.append(result)\n                self.stats["processed"] += 1\n                \n            except Exception as e:\n                # Bug: swallowing exceptions without proper logging\n                self.stats["errors"] += 1\n                continue  # Bug: should handle partial failures better\n        \n        return results\n    \n    def _process_single(self, data):\n        # Bug: no input validation\n        return data * 2  # Oversimplified processing',
                'explanation': f'The bugs are: 1) Not handling None input properly, 2) Cache key collisions with str() conversion, 3) Unbounded cache growth leading to memory leaks, 4) Swallowing exceptions without logging, 5) Poor error handling for partial failures, and 6) No input validation. Fix by proper input validation, better cache key generation, cache size limits, proper exception handling, and logging.'
            }
        ]
    }
    
    template = debugging_templates[difficulty][index % 2]
    
    return {
        'id': str(uuid.uuid4()),
        'type': 'debugging',
        'topic': topic,
        'question': template['question'],
        'code_stub': template['buggy_code'],
        'buggy_code': template['buggy_code'],
        'explanation': template['explanation'],
        'difficulty': difficulty,
        'generated_by': 'static'
    }

