"""
File utility functions for the quote vault manager.
"""

import os
from typing import List


def has_sync_quotes_flag(file_path: str) -> bool:
    """
    Checks if a markdown file has sync_quotes: true in its frontmatter.
    Returns True if the flag is set, False otherwise.
    """
    frontmatter, _ = split_frontmatter_from_file(file_path)
    if frontmatter:
        return 'sync_quotes: true' in frontmatter
    return False


def get_markdown_files(directory: str) -> List[str]:
    """
    Recursively finds all markdown files in the given directory.
    Returns a list of file paths.
    """
    markdown_files = []
    
    if not os.path.exists(directory):
        return markdown_files
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    
    return markdown_files


def get_book_title_from_path(file_path: str) -> str:
    """
    Extracts the book title from a file path.
    Removes the .md extension and returns the filename.
    """
    filename = os.path.basename(file_path)
    return filename.replace('.md', '')


def get_vault_name_from_path(vault_path: str) -> str:
    """Extracts the vault name (last folder) from a full vault path."""
    return os.path.basename(os.path.normpath(vault_path)) 


def split_frontmatter(content: str) -> tuple:
    """
    Splits markdown content into (frontmatter, body) tuple.
    If frontmatter is present (YAML between ---), returns (frontmatter, body).
    If not, returns (None, content).
    """
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].lstrip('\n')
            return frontmatter, body
    return None, content 


def split_frontmatter_from_file(path: str) -> tuple:
    """
    Opens the file at the given path and splits its content into (frontmatter, body) tuple.
    Returns (frontmatter, body) or (None, content) if no frontmatter is present or file can't be read.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return split_frontmatter(content)
    except Exception:
        return None, None 