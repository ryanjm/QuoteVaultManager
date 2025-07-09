"""
Source file synchronization logic for processing individual source files.
"""

import os
from typing import Dict, Any
from .quote_parser import extract_blockquotes_with_ids, validate_block_ids
from .quote_writer import (
    write_quote_file, update_quote_file_if_changed, delete_quote_file,
    find_quote_files_for_source, ensure_block_id_in_source, create_quote_filename
)
from .file_utils import get_book_title_from_path, get_vault_name_from_path


def sync_source_file(
    source_file: str, 
    destination_path: str, 
    dry_run: bool = False, 
    source_vault_path: str | None = None
) -> Dict[str, Any]:
    """
    Syncs a single source file to the quote vault.
    Returns a dictionary with sync results.
    """
    results = {
        'file': source_file,
        'quotes_processed': 0,
        'quotes_created': 0,
        'quotes_updated': 0,
        'block_ids_added': 0,
        'errors': []
    }
    
    # Extract vault name for Obsidian URI
    vault_name = get_vault_name_from_path(source_vault_path) if source_vault_path else "Notes"
    
    try:
        # Read and validate source file
        content = _read_source_file_content(source_file, results)
        if content is None:
            return results
        
        # Validate block IDs before processing
        block_id_errors = validate_block_ids(content)
        if block_id_errors:
            for error in block_id_errors:
                results['errors'].append(f"{source_file}: {error}")
            return results
        
        # Process quotes
        _process_quotes_from_source(
            source_file, content, destination_path, vault_name, 
            source_vault_path or "", dry_run, results
        )
        
        # Handle orphaned quotes
        _handle_orphaned_quotes(source_file, destination_path, dry_run, results)
        
    except Exception as e:
        results['errors'].append(f"Error processing {source_file}: {str(e)}")
    
    return results


def _read_source_file_content(source_file: str, results: Dict[str, Any]) -> str | None:
    """Read source file content with error handling."""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError as e:
        results['errors'].append(f"Unicode decode error in {source_file}: {e}")
        return None
    except PermissionError as e:
        results['errors'].append(f"Permission denied reading {source_file}: {e}")
        return None
    except Exception as e:
        results['errors'].append(f"Error reading {source_file}: {e}")
        return None


def _process_quotes_from_source(
    source_file: str, content: str, destination_path: str, 
    vault_name: str, source_vault_path: str, dry_run: bool, results: Dict[str, Any]
) -> None:
    """Process all quotes from a source file."""
    quotes_with_ids = extract_blockquotes_with_ids(content)
    
    # Track used block IDs
    used_block_nums = set()
    for _, block_id in quotes_with_ids:
        if block_id and block_id.startswith('^Quote'):
            try:
                used_block_nums.add(int(block_id.replace('^Quote', '')))
            except Exception:
                pass
    next_block_num = max(used_block_nums) + 1 if used_block_nums else 1
    
    # Get book title
    book_title = get_book_title_from_path(source_file)
    
    # Process each quote
    for quote_text, block_id in quotes_with_ids:
        results['quotes_processed'] += 1
        
        # Assign block ID if missing
        if block_id is None:
            block_id = f'^Quote{next_block_num:03d}'
            next_block_num += 1
            ensure_block_id_in_source(source_file, quote_text, block_id, dry_run)
            results['block_ids_added'] += 1
            # Update content so subsequent processing sees the new ID
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Generate quote filename and path
        filename = create_quote_filename(book_title, block_id, quote_text)
        quote_file_path = os.path.join(destination_path, book_title, filename)
        
        # Create or update quote file
        if os.path.exists(quote_file_path):
            updated = update_quote_file_if_changed(
                quote_file_path, quote_text, source_file, block_id, 
                dry_run, vault_name, source_vault_path or ""
            )
            if updated:
                results['quotes_updated'] += 1
        else:
            write_quote_file(
                destination_path, book_title, block_id, quote_text, 
                source_file, dry_run, vault_name, source_vault_path or ""
            )
            results['quotes_created'] += 1


def _handle_orphaned_quotes(
    source_file: str, destination_path: str, dry_run: bool, results: Dict[str, Any]
) -> None:
    """Handle quotes that exist in destination but not in source."""
    # Re-extract quotes to get updated block IDs after assignment
    with open(source_file, 'r', encoding='utf-8') as f:
        updated_content = f.read()
    updated_quotes_with_ids = extract_blockquotes_with_ids(updated_content)
    existing_block_ids = {block_id for _, block_id in updated_quotes_with_ids if block_id is not None}
    
    existing_quote_files = find_quote_files_for_source(destination_path, source_file)
    
    for quote_file in existing_quote_files:
        # Extract block ID from filename
        filename = os.path.basename(quote_file)
        if ' - Quote' in filename:
            parts = filename.split(' - Quote')
            if len(parts) >= 2:
                block_id_part = parts[1].split(' - ')[0]
                block_id = f"^Quote{block_id_part}"
                
                if block_id not in existing_block_ids:
                    # This quote no longer exists in source, delete it
                    results['quotes_deleted'] = results.get('quotes_deleted', 0) + 1
                    delete_quote_file(quote_file, dry_run) 