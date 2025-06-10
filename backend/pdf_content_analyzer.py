"""
Enhanced PDF Content Analyzer for Programming Challenge Website

This module provides improved functionality to analyze PDF documents and extract
structured content for generating programming challenges.
"""

import os
import re
import fitz  # PyMuPDF

def extract_topics_and_content(pdf_path):
    """
    Extract topics and their content from a PDF file.
    This is the main entry point function that app.py imports.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of dictionaries containing topic information
    """
    analyzer = PDFContentAnalyzer()
    structured_content = analyzer.analyze_pdf(pdf_path)
    
    # Format the output as expected by the challenge generator
    topics_with_content = []
    
    if structured_content and 'topics' in structured_content:
        for topic in structured_content['topics']:
            # Get content for this topic
            topic_content = ""
            code_examples = []
            key_concepts = []
            
            # Find the section for this topic
            for section in structured_content.get('topic_sections', []):
                if section['title'] == topic:
                    # Extract content for this section
                    topic_content = structured_content['text'][section['start']:section['end']]
                    break
            
            # Get code examples for this topic
            if topic in structured_content.get('topic_code_blocks', {}):
                code_examples = structured_content['topic_code_blocks'][topic]
            
            # Get key concepts for this topic
            if topic in structured_content.get('topic_key_concepts', {}):
                key_concepts = structured_content['topic_key_concepts'][topic]
            
            # Add to the result
            topics_with_content.append({
                'name': topic,
                'content': topic_content,
                'code_examples': code_examples,
                'key_concepts': key_concepts,
                'language': structured_content.get('primary_language', 'python')
            })
    
    return {
    'topics': [ t['name'] for t in topics_with_content ],
    'topics_with_content': topics_with_content
    }


class PDFContentAnalyzer:
    """
    A class for analyzing PDF documents and extracting structured content
    for programming challenge generation.
    """
    
    def __init__(self):
        """Initialize the PDF Content Analyzer."""
        # Common programming languages and their keywords
        self.programming_languages = {
            'python': ['def', 'class', 'import', 'for', 'while', 'if', 'else', 'try', 'except', 'with', 'as', 'return'],
            'java': ['public', 'class', 'static', 'void', 'int', 'String', 'import', 'extends', 'implements'],
            'javascript': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'async', 'await'],
            'c++': ['int', 'void', 'class', 'struct', 'template', 'namespace', 'std', 'cout', 'cin', 'vector'],
            'c#': ['using', 'namespace', 'class', 'public', 'private', 'static', 'void', 'int', 'string']
        }
        
        # Common stop words for filtering
        self.stop_words = set([
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
            'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
            'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren',
            'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
            'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won',
            'wouldn', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
            'does', 'did', 'doing', 'to', 'from', 'by', 'for', 'with', 'about',
            'against', 'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'of', 'at', 'by', 'for', 'with'
        ])
    
    def analyze_pdf(self, pdf_path):
        """
        Analyze a PDF document and extract structured content.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Structured content from the PDF
        """
        try:
            # Extract text and formatting information from PDF
            text, section_info = self._extract_text_with_formatting(pdf_path)
            if not text:
                return None
            
            # Extract topics using improved section detection
            topics = self._extract_unique_topics_from_sections(section_info)
            
            # Extract code blocks for each topic
            topic_code_blocks = self._extract_topic_code_blocks(text, section_info)
            
            # Extract key concepts for each topic
            topic_key_concepts = self._extract_topic_key_concepts(text, section_info)
            
            # Determine primary programming language
            primary_language = self._determine_primary_language(text, topic_code_blocks)
            
            # Create structured content with section-specific information
            structured_content = {
                'text': text[:5000],  # Limit full text to 5000 chars
                'topics': topics,
                'topic_sections': section_info,
                'topic_code_blocks': topic_code_blocks,
                'topic_key_concepts': topic_key_concepts,
                'primary_language': primary_language
            }
            
            return structured_content
        except Exception as e:
            print(f"Error analyzing PDF: {e}")
            return None
    
    def _extract_text_with_formatting(self, pdf_path):
        """
        Extract text from a PDF document with formatting information.
        This improved method detects section headings based on font size and style.
        """
        try:
            full_text = ""
            section_info = []
            
            with fitz.open(pdf_path) as doc:
                text_length = 0
                
                # First pass: collect all potential headings with their formatting
                potential_headings = []
                
                for page_num, page in enumerate(doc):
                    # Get blocks that include formatting information
                    blocks = page.get_text("dict")["blocks"]
                    
                    for block in blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    text = span["text"].strip()
                                    font_size = span["size"]
                                    font_flags = span["flags"]  # Bold, italic, etc.
                                    
                                    # Check if this might be a heading (larger font or bold)
                                    is_heading = font_size > 11 or (font_flags & 4) != 0  # 4 is bold
                                    
                                    if is_heading and text and len(text.split()) <= 7:
                                        # This looks like a section heading
                                        potential_headings.append({
                                            "text": text,
                                            "font_size": font_size,
                                            "font_flags": font_flags,
                                            "page": page_num,
                                            "position": text_length
                                        })
                                    
                                    full_text += text + " "
                                    text_length = len(full_text)
                
                # Second pass: analyze potential headings to identify true section headings
                if potential_headings:
                    # Sort headings by font size to identify hierarchy
                    font_sizes = sorted(set(h["font_size"] for h in potential_headings), reverse=True)
                    
                    # Map font sizes to heading levels
                    font_size_to_level = {}
                    for i, size in enumerate(font_sizes[:3]):  # Consider at most 3 heading levels
                        font_size_to_level[size] = i + 1
                    
                    # Skip the document title (first heading) and process the rest
                    title_processed = False
                    
                    # Process headings in document order
                    for heading in sorted(potential_headings, key=lambda h: h["position"]):
                        # Skip the document title (first heading with largest font)
                        if not title_processed and heading["font_size"] == font_sizes[0]:
                            title_processed = True
                            continue
                        
                        # Skip if this is likely not a real heading (e.g., just bold text in a paragraph)
                        if heading["text"].endswith('.') and len(heading["text"].split()) > 3:
                            continue
                        
                        # Determine heading level
                        level = font_size_to_level.get(heading["font_size"], 3)
                        
                        # Close previous section if it exists
                        if section_info and section_info[-1]["end"] == 0:
                            section_info[-1]["end"] = heading["position"]
                        
                        # Start new section
                        section_info.append({
                            "title": heading["text"],
                            "start": heading["position"],
                            "end": 0,
                            "level": level,
                            "page": heading["page"]
                        })
                    
                    # Close the last section
                    if section_info and section_info[-1]["end"] == 0:
                        section_info[-1]["end"] = text_length
            
            # If no sections were detected, try a simpler approach
            if not section_info:
                section_info = self._extract_sections_from_text(full_text)
            
            return full_text, section_info
        except Exception as e:
            print(f"Error extracting text with formatting: {e}")
            return "", []
    
    def _extract_sections_from_text(self, text):
        """
        Fallback method to extract sections from plain text when formatting detection fails.
        Looks for patterns that might indicate section headings.
        """
        lines = text.split('\n')
        section_info = []
        current_pos = 0
        title_processed = False
        
        for line in lines:
            line = line.strip()
            # Look for potential section headings (short, capitalized lines)
            if line and len(line) < 50 and len(line.split()) <= 5 and line[0].isupper():
                # Skip the document title (first heading)
                if not title_processed:
                    title_processed = True
                    current_pos += len(line) + 1
                    continue
                
                # Check if it's not just a normal sentence (ends with period)
                if not line.endswith('.'):
                    # This might be a section heading
                    if section_info and section_info[-1]["end"] == 0:
                        # Close previous section
                        section_info[-1]["end"] = current_pos
                    
                    # Start new section
                    section_info.append({
                        "title": line,
                        "start": current_pos,
                        "end": 0,
                        "level": 1 if line.isupper() else 2,
                        "page": 0  # We don't have page info in this method
                    })
            
            current_pos += len(line) + 1  # +1 for the newline
        
        # Close the last section
        if section_info and section_info[-1]["end"] == 0:
            section_info[-1]["end"] = current_pos
        
        return section_info
    
    def _extract_unique_topics_from_sections(self, section_info):
        """
        Extract unique topics from section headings.
        This improved method ensures all major sections are recognized as topics
        and eliminates duplicates.
        """
        # Extract all potential topics
        potential_topics = []
        
        for section in section_info:
            title = section["title"].strip()
            # Skip very short titles or titles that are just numbers
            if len(title) < 3 or title.isdigit():
                continue
                
            # Skip generic titles
            generic_titles = ["introduction", "conclusion", "summary", "overview", "appendix", "references"]
            if title.lower() in generic_titles:
                continue
                
            # Add to potential topics
            potential_topics.append({
                "title": title,
                "level": section["level"]
            })
        
        # If no potential topics, use a fallback
        if not potential_topics:
            return ["Programming"]
        
        # First try to get level 1 headings
        topics = []
        for topic in potential_topics:
            if topic["level"] == 1 and topic["title"] not in topics:
                topics.append(topic["title"])
        
        # If no level 1 headings, use level 2
        if not topics:
            for topic in potential_topics:
                if topic["level"] == 2 and topic["title"] not in topics:
                    topics.append(topic["title"])
        
        # If still no topics, use all headings
        if not topics:
            for topic in potential_topics:
                if topic["title"] not in topics:
                    topics.append(topic["title"])
        
        # Ensure we don't have duplicate topics
        unique_topics = []
        for topic in topics:
            # Check if this topic is a substring of another topic
            is_substring = False
            for other_topic in topics:
                if topic != other_topic and topic in other_topic:
                    is_substring = True
                    break
            
            # Only add if it's not a substring of another topic
            if not is_substring and topic not in unique_topics:
                unique_topics.append(topic)
        
        # If we have too many topics, limit to the most important ones
        if len(unique_topics) > 5:
            unique_topics = unique_topics[:5]
        
        # If we still don't have topics, try a more aggressive approach
        if not unique_topics:
            # Look for common programming topics in the text
            common_topics = ["Python Basics", "Data Structures", "Algorithms", "Functions", "Error Handling"]
            for section in section_info:
                for topic in common_topics:
                    if topic.lower() in section["title"].lower() and topic not in unique_topics:
                        unique_topics.append(topic)
        
        return unique_topics
    
    def _extract_topic_code_blocks(self, text, section_info):
        """
        Extract code blocks for each topic/section.
        """
        topic_code_blocks = {}
        
        for section in section_info:
            topic = section["title"]
            section_text = text[section["start"]:section["end"]]
            
            # Extract code blocks from this section
            code_blocks = self._extract_code_blocks_from_text(section_text)
            
            if code_blocks:
                topic_code_blocks[topic] = code_blocks
        
        return topic_code_blocks
    
    def _extract_code_blocks_from_text(self, text):
        """
        Extract potential code blocks from the text.
        """
        # Look for indented blocks or blocks between code markers
        lines = text.split('\n')
        code_blocks = []
        current_block = []
        in_block = False
        
        # Common code block markers
        code_markers = ['```', '---', '===', 'code:', 'example:', 'function', 'def ', 'class ']
        
        for line in lines:
            # Check if line might be start/end of code block
            is_code_marker = any(marker in line.lower() for marker in code_markers)
            is_indented = line.startswith('    ') or line.startswith('\t')
            
            # Start of code block
            if (is_code_marker or is_indented) and not in_block and not current_block:
                in_block = True
                current_block.append(line)
            # Continuation of code block
            elif in_block:
                if not line.strip():  # Empty line might end a block
                    if len(current_block) > 2:  # Only keep blocks with at least 3 lines
                        code_blocks.append('\n'.join(current_block))
                    current_block = []
                    in_block = False
                else:
                    current_block.append(line)
            
            # If block gets too long, end it
            if len(current_block) > 20:
                code_blocks.append('\n'.join(current_block))
                current_block = []
                in_block = False
        
        # Add the last block if it exists
        if current_block and len(current_block) > 2:
            code_blocks.append('\n'.join(current_block))
        
        return code_blocks
    
    def _extract_topic_key_concepts(self, text, section_info):
        """
        Extract key concepts for each topic/section.
        """
        topic_key_concepts = {}
        
        for section in section_info:
            topic = section["title"]
            section_text = text[section["start"]:section["end"]]
            
            # Extract key concepts from this section
            key_concepts = self._extract_key_concepts_from_text(section_text)
            
            if key_concepts:
                topic_key_concepts[topic] = key_concepts
        
        return topic_key_concepts
    
    def _extract_key_concepts_from_text(self, text):
        """
        Extract key concepts from the text.
        """
        # Look for definitional sentences
        sentences = re.split(r'[.!?]', text)
        key_concepts = []
        
        # Patterns that might indicate a definition
        definition_patterns = [
            r'is a', r'are a', r'refers to', r'defined as', r'means', 
            r'consists of', r'represents', r'describes', r'known as'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
                
            # Check if this sentence might be a definition
            is_definition = any(re.search(pattern, sentence.lower()) for pattern in definition_patterns)
            
            if is_definition:
                # Extract the concept being defined (usually before the definition pattern)
                for pattern in definition_patterns:
                    match = re.search(pattern, sentence.lower())
                    if match:
                        concept = sentence[:match.start()].strip()
                        # Only keep if concept is not too long and not just a stop word
                        if 2 < len(concept.split()) < 6 and not all(word.lower() in self.stop_words for word in concept.split()):
                            key_concepts.append(concept)
                        break
        
        # Limit to top concepts
        return key_concepts[:5]
    
    def _determine_primary_language(self, text, topic_code_blocks):
        """
        Determine the primary programming language used in the document.
        """
        # Count language keywords in the text and code blocks
        language_counts = {lang: 0 for lang in self.programming_languages}
        
        # Check all code blocks
        for topic, blocks in topic_code_blocks.items():
            for block in blocks:
                for lang, keywords in self.programming_languages.items():
                    for keyword in keywords:
                        # Count exact keyword matches (with word boundaries)
                        language_counts[lang] += len(re.findall(r'\b' + re.escape(keyword) + r'\b', block))
        
        # Also check the full text for language mentions
        for lang in self.programming_languages:
            # Count mentions of the language name
            language_counts[lang] += len(re.findall(r'\b' + re.escape(lang) + r'\b', text.lower()))
        
        # Determine the most likely language
        if language_counts:
            primary_language = max(language_counts.items(), key=lambda x: x[1])[0]
            return primary_language
        
        # Default to Python if no clear language is detected
        return "python"
