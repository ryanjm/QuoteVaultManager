"""
Source file synchronization logic for processing individual source files.
"""

import os
from typing import Dict, Any, Optional
from .models.source_file import SourceFile
from .models.destination_file import DestinationFile, Quote
from .file_utils import get_book_title_from_path, get_vault_name_from_path

def sync_source_file(
    source_file: str, 
    destination_path: str, 
    dry_run: bool = False, 
    source_vault_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Syncs a single source file to the quote vault.
    Returns a dictionary with sync results.
    """
    results = _init_results(source_file)
    vault_name = get_vault_name_from_path(source_vault_path) if source_vault_path else "Notes"

    # Use SourceFile object for all operations
    source = SourceFile.from_file(source_file)
    errors = source.validate_block_ids()
    if errors:
        results['errors'].extend(errors)
        return results

    block_ids_added = source.assign_missing_block_ids(dry_run)
    results['block_ids_added'] += block_ids_added
    if block_ids_added and not dry_run:
        source = SourceFile.from_file(source_file)  # Reload to get updated block IDs

    # Prepare quotes_with_ids for downstream logic
    quotes_with_ids = [(q.text, q.block_id) for q in source.quotes]
    block_id_map = {i: q.block_id for i, q in enumerate(source.quotes) if q.block_id}

    _sync_quote_files(
        source_file, destination_path, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path, results
    )
    _remove_orphaned_quote_files(source_file, destination_path, block_id_map, dry_run, results)

    # Save any changes to the source file (quotes, block IDs)
    if block_ids_added and not dry_run:
        source.save()

    return results



def _init_results(source_file: str) -> Dict[str, Any]:
    """Initialize the results dictionary for sync operations."""
    return {
        'file': source_file,
        'quotes_processed': 0,
        'quotes_created': 0,
        'quotes_updated': 0,
        'block_ids_added': 0,
        'errors': []
    }

def _sync_quote_files(
    source_file, destination_path, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path, results
):
    """Create or update quote files for all quotes in the source file."""
    book_title = get_book_title_from_path(source_file)
    for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
        results['quotes_processed'] += 1
        if block_id is None:
            results['errors'].append(f"Quote at index {idx} has no block ID after assignment")
            continue
        filename = DestinationFile.create_quote_filename(book_title, block_id, quote_text)
        quote_file_path = os.path.join(destination_path, book_title, filename)
        if os.path.exists(quote_file_path):
            dest = DestinationFile.from_file(quote_file_path)
            updated = False
            if dest.quote.text != quote_text:
                dest.quote.text = quote_text
                updated = True
            if dest.quote.block_id != block_id:
                dest.quote.block_id = block_id
                updated = True
            if updated and not dry_run:
                dest.save(quote_file_path)
                results['quotes_updated'] += 1
        else:
            # Create new DestinationFile and save
            frontmatter = {
                'block_id': block_id,
                'vault': vault_name,
                'delete': False,
                'favorite': False,
                'edited': False
            }
            dest = DestinationFile(frontmatter, Quote(quote_text, block_id))
            if not dry_run:
                os.makedirs(os.path.dirname(quote_file_path), exist_ok=True)
                dest.save(quote_file_path)
            results['quotes_created'] += 1

def _remove_orphaned_quote_files(source_file, destination_path, block_id_map, dry_run, results):
    """Remove quote files that no longer have a corresponding blockquote in the source file."""
    from .models.destination_vault import DestinationVault
    existing_block_ids = set(block_id_map.values())
    vault = DestinationVault(destination_path)
    existing_quote_files = vault.find_quote_files_for_source(source_file)
    for quote_file in existing_quote_files:
        filename = os.path.basename(quote_file)
        block_id = DestinationFile.extract_block_id_from_filename(filename)
        if block_id and block_id not in existing_block_ids:
            results['quotes_deleted'] = results.get('quotes_deleted', 0) + 1
            if not dry_run:
                DestinationFile.delete(quote_file) 