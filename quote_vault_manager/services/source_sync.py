"""
Source file synchronization logic for processing individual source files.
"""

import os
from typing import Dict, Any, Optional
from quote_vault_manager.models.source_file import SourceFile
from quote_vault_manager.models.destination_file import DestinationFile, Quote
from quote_vault_manager.file_utils import get_book_title_from_path, get_vault_name_from_path

def sync_source_file(
    source_file: str, 
    destination_vault, 
    dry_run: bool = False, 
    source_vault_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Syncs a single source file to the quote vault.
    Returns a dictionary with sync results.
    """
    results = _init_results(source_file)
    
    # Handle both string path and DestinationVault object
    if isinstance(destination_vault, str):
        # Legacy API - create a temporary DestinationVault
        from quote_vault_manager.models.destination_vault import DestinationVault
        temp_dest_vault = DestinationVault(destination_vault)
        vault_name = "Notes"  # Default for legacy API
    else:
        # New API - use the provided DestinationVault
        temp_dest_vault = destination_vault
        vault_name = destination_vault.source_vault.vault_name if destination_vault.source_vault else "Notes"

    # Use SourceFile object for all operations
    source = SourceFile.from_file(source_file)
    errors = source.validate_block_ids()
    if errors:
        results['errors'].extend(errors)
        return results

    block_ids_added = source.assign_missing_block_ids(dry_run)
    results['block_ids_added'] += block_ids_added
    if block_ids_added and not dry_run:
        source.save()

    # Prepare quotes_with_ids for downstream logic
    quotes_with_ids = [(q.text, q.block_id) for q in source.quotes]
    block_id_map = {i: q.block_id for i, q in enumerate(source.quotes) if q.block_id}
    
    # Sync quotes to destination
    sync_results = temp_dest_vault.sync_quotes_from_source(
        source_file, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path
    )
    results.update(sync_results)
    
    # Remove orphaned quotes
    orphan_results = temp_dest_vault.remove_orphaned_quotes_for_source(
        source_file, block_id_map, dry_run
    )
    results.update(orphan_results)

    # Save any changes to the source file (quotes, block IDs)
    # (Already saved above after assigning block IDs)

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