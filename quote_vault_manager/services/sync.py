"""
Main synchronization orchestrator for the quote vault manager.
"""

from typing import Dict, Any
from quote_vault_manager.config import load_config, ConfigError
from quote_vault_manager.file_utils import has_sync_quotes_flag, get_markdown_files
from quote_vault_manager.services.transformation_manager import transformation_manager
from quote_vault_manager.services.source_sync import sync_source_file
from quote_vault_manager.models.source_vault import SourceVault
from quote_vault_manager.models.destination_vault import DestinationVault
from quote_vault_manager import VERSION


def sync_vaults(config: Dict[str, str], dry_run: bool = False) -> Dict[str, Any]:
    """
    Main sync function that orchestrates the entire quote vault synchronization process.
    Returns a dictionary with overall sync results.
    """
    results = {
        'source_files_processed': 0,
        'total_quotes_processed': 0,
        'total_quotes_created': 0,
        'total_quotes_updated': 0,
        'total_block_ids_added': 0,
        'total_quotes_deleted': 0,
        'total_quotes_unwrapped': 0,
        'total_edited_quotes_synced': 0,
        'errors': []
    }
    
    source_vault_path = config['source_vault_path']
    destination_vault_path = config['destination_vault_path']

    # Instantiate vaults
    source_vault = SourceVault(source_vault_path)
    destination_vault = DestinationVault(destination_vault_path)

    # Step 0: Apply transformations to all quote files before sync
    destination_vault.transform_all(lambda dest: None)  # Placeholder for actual transformation logic
    destination_vault.save_all()

    # Step 1: Validate and assign block IDs in all source files
    errors = source_vault.validate_all()
    results['errors'].extend(errors)
    block_ids_added = source_vault.assign_block_ids_all()
    results['total_block_ids_added'] += block_ids_added
    source_vault.save_all()

    # Step 2: Sync all source files to the destination vault
    sync_results = source_vault.sync_to_destination(destination_vault, dry_run)
    for k in sync_results:
        if k == 'errors':
            results['errors'].extend(sync_results[k])
        else:
            results[k] += sync_results[k]

    # Step 3: Batch delete quote files with delete flag
    delete_results = destination_vault.delete_flagged(source_vault_path, dry_run)
    results['total_quotes_unwrapped'] = delete_results.get('quotes_unwrapped', 0)
    results['errors'].extend(delete_results.get('errors', []))

    # Step 4: Batch sync edited quotes back to source files
    edited_synced = destination_vault.sync_edited_back(source_vault_path, dry_run)
    results['total_edited_quotes_synced'] = edited_synced

    return results


def _apply_transformations(destination_vault_path: str, dry_run: bool) -> None:
    """Apply transformations to all quote files and notify user of updates."""
    files_updated = transformation_manager.apply_transformations_to_all_quotes(destination_vault_path, dry_run=dry_run)
    if files_updated:
        if dry_run:
            print(f"🔄 [DRY-RUN] {files_updated} quote files would be updated to version {VERSION}")
        else:
            print(f"🔄 {files_updated} quote files updated to version {VERSION}")


def _process_source_files(source_vault_path: str, destination_vault_path: str, dry_run: bool, results: Dict[str, Any]) -> None:
    """Process all source files with sync_quotes flag and update results."""
    markdown_files = get_markdown_files(source_vault_path)
    
    for file_path in markdown_files:
        if has_sync_quotes_flag(file_path):
            file_results = sync_source_file(file_path, destination_vault_path, dry_run, source_vault_path)
            
            results['source_files_processed'] += 1
            results['total_quotes_processed'] += file_results['quotes_processed']
            results['total_quotes_created'] += file_results['quotes_created']
            results['total_quotes_updated'] += file_results['quotes_updated']
            results['total_block_ids_added'] += file_results['block_ids_added']
            results['total_quotes_deleted'] += file_results.get('quotes_deleted', 0)
            results['errors'].extend(file_results['errors']) 


 