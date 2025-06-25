import re
from typing import List, Optional, Tuple

def extract_blockquotes(markdown: str) -> List[str]:
    """
    Extracts multiline blockquotes from markdown text.
    Groups consecutive lines starting with '>' as a single quote.
    Returns a list of blockquote strings (with leading '> ' removed).
    """
    blockquotes = []
    current = []
    for line in markdown.splitlines():
        if line.strip().startswith('>'):
            current.append(line.lstrip('> ').rstrip())
        else:
            if current:
                blockquotes.append('\n'.join(current).strip())
                current = []
    if current:
        blockquotes.append('\n'.join(current).strip())
    return blockquotes

BLOCK_ID_PATTERN = re.compile(r'^\^Quote(\d{3})$', re.MULTILINE)

def extract_blockquotes_with_ids(markdown: str) -> List[Tuple[str, Optional[str]]]:
    """
    Extracts blockquotes and their associated block IDs (^QuoteNNN) from markdown text.
    Returns a list of (quote_text, block_id or None) tuples.
    """
    blockquotes = []
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].lstrip('> ').rstrip())
                i += 1
            # Look ahead for block ID
            block_id = None
            if i < len(lines) and BLOCK_ID_PATTERN.match(lines[i].strip()):
                block_id = lines[i].strip()
                i += 1
            blockquotes.append(('\n'.join(quote_lines).strip(), block_id))
        else:
            i += 1
    return blockquotes

def get_next_block_id(markdown: str) -> str:
    """
    Finds the highest existing block ID in the markdown and returns the next sequential ID.
    If no block IDs exist, returns '^Quote001'.
    """
    existing_ids = []
    for line in markdown.splitlines():
        match = BLOCK_ID_PATTERN.match(line.strip())
        if match:
            existing_ids.append(int(match.group(1)))
    
    if not existing_ids:
        return '^Quote001'
    
    next_num = max(existing_ids) + 1
    return f'^Quote{next_num:03d}' 