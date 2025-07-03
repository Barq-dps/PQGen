import re
import logging
import os
from typing import List, Dict, Any, Optional, Tuple

# PDF processing libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    print("pdfplumber not available. Install with: pip install pdfplumber")
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    print("PyPDF2 not available. Install with: pip install PyPDF2")
    PYPDF2_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("PyMuPDF not available. Install with: pip install PyMuPDF")
    PYMUPDF_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using multiple methods for maximum compatibility
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return ""
    
    text = ""
    
    # Method 1: Try pdfplumber (best for structured text)
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                logger.info(f"Successfully extracted {len(text)} characters using pdfplumber")
                return text
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
    
    # Method 2: Try PyMuPDF (good for complex layouts)
    if PYMUPDF_AVAILABLE and not text.strip():
        try:
            pdf_document = fitz.open(pdf_path)
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            pdf_document.close()
            
            if text.strip():
                logger.info(f"Successfully extracted {len(text)} characters using PyMuPDF")
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
    
    # Method 3: Try PyPDF2 (fallback)
    if PYPDF2_AVAILABLE and not text.strip():
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                logger.info(f"Successfully extracted {len(text)} characters using PyPDF2")
                return text
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
    
    if not text.strip():
        logger.error("All PDF extraction methods failed")
        return ""
    
    return text

def analyze_pdf_content(text: str) -> Dict[str, Any]:
    """
    Enhanced analysis of PDF content with improved topic extraction
    """
    if not text or len(text.strip()) < 10:
        logger.warning("Text too short for analysis")
        return {
            'topics': [],
            'programming_languages': [],
            'complexity_level': 'unknown',
            'content_type': 'unknown',
            'code_snippets': []
        }
    
    # Extract topics using multiple methods
    topics = extract_comprehensive_topics(text)
    
    # Detect programming languages
    languages = detect_programming_languages(text)
    
    # Determine complexity level
    complexity = determine_complexity_level(text)
    
    # Determine content type
    content_type = determine_content_type(text)
    
    # Extract code snippets
    code_snippets = extract_code_snippets(text)
    
    analysis = {
        'topics': topics,
        'programming_languages': languages,
        'complexity_level': complexity,
        'content_type': content_type,
        'code_snippets': code_snippets[:5],  # Limit to 5 snippets
        'text_length': len(text),
        'has_code': len(code_snippets) > 0
    }
    
    logger.info(f"PDF analysis complete: {len(topics)} topics, {len(languages)} languages, {complexity} complexity")
    return analysis

def extract_comprehensive_topics(text: str) -> List[str]:
    """
    Extract topics using multiple enhanced methods
    """
    topics = []
    
    # Method 1: Heading-based extraction
    heading_topics = extract_topics_from_headings(text)
    topics.extend(heading_topics)
    
    # Method 2: Enhanced pattern matching
    pattern_topics = extract_topics_by_enhanced_patterns(text)
    topics.extend(pattern_topics)
    
    # Method 3: Code-based topic inference
    code_topics = extract_topics_from_code_analysis(text)
    topics.extend(code_topics)
    
    # Method 4: Keyword density analysis
    keyword_topics = extract_topics_by_keyword_density(text)
    topics.extend(keyword_topics)
    
    # Deduplicate and validate topics
    unique_topics = []
    seen = set()
    
    for topic in topics:
        topic_clean = topic.strip()
        if (topic_clean and 
            len(topic_clean) > 2 and 
            len(topic_clean) < 50 and
            topic_clean.lower() not in seen and
            is_valid_programming_topic(topic_clean)):
            seen.add(topic_clean.lower())
            unique_topics.append(topic_clean)
    
    # Limit to top 10 most relevant topics
    return unique_topics[:10]

def extract_topics_from_headings(text: str) -> List[str]:
    """
    Extract topics from document headings and structure
    """
    topics = []
    lines = text.split('\n')
    
    # Various heading patterns
    heading_patterns = [
        r'^#+\s+(.+)$',  # Markdown headings
        r'^\d+\.\s*(.+)$',  # Numbered sections
        r'^\d+\.\d+\s*(.+)$',  # Sub-numbered sections
        r'^[A-Z][A-Z\s]{5,}$',  # ALL CAPS headings
        r'^(.+):$',  # Colon-terminated headings
        r'^\*\*(.+)\*\*$',  # Bold headings
        r'^(.+)\n[=-]{3,}$',  # Underlined headings
    ]
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Check for underlined headings
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if re.match(r'^[=-]{3,}$', next_line):
                if is_valid_programming_topic(line):
                    topics.append(clean_topic_text(line))
                continue
        
        # Check other heading patterns
        for pattern in heading_patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                heading = match.group(1).strip()
                if is_valid_programming_topic(heading):
                    topics.append(clean_topic_text(heading))
                break
    
    return topics

def extract_topics_by_enhanced_patterns(text: str) -> List[str]:
    """
    Extract topics using enhanced pattern matching with context awareness
    """
    topics = []
    text_lower = text.lower()
    
    # Enhanced topic patterns with context
    enhanced_patterns = {
        'Variables and Data Types': [
            r'\bvariable\s+(declaration|assignment|initialization)\b',
            r'\bdata\s+types?\b.*\b(int|string|float|boolean)\b',
            r'\b(integer|string|float|boolean)\s+variables?\b'
        ],
        'Control Flow Statements': [
            r'\bif\s+statements?\b.*\belse\b',
            r'\bconditional\s+(logic|statements?)\b',
            r'\bbranching\s+(logic|statements?)\b'
        ],
        'Loop Structures': [
            r'\bfor\s+loops?\b.*\biteration\b',
            r'\bwhile\s+loops?\b.*\bcondition\b',
            r'\bnested\s+loops?\b',
            r'\bloop\s+(control|iteration)\b'
        ],
        'Function Definition': [
            r'\bfunction\s+(definition|declaration)\b',
            r'\bdefining\s+functions?\b',
            r'\bfunction\s+parameters?\b.*\barguments?\b'
        ],
        'Object-Oriented Programming': [
            r'\bclass\s+(definition|declaration)\b',
            r'\bobject\s+oriented\s+programming\b',
            r'\binheritance\b.*\bpolymorphism\b',
            r'\bencapsulation\b.*\babstraction\b'
        ],
        'Data Structures': [
            r'\b(arrays?|lists?)\b.*\b(indexing|elements?)\b',
            r'\bdictionaries\b.*\b(keys?|values?)\b',
            r'\bdata\s+structures?\b.*\b(implementation|operations?)\b'
        ],
        'Error Handling': [
            r'\berror\s+handling\b.*\bexceptions?\b',
            r'\btry\s+catch\b.*\bfinally\b',
            r'\bexception\s+handling\b'
        ],
        'File Operations': [
            r'\bfile\s+(handling|operations?)\b',
            r'\breading\s+files?\b.*\bwriting\s+files?\b',
            r'\binput\s+output\s+operations?\b'
        ],
        'Algorithm Design': [
            r'\balgorithm\s+(design|implementation)\b',
            r'\bsorting\s+algorithms?\b',
            r'\bsearch\s+algorithms?\b',
            r'\brecursive\s+algorithms?\b'
        ]
    }
    
    for topic, patterns in enhanced_patterns.items():
        topic_score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            topic_score += len(matches)
        
        # Require minimum score for confidence
        if topic_score >= 2:
            topics.append(topic)
    
    return topics

def extract_topics_from_code_analysis(text: str) -> List[str]:
    """
    Infer topics from code snippets and programming constructs
    """
    topics = []
    
    # Extract code blocks
    code_snippets = extract_code_snippets(text)
    
    # Analyze code patterns
    code_patterns = {
        'Function Definition': [r'\bdef\s+\w+\s*\(', r'\bfunction\s+\w+\s*\('],
        'Class Definition': [r'\bclass\s+\w+\s*[:\(]'],
        'Loop Constructs': [r'\bfor\s+\w+\s+in\b', r'\bwhile\s+.+:'],
        'Conditional Logic': [r'\bif\s+.+:', r'\belif\s+.+:', r'\belse\s*:'],
        'Exception Handling': [r'\btry\s*:', r'\bexcept\s+\w*:', r'\bfinally\s*:'],
        'List Operations': [r'\[.*\]', r'\.append\(', r'\.extend\('],
        'Dictionary Operations': [r'\{.*\}', r'\.keys\(\)', r'\.values\(\)'],
        'String Operations': [r'\.split\(', r'\.join\(', r'\.replace\('],
        'File Operations': [r'\bopen\s*\(', r'\.read\(\)', r'\.write\('],
        'Import Statements': [r'\bimport\s+\w+', r'\bfrom\s+\w+\s+import']
    }
    
    all_code = ' '.join(code_snippets)
    
    for topic, patterns in code_patterns.items():
        for pattern in patterns:
            if re.search(pattern, all_code):
                topics.append(topic)
                break  # Only add each topic once
    
    return topics

def extract_topics_by_keyword_density(text: str) -> List[str]:
    """
    Extract topics based on keyword density and co-occurrence
    """
    topics = []
    text_lower = text.lower()
    
    # Programming concept keywords with weights
    concept_keywords = {
        'Python Fundamentals': {
            'keywords': ['python', 'syntax', 'indentation', 'interpreter', 'script'],
            'weight': 1.0
        },
        'Data Types and Variables': {
            'keywords': ['variable', 'integer', 'string', 'float', 'boolean', 'type'],
            'weight': 1.2
        },
        'Control Structures': {
            'keywords': ['if', 'else', 'elif', 'condition', 'boolean', 'logic'],
            'weight': 1.1
        },
        'Iteration and Loops': {
            'keywords': ['for', 'while', 'range', 'iteration', 'loop', 'break', 'continue'],
            'weight': 1.1
        },
        'Functions and Methods': {
            'keywords': ['function', 'def', 'parameter', 'argument', 'return', 'call'],
            'weight': 1.3
        },
        'Data Structures': {
            'keywords': ['list', 'array', 'dictionary', 'tuple', 'set', 'index', 'key'],
            'weight': 1.2
        },
        'Object-Oriented Programming': {
            'keywords': ['class', 'object', 'method', 'attribute', 'inheritance', 'instance'],
            'weight': 1.4
        },
        'Error Handling': {
            'keywords': ['try', 'except', 'finally', 'exception', 'error', 'raise'],
            'weight': 1.3
        },
        'File and I/O Operations': {
            'keywords': ['file', 'open', 'read', 'write', 'close', 'input', 'output'],
            'weight': 1.2
        },
        'Modules and Libraries': {
            'keywords': ['import', 'module', 'library', 'package', 'from'],
            'weight': 1.1
        }
    }
    
    for topic, data in concept_keywords.items():
        keywords = data['keywords']
        weight = data['weight']
        
        # Count keyword occurrences
        keyword_count = sum(len(re.findall(r'\b' + keyword + r'\b', text_lower)) 
                          for keyword in keywords)
        
        # Calculate weighted score
        score = keyword_count * weight
        
        # Require minimum score and multiple keywords for confidence
        unique_keywords_found = sum(1 for keyword in keywords 
                                  if re.search(r'\b' + keyword + r'\b', text_lower))
        
        if score >= 3 and unique_keywords_found >= 2:
            topics.append(topic)
    
    return topics

def detect_programming_languages(text: str) -> List[str]:
    """
    Detect programming languages mentioned or used in the text
    """
    languages = []
    text_lower = text.lower()
    
    # Language detection patterns
    language_patterns = {
        'Python': [
            r'\bpython\b', r'\.py\b', r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+',
            r'\bprint\s*\(', r'\bif\s+__name__\s*==\s*["\']__main__["\']'
        ],
        'Java': [
            r'\bjava\b', r'\.java\b', r'\bpublic\s+class\b', r'\bpublic\s+static\s+void\s+main',
            r'\bSystem\.out\.println', r'\bpublic\s+\w+\s+\w+\s*\('
        ],
        'JavaScript': [
            r'\bjavascript\b', r'\.js\b', r'\bfunction\s+\w+\s*\(', r'\bvar\s+\w+',
            r'\bconsole\.log', r'\bdocument\.\w+', r'\bwindow\.\w+'
        ],
        'C++': [
            r'\bc\+\+\b', r'\.cpp\b', r'\.h\b', r'\b#include\b',
            r'\bstd::', r'\bcout\s*<<', r'\bint\s+main\s*\('
        ],
        'C': [
            r'\b(?<!c\+\+)c\b', r'\.c\b', r'\bprintf\s*\(', r'\bscanf\s*\(',
            r'\b#include\s*<stdio\.h>', r'\bmain\s*\(\s*\)'
        ],
        'SQL': [
            r'\bsql\b', r'\bselect\s+\w+\s+from\b', r'\binsert\s+into\b',
            r'\bupdate\s+\w+\s+set\b', r'\bdelete\s+from\b', r'\bcreate\s+table\b'
        ]
    }
    
    for language, patterns in language_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                languages.append(language)
                break  # Only add each language once
    
    return languages

def determine_complexity_level(text: str) -> str:
    """
    Determine the complexity level of the content
    """
    text_lower = text.lower()
    
    # Complexity indicators
    beginner_indicators = [
        'introduction', 'basic', 'fundamentals', 'getting started',
        'hello world', 'first program', 'simple', 'easy'
    ]
    
    intermediate_indicators = [
        'intermediate', 'advanced', 'complex', 'algorithm',
        'data structure', 'object oriented', 'inheritance', 'polymorphism'
    ]
    
    advanced_indicators = [
        'expert', 'professional', 'optimization', 'performance',
        'design pattern', 'architecture', 'framework', 'concurrent'
    ]
    
    beginner_score = sum(1 for indicator in beginner_indicators 
                        if indicator in text_lower)
    intermediate_score = sum(1 for indicator in intermediate_indicators 
                           if indicator in text_lower)
    advanced_score = sum(1 for indicator in advanced_indicators 
                        if indicator in text_lower)
    
    if advanced_score >= 2:
        return 'hard'
    elif intermediate_score >= 2:
        return 'medium'
    elif beginner_score >= 2:
        return 'easy'
    else:
        return 'medium'  # Default to medium

def determine_content_type(text: str) -> str:
    """
    Determine the type of content (tutorial, exercise, reference, etc.)
    """
    text_lower = text.lower()
    
    # Content type indicators
    tutorial_indicators = [
        'tutorial', 'guide', 'how to', 'step by step',
        'learn', 'example', 'demonstration'
    ]
    
    exercise_indicators = [
        'exercise', 'problem', 'challenge', 'practice',
        'assignment', 'homework', 'quiz'
    ]
    
    reference_indicators = [
        'reference', 'documentation', 'manual', 'specification',
        'api', 'library', 'function list'
    ]
    
    code_example_indicators = [
        'code example', 'sample code', 'implementation',
        'source code', 'program', 'script'
    ]
    
    tutorial_score = sum(1 for indicator in tutorial_indicators 
                        if indicator in text_lower)
    exercise_score = sum(1 for indicator in exercise_indicators 
                        if indicator in text_lower)
    reference_score = sum(1 for indicator in reference_indicators 
                         if indicator in text_lower)
    code_example_score = sum(1 for indicator in code_example_indicators 
                            if indicator in text_lower)
    
    scores = {
        'tutorial': tutorial_score,
        'exercise': exercise_score,
        'reference': reference_score,
        'code_example': code_example_score
    }
    
    max_score = max(scores.values())
    if max_score == 0:
        return 'general'
    
    return max(scores, key=scores.get)

def extract_code_snippets(text: str) -> List[str]:
    """
    Extract code snippets from the text using multiple patterns
    """
    code_snippets = []
    
    # Pattern 1: Code blocks with triple backticks
    code_block_pattern = r'```(?:\w+)?\n?(.*?)\n?```'
    code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
    code_snippets.extend([block.strip() for block in code_blocks if block.strip()])
    
    # Pattern 2: Indented code blocks (4+ spaces)
    lines = text.split('\n')
    current_snippet = []
    
    for line in lines:
        if len(line) >= 4 and line[:4] == '    ' and line.strip():
            current_snippet.append(line[4:])  # Remove 4-space indentation
        else:
            if current_snippet and len('\n'.join(current_snippet).strip()) > 20:
                code_snippets.append('\n'.join(current_snippet).strip())
            current_snippet = []
    
    # Add final snippet if exists
    if current_snippet and len('\n'.join(current_snippet).strip()) > 20:
        code_snippets.append('\n'.join(current_snippet).strip())
    
    # Pattern 3: Inline code with specific programming keywords
    inline_code_pattern = r'`([^`]+)`'
    inline_codes = re.findall(inline_code_pattern, text)
    
    programming_keywords = ['def ', 'class ', 'import ', 'for ', 'while ', 'if ', 'else:', 'return ']
    for code in inline_codes:
        if any(keyword in code for keyword in programming_keywords):
            code_snippets.append(code.strip())
    
    # Remove duplicates and filter by length
    unique_snippets = []
    seen = set()
    
    for snippet in code_snippets:
        snippet_clean = snippet.strip()
        if (snippet_clean and 
            len(snippet_clean) >= 10 and 
            snippet_clean not in seen):
            seen.add(snippet_clean)
            unique_snippets.append(snippet_clean)
    
    return unique_snippets[:10]  # Limit to 10 snippets

def is_valid_programming_topic(text: str) -> bool:
    """
    Determine if a text string represents a valid programming topic
    """
    text_lower = text.lower()
    
    # Programming-related keywords
    programming_keywords = [
        'function', 'variable', 'loop', 'condition', 'class', 'object',
        'algorithm', 'data', 'structure', 'syntax', 'code', 'programming',
        'method', 'parameter', 'return', 'array', 'list', 'dictionary',
        'string', 'integer', 'boolean', 'exception', 'error', 'debug',
        'import', 'module', 'library', 'framework', 'api', 'database',
        'iteration', 'recursion', 'inheritance', 'polymorphism', 'encapsulation'
    ]
    
    # Check if any programming keywords are present
    has_programming_keywords = any(keyword in text_lower for keyword in programming_keywords)
    
    # Filter out generic/non-programming terms
    generic_terms = [
        'introduction', 'overview', 'summary', 'conclusion', 'chapter',
        'section', 'part', 'appendix', 'index', 'table of contents',
        'references', 'bibliography', 'about', 'preface', 'page',
        'figure', 'image', 'note', 'tip', 'warning', 'example'
    ]
    
    is_generic = any(term in text_lower for term in generic_terms)
    
    # Check length constraints
    word_count = len(text.split())
    is_reasonable_length = 1 <= word_count <= 8
    
    # Must have programming keywords, not be generic, and be reasonable length
    return has_programming_keywords and not is_generic and is_reasonable_length

def clean_topic_text(text: str) -> str:
    """
    Clean and normalize topic text
    """
    # Remove leading numbers, bullets, and special characters
    text = re.sub(r'^[\d\.\-\*\#\s]+', '', text)
    
    # Remove trailing punctuation except necessary ones
    text = re.sub(r'[^\w\s\-\(\)]+$', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Capitalize properly
    if text and not text[0].isupper():
        text = text[0].upper() + text[1:]
    
    return text.strip()

# Backward compatibility functions (maintain original API)
def get_topics_from_pdf_analysis(pdf_path: str) -> List[str]:
    """
    Backward compatibility function for topic extraction
    """
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        analysis = analyze_pdf_content(text)
        return analysis.get('topics', [])
    except Exception as e:
        logger.error(f"Error in get_topics_from_pdf_analysis: {e}")
        return []

