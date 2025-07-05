import re
import json
import uuid
import time
import threading
import logging
import os
from typing import List, Dict, Any, Optional

# Replace torch/transformers with openai
try:
    import openai
except ImportError:
    print("OpenAI library not found. Please install with: pip install openai")
    openai = None

# Import PDF content analyzer
try:
    from pdf_content_analyzer import (
        extract_text_from_pdf,
        analyze_pdf_content,
        extract_code_snippets
    )
    PDF_ANALYZER_AVAILABLE = True
except ImportError:
    print("PDF content analyzer not found. Dynamic topic extraction will be limited.")
    PDF_ANALYZER_AVAILABLE = False

# Import fallback hint generator
try:
    from fallback_hints import (
        generate_fallback_hint_for_multiple_choice,
        generate_fallback_hint_for_debugging,
        generate_fallback_hint_for_fib
    )
    FALLBACK_HINTS_AVAILABLE = True
except ImportError:
    print("Fallback hints module not found. Will use OpenAI for all hints.")
    FALLBACK_HINTS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
DEBUG_PARSING = False  # Reduced debug logging for speed
if DEBUG_PARSING:
    logger.setLevel(logging.DEBUG)

# Global OpenAI client
openai_client = None

def initialize_openai():
    """Initialize OpenAI client with new v1.0+ API"""
    global openai_client
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return False
        
        # Initialize client with new v1.0+ syntax
        openai_client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAI API initialized successfully")
        logger.info("OpenAI API ready for use")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI: {e}")
        return False

def is_model_ready():
    """Check if the OpenAI model is ready for use"""
    global openai_client
    
    if openai_client is None:
        # Try to initialize if not already done
        return initialize_openai()
    
    return True

def make_openai_request(messages, model="gpt-3.5-turbo", max_tokens=1000, temperature=0.7):
    """Make OpenAI API request with new v1.0+ syntax"""
    global openai_client
    
    try:
        if not openai_client:
            if not initialize_openai():
                return None
        
        # Use new v1.0+ syntax
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract content from response
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            return content
        else:
            logger.warning("Empty response from OpenAI API")
            return None
            
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None

# Initialize OpenAI on module import
initialize_openai()

def extract_and_parse_json(text: str, expected_keys: List[str] = None) -> Dict[str, Any]:
    """
    Enhanced JSON extraction and parsing with multiple strategies
    """
    if not text:
        logger.warning("Empty text provided for JSON parsing")
        return {}
    
    # Strategy 1: Direct JSON parsing
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            logger.debug("Direct JSON parsing successful")
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from code blocks
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # Nested braces
        r'(\{[^{}]+\})',  # Simple braces
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict):
                    logger.debug(f"JSON extracted with pattern: {pattern[:20]}...")
                    return parsed
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: JSON repair for common issues
    try:
        # Fix common JSON issues
        cleaned = text.strip()
        
        # Remove markdown code blocks
        cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        # Fix trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # Fix single quotes to double quotes
        cleaned = re.sub(r"'([^']*)':", r'"\1":', cleaned)
        cleaned = re.sub(r":\s*'([^']*)'", r': "\1"', cleaned)
        
        # Try parsing the cleaned version
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            logger.debug("JSON repair successful")
            return parsed
            
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Extract key-value pairs manually
    if expected_keys:
        result = {}
        for key in expected_keys:
            # Look for key: "value" or key: value patterns
            patterns = [
                rf'"{key}"\s*:\s*"([^"]*)"',
                rf'"{key}"\s*:\s*([^,\}}]+)',
                rf'{key}\s*:\s*"([^"]*)"',
                rf'{key}\s*:\s*([^,\}}]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = value.strip('"\'')
                    result[key] = value
                    break
        
        if result:
            logger.debug(f"Manual key extraction successful: {list(result.keys())}")
            return result
    
    logger.warning("All JSON parsing strategies failed")
    return {}

def generate_multiple_choice_challenge(content: str, difficulty: str, topic: str) -> Dict[str, Any]:
    """Generate multiple choice challenge with improved prompts"""
    
    prompt = f"""Create a multiple-choice programming question about "{topic}" with {difficulty} difficulty.

Content context: {content[:1500]}

Requirements:
1. Create a clear, specific question about {topic}
2. Provide exactly 4 answer options (A, B, C, D)
3. Make sure only ONE option is clearly correct
4. Include a brief explanation of why the correct answer is right
5. Base the question on the provided content context

Return ONLY a JSON object with this exact structure:
{{
    "question": "Your question here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Brief explanation of the correct answer",
    "topic": "{topic}",
    "difficulty": "{difficulty}"
}}

Make sure the JSON is valid and complete."""

    messages = [
        {
            "role": "system",
            "content": "You are an expert programming instructor. Create educational multiple-choice questions that test understanding of programming concepts. Always respond with valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    response = make_openai_request(messages, max_tokens=800, temperature=0.7)
    
    if not response:
        logger.warning("Empty response from OpenAI for multiple-choice challenge")
        return {}
    
    # Parse the JSON response
    challenge = extract_and_parse_json(response, ["question", "options", "correct_answer", "explanation"])
    
    if not challenge:
        logger.warning("Failed to parse multiple-choice challenge JSON")
        return {}
    
    # Validate and clean up the challenge
    if "question" not in challenge or "options" not in challenge:
        logger.warning("Multiple-choice challenge missing required fields")
        return {}
    
    # Ensure options is a list
    if isinstance(challenge.get("options"), str):
        # Try to parse as JSON array
        try:
            challenge["options"] = json.loads(challenge["options"])
        except:
            # Split by common delimiters
            options_str = challenge["options"]
            challenge["options"] = [opt.strip() for opt in re.split(r'[,\n]', options_str) if opt.strip()]
    
    # Ensure we have 4 options
    if not isinstance(challenge.get("options"), list) or len(challenge["options"]) != 4:
        logger.warning("Multiple-choice challenge doesn't have exactly 4 options")
        return {}
    
    # Ensure correct_answer is an integer
    try:
        challenge["correct_answer"] = int(challenge.get("correct_answer", 0))
    except (ValueError, TypeError):
        challenge["correct_answer"] = 0
    
    # Add metadata
    challenge["id"] = f"mc_{uuid.uuid4().hex[:8]}"
    challenge["type"] = "multiple-choice"
    challenge["topic"] = topic
    challenge["difficulty"] = difficulty
    
    return challenge

def generate_debugging_challenge(content: str, difficulty: str, topic: str) -> Dict[str, Any]:
    """Generate debugging challenge with actual buggy code"""
    
    # Define different debugging scenarios to ensure variety
    debugging_scenarios = [
        "data processing and validation",
        "file operations and error handling", 
        "mathematical calculations and algorithms",
        "string manipulation and parsing",
        "list/array operations and indexing",
        "object-oriented programming and classes",
        "function definitions and parameters",
        "loop logic and iteration",
        "conditional statements and branching",
        "exception handling and try-catch blocks"
    ]
    
    # Select a scenario based on topic or use a random one
    import random
    scenario = random.choice(debugging_scenarios)
    
    prompt = f"""Create a debugging challenge about "{topic}" with {difficulty} difficulty, focusing on {scenario}.

Content context: {content[:1500]}

Requirements:
1. Write actual Python code that contains a specific, realistic bug related to {scenario}
2. The bug should be related to {topic} and {scenario}
3. Use function names and variable names related to {scenario} (e.g., process_data, validate_input, calculate_result)
4. Provide a clear description of what the code should do
5. Include the type of bug (syntax_error, logic_error, runtime_error)
6. Provide a clear explanation of what's wrong and how to fix it
7. Make the code runnable and realistic (not just pseudocode)

Common bug types to use:
- Syntax errors: wrong operators (= vs ==), missing colons, incorrect indentation
- Logic errors: off-by-one errors, wrong conditions, incorrect loop bounds
- Runtime errors: division by zero, index out of range, type mismatches

Return ONLY a JSON object with this exact structure:
{{
    "question": "Find and fix the bug in this code that should [describe what it should do related to {scenario}]",
    "code_stub": "def process_function():\\n    # Actual buggy Python code here related to {scenario}\\n    pass",
    "bug_type": "syntax_error",
    "expected_output": "What the output should be",
    "actual_output": "What the buggy code actually produces (or error message)",
    "correct_answer": "Clear explanation of the bug and how to fix it",
    "fix_explanation": "Detailed explanation of the bug and how to fix it",
    "topic": "{topic}",
    "difficulty": "{difficulty}"
}}

Make sure the code_stub contains REAL, RUNNABLE Python code with an actual bug related to {scenario}."""

    messages = [
        {
            "role": "system",
            "content": f"You are an expert programming instructor who creates realistic debugging exercises focused on {scenario}. Always include actual buggy code that students can run and debug. Respond with valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    response = make_openai_request(messages, max_tokens=1000, temperature=0.8)
    
    if not response:
        logger.warning("Empty response from OpenAI for debugging challenge")
        return {}
    
    # Parse the JSON response
    challenge = extract_and_parse_json(response, ["question", "code_stub", "bug_type", "expected_output", "actual_output", "fix_explanation", "correct_answer"])
    
    if not challenge:
        logger.warning("Failed to parse debugging challenge JSON")
        return {}
    
    # Validate required fields
    required_fields = ["question", "code_stub"]
    if not all(field in challenge for field in required_fields):
        logger.warning("Debugging challenge missing required fields")
        return {}
    
    # Clean up code_stub
    code_stub = challenge.get("code_stub", "")
    if code_stub:
        # Ensure proper formatting
        code_stub = code_stub.replace("\\n", "\n").replace("\\t", "\t")
        challenge["code_stub"] = code_stub
    
    # Add metadata
    challenge["id"] = f"debug_{uuid.uuid4().hex[:8]}"
    challenge["type"] = "debugging"
    challenge["topic"] = topic
    challenge["difficulty"] = difficulty
    
    # Set defaults for missing fields
    challenge.setdefault("bug_type", "logic_error")
    challenge.setdefault("expected_output", "See code comments for expected behavior")
    challenge.setdefault("actual_output", "Code contains a bug")
    challenge.setdefault("fix_explanation", "Analyze the code to find and fix the bug")
    challenge.setdefault("correct_answer", challenge.get("fix_explanation", "Analyze the code to find and fix the bug"))
    
    return challenge

def generate_fill_in_blank_challenge(content: str, difficulty: str, topic: str) -> Dict[str, Any]:
    """Generate fill-in-the-blank challenge with proper ____ formatting"""
    
    # Define different algorithmic scenarios to ensure variety
    algorithmic_scenarios = [
        "recursive algorithms and base cases",
        "sorting algorithms and comparisons", 
        "search algorithms and binary operations",
        "graph traversal and path finding",
        "dynamic programming and memoization",
        "tree operations and node manipulation",
        "hash table operations and key-value pairs",
        "stack and queue data structures",
        "linked list operations and pointers",
        "mathematical computations and formulas"
    ]
    
    # Select a scenario based on topic or use a random one
    import random
    scenario = random.choice(algorithmic_scenarios)
    
    prompt = f"""Create a fill-in-the-blank programming exercise about "{topic}" with {difficulty} difficulty, focusing on {scenario}.

Content context: {content[:1500]}

Requirements:
1. Provide Python code containing exactly 2–4 blanks, each marked with "____" (4 underscores)
2. Focus on {scenario} and use appropriate function names (e.g., binary_search, merge_sort, dfs_traversal)
3. Each blank should test understanding of {topic} and {scenario}
4. For every blank, supply multiple-choice options and indicate the correct one
5. Include the full working solution
6. Explain each blank in the context of {scenario}
7. Use realistic algorithm implementations, not simple examples

Return **only** a JSON object matching this schema:
{{
    "question": "Complete the {scenario} implementation by filling in the blanks",
    "code_with_blanks": "def algorithm_function():\\n    # Python code with ____ placeholders for {scenario}\\n    pass",
    "blanks": [
        {{
            "blank_number": 1,
            "correct_answer": "specific_value",
            "options": ["option1", "option2", "option3", "option4"],
            "explanation": "Why this value is correct for {scenario}"
        }}
    ],
    "complete_solution": "def algorithm_function():\\n    # Complete working code\\n    pass",
    "topic": "{topic}",
    "difficulty": "{difficulty}"
}}

Use exactly "____" for each blank placeholder. Focus on {scenario} concepts."""

    messages = [
        {
            "role": "system",
            "content": f"You are an expert programming instructor creating fill-in-the-blank exercises focused on {scenario}. Use exactly 4 underscores (____) for each blank. Create realistic algorithm implementations. Respond with valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    response = make_openai_request(messages, max_tokens=1000, temperature=0.7)
    
    if not response:
        logger.warning("Empty response from OpenAI for fill-in-the-blank challenge")
        return {}
    
    # Parse the JSON response
    challenge = extract_and_parse_json(response, ["question", "code_with_blanks", "blanks", "complete_solution"])
    
    if not challenge:
        logger.warning("Failed to parse fill-in-the-blank challenge JSON")
        return {}
    
    # Validate required fields
    required_fields = ["question", "code_with_blanks", "blanks"]
    if not all(field in challenge for field in required_fields):
        logger.warning("Fill-in-the-blank challenge missing required fields")
        return {}
    
    # Clean up code formatting
    code_with_blanks = challenge.get("code_with_blanks", "")
    if code_with_blanks:
        code_with_blanks = code_with_blanks.replace("\\n", "\n").replace("\\t", "\t")
        challenge["code_with_blanks"] = code_with_blanks
    
    complete_solution = challenge.get("complete_solution", "")
    if complete_solution:
        complete_solution = complete_solution.replace("\\n", "\n").replace("\\t", "\t")
        challenge["complete_solution"] = complete_solution
    
    # Validate blanks
    blanks = challenge.get("blanks", [])
    if not isinstance(blanks, list) or len(blanks) == 0:
        logger.warning("Fill-in-the-blank challenge has no valid blanks")
        return {}
    
    # Ensure each blank has required fields
    for i, blank in enumerate(blanks):
        if not isinstance(blank, dict):
            continue
        blank.setdefault("blank_number", i + 1)
        blank.setdefault("correct_answer", "")
        blank.setdefault("options", [])
        blank.setdefault("explanation", "")
    
    # Add metadata
    challenge["id"] = f"fib_{uuid.uuid4().hex[:8]}"
    challenge["type"] = "fill-in-the-blank"
    challenge["topic"] = topic
    challenge["difficulty"] = difficulty
    
    return challenge

def generate_single_challenge(content: str, challenge_type: str, difficulty: str, topic: str) -> Dict[str, Any]:
    """Generate a single challenge of the specified type"""
    
    logger.info(f"Generating {challenge_type} challenge for topic: {topic}")
    
    try:
        if challenge_type == "multiple-choice":
            return generate_multiple_choice_challenge(content, difficulty, topic)
        elif challenge_type == "debugging":
            return generate_debugging_challenge(content, difficulty, topic)
        elif challenge_type == "fill-in-the-blank":
            return generate_fill_in_blank_challenge(content, difficulty, topic)
        else:
            logger.warning(f"Unknown challenge type: {challenge_type}")
            return {}
    
    except Exception as e:
        logger.error(f"Error generating {challenge_type} challenge: {e}")
        return {}

def generate_short_hint_for_challenge(challenge: Dict[str, Any]) -> str:
    """Generate a short hint for a challenge"""
    
    challenge_type = challenge.get("type", "")
    topic = challenge.get("topic", "programming")
    
    # Try to use pre-generated hint first
    if "hint" in challenge:
        return challenge["hint"]
    
    # Generate hint based on challenge type
    if challenge_type == "multiple-choice":
        if FALLBACK_HINTS_AVAILABLE:
            try:
                return generate_fallback_hint_for_multiple_choice(challenge)
            except:
                pass
        return f"Think about the key concepts in {topic}. Review the question carefully."
    
    elif challenge_type == "debugging":
        if FALLBACK_HINTS_AVAILABLE:
            try:
                return generate_fallback_hint_for_debugging(challenge)
            except:
                pass
        
        bug_type = challenge.get("bug_type", "")
        if "syntax" in bug_type.lower():
            return "Look for syntax errors like wrong operators or missing punctuation."
        elif "logic" in bug_type.lower():
            return "Check the logic flow - are the conditions and loops correct?"
        else:
            return "Run the code and analyze the error message or unexpected output."
    
    elif challenge_type == "fill-in-the-blank":
        if FALLBACK_HINTS_AVAILABLE:
            try:
                return generate_fallback_hint_for_fib(challenge)
            except:
                pass
        return f"Consider the syntax and concepts related to {topic}."
    
    else:
        return f"Think about the fundamental concepts of {topic}."

def extract_topics_from_content(content: str, file_path: str = None) -> List[str]:
    """Extract topics from content using enhanced methods"""
    
    logger.info("Using dynamic PDF content analysis for topic extraction")
    
    try:
        if PDF_ANALYZER_AVAILABLE and file_path:
            # Use enhanced PDF analysis
            analysis = analyze_pdf_content(content)
            topics = analysis.get('topics', [])
            
            if topics and len(topics) > 0:
                logger.info(f"Enhanced topic extraction successful: {len(topics)} topics")
                return topics
        
        # Fallback to LLM-based extraction
        logger.info("Using LLM-based topic extraction as fallback")
        
        prompt = f"""Analyze this programming content and extract the main topics covered.

Content: {content[:2000]}

Requirements:
1. Extract 5-10 specific programming topics
2. Focus on concrete concepts, not general terms
3. Use clear, educational topic names
4. Return as a JSON array of strings

Return ONLY a JSON array like: ["Topic 1", "Topic 2", "Topic 3"]"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert at analyzing programming content. Extract specific, educational topics that can be used to create programming challenges."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = make_openai_request(messages, max_tokens=500, temperature=0.5)
        
        if not response:
            logger.warning("LLM topic extraction returned no response")
            return []
        
        # Try to parse as JSON array
        try:
            topics = json.loads(response)
            if isinstance(topics, list):
                # Clean and validate topics
                clean_topics = []
                for topic in topics:
                    if isinstance(topic, str) and len(topic.strip()) > 2:
                        clean_topics.append(topic.strip())
                
                if clean_topics:
                    logger.info(f"LLM topic extraction successful: {len(clean_topics)} topics")
                    return clean_topics
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, try to extract topics from text
        lines = response.split('\n')
        topics = []
        for line in lines:
            line = line.strip()
            # Look for quoted strings or list items
            if line.startswith('"') and line.endswith('"'):
                topics.append(line[1:-1])
            elif line.startswith('- '):
                topics.append(line[2:])
            elif re.match(r'^\d+\.\s+', line):
                topics.append(re.sub(r'^\d+\.\s+', '', line))
        
        if topics:
            logger.info(f"Text-based topic extraction successful: {len(topics)} topics")
            return topics[:10]  # Limit to 10 topics
        
        logger.warning("All topic extraction methods failed")
        return []
        
    except Exception as e:
        logger.error(f"Error in topic extraction: {e}")
        return []

def validate_topics(topics: List[str]) -> List[str]:
    """Validate and clean extracted topics"""
    valid_topics = []
    
    for topic in topics:
        if not topic or not isinstance(topic, str):
            continue
        
        topic = topic.strip()
        
        # Skip empty or very short topics
        if len(topic) < 3:
            continue
        
        # Skip very long topics
        if len(topic) > 50:
            continue
        
        # Skip topics that are just numbers
        if topic.isdigit():
            continue
        
        # Clean up the topic
        topic = topic.replace('_', ' ').title()
        
        # Add if not already present
        if topic not in valid_topics:
            valid_topics.append(topic)
    
    logger.info(f"Final extracted {len(valid_topics)} topics: {valid_topics}")
    return valid_topics[:10]  # Limit to 10 topics

# Backward compatibility functions
def generate_with_llm(content: str, difficulty: str = "medium", topic: str = "programming") -> List[Dict[str, Any]]:
    """Backward compatibility function for generating challenges"""
    challenges = []
    
    challenge_types = ["multiple-choice", "debugging", "fill-in-the-blank"]
    
    for challenge_type in challenge_types:
        challenge = generate_single_challenge(content, challenge_type, difficulty, topic)
        if challenge:
            challenges.append(challenge)
    
    return challenges

