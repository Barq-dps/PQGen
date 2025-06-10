import json
import re
import uuid
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Import the LLM-based challenge generator
try:
    from llm_challenge_generator import (
        generate_challenge_with_llm, 
        is_model_ready, 
        load_model_in_background
    )
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("LLM challenge generator not available. Using template-based generation only.")

# Add the missing function that app.py is trying to import
def generate_challenges_for_topics(pdf_content, max_challenges_per_topic=None, difficulty="medium"):
    """
    Generate programming challenges based on PDF content with specified difficulty.
    This is the main entry function that app.py imports.
    
    Args:
        pdf_content (dict or list): Structured content from the PDF or list of topics
        max_challenges_per_topic (int or str, optional): Maximum number of challenges per topic
        difficulty (str, optional): Difficulty level - "easy", "medium", or "hard"
        
    Returns:
        list: Generated challenges
    """
    # Handle different input types
    if pdf_content is None:
        return []
    
    # Convert max_challenges_per_topic to int if it's a string
    if max_challenges_per_topic is not None:
        try:
            max_challenges_per_topic = int(max_challenges_per_topic)
        except (ValueError, TypeError):
            max_challenges_per_topic = None
        
    # If pdf_content is a list, convert it to the expected dict format
    if isinstance(pdf_content, list):
        # Create a structured dict with the list as topics
        structured_content = {
            'topics': pdf_content,
            'text': '',
            'topic_sections': [],
            'topic_code_blocks': {},
            'topic_key_concepts': {}
        }
        pdf_content = structured_content
    
    # Ensure pdf_content is a dict with a 'topics' key
    if not isinstance(pdf_content, dict):
        return []
    
    # If 'topics' is missing, try to extract it from other keys
    if 'topics' not in pdf_content:
        # Try to find topics in other possible keys
        for key in ['topic_sections', 'sections', 'headings']:
            if key in pdf_content and pdf_content[key]:
                pdf_content['topics'] = [section.get('title', 'Unknown Topic') 
                                        for section in pdf_content[key]]
                break
        
        # If still no topics, return empty list
        if 'topics' not in pdf_content:
            return []
    
    # Start loading the LLM model in the background if available
    if LLM_AVAILABLE:
        load_model_in_background()
    
    generator = ChallengeGenerator()
    return generator.generate_challenges(pdf_content, max_challenges_per_topic, difficulty)

class ChallengeGenerator:
    """
    Enhanced Challenge Generator with difficulty selection and dynamic prompt generation.
    Generates programming challenges based on PDF content with adjustable difficulty levels.
    """
    
    def __init__(self, llm=None):
        """Initialize the Challenge Generator."""
        self.llm = llm
        
        # Define challenge types and their templates
        self.challenge_types = {
            "multiple_choice": {
                "prefix": "MULTIPLE CHOICE QUESTION:",
                "template": self._get_multiple_choice_template()
            },
            "debugging": {
                "prefix": "DEBUGGING CHALLENGE:",
                "template": self._get_debugging_template()
            },
            "coding": {
                "prefix": "CODING CHALLENGE:",
                "template": self._get_coding_template()
            }
        }
        
        # Enhanced mapping of topics to their most appropriate challenge types
        # Primary challenge type is first in the list (highest priority)
        self.topic_to_challenge_types = {
            "python basics": ["multiple_choice"],
            "basics": ["multiple_choice"],
            "introduction": ["multiple_choice"],
            "overview": ["multiple_choice"],
            "syntax": ["multiple_choice"],
            
            "data structures": ["coding"],
            "lists": ["coding"],
            "dictionaries": ["coding"],
            "arrays": ["coding"],
            "sets": ["coding"],
            "tuples": ["coding"],
            "stacks": ["coding"],
            "queues": ["coding"],
            "linked lists": ["coding"],
            "trees": ["coding"],
            "graphs": ["coding"],
            
            "algorithms": ["coding"],
            "sorting": ["coding"],
            "searching": ["coding"],
            "recursion": ["coding"],
            "dynamic programming": ["coding"],
            "greedy": ["coding"],
            
            "functions": ["coding"],
            "methods": ["coding"],
            "parameters": ["multiple_choice"],
            "arguments": ["multiple_choice"],
            
            "modules": ["multiple_choice"],
            "packages": ["multiple_choice"],
            "libraries": ["multiple_choice"],
            "imports": ["multiple_choice"],
            
            "error handling": ["debugging"],
            "exceptions": ["debugging"],
            "try except": ["debugging"],
            "debugging": ["debugging"],
            "errors": ["debugging"],
            "bugs": ["debugging"],
            "troubleshooting": ["debugging"],
            
            "classes": ["coding"],
            "objects": ["coding"],
            "oop": ["coding"],
            "inheritance": ["coding"],
            "polymorphism": ["coding"],
            "encapsulation": ["coding"],
            
            "file handling": ["debugging"],
            "file operations": ["debugging"],
            "io": ["debugging"],
            "input output": ["debugging"],
            
            "regular expressions": ["debugging"],
            "regex": ["debugging"],
            "pattern matching": ["debugging"],
            
            "web development": ["coding"],
            "web": ["coding"],
            "html": ["coding"],
            "css": ["coding"],
            "javascript": ["coding"],
            "frontend": ["coding"],
            
            "database": ["coding"],
            "sql": ["coding"],
            "nosql": ["coding"],
            "data storage": ["coding"],
            
            "api": ["coding"],
            "rest": ["coding"],
            "graphql": ["coding"],
            "endpoints": ["coding"],
            
            "testing": ["debugging"],
            "unit tests": ["debugging"],
            "integration tests": ["debugging"],
            "test cases": ["debugging"],
            
            "object-oriented programming": ["coding"],
            "functional programming": ["debugging"],
            "concurrent programming": ["coding"],
            
            "default": ["multiple_choice", "coding", "debugging"]
        }
        
        # Define topic categories for specialized templates
        self.topic_categories = {
            # Programming paradigms
            "paradigm": [
                "object-oriented", "oop", "functional", "concurrent", "procedural", 
                "declarative", "imperative", "event-driven", "aspect-oriented"
            ],
            
            # Data structures
            "data_structure": [
                "data structure", "list", "array", "dictionary", "set", "tuple", "stack", 
                "queue", "linked list", "tree", "graph", "hash", "map", "heap"
            ],
            
            # Algorithms
            "algorithm": [
                "algorithm", "sort", "search", "recursion", "dynamic programming", 
                "greedy", "divide and conquer", "backtracking", "branch and bound"
            ],
            
            # Language features
            "language_feature": [
                "function", "method", "class", "module", "package", "library", 
                "import", "variable", "constant", "parameter", "argument"
            ],
            
            # Error handling
            "error_handling": [
                "error handling", "exception", "try except", "debugging", 
                "error", "bug", "troubleshooting"
            ],
            
            # Web development
            "web_development": [
                "web", "html", "css", "javascript", "frontend", "backend", 
                "fullstack", "responsive", "dom", "api", "rest", "graphql"
            ],
            
            # Database
            "database": [
                "database", "sql", "nosql", "data storage", "query", "table", 
                "record", "field", "index", "join", "transaction"
            ],
            
            # Testing
            "testing": [
                "testing", "unit test", "integration test", "test case", 
                "assertion", "mock", "stub", "coverage"
            ]
        }
        
        # Define difficulty levels and their characteristics
        self.difficulty_levels = {
            "easy": {
                "description": "Basic concepts with clear guidance",
                "prompt_modifier": "Create a straightforward question focusing on basic concepts. Include clear hints and guidance.",
                "test_case_count": 2,
                "code_complexity": "low",
                "option_clarity": "high"
            },
            "medium": {
                "description": "Core concepts with moderate guidance",
                "prompt_modifier": "Create a moderately challenging question covering core concepts. Provide some guidance but require deeper understanding.",
                "test_case_count": 3,
                "code_complexity": "medium",
                "option_clarity": "medium"
            },
            "hard": {
                "description": "Advanced concepts with minimal guidance",
                "prompt_modifier": "Create a challenging question focusing on advanced concepts. Provide minimal guidance and require comprehensive understanding.",
                "test_case_count": 4,
                "code_complexity": "high",
                "option_clarity": "low"
            }
        }
        
        # Store the prompts used for transparency
        self.last_used_prompts = {}
    
    def generate_challenges(self, pdf_content, max_challenges_per_topic=None, difficulty="medium"):
        """
        Generate programming challenges based on PDF content with specified difficulty.
        
        Args:
            pdf_content (dict): Structured content from the PDF
            max_challenges_per_topic (int or str): Maximum number of challenges per topic
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            list: Generated challenges
        """
        if not pdf_content or not pdf_content.get('topics'):
            return []
        
        # Ensure max_challenges_per_topic is an integer
        if max_challenges_per_topic is not None:
            try:
                max_challenges_per_topic = int(max_challenges_per_topic)
            except (ValueError, TypeError):
                max_challenges_per_topic = None
        
        # Validate and set difficulty
        if difficulty not in self.difficulty_levels:
            difficulty = "medium"
        
        # Store the selected difficulty for use in prompt generation
        self.selected_difficulty = difficulty
        
        topics = pdf_content.get('topics', [])
        
        # Dynamically adjust max_challenges_per_topic based on number of topics
        if max_challenges_per_topic is None:
            if len(topics) <= 3:
                max_challenges_per_topic = 2
            else:
                max_challenges_per_topic = 1
        
        # Ensure max_challenges_per_topic is an integer for comparisons
        max_challenges_per_topic = int(max_challenges_per_topic)
        
        challenges = []
        
        # Process each topic to generate challenges
        for topic in topics:
            # If topic is a dict, extract the name
            if isinstance(topic, dict) and 'name' in topic:
                topic_name = topic['name']
            elif isinstance(topic, dict) and 'title' in topic:
                topic_name = topic['title']
            else:
                topic_name = str(topic)
                
            # Get appropriate challenge types for this topic
            challenge_types = self._get_challenge_types_for_topic(topic_name)
            
            # Limit to max_challenges_per_topic
            # Ensure we're comparing integers
            if len(challenge_types) > max_challenges_per_topic:
                challenge_types = challenge_types[:max_challenges_per_topic]
            
            # Generate one challenge for each selected type
            topic_challenges = []
            
            for challenge_type in challenge_types:
                challenge = self._generate_challenge_for_topic(
                    topic_name, 
                    challenge_type, 
                    pdf_content,
                    difficulty
                )
                if challenge:
                    # Add difficulty to the challenge object
                    challenge['difficulty'] = difficulty
                    topic_challenges.append(challenge)
            
            challenges.extend(topic_challenges)
        
        return challenges
    
    def _get_challenge_types_for_topic(self, topic):
        """
        Determine the most appropriate challenge types for a given topic.
        
        Args:
            topic (str): The topic to generate challenges for
            
        Returns:
            list: Challenge types appropriate for this topic
        """
        # Normalize topic for matching
        normalized_topic = topic.lower()
        
        # Check for direct matches in our mapping
        for key, challenge_types in self.topic_to_challenge_types.items():
            if key == normalized_topic:
                return challenge_types
        
        # Check for partial matches (key is contained in topic)
        best_match = None
        best_match_length = 0
        
        for key, challenge_types in self.topic_to_challenge_types.items():
            if key in normalized_topic and len(key) > best_match_length:
                best_match = challenge_types
                best_match_length = len(key)
        
        if best_match:
            return best_match
        
        # Check for word-level matches
        topic_words = set(normalized_topic.split())
        
        for key, challenge_types in self.topic_to_challenge_types.items():
            key_words = set(key.split())
            if topic_words.intersection(key_words):
                return challenge_types
        
        # Use default if no match found
        return self.topic_to_challenge_types["default"]
    
    def _get_topic_category(self, topic):
        """
        Determine the category of a given topic for specialized template generation.
        
        Args:
            topic (str): The topic to categorize
            
        Returns:
            str: The category of the topic
        """
        topic_lower = topic.lower()
        
        # Check each category for matches
        for category, keywords in self.topic_categories.items():
            for keyword in keywords:
                if keyword in topic_lower:
                    return category
        
        # Default category if no match found
        return "general"
    
    def _generate_challenge_for_topic(self, topic, challenge_type, pdf_content, difficulty):
        """
        Generate a single challenge of the specified type for the given topic with specified difficulty.
        
        Args:
            topic (str): The topic to generate a challenge for
            challenge_type (str): The type of challenge to generate
            pdf_content (dict): Structured content from the PDF
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            dict: Generated challenge
        """
        # Get topic-specific content if available
        topic_text = ""
        
        # Try to find topic content in different possible locations
        if "topic_sections" in pdf_content:
            for section in pdf_content.get("topic_sections", []):
                if section.get("title", "").lower() == topic.lower():
                    topic_text = section.get("content", "")
                    break
        
        if not topic_text and "topics_with_content" in pdf_content:
            for t in pdf_content.get("topics_with_content", []):
                if isinstance(t, dict) and t.get("name", "").lower() == topic.lower():
                    topic_text = t.get("content", "")
                    break
        
        # If still no content, use general text
        if not topic_text:
            topic_text = pdf_content.get("text", "")[:1000]  # Limit to first 1000 chars
        
        # Try to generate with LLM first if available
        if LLM_AVAILABLE and is_model_ready():
            challenge = self._generate_with_llm(topic, topic_text, challenge_type, difficulty)
            if challenge:
                challenge["topic"] = topic
                challenge["type"] = challenge_type
                # Add difficulty to the challenge object
                challenge["difficulty"] = difficulty
                return challenge
        
        # Fall back to template-based generation
        return self._generate_with_template(topic, topic_text, challenge_type, difficulty)
    
    def _generate_with_llm(self, topic, topic_text, challenge_type, difficulty):
        """
        Generate a challenge using the LLM.
        
        Args:
            topic (str): The topic to generate a challenge for
            topic_text (str): Text content related to the topic
            challenge_type (str): The type of challenge to generate
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            dict: Generated challenge or None if generation failed
        """
        try:
            challenge = generate_challenge_with_llm(topic, topic_text, challenge_type, difficulty)
            if challenge:
                # Add difficulty to the challenge object
                challenge["difficulty"] = difficulty
                return challenge
        except Exception as e:
            logging.error(f"Error generating challenge with LLM: {e}")
        
        return None
    
    def _generate_with_template(self, topic, topic_text, challenge_type, difficulty):
        """
        Generate a challenge using templates.
        
        Args:
            topic (str): The topic to generate a challenge for
            topic_text (str): Text content related to the topic
            challenge_type (str): The type of challenge to generate
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            dict: Generated challenge
        """
        # Get topic category for specialized templates
        topic_category = self._get_topic_category(topic)
        
        # Get difficulty characteristics
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels["medium"])
        
        # Generate challenge based on type
        if challenge_type == "multiple_choice":
            return self._generate_multiple_choice(topic, topic_text, topic_category, difficulty)
        elif challenge_type == "debugging":
            return self._generate_debugging(topic, topic_text, topic_category, difficulty)
        elif challenge_type == "coding":
            return self._generate_coding(topic, topic_text, topic_category, difficulty)
        else:
            logging.warning(f"Unknown challenge type: {challenge_type}")
            return None
    
    def _generate_multiple_choice(self, topic, topic_text, topic_category, difficulty):
        """
        Generate a multiple-choice challenge.
        
        Args:
            topic (str): The topic to generate a challenge for
            topic_text (str): Text content related to the topic
            topic_category (str): Category of the topic
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            dict: Generated multiple-choice challenge
        """
        # Get template for this topic category
        template = self._get_multiple_choice_template(topic_category)
        
        # Get difficulty characteristics
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels["medium"])
        
        # Generate question based on difficulty
        if difficulty == "easy":
            question = f"Which of the following correctly describes {topic}?"
        elif difficulty == "medium":
            question = f"What is the most appropriate use case for {topic}?"
        else:  # hard
            question = f"Which statement about {topic} is true in complex scenarios?"
        
        # Generate options based on topic and difficulty
        options = self._generate_options_for_topic(topic, topic_category, difficulty)
        
        # Generate a hint based on difficulty
        if difficulty == "easy":
            hint = f"Think about the basic definition of {topic}."
        elif difficulty == "medium":
            hint = f"Consider the key characteristics of {topic}."
        else:  # hard
            hint = f"Analyze the advanced applications of {topic}."
        
        return {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "type": "multiple_choice",
            "question": question,
            "options": options,
            "correct_index": 0,  # First option is correct
            "hint": hint,
            "difficulty": difficulty  # Add difficulty to the challenge object
        }
    
    def _generate_debugging(self, topic, topic_text, topic_category, difficulty):
        """
        Generate a debugging challenge.
        
        Args:
            topic (str): The topic to generate a challenge for
            topic_text (str): Text content related to the topic
            topic_category (str): Category of the topic
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            dict: Generated debugging challenge
        """
        # Get template for this topic category
        template = self._get_debugging_template(topic_category)
        
        # Get difficulty characteristics
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels["medium"])
        
        # Generate question based on difficulty
        if difficulty == "easy":
            question = f"Fix the bug in this {topic} code:"
        elif difficulty == "medium":
            question = f"Identify and fix the error in this {topic} implementation:"
        else:  # hard
            question = f"Debug this complex {topic} code and fix all issues:"
        
        # Generate buggy code based on topic and difficulty
        buggy_code = self._generate_buggy_code_for_topic(topic, topic_category, difficulty)
        
        # Generate a hint based on difficulty
        if difficulty == "easy":
            hint = f"Check for syntax errors in the {topic} implementation."
        elif difficulty == "medium":
            hint = f"Look for logical errors in how {topic} is being used."
        else:  # hard
            hint = f"Consider edge cases and error handling in this {topic} implementation."
        
        return {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "type": "debugging",
            "question": question,
            "buggy_code": buggy_code,
            "hint": hint,
            "difficulty": difficulty  # Add difficulty to the challenge object
        }
    
    def _generate_coding(self, topic, topic_text, topic_category, difficulty):
        """
        Generate a coding challenge.
        
        Args:
            topic (str): The topic to generate a challenge for
            topic_text (str): Text content related to the topic
            topic_category (str): Category of the topic
            difficulty (str): Difficulty level - "easy", "medium", or "hard"
            
        Returns:
            dict: Generated coding challenge
        """
        # Get template for this topic category
        template = self._get_coding_template(topic_category)
        
        # Get difficulty characteristics
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels["medium"])
        
        # Generate question based on difficulty
        if difficulty == "easy":
            question = f"Write a function that implements a basic {topic} operation:"
        elif difficulty == "medium":
            question = f"Implement a function that performs the following {topic} task:"
        else:  # hard
            question = f"Create an efficient solution for this advanced {topic} problem:"
        
        # Generate code stub based on topic and difficulty
        code_stub = self._generate_code_stub_for_topic(topic, topic_category, difficulty)
        
        # Generate test cases based on difficulty
        test_cases = self._generate_test_cases_for_topic(
            topic, 
            topic_category, 
            difficulty, 
            difficulty_info["test_case_count"]
        )
        
        # Generate a hint based on difficulty
        if difficulty == "easy":
            hint = f"Start by understanding the basic operations needed for {topic}."
        elif difficulty == "medium":
            hint = f"Break down the problem into smaller steps involving {topic}."
        else:  # hard
            hint = f"Consider optimization techniques specific to {topic}."
        
        return {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "type": "coding",
            "question": question,
            "code_stub": code_stub,
            "test_cases": test_cases,
            "hint": hint,
            "difficulty": difficulty  # Add difficulty to the challenge object
        }
    
    def _generate_options_for_topic(self, topic, topic_category, difficulty):
        """Generate options for a multiple-choice question."""
        # This is a simplified implementation
        if topic_category == "data_structure":
            return [
                f"{topic} is used to store and organize data efficiently",
                f"{topic} is only used for mathematical calculations",
                f"{topic} cannot be implemented in Python",
                f"{topic} always has O(1) time complexity for all operations"
            ]
        elif topic_category == "algorithm":
            return [
                f"{topic} is an efficient approach to solving computational problems",
                f"{topic} can only be used with specific programming languages",
                f"{topic} always requires recursion",
                f"{topic} cannot be optimized further"
            ]
        else:
            return [
                f"{topic} is a fundamental concept in programming",
                f"{topic} is only relevant in legacy systems",
                f"{topic} cannot be used in modern applications",
                f"{topic} is only theoretical and has no practical applications"
            ]
    
    def _generate_buggy_code_for_topic(self, topic, topic_category, difficulty):
        """Generate buggy code for a debugging challenge."""
        # This is a simplified implementation
        if topic_category == "data_structure":
            return f"""def use_{topic.replace(' ', '_')}(data):
    result = []
    for item in data:
        # BUG: Incorrect implementation of {topic}
        result.append(item - 1)  # Should be item + 1
    return result"""
        elif topic_category == "algorithm":
            return f"""def {topic.replace(' ', '_')}_algorithm(arr):
    # BUG: Incorrect loop condition
    for i in range(len(arr) - 1):  # Should be range(len(arr))
        if arr[i] > arr[i+1]:
            arr[i], arr[i+1] = arr[i+1], arr[i]
    return arr"""
        else:
            return f"""def process_{topic.replace(' ', '_')}(value):
    # BUG: Missing error handling
    result = 10 / value  # Should check if value is zero
    return result"""
    
    def _generate_code_stub_for_topic(self, topic, topic_category, difficulty):
        """Generate code stub for a coding challenge."""
        # This is a simplified implementation
        if topic_category == "data_structure":
            return f"""def implement_{topic.replace(' ', '_')}(data):
    # Your code here
    result = None
    
    return result"""
        elif topic_category == "algorithm":
            return f"""def {topic.replace(' ', '_')}_solution(arr):
    # Your code here
    result = None
    
    return result"""
        else:
            return f"""def solve_{topic.replace(' ', '_')}(input_data):
    # Your code here
    result = None
    
    return result"""
    
    def _generate_test_cases_for_topic(self, topic, topic_category, difficulty, count=3):
        """Generate test cases for a coding challenge."""
        # This is a simplified implementation
        test_cases = []
        
        if topic_category == "data_structure":
            test_cases = [
                {"input": [1, 2, 3], "expected": [2, 4, 6]},
                {"input": [5, 10, 15], "expected": [10, 20, 30]},
                {"input": [0, -1, -2], "expected": [0, -2, -4]},
                {"input": [100, 200], "expected": [200, 400]}
            ]
        elif topic_category == "algorithm":
            test_cases = [
                {"input": [3, 1, 4, 1, 5], "expected": [1, 1, 3, 4, 5]},
                {"input": [9, 8, 7, 6, 5], "expected": [5, 6, 7, 8, 9]},
                {"input": [2, 2, 1, 1, 3], "expected": [1, 1, 2, 2, 3]},
                {"input": [5, 3, 8, 4, 2], "expected": [2, 3, 4, 5, 8]}
            ]
        else:
            test_cases = [
                {"input": "hello", "expected": "HELLO"},
                {"input": "world", "expected": "WORLD"},
                {"input": "python", "expected": "PYTHON"},
                {"input": "programming", "expected": "PROGRAMMING"}
            ]
        
        # Return only the requested number of test cases
        return test_cases[:count]
    
    def _get_multiple_choice_template(self, topic_category="general"):
        """Get template for multiple-choice questions."""
        templates = {
            "data_structure": "Which of the following correctly describes how {topic} stores and organizes data?",
            "algorithm": "What is the time complexity of {topic} in the worst case?",
            "language_feature": "Which statement about {topic} in Python is correct?",
            "error_handling": "What is the best practice for handling errors in {topic}?",
            "web_development": "Which approach is most appropriate when implementing {topic} in a web application?",
            "database": "How should {topic} be used in database operations?",
            "testing": "What is the most effective way to test {topic}?",
            "general": "Which of the following statements about {topic} is correct?"
        }
        
        return templates.get(topic_category, templates["general"])
    
    def _get_debugging_template(self, topic_category="general"):
        """Get template for debugging challenges."""
        templates = {
            "data_structure": "Fix the bug in this {topic} implementation:",
            "algorithm": "Debug this {topic} algorithm and fix the error:",
            "language_feature": "This code using {topic} has a bug. Find and fix it:",
            "error_handling": "The error handling in this {topic} code is incorrect. Debug it:",
            "web_development": "This {topic} code for a web application has an issue. Fix it:",
            "database": "Debug this database operation involving {topic}:",
            "testing": "This test for {topic} is failing. Find and fix the bug:",
            "general": "Find and fix the bug in this code related to {topic}:"
        }
        
        return templates.get(topic_category, templates["general"])
    
    def _get_coding_template(self, topic_category="general"):
        """Get template for coding challenges."""
        templates = {
            "data_structure": "Implement a function that uses {topic} to solve the following problem:",
            "algorithm": "Write a function that implements the {topic} algorithm:",
            "language_feature": "Create a function that demonstrates the use of {topic} in Python:",
            "error_handling": "Implement a function with proper error handling for {topic}:",
            "web_development": "Write a function that would be used in a web application for {topic}:",
            "database": "Implement a function that performs a database operation involving {topic}:",
            "testing": "Create a function that can be used to test {topic}:",
            "general": "Write a function related to {topic} that solves the following problem:"
        }
        
        return templates.get(topic_category, templates["general"])
