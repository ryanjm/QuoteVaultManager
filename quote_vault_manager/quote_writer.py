import os
from typing import Optional
from urllib.parse import quote
import re
import yaml
from quote_vault_manager.models.destination_file import DestinationFile

def find_quote_files_for_source(destination_path: str, source_file: str) -> list[str]:
    """Finds all quote files that reference a specific source file."""
    quote_files = []
    
    if not os.path.exists(destination_path):
        return quote_files
    
    # Extract just the filename from the source_file path
    source_filename = os.path.basename(source_file)
    
    for root, dirs, files in os.walk(destination_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    frontmatter, _ = DestinationFile.read_quote_file_content(file_path)
                    if frontmatter and f'source_path: "{source_filename}"' in frontmatter:
                        quote_files.append(file_path)
                except Exception:
                    continue
    
    return quote_files

def unwrap_quote_in_source(source_file_path: str, block_id: str, dry_run: bool = False) -> bool:
    """Unwraps a quote in the source file by removing blockquote formatting and block ID."""
    if not os.path.exists(source_file_path):
        return False
    
    try:
        with open(source_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        modified = False
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if _is_blockquote_line(line):
                processed_lines, new_i, was_unwrapped = _process_blockquote_section(lines, i, block_id)
                new_lines.extend(processed_lines)
                i = new_i
                if was_unwrapped:
                    modified = True
            else:
                new_lines.append(line)
                i += 1
        
        if modified and not dry_run:
            with open(source_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        
        return modified
        
    except Exception:
        return False

def _is_blockquote_line(line: str) -> bool:
    """Check if a line starts a blockquote."""
    return line.strip().startswith('>')

def _collect_blockquote_lines(lines: list[str], start_index: int) -> tuple[list[str], int]:
    """Collect consecutive blockquote lines starting from start_index. Returns (quote_lines, end_index)."""
    quote_lines = []
    i = start_index
    while i < len(lines) and _is_blockquote_line(lines[i]):
        quote_lines.append(lines[i].lstrip('> ').rstrip())
        i += 1
    return quote_lines, i

def _process_blockquote_section(lines: list[str], i: int, target_block_id: str) -> tuple[list[str], int, bool]:
    """Process a blockquote section and check if it matches the target block ID."""
    quote_lines, i = _collect_blockquote_lines(lines, i)
    
    # Check if the next line is the block ID we're looking for
    if i < len(lines) and lines[i].strip() == target_block_id:
        # This is the quote we need to unwrap
        quote_text = ' '.join(quote_lines)
        return [f'"{quote_text}"'], i + 1, True  # Skip the block ID line
    else:
        # Not the right quote, keep original lines
        original_lines = []
        for j in range(i - len(quote_lines), i):
            original_lines.append(lines[j])
        return original_lines, i, False

def _has_block_id_at_index(lines: list[str], index: int) -> bool:
    """Check if there's a block ID at the given index."""
    return index < len(lines) and lines[index].strip().startswith('^Quote')

def _process_blockquote_for_id_assignment(lines: list[str], i: int, target_quote_text: str) -> tuple[list[str], int, bool]:
    """Process a blockquote section for block ID assignment."""
    quote_lines, i = _collect_blockquote_lines(lines, i)
    has_block_id = _has_block_id_at_index(lines, i)
    
    # Check if this quote matches our target quote
    current_quote_text = '\n'.join(quote_lines).strip()
    target_quote_text = target_quote_text.strip()
    
    if current_quote_text == target_quote_text and not has_block_id:
        # This is our target quote and it doesn't have a block ID
        # We'll add the block ID later, for now just return the lines
        original_lines = []
        for j in range(i - len(quote_lines), i):
            original_lines.append(lines[j])
        return original_lines, i, True  # Signal that we need to add block ID
    else:
        # Not our target quote or already has block ID, keep as is
        original_lines = []
        for j in range(i - len(quote_lines), i):
            original_lines.append(lines[j])
        if has_block_id:
            original_lines.append(lines[i])  # Include the block ID line
            i += 1
        return original_lines, i, False

def _find_blockquote_with_id(lines, block_id):
    """Find the start/end indices of the blockquote with the given block_id."""
    i = 0
    while i < len(lines):
        if _is_blockquote_line(lines[i]):
            start = i
            # Collect all consecutive blockquote lines
            while i < len(lines) and _is_blockquote_line(lines[i]):
                i += 1
            # Check if the next line is the block ID
            if i < len(lines) and lines[i].strip() == block_id:
                end = i  # end is index of block_id line
                return start, end
        i += 1
    return None, None

def _replace_blockquote(lines, start, end, new_quote_text, block_id):
    """Replace lines[start:end+1] with new blockquote and block_id."""
    formatted_new = new_quote_text.split('\n') # No longer need _format_quote_text
    return lines[:start] + formatted_new + [block_id] + lines[end+1:]

def _format_quote_text(quote_text: str) -> str:
    """Formats the quote text for blockquote replacement."""
    # Remove leading/trailing quotes if they exist
    quote_text = re.sub(r'^"([^"]*)"$', r'\1', quote_text)
    quote_text = re.sub(r'^"([^"]*)"$', r'\1', quote_text)
    
    # Split into lines and format each line
    lines = quote_text.split('\n')
    formatted_lines = []
    for line in lines:
        if line.strip().startswith('>'):
            formatted_lines.append(line)
        else:
            formatted_lines.append(f'> {line}')
    return '\n'.join(formatted_lines) 