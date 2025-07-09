"""
Delete flag processor for handling quote file deletions.
"""

import os
from typing import Dict, Any
from .quote_writer import (
    read_quote_file_content, has_delete_flag, unwrap_quote_in_source, delete_quote_file
)


def process_delete_flags(destination_path: str, source_vault_path: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Processes quote files with delete: true flag and unwraps them in source files.
    Returns a dictionary with processing results.
    """
    results = {
        'quotes_unwrapped': 0,
        'errors': []
    }
    
    if not os.path.exists(destination_path):
        return results
    
    # Find all quote files with delete: true
    for root, dirs, files in os.walk(destination_path):
        for file in files:
            if file.endswith('.md'):
                quote_file_path = os.path.join(root, file)
                
                if has_delete_flag(quote_file_path):
                    try:
                        _process_single_delete_flag(
                            quote_file_path, source_vault_path, dry_run, results
                        )
                    except Exception as e:
                        results['errors'].append(
                            f"Error processing delete flag for {quote_file_path}: {str(e)}"
                        )
    
    return results


def _process_single_delete_flag(
    quote_file_path: str, 
    source_vault_path: str, 
    dry_run: bool, 
    results: Dict[str, Any]
) -> None:
    """Helper function to process a single quote file with delete flag."""
    frontmatter, _ = read_quote_file_content(quote_file_path)
    if not frontmatter:
        return
    
    # Extract source file from frontmatter
    source_file = _extract_source_file_from_frontmatter(frontmatter)
    if not source_file:
        return
    
    source_file_path = _find_source_file_path(source_file, source_vault_path)
    if not source_file_path:
        error_msg = f"Could not find source file {source_file} in {source_vault_path} for quote file {quote_file_path}"
        print(f"  ERROR: {error_msg}")
        results['errors'].append(error_msg)
        return
    
    # Extract block ID from filename
    block_id = _extract_block_id_from_filename(quote_file_path)
    if not block_id:
        return
    
    # Unwrap the quote in source file
    unwrapped = unwrap_quote_in_source(source_file_path, block_id, dry_run)
    if unwrapped:
        results['quotes_unwrapped'] += 1
    
    # Delete the quote file
    delete_quote_file(quote_file_path, dry_run)


def _extract_source_file_from_frontmatter(frontmatter: str) -> str:
    """Extract source file path from frontmatter string."""
    for line in frontmatter.split('\n'):
        if line.strip().startswith('source_path:'):
            return line.split('source_path:', 1)[1].strip().strip('"')
    return ""


def _find_source_file_path(source_file: str, source_vault_path: str) -> str:
    """Find the full path to a source file within the vault."""
    source_file_path = os.path.join(source_vault_path, source_file)
    
    if os.path.exists(source_file_path):
        return source_file_path
    
    # Recursively search for the file in the source vault
    for root_dir, _, files_in_dir in os.walk(source_vault_path):
        if source_file in files_in_dir:
            return os.path.join(root_dir, source_file)
    
    return ""


def _extract_block_id_from_filename(quote_file_path: str) -> str:
    """Extract block ID from quote filename."""
    filename = os.path.basename(quote_file_path)
    if ' - Quote' in filename:
        parts = filename.split(' - Quote')
        if len(parts) >= 2:
            block_id_part = parts[1].split(' - ')[0]
            return f"^Quote{block_id_part}"
    return "" 