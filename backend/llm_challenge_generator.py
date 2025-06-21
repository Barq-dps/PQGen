import os
import re
import json
import uuid
import time
import threading
import logging

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Import fallback hint generator
from fallback_hints import (
    generate_fallback_hint_for_multiple_choice,
    generate_fallback_hint_for_debugging,
    generate_fallback_hint_for_coding
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
DEBUG_PARSING = True
if DEBUG_PARSING:
    logger.setLevel(logging.DEBUG)

# Model globals
tokenizer = None
model = None

# Loading flags and lock
model_loading_lock = threading.Lock()
is_model_loaded = False
is_model_loading = False

# Model configuration
MODEL_NAME = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.7
TOP_P = 0.95
REPETITION_PENALTY = 1.1


def load_model_in_background():
    global tokenizer, model, is_model_loaded, is_model_loading
    with model_loading_lock:
        if is_model_loaded or is_model_loading:
            return
        is_model_loading = True

    def _load():
        global tokenizer, model, is_model_loaded, is_model_loading
        try:
            logger.info(f"Loading model {MODEL_NAME}...")
            start = time.time()
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            model.eval()
            logger.info(f"Model loaded in {time.time() - start:.2f}s")
            with model_loading_lock:
                is_model_loaded = True
                is_model_loading = False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            with model_loading_lock:
                is_model_loading = False

    thread = threading.Thread(target=_load, daemon=True)
    thread.start()


def is_model_ready() -> bool:
    with model_loading_lock:
        return is_model_loaded


def generate_with_llm(prompt: str, max_tokens: int = MAX_NEW_TOKENS, temperature: float = TEMPERATURE) -> str | None:
    if not is_model_ready():
        logger.warning("Model not ready for generation")
        return None
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=TOP_P,
                repetition_penalty=REPETITION_PENALTY,
                do_sample=True
            )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        prefix = tokenizer.decode(inputs.input_ids[0], skip_special_tokens=True)
        return text[len(prefix):].strip()
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        return None


def clean_json_string(s: str) -> str:
    # strip out triple-quoted Python strings
    s = re.sub(r'""".*?"""', '', s, flags=re.DOTALL)
    s = re.sub(r"'''(.*?)'''", '', s, flags=re.DOTALL)
    # remove code fences
    s = re.sub(r'```(?:json|python)?|```', '', s)
    # normalize quotes
    s = s.replace(""", '"').replace(""", '"')
    # remove trailing commas
    s = re.sub(r',\s*}', '}', s)
    s = re.sub(r',\s*]', ']', s)
    # convert Python literals to JSON literals
    s = re.sub(r'\bTrue\b', 'true', s)
    s = re.sub(r'\bFalse\b', 'false', s)
    s = re.sub(r'\bNone\b', 'null', s)
    # Fix common empty value errors: "field": , -> "field": ""
    s = re.sub(r':\s*,', ': "",', s)
    s = re.sub(r':\s*\n', ': "",\n', s)
    return s.strip()


def extract_json_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    # Look for JSON objects with more aggressive pattern matching
    for match in re.finditer(r'\{.*?\}', text, re.DOTALL):
        blocks.append(match.group(0))
    # Look for JSON arrays
    for match in re.finditer(r'\[.*?\]', text, re.DOTALL):
        blocks.append(match.group(0))
    return blocks


def normalize_mc(parsed: dict) -> dict | None:
    """Normalize multiple choice question format and ensure correct answer is marked."""
    # Case 1: Standard format with options as strings and correct_index
    if ('options' in parsed and isinstance(parsed['options'], list) and 
            all(isinstance(o, str) for o in parsed['options']) and
            'correct_index' in parsed and isinstance(parsed['correct_index'], int)):
        # Ensure correct_index is within bounds
        if 0 <= parsed['correct_index'] < len(parsed['options']):
            return parsed
        else:
            # Fix out-of-bounds correct_index
            parsed['correct_index'] = 0
            return parsed
    
    # Case 2: Options as strings but no correct_index
    if ('options' in parsed and isinstance(parsed['options'], list) and 
            all(isinstance(o, str) for o in parsed['options']) and
            'correct_index' not in parsed):
        # Try to find correct_index in other fields
        if 'correct_option' in parsed and isinstance(parsed['correct_option'], int):
            parsed['correct_index'] = parsed['correct_option']
            return parsed
        elif 'answer_index' in parsed and isinstance(parsed['answer_index'], int):
            parsed['correct_index'] = parsed['answer_index']
            return parsed
        else:
            # Default to first option if no correct index is found
            parsed['correct_index'] = 0
            return parsed
    
    # Case 3: Options as objects with 'correct' property
    if ('options' in parsed and isinstance(parsed['options'], list) and 
            all(isinstance(o, dict) for o in parsed['options'])):
        # Find the correct option
        correct_index = -1
        for i, option in enumerate(parsed['options']):
            if option.get('correct') is True:
                correct_index = i
                break
        
        # Convert options to strings and set correct_index
        if correct_index >= 0:
            string_options = [opt.get('text', str(opt)) for opt in parsed['options']]
            parsed['options'] = string_options
            parsed['correct_index'] = correct_index
            return parsed
    
    # Case 4: Choices format (common in some LLM outputs)
    if 'choices' in parsed and isinstance(parsed['choices'], list):
        # Extract text from choices
        string_options = []
        correct_index = -1
        
        for i, choice in enumerate(parsed['choices']):
            if isinstance(choice, dict) and 'text' in choice:
                string_options.append(choice['text'])
                # Check if this choice is marked as correct
                if choice.get('correct') is True or choice.get('is_correct') is True:
                    correct_index = i
        
        if string_options:
            parsed['options'] = string_options
            parsed['explanation'] = parsed.get('explanation', parsed.get('hint', ''))
            
            # Set correct_index if found, otherwise default to 0
            if correct_index >= 0:
                parsed['correct_index'] = correct_index
            else:
                parsed['correct_index'] = 0
                
            return parsed
    
    # If we can't normalize the format, return None
    return None


def fix_json_syntax(json_str: str) -> str:
    """Fix common JSON syntax errors that the LLM might produce."""
    # Fix missing values for fields (e.g., "code_stub": , -> "code_stub": "",)
    json_str = re.sub(r':\s*,', ': "",', json_str)
    json_str = re.sub(r':\s*\n', ': "",\n', json_str)
    
    # Fix missing commas between fields
    json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
    
    # Fix trailing commas
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    return json_str


def extract_first_json_object(text: str) -> str:
    """Extract the first complete JSON object from text."""
    # Find the first opening brace
    start = text.find('{')
    if start == -1:
        return ""
    
    # Count braces to find the matching closing brace
    count = 1
    for i in range(start + 1, len(text)):
        if text[i] == '{':
            count += 1
        elif text[i] == '}':
            count -= 1
            if count == 0:
                # Found the matching closing brace
                return text[start:i+1]
    
    # No matching closing brace found
    return ""


def parse_llm_response(response: str, default=None) -> dict | None:
    if not response:
        return default
    
    # First, try to extract the first complete JSON object
    json_obj = extract_first_json_object(response)
    if json_obj:
        # Fix common syntax errors
        json_obj = fix_json_syntax(json_obj)
        try:
            data = json.loads(json_obj)
            # Check if it's a valid challenge object
            if 'question' in data:
                # Check for multiple-choice format
                mc = normalize_mc(data)
                if mc and 'options' in mc:
                    return mc
                    
                # Check for debugging challenge format
                if 'buggy_code' in data:
                    # Ensure buggy_code has a value
                    if not data.get('buggy_code'):
                        data['buggy_code'] = "# Empty code stub"
                    return data
                    
                # Check for coding challenge format
                if 'code_stub' in data or 'function_template' in data:
                    # Ensure code_stub has a value
                    if 'code_stub' in data and not data.get('code_stub'):
                        data['code_stub'] = "# Empty code stub"
                    if 'function_template' in data and not data.get('function_template'):
                        data['function_template'] = "# Empty function template"
                    # Ensure test_cases exists and has a value
                    if 'test_cases' not in data or not data.get('test_cases'):
                        data['test_cases'] = [{"input": "example", "expected": "example"}]
                    return data
        except json.JSONDecodeError:
            pass
    
    # If direct extraction failed, try the standard approach with cleaning
    cleaned = clean_json_string(response)
    if DEBUG_PARSING:
        logger.debug(f"Cleaned response:\n{cleaned}")
    
    # Try to parse the entire cleaned response first
    try:
        full = json.loads(cleaned)
        
        # Check for multiple-choice format
        mc = normalize_mc(full)
        if mc and 'question' in mc and 'options' in mc:
            if DEBUG_PARSING:
                logger.debug(f"Parsed full cleaned response as MC")
            return mc
            
        # Check for debugging or coding challenge format
        if 'question' in full:
            if 'buggy_code' in full:
                # Ensure buggy_code has a value
                if not full.get('buggy_code'):
                    full['buggy_code'] = "# Empty code stub"
                if DEBUG_PARSING:
                    logger.debug(f"Parsed full cleaned response as debugging challenge")
                return full
            elif 'code_stub' in full or 'function_template' in full:
                # Ensure code_stub has a value
                if 'code_stub' in full and not full.get('code_stub'):
                    full['code_stub'] = "# Empty code stub"
                if 'function_template' in full and not full.get('function_template'):
                    full['function_template'] = "# Empty function template"
                # Ensure test_cases exists and has a value
                if 'test_cases' not in full or not full.get('test_cases'):
                    full['test_cases'] = [{"input": "example", "expected": "example"}]
                if DEBUG_PARSING:
                    logger.debug(f"Parsed full cleaned response as coding challenge")
                return full
    except json.JSONDecodeError:
        pass
    
    # If that fails, extract and try individual JSON blocks
    blocks = extract_json_blocks(cleaned)
    
    # Try parsing each extracted JSON block
    for i, block in enumerate(blocks):
        # Fix common syntax errors
        block = fix_json_syntax(block)
        try:
            data = json.loads(block)
            
            # Check for multiple-choice format
            mc = normalize_mc(data)
            if mc and 'question' in mc and 'options' in mc:
                if DEBUG_PARSING:
                    logger.debug(f"Parsed block {i} as MC")
                return mc
                
            # Check for debugging challenge format
            if 'question' in data and 'buggy_code' in data:
                # Ensure buggy_code has a value
                if not data.get('buggy_code'):
                    data['buggy_code'] = "# Empty code stub"
                if DEBUG_PARSING:
                    logger.debug(f"Parsed block {i} as debugging challenge")
                return data
                
            # Check for coding challenge format
            if 'question' in data and ('code_stub' in data or 'function_template' in data):
                # Ensure code_stub has a value
                if 'code_stub' in data and not data.get('code_stub'):
                    data['code_stub'] = "# Empty code stub"
                if 'function_template' in data and not data.get('function_template'):
                    data['function_template'] = "# Empty function template"
                # Ensure test_cases exists and has a value
                if 'test_cases' not in data or not data.get('test_cases'):
                    data['test_cases'] = [{"input": "example", "expected": "example"}]
                if DEBUG_PARSING:
                    logger.debug(f"Parsed block {i} as coding challenge")
                return data
                
        except json.JSONDecodeError as e:
            if DEBUG_PARSING:
                logger.debug(f"Block {i} parse failed: {e}")
    
    # Last resort: try to parse the raw response
    try:
        raw = json.loads(response)
        
        # Check for multiple-choice format
        mc = normalize_mc(raw)
        if mc and 'question' in mc and 'options' in mc:
            if DEBUG_PARSING:
                logger.debug(f"Parsed raw response as MC")
            return mc
            
        # Check for debugging or coding challenge format
        if 'question' in raw:
            if 'buggy_code' in raw:
                # Ensure buggy_code has a value
                if not raw.get('buggy_code'):
                    raw['buggy_code'] = "# Empty code stub"
                if DEBUG_PARSING:
                    logger.debug(f"Parsed raw response as debugging challenge")
                return raw
            elif 'code_stub' in raw or 'function_template' in raw:
                # Ensure code_stub has a value
                if 'code_stub' in raw and not raw.get('code_stub'):
                    raw['code_stub'] = "# Empty code stub"
                if 'function_template' in raw and not raw.get('function_template'):
                    raw['function_template'] = "# Empty function template"
                # Ensure test_cases exists and has a value
                if 'test_cases' not in raw or not raw.get('test_cases'):
                    raw['test_cases'] = [{"input": "example", "expected": "example"}]
                if DEBUG_PARSING:
                    logger.debug(f"Parsed raw response as coding challenge")
                return raw
    except json.JSONDecodeError:
        pass
    
    logger.warning(f"Failed to parse LLM response: {response[:200]}...")
    return default


def create_multiple_choice_prompt(topic: str, topic_text: str, difficulty: str, language: str = "python") -> str:
    """Create a prompt for generating a multiple choice question with the specified difficulty."""
    
    # Define difficulty-specific guidance
    difficulty_guidance = {
        "easy": (
            "For EASY difficulty:\n"
            "- Focus on basic concepts and definitions\n"
            "- Use straightforward language and clear examples\n"
            "- Make the correct answer obvious to someone who understands the basics\n"
            "- Include distractors that are clearly wrong to knowledgeable users\n"
            "- Provide a helpful hint that guides toward the correct answer\n"
        ),
        "medium": (
            "For MEDIUM difficulty:\n"
            "- Focus on practical application and understanding\n"
            "- Require knowledge of how concepts work together\n"
            "- Make distractors plausible but incorrect\n"
            "- Test understanding rather than just memorization\n"
            "- Provide a hint that points to the relevant concept\n"
        ),
        "hard": (
            "For HARD difficulty:\n"
            "- Focus on edge cases, advanced concepts, or subtle distinctions\n"
            "- Require deep understanding and critical thinking\n"
            "- Make distractors very plausible and require careful analysis\n"
            "- Test advanced knowledge and problem-solving skills\n"
            "- Provide a subtle hint that requires analysis to apply\n"
        )
    }
    
    # Get the appropriate guidance for the requested difficulty
    guidance = difficulty_guidance.get(difficulty.lower(), difficulty_guidance["medium"])
    
    return (
        f"<s>\n"
        f"You are a JSON-generating API that creates programming challenges. You must output ONLY valid JSON with NO additional text.\n"
        f"</s>\n\n"
        f"<TASK>\n"
        f"Generate a multiple choice question about {topic} in {language} at {difficulty} difficulty.\n"
        f"{guidance}\n"
        f"</TASK>\n\n"
        f"<CONTEXT>\n{topic_text[:500]}\n</CONTEXT>\n\n"
        "<OUTPUT_REQUIREMENTS>\n"
        "1. Output EXACTLY ONE valid JSON object\n"
        "2. DO NOT include ANY text before or after the JSON\n"
        "3. DO NOT include markdown code fences (```)\n"
        "4. DO NOT include explanatory comments\n"
        "5. DO NOT leave any fields empty or null\n"
        "6. Use ONLY double quotes for strings\n"
        "</OUTPUT_REQUIREMENTS>\n\n"
        "<JSON_SCHEMA>\n"
        "{\n"
        '  "question": "A clear, specific question about the topic",\n'
        '  "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        '  "correct_index": 0,\n'
        '  "hint": "A helpful hint for solving the question"\n'
        "}\n"
        "</JSON_SCHEMA>\n\n"
        "Output the JSON object now:"
    )


def create_debugging_prompt(topic: str, topic_text: str, difficulty: str, language: str = "python") -> str:
    """Create a prompt for generating a debugging challenge with the specified difficulty."""
    
    # Define difficulty-specific guidance
    difficulty_guidance = {
        "easy": (
            "For EASY difficulty:\n"
            "- Include a single, obvious bug that's easy to spot\n"
            "- Use simple code with clear structure\n"
            "- Focus on common syntax errors or basic logical mistakes\n"
            "- Provide clear hints that point directly to the issue\n"
            "- Code should be 5-10 lines maximum\n"
        ),
        "medium": (
            "For MEDIUM difficulty:\n"
            "- Include 1-2 bugs that require understanding the code flow\n"
            "- Use moderately complex code with multiple functions or classes\n"
            "- Focus on logical errors, edge cases, or incorrect algorithm implementation\n"
            "- Provide hints that guide toward the general area of the issue\n"
            "- Code should be 10-20 lines\n"
        ),
        "hard": (
            "For HARD difficulty:\n"
            "- Include subtle bugs that require deep understanding\n"
            "- Use complex code with multiple components or advanced patterns\n"
            "- Focus on complex logical errors, race conditions, or optimization issues\n"
            "- Provide hints that require analysis to apply correctly\n"
            "- Code should be 20-30 lines with appropriate complexity\n"
        )
    }
    
    # Get the appropriate guidance for the requested difficulty
    guidance = difficulty_guidance.get(difficulty.lower(), difficulty_guidance["medium"])
    
    return (
        f"<s>\n"
        f"You are a JSON-generating API that creates programming challenges. You must output ONLY valid JSON with NO additional text.\n"
        f"</s>\n\n"
        f"<TASK>\n"
        f"Generate a debugging challenge about {topic} in {language} at {difficulty} difficulty.\n"
        f"{guidance}\n"
        f"</TASK>\n\n"
        f"<CONTEXT>\n{topic_text[:500]}\n</CONTEXT>\n\n"
        "<OUTPUT_REQUIREMENTS>\n"
        "1. Output EXACTLY ONE valid JSON object\n"
        "2. DO NOT include ANY text before or after the JSON\n"
        "3. DO NOT include markdown code fences (```)\n"
        "4. DO NOT include explanatory comments\n"
        "5. DO NOT leave any fields empty or null\n"
        "6. Use ONLY double quotes for strings\n"
        "7. For code in JSON strings, escape newlines with \\n and quotes with \\\"\n"
        "</OUTPUT_REQUIREMENTS>\n\n"
        "<JSON_SCHEMA>\n"
        "{\n"
        '  "question": "A clear description of the bug to fix",\n'
        '  "buggy_code": "def example():\\n    return \\"buggy code here\\"",\n'
        '  "bug_description": "A specific description of what is wrong",\n'
        '  "hint": "A hint to help solve the problem"\n'
        "}\n"
        "</JSON_SCHEMA>\n\n"
        "Output the JSON object now:"
    )


def create_coding_prompt(topic: str, topic_text: str, difficulty: str, language: str = "python") -> str:
    """Create a prompt for generating a coding challenge with the specified difficulty."""
    
    # Define difficulty-specific guidance
    difficulty_guidance = {
        "easy": (
            "For EASY difficulty:\n"
            "- Create a straightforward implementation task\n"
            "- Focus on basic algorithms or data structures\n"
            "- Require only fundamental programming concepts\n"
            "- Include 1-2 simple test cases with clear inputs/outputs\n"
            "- Solution should be achievable in 5-10 lines of code\n"
            "- Provide a helpful hint that guides toward the solution approach\n"
        ),
        "medium": (
            "For MEDIUM difficulty:\n"
            "- Create a challenge requiring algorithmic thinking\n"
            "- Focus on efficiency and proper implementation\n"
            "- Require understanding of intermediate programming concepts\n"
            "- Include 2-3 test cases covering normal and edge cases\n"
            "- Solution should require 10-20 lines of code\n"
            "- Provide a hint that points to the general solution strategy\n"
        ),
        "hard": (
            "For HARD difficulty:\n"
            "- Create a complex challenge requiring optimization\n"
            "- Focus on advanced algorithms or data structures\n"
            "- Require understanding of advanced programming concepts\n"
            "- Include 3-4 test cases covering normal, edge, and corner cases\n"
            "- Solution may require 20-30 lines of code\n"
            "- Provide a subtle hint that requires analysis to apply\n"
        )
    }
    
    # Get the appropriate guidance for the requested difficulty
    guidance = difficulty_guidance.get(difficulty.lower(), difficulty_guidance["medium"])
    
    return (
        f"<s>\n"
        f"You are a JSON-generating API that creates programming challenges. You must output ONLY valid JSON with NO additional text.\n"
        f"</s>\n\n"
        f"<TASK>\n"
        f"Generate a coding challenge about {topic} in {language} at {difficulty} difficulty.\n"
        f"{guidance}\n"
        f"</TASK>\n\n"
        f"<CONTEXT>\n{topic_text[:500]}\n</CONTEXT>\n\n"
        "<OUTPUT_REQUIREMENTS>\n"
        "1. Output EXACTLY ONE valid JSON object\n"
        "2. DO NOT include ANY text before or after the JSON\n"
        "3. DO NOT include markdown code fences (```)\n"
        "4. DO NOT include explanatory comments\n"
        "5. DO NOT leave any fields empty or null\n"
        "6. Use ONLY double quotes for strings\n"
        "7. For code in JSON strings, escape newlines with \\n and quotes with \\\"\n"
        "</OUTPUT_REQUIREMENTS>\n\n"
        "<JSON_SCHEMA>\n"
        "{\n"
        '  "question": "A clear problem description",\n'
        '  "code_stub": "def solution():\\n    # Your code here\\n    pass",\n'
        '  "test_cases": [{"input": "example input", "expected": "expected output"}],\n'
        '  "hint": "A helpful hint for solving the problem"\n'
        "}\n"
        "</JSON_SCHEMA>\n\n"
        "Output the JSON object now:"
    )


def generate_multiple_choice(topic: str, topic_text: str, difficulty: str, language: str = "python") -> dict | None:
    """Generate a multiple choice question using the LLM with specified difficulty."""
    prompt = create_multiple_choice_prompt(topic, topic_text, difficulty, language)
    resp = generate_with_llm(prompt)
    parsed = parse_llm_response(resp, {})
    
    if not parsed or "question" not in parsed or "options" not in parsed:
        logger.warning(f"Invalid multiple choice JSON: {parsed}")
        return None
    
    # Normalize the multiple choice format
    mc = normalize_mc(parsed)
    if not mc:
        logger.warning(f"Failed to normalize multiple choice format: {parsed}")
        return None
    
    # Validate option count based on difficulty
    option_count = len(mc["options"])
    if option_count < 3:
        logger.warning(f"Too few options for multiple choice: {option_count}")
        # Add default options if needed
        while len(mc["options"]) < 4:
            mc["options"].append(f"Option {len(mc['options']) + 1}")
    
    # Get hint or generate fallback
    hint = mc.get("hint", mc.get("explanation", ""))
    if not hint or len(hint.strip()) < 10:  # Check if hint is empty or too short
        logger.info(f"Generating fallback hint for multiple choice about {topic}")
        hint = generate_fallback_hint_for_multiple_choice(topic, difficulty, mc["question"])
    
    return {
        "id": str(uuid.uuid4()),
        "topic": topic,
        "type": "multiple-choice",
        "question": mc["question"],
        "options": mc["options"],
        "correct_index": mc["correct_index"],
        "hint": hint,
        "difficulty": difficulty
    }


def generate_debugging(topic: str, topic_text: str, difficulty: str, language: str = "python") -> dict | None:
    """Generate a debugging challenge using the LLM with specified difficulty."""
    prompt = create_debugging_prompt(topic, topic_text, difficulty, language)
    resp = generate_with_llm(prompt)
    parsed = parse_llm_response(resp, {})
    
    if not parsed or "question" not in parsed or "buggy_code" not in parsed:
        logger.warning(f"Invalid debugging JSON: {parsed}")
        return None
    
    # Validate code complexity based on difficulty
    code_lines = parsed["buggy_code"].count('\n') + 1
    expected_min_lines = {
        "easy": 5,
        "medium": 10,
        "hard": 20
    }
    expected_max_lines = {
        "easy": 10,
        "medium": 20,
        "hard": 30
    }
    
    min_lines = expected_min_lines.get(difficulty.lower(), expected_min_lines["medium"])
    max_lines = expected_max_lines.get(difficulty.lower(), expected_max_lines["medium"])
    
    if code_lines < min_lines:
        logger.warning(f"Debugging challenge code too short for {difficulty} difficulty: {code_lines} lines")
    elif code_lines > max_lines:
        logger.warning(f"Debugging challenge code too long for {difficulty} difficulty: {code_lines} lines")
    
    # Get bug description for hint
    bug_description = parsed.get("bug_description", "")
    
    # Get hint or generate fallback
    hint = parsed.get("hint", bug_description)
    if not hint or len(hint.strip()) < 10:  # Check if hint is empty or too short
        logger.info(f"Generating fallback hint for debugging challenge about {topic}")
        hint = generate_fallback_hint_for_debugging(topic, difficulty, parsed["buggy_code"])
    
    return {
        "id": str(uuid.uuid4()),
        "topic": topic,
        "type": "debugging",
        "question": parsed["question"],
        "code_stub": parsed["buggy_code"],
        "hint": hint,
        "bug_comment": bug_description or hint,  # Use hint as bug comment if no description provided
        "difficulty": difficulty
    }


def generate_coding(topic: str, topic_text: str, difficulty: str, language: str = "python") -> dict | None:
    """Generate a coding challenge using the LLM with specified difficulty."""
    prompt = create_coding_prompt(topic, topic_text, difficulty, language)
    resp = generate_with_llm(prompt)
    parsed = parse_llm_response(resp, {})
    
    if not parsed or "question" not in parsed or "code_stub" not in parsed or "test_cases" not in parsed:
        logger.warning(f"Invalid coding JSON: {parsed}")
        return None
    
    # Validate code complexity based on difficulty
    code_lines = parsed["code_stub"].count('\n') + 1
    expected_min_lines = {
        "easy": 3,
        "medium": 5,
        "hard": 8
    }
    expected_max_lines = {
        "easy": 10,
        "medium": 15,
        "hard": 20
    }
    
    min_lines = expected_min_lines.get(difficulty.lower(), expected_min_lines["medium"])
    max_lines = expected_max_lines.get(difficulty.lower(), expected_max_lines["medium"])
    
    if code_lines < min_lines:
        logger.warning(f"Coding challenge stub too short for {difficulty} difficulty: {code_lines} lines")
    elif code_lines > max_lines:
        logger.warning(f"Coding challenge stub too long for {difficulty} difficulty: {code_lines} lines")
    
    # Validate test case count based on difficulty
    test_case_count = len(parsed["test_cases"])
    expected_test_cases = {
        "easy": 1,
        "medium": 2,
        "hard": 3
    }
    
    min_test_cases = expected_test_cases.get(difficulty.lower(), expected_test_cases["medium"])
    
    if test_case_count < min_test_cases:
        logger.warning(f"Too few test cases for {difficulty} difficulty: {test_case_count} test cases")
    
    # Get hint or generate fallback
    hint = parsed.get("hint", "")
    if not hint or len(hint.strip()) < 10:  # Check if hint is empty or too short
        logger.info(f"Generating fallback hint for coding challenge about {topic}")
        hint = generate_fallback_hint_for_coding(topic, difficulty, parsed["question"])
    
    return {
        "id": str(uuid.uuid4()),
        "topic": topic,
        "type": "coding",
        "question": parsed["question"],
        "code_stub": parsed["code_stub"],
        "test_cases": parsed["test_cases"],
        "hint": hint,
        "difficulty": difficulty
    }


def generate_challenge_with_llm(topic: str, topic_text: str, challenge_type: str, difficulty: str = "medium") -> dict | None:
    """
    Generate a programming challenge using the LLM with the specified difficulty.
    
    Args:
        topic: The topic to generate a challenge about
        topic_text: Text content related to the topic
        challenge_type: Type of challenge ("multiple_choice", "debugging", "coding")
        difficulty: Difficulty level ("easy", "medium", "hard")
        
    Returns:
        A dictionary containing the challenge, or None if generation failed
    """
    logger.info(f"Generating {challenge_type} challenge for topic '{topic}' at {difficulty} difficulty")
    
    if not is_model_ready():
        logger.warning("Model not ready, loading in background")
        load_model_in_background()
        return None
        
    if challenge_type == "multiple_choice":
        return generate_multiple_choice(topic, topic_text, difficulty)
    elif challenge_type == "debugging":
        return generate_debugging(topic, topic_text, difficulty)
    elif challenge_type == "coding":
        return generate_coding(topic, topic_text, difficulty)
    else:
        logger.warning(f"Unknown challenge type: {challenge_type}")
        return None


# Load model when running under Flask
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    logger.info("Flask detected, starting model loading in background")
    load_model_in_background()

