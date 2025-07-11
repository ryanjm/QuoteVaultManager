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

    # Use DestinationVault for destination operations
    from .models.destination_vault import DestinationVault
    destination_vault = DestinationVault(destination_path)
    
    # Sync quotes to destination
    sync_results = destination_vault.sync_quotes_from_source(
        source_file, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path
    )
    results.update(sync_results)
    
    # Remove orphaned quotes
    orphan_results = destination_vault.remove_orphaned_quotes_for_source(
        source_file, block_id_map, dry_run
    )
    results.update(orphan_results)

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