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
    from .models.destination_file import DestinationFile
    from .models.source_file import SourceFile
    # Read the quote file using DestinationFile
    dest = DestinationFile.from_file(quote_file_path)
    frontmatter = dest.frontmatter
    if not frontmatter:
        return
    # Extract source file from frontmatter
    source_file = frontmatter.get('source_path')
    if not source_file:
        return
    import os
    source_file_path = os.path.join(source_vault_path, source_file) if source_vault_path else source_file
    if not os.path.exists(source_file_path):
        error_msg = f"Could not find source file {source_file} in {source_vault_path} for quote file {quote_file_path}"
        print(f"  ERROR: {error_msg}")
        results['errors'].append(error_msg)
        return
    # Extract block ID from frontmatter
    block_id = frontmatter.get('block_id')
    if not block_id:
        return
    # Remove the quote from the source file
    source = SourceFile.from_file(source_file_path)
    removed = source.remove_quote(block_id)
    if removed and not dry_run:
        source.save()
        results['quotes_unwrapped'] += 1
    # Delete the quote file
    if not dry_run:
        DestinationFile.delete(quote_file_path) 