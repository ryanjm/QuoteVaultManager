"""
Main synchronization orchestrator for the quote vault manager.
"""

from typing import Dict, Any
from .config import load_config, ConfigError
from .file_utils import has_sync_quotes_flag, get_markdown_files
from .transformation_manager import apply_transformations_to_all_quotes
from .delete_processor import process_delete_flags
from .source_sync import sync_source_file
from . import VERSION


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
        'errors': []
    }
    
    source_vault_path = config['source_vault_path']
    destination_vault_path = config['destination_vault_path']
    
    # Step 0: Apply transformations to all quote files before sync
    _apply_transformations(destination_vault_path, dry_run)
    
    # Step 1: Process delete flags first
    _process_deletions(destination_vault_path, source_vault_path, dry_run, results)
    
    # Step 2: Process source files
    _process_source_files(source_vault_path, destination_vault_path, dry_run, results)
    
    return results


def _apply_transformations(destination_vault_path: str, dry_run: bool) -> None:
    """Apply transformations to all quote files and notify user of updates."""
    files_updated = apply_transformations_to_all_quotes(destination_vault_path, dry_run=dry_run)
    if files_updated:
        if dry_run:
            print(f"🔄 [DRY-RUN] {files_updated} quote files would be updated to version {VERSION}")
        else:
            print(f"🔄 {files_updated} quote files updated to version {VERSION}")


def _process_deletions(destination_vault_path: str, source_vault_path: str, dry_run: bool, results: Dict[str, Any]) -> None:
    """Process delete flags and update results."""
    delete_results = process_delete_flags(destination_vault_path, source_vault_path, dry_run)
    results['total_quotes_unwrapped'] = delete_results['quotes_unwrapped']
    results['errors'].extend(delete_results['errors'])


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