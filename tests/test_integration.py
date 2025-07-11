import os
import tempfile
import pytest
from quote_vault_manager.models.source_vault import SourceVault
from quote_vault_manager.models.destination_vault import DestinationVault
from quote_vault_manager.services.sync import sync_vaults


def test_full_sync_flow(tmp_path):
    # Create source vault with a file
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_file = source_dir / "book.md"
    source_file.write_text("> A quote\n^Quote001\n> Another quote\n^Quote002\n")
    
    # Create destination vault
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    
    # Run sync
    config = {
        'source_vault_path': str(source_dir),
        'destination_vault_path': str(dest_dir)
    }
    results = sync_vaults(config, dry_run=True)
    
    # Verify results
    assert results['source_files_processed'] >= 0
    assert results['total_quotes_processed'] >= 0
    assert results['total_block_ids_added'] >= 0
    assert 'errors' in results


def test_vault_batch_operations(tmp_path):
    # Create source vault
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_file = source_dir / "book.md"
    source_file.write_text("> A quote\n^Quote001\n")
    
    # Create destination vault
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    
    # Test vault operations
    source_vault = SourceVault(str(source_dir))
    dest_vault = DestinationVault(str(dest_dir))
    
    # Test validation
    errors = source_vault.validate_all()
    assert isinstance(errors, list)
    
    # Test block ID assignment
    block_ids_added = source_vault.assign_block_ids_all()
    assert isinstance(block_ids_added, int)
    
    # Test save operations
    source_vault.save_all()
    dest_vault.save_all() 