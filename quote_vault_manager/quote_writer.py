import os
from typing import Optional
from urllib.parse import quote
import re
import yaml

def create_obsidian_uri(source_file: str, block_id: str, source_vault: str = "Notes", vault_root: str = "") -> str:
    """Creates an Obsidian URI in the correct format."""
    # Remove .md extension
    if source_file.endswith('.md'):
        source_file = source_file[:-3]
    # If vault_root is provided, make path relative
    if vault_root:
        rel_path = os.path.relpath(source_file, vault_root)
    else:
        rel_path = source_file
    # Normalize to forward slashes
    rel_path = rel_path.replace(os.sep, '/')
    encoded_file = quote(rel_path)
    encoded_block = quote(block_id)
    return f"obsidian://open?vault={source_vault}&file={encoded_file}%23{encoded_block}"

def _truncate_words_to_length(text: str, max_length: int = 30) -> str:
    """Truncate text to max_length, but don't cut words in the middle."""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space]
    return truncated

def _clean_filename_text(text: str) -> str:
    """Clean text for use in filenames by replacing unsafe characters."""
    # Replace unsafe characters with hyphens
    cleaned = text.replace('\\', '-').replace('/', '-').replace(':', '-')
    # Remove multiple consecutive hyphens and trim
    cleaned = re.sub(r'-+', '-', cleaned)
    return cleaned.strip('- ')

def create_quote_filename(book_title: str, block_id: str, quote_text: str) -> str:
    """Creates a filename for a quote file using the convention: [Book Title] - QuoteNNN - [First Few Words].md"""
    clean_block_id = block_id.lstrip('^')
    clean_quote_text = quote_text.strip()
    
    # Extract the first few words (up to 5 words, max 30 chars)
    words = clean_quote_text.split()[:5]
    first_words = ' '.join(words)
    first_words = _truncate_words_to_length(first_words, 30)
    first_words = _clean_filename_text(first_words)
    
    return f"{book_title} - {clean_block_id} - {first_words}.md"

def _format_quote_text(quote_text: str) -> str:
    """Format quote text with proper blockquote formatting."""
    quote_lines = quote_text.split('\n')
    return '\n'.join(f'> {line}' for line in quote_lines)

def _create_quote_content_template(quote_text: str, source_file: str, block_id: str, frontmatter: str, vault_name: str, vault_root: str) -> str:
    """Create quote content with the given frontmatter and quote text."""
    from . import VERSION
    from .transformations.v0_2_add_random_note_link import RANDOM_NOTE_LINK
    
    uri = create_obsidian_uri(source_file, block_id, vault_name, vault_root)
    link_text = os.path.basename(source_file).replace('.md', '')
    formatted_quote = _format_quote_text(quote_text)
    
    return f"""---
{frontmatter}
---

{formatted_quote}

**Source:** [{link_text}]({uri})

{RANDOM_NOTE_LINK}
"""

def create_quote_content(quote_text: str, source_file: str, block_id: str, vault_name: str = "Notes", vault_root: str = "") -> str:
    """Creates the content for a quote file including frontmatter and source link."""
    from . import VERSION
    
    default_frontmatter = f"""delete: false
favorite: false
source_path: "{os.path.basename(source_file)}"
version: "{VERSION}"
"""
    return _create_quote_content_template(quote_text, source_file, block_id, default_frontmatter, vault_name, vault_root)

def read_quote_file_content(file_path: str) -> tuple[Optional[str], Optional[str]]:
    """Reads a quote file and returns (frontmatter, quote_content) tuple."""
    if not os.path.exists(file_path):
        return None, None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split frontmatter and content
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            quote_content = parts[2].strip()
            return frontmatter, quote_content
        else:
            return None, content.strip()
    except Exception:
        return None, None

def extract_quote_text_from_content(content: Optional[str]) -> Optional[str]:
    """Extracts the actual quote text from quote file content (removes > prefix)."""
    if content is None:
        return None
    lines = content.split('\n')
    quote_lines = []
    for line in lines:
        if line.strip().startswith('>'):
            quote_lines.append(line.lstrip('> ').rstrip())
        elif line.strip().startswith('**Source:'):
            break
    return '\n'.join(quote_lines) if quote_lines else None

# DEPRECATED: Use DestinationFile/SourceFile methods instead.
def update_quote_file_if_changed(file_path: str, new_quote_text: str, source_file: str, 
                                block_id: str, dry_run: bool = False, vault_name: str = "Notes", vault_root: str = "") -> bool:
    """Updates a quote file if the quote content has changed. Preserves existing frontmatter."""
    frontmatter, existing_content = read_quote_file_content(file_path)
    
    if frontmatter is None:
        # File doesn't exist or is corrupted, create new one
        if not dry_run:
            content = create_quote_content(new_quote_text, source_file, block_id, vault_name, vault_root)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return True
    
    if existing_content is None:
        return False
    
    existing_quote_text = extract_quote_text_from_content(existing_content)
    if existing_quote_text != new_quote_text:
        # Quote content has changed, update it
        if not dry_run:
            new_content = _create_quote_content_template(new_quote_text, source_file, block_id, frontmatter, vault_name, vault_root)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        return True
    
    return False

# DEPRECATED: Use DestinationFile/SourceFile methods instead.
def write_quote_file(destination_path: str, book_title: str, block_id: str, 
                    quote_text: str, source_file: str, dry_run: bool = False, vault_name: str = "Notes", vault_root: str = "") -> str:
    """Creates a quote file in the destination directory."""
    # Create book directory if it doesn't exist
    book_dir = os.path.join(destination_path, book_title)
    if not dry_run:
        os.makedirs(book_dir, exist_ok=True)
    
    # Generate filename and content
    filename = create_quote_filename(book_title, block_id, quote_text)
    file_path = os.path.join(book_dir, filename)
    
    if not dry_run:
        content = create_quote_content(quote_text, source_file, block_id, vault_name, vault_root)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return file_path

# DEPRECATED: Use DestinationFile/SourceFile methods instead.
def delete_quote_file(file_path: str, dry_run: bool = False) -> bool:
    """Deletes a quote file."""
    if not os.path.exists(file_path):
        return False
    
    if not dry_run:
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    else:
        return True

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
                    frontmatter, _ = read_quote_file_content(file_path)
                    if frontmatter and f'source_path: "{source_filename}"' in frontmatter:
                        quote_files.append(file_path)
                except Exception:
                    continue
    
    return quote_files

def has_delete_flag(file_path: str) -> bool:
    """Checks if a quote file has delete: true in its frontmatter."""
    frontmatter, _ = read_quote_file_content(file_path)
    if frontmatter is None:
        return False
    
    return 'delete: true' in frontmatter

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

# DEPRECATED: Use DestinationFile/SourceFile methods instead.
def ensure_block_id_in_source(source_file_path: str, quote_text: str, block_id: str, dry_run: bool = False) -> bool:
    """Ensures that a quote in the source file has the specified block ID."""
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
                processed_lines, new_i, needs_block_id = _process_blockquote_for_id_assignment(lines, i, quote_text)
                new_lines.extend(processed_lines)
                i = new_i
                if needs_block_id:
                    new_lines.append(block_id)
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
    formatted_new = _format_quote_text(new_quote_text).split('\n')
    return lines[:start] + formatted_new + [block_id] + lines[end+1:]

# DEPRECATED: Use DestinationFile/SourceFile methods instead.
def overwrite_quote_in_source(source_file_path: str, block_id: str, new_quote_text: str, dry_run: bool = False) -> bool:
    """Overwrite a quote in the source file (by block ID) with new text, preserving blockquote formatting and block ID."""
    if not os.path.exists(source_file_path):
        return False
    try:
        with open(source_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.splitlines()
        start, end = _find_blockquote_with_id(lines, block_id)
        if start is None or end is None:
            return False
        # Prepare new blockquote section
        formatted_new = _format_quote_text(new_quote_text).split('\n')
        old_blockquote = lines[start:end]
        new_blockquote = formatted_new
        if old_blockquote == new_blockquote:
            return False
        new_lines = lines[:start] + new_blockquote + [block_id] + lines[end+1:]
        if not dry_run:
            with open(source_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        return True
    except Exception:
        return False

def frontmatter_str_to_dict(frontmatter: str) -> dict:
    """Converts a YAML frontmatter string to a Python dict."""
    try:
        return yaml.safe_load(frontmatter) or {}
    except Exception:
        return {}

def frontmatter_dict_to_str(frontmatter_dict: dict) -> str:
    """Converts a Python dict to a YAML frontmatter string."""
    try:
        return yaml.safe_dump(frontmatter_dict, sort_keys=False).strip()
    except Exception:
        return "" 