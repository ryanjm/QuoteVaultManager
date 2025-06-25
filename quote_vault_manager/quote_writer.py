import os
from typing import Optional
from urllib.parse import quote
import re

def create_quote_filename(book_title: str, block_id: str, quote_text: str) -> str:
    """
    Creates a filename for a quote file using the convention:
    [Book Title] - QuoteNNN - [First Few Words].md
    """
    # Remove caret from block_id for filename
    clean_block_id = block_id.lstrip('^')
    
    # Strip whitespace from quote text
    clean_quote_text = quote_text.strip()
    
    # Extract the first few words (up to 5 words, max 30 chars)
    words = clean_quote_text.split()[:5]
    first_words = ' '.join(words)
    
    # Truncate to 30 chars, but don't cut words in the middle
    if len(first_words) > 30:
        truncated = first_words[:30]
        # Find the last space and truncate there
        last_space = truncated.rfind(' ')
        if last_space > 0:
            first_words = truncated[:last_space]
        else:
            first_words = truncated
    
    # Clean up the first words for filename safety
    first_words = first_words.replace('\\', '-').replace('/', '-').replace(':', '-')
    # Remove multiple consecutive hyphens and trim
    first_words = re.sub(r'-+', '-', first_words)
    first_words = first_words.strip('- ')
    
    return f"{book_title} - {clean_block_id} - {first_words}.md"

def create_quote_content(quote_text: str, source_file: str, block_id: str, source_vault: str = "Notes") -> str:
    """
    Creates the content for a quote file including frontmatter and source link.
    """
    # Create Obsidian URI for source
    encoded_file = quote(source_file)
    encoded_block = quote(block_id)
    uri = f"obsidian://open?vault={source_vault}&file={encoded_file}%23{encoded_block}"
    
    # Remove .md extension from link text
    link_text = source_file.replace('.md', '')
    
    content = f"""---
delete: false
favorite: false
source_path: "{source_file}"
---

> {quote_text}

**Source:** [{link_text}]({uri})
"""
    return content

def read_quote_file_content(file_path: str) -> tuple[Optional[str], Optional[str]]:
    """
    Reads a quote file and returns (frontmatter, quote_content) tuple.
    Returns (None, None) if file doesn't exist or can't be read.
    """
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

def extract_quote_text_from_content(content: str) -> Optional[str]:
    """
    Extracts the actual quote text from quote file content (removes > prefix).
    """
    lines = content.split('\n')
    quote_lines = []
    for line in lines:
        if line.strip().startswith('>'):
            quote_lines.append(line.lstrip('> ').rstrip())
        elif line.strip().startswith('**Source:'):
            break
    return '\n'.join(quote_lines) if quote_lines else None

def update_quote_file_if_changed(file_path: str, new_quote_text: str, source_file: str, 
                                block_id: str, dry_run: bool = False) -> bool:
    """
    Updates a quote file if the quote content has changed.
    Preserves existing frontmatter.
    Returns True if file was updated, False otherwise.
    """
    frontmatter, existing_content = read_quote_file_content(file_path)
    
    if frontmatter is None:
        # File doesn't exist or is corrupted, create new one
        if not dry_run:
            content = create_quote_content(new_quote_text, source_file, block_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return True
    
    # Extract existing quote text
    if existing_content is None:
        return False
    
    existing_quote_text = extract_quote_text_from_content(existing_content)
    
    if existing_quote_text != new_quote_text:
        # Quote content has changed, update it
        if not dry_run:
            # Create new content with existing frontmatter
            encoded_file = quote(source_file)
            encoded_block = quote(block_id)
            uri = f"obsidian://open?vault=Notes&file={encoded_file}%23{encoded_block}"
            
            # Remove .md extension from link text
            link_text = source_file.replace('.md', '')
            
            new_content = f"""---
{frontmatter}
---

> {new_quote_text}

**Source:** [{link_text}]({uri})
"""
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        return True
    
    return False

def write_quote_file(destination_path: str, book_title: str, block_id: str, 
                    quote_text: str, source_file: str, dry_run: bool = False) -> str:
    """
    Creates a quote file in the destination directory.
    Returns the path to the created file.
    """
    # Create book directory if it doesn't exist
    book_dir = os.path.join(destination_path, book_title)
    if not dry_run:
        os.makedirs(book_dir, exist_ok=True)
    
    # Generate filename and content
    filename = create_quote_filename(book_title, block_id, quote_text)
    file_path = os.path.join(book_dir, filename)
    
    if not dry_run:
        content = create_quote_content(quote_text, source_file, block_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return file_path

def delete_quote_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Deletes a quote file.
    Returns True if file was deleted or would be deleted in dry run, False if file doesn't exist.
    """
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
    """
    Finds all quote files that reference a specific source file.
    Returns a list of file paths.
    """
    quote_files = []
    
    if not os.path.exists(destination_path):
        return quote_files
    
    for root, dirs, files in os.walk(destination_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    frontmatter, _ = read_quote_file_content(file_path)
                    if frontmatter and f'source_path: "{source_file}"' in frontmatter:
                        quote_files.append(file_path)
                except Exception:
                    continue
    
    return quote_files

def has_delete_flag(file_path: str) -> bool:
    """
    Checks if a quote file has delete: true in its frontmatter.
    Returns True if delete flag is set, False otherwise.
    """
    frontmatter, _ = read_quote_file_content(file_path)
    if frontmatter is None:
        return False
    
    return 'delete: true' in frontmatter

def unwrap_quote_in_source(source_file_path: str, block_id: str, dry_run: bool = False) -> bool:
    """
    Unwraps a quote in the source file by removing blockquote formatting and block ID.
    Wraps the text in quotation marks.
    Returns True if the file was modified, False otherwise.
    """
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
            
            # Check if this line starts a blockquote
            if line.strip().startswith('>'):
                quote_lines = []
                quote_start = i
                
                # Collect all consecutive blockquote lines
                while i < len(lines) and lines[i].strip().startswith('>'):
                    quote_lines.append(lines[i].lstrip('> ').rstrip())
                    i += 1
                
                # Check if the next line is the block ID we're looking for
                if i < len(lines) and lines[i].strip() == block_id:
                    # This is the quote we need to unwrap
                    quote_text = ' '.join(quote_lines)
                    new_lines.append(f'"{quote_text}"')
                    i += 1  # Skip the block ID line
                    modified = True
                else:
                    # Not the right quote, keep original lines
                    for j in range(quote_start, i):
                        new_lines.append(lines[j])
            else:
                new_lines.append(line)
                i += 1
        
        if modified and not dry_run:
            with open(source_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        
        return modified
        
    except Exception:
        return False 