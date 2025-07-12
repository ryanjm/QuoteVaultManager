"""
Main synchronization orchestrator for the quote vault manager.
"""

from typing import Dict, Any, Optional
from quote_vault_manager.config import load_config, ConfigError
from quote_vault_manager.file_utils import has_sync_quotes_flag, get_markdown_files, get_vault_name_from_path
from quote_vault_manager.services.transformation_manager import transformation_manager
from quote_vault_manager.services.quote_sync import QuoteSyncService
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
    source_vault_name = get_vault_name_from_path(source_vault_path)
    destination_vault_name = get_vault_name_from_path(destination_vault_path)

    # Step 0: Apply transformations to all quote files before sync
    _apply_transformations(destination_vault_path, dry_run)

    # Step 1: Validate and assign block IDs in all source files
    source_vault = SourceVault(source_vault_path, source_vault_name)
    errors = source_vault.validate_all()
    results['errors'].extend(errors)
    block_ids_added = source_vault.assign_block_ids_all()
    results['total_block_ids_added'] += block_ids_added
    source_vault.save_all()

    # Step 2: Use the new QuoteSyncService for improved sync
    quote_sync_service = QuoteSyncService(source_vault_path, destination_vault_path)
    sync_results = quote_sync_service.sync_all(dry_run)
    
    # Update results with new sync service results
    results['source_files_processed'] = sync_results['source_files_processed']
    results['total_quotes_processed'] = sync_results['total_quotes_processed']
    results['total_quotes_created'] = sync_results['total_quotes_created']
    results['total_quotes_updated'] = sync_results['total_quotes_updated']
    results['total_edited_quotes_synced'] = sync_results['total_quotes_synced_back']
    results['errors'].extend(sync_results['errors'])

    # Step 3: Handle delete flags (still using existing logic for now)
    destination_vault = DestinationVault(destination_vault_path, destination_vault_name, source_vault)
    delete_results = destination_vault.delete_flagged(source_vault_path, dry_run)
    results['total_quotes_unwrapped'] = delete_results.get('quotes_unwrapped', 0)
    results['errors'].extend(delete_results.get('errors', []))

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


def sync_source_file(source_file: str, destination_vault_path: str, dry_run: bool = False, 
                    source_vault_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Now delegates to the new QuoteSyncService.
    """
    from quote_vault_manager.services.quote_sync import QuoteSyncService
    
    quote_sync_service = QuoteSyncService(source_vault_path or "", destination_vault_path)
    return quote_sync_service.sync_source_file(source_file, dry_run)


 