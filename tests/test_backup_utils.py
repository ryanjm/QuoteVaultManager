"""
Tests for backup utilities.
"""

import pytest
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from quote_vault_manager.services.backup_service import BackupService
backup_service = BackupService.get_instance()


def test_create_backup_path():
    """Test backup path creation with version and date."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backup_path = backup_service.create_backup_path(temp_dir, "V0.2")
        
        # Should contain .backup/v0_2_YYYY_MM_DD format
        assert ".backup" in backup_path
        assert "v0_2_" in backup_path
        assert datetime.now().strftime("%Y_%m_%d") in backup_path


def test_create_backup_dry_run():
    """Test backup creation in dry run mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        test_file = os.path.join(temp_dir, "test.md")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        backup_path = backup_service.create_backup(temp_dir, "V0.2", dry_run=True)
        
        # Should return path but not create actual backup
        assert ".backup" in backup_path
        assert "v0_2_" in backup_path
        assert not os.path.exists(backup_path)


def test_create_backup_actual():
    """Test actual backup creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory structure
        test_dir = os.path.join(temp_dir, "Book1")
        os.makedirs(test_dir)
        
        test_file1 = os.path.join(test_dir, "quote1.md")
        test_file2 = os.path.join(temp_dir, "quote2.md")
        
        with open(test_file1, 'w') as f:
            f.write("Quote 1 content")
        with open(test_file2, 'w') as f:
            f.write("Quote 2 content")
        
        backup_path = backup_service.create_backup(temp_dir, "V0.2", dry_run=False)
        
        # Should create backup directory
        assert os.path.exists(backup_path)
        assert "v0_2_" in backup_path
        
        # Should copy files maintaining directory structure
        backup_file1 = os.path.join(backup_path, "Book1", "quote1.md")
        backup_file2 = os.path.join(backup_path, "quote2.md")
        
        assert os.path.exists(backup_file1)
        assert os.path.exists(backup_file2)
        
        # Should not copy .backup directory itself
        backup_backup = os.path.join(backup_path, ".backup")
        assert not os.path.exists(backup_backup)


def test_cleanup_old_backups():
    """Test cleanup of old backup directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backup_root = os.path.join(temp_dir, ".backup")
        os.makedirs(backup_root)
        
        # Create old backup (8 days ago)
        old_date = (datetime.now() - timedelta(days=8)).strftime("%Y_%m_%d")
        old_backup = os.path.join(backup_root, f"v0_1_{old_date}")
        os.makedirs(old_backup)
        
        # Create recent backup (3 days ago)
        recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y_%m_%d")
        recent_backup = os.path.join(backup_root, f"v0_2_{recent_date}")
        os.makedirs(recent_backup)
        
        # Create invalid backup name
        invalid_backup = os.path.join(backup_root, "invalid-name")
        os.makedirs(invalid_backup)
        
        # Test dry run
        removed = backup_service.cleanup_old_backups(temp_dir, dry_run=True)
        assert len(removed) == 1
        assert old_backup in removed[0]
        
        # Old backup should still exist
        assert os.path.exists(old_backup)
        assert os.path.exists(recent_backup)
        assert os.path.exists(invalid_backup)
        
        # Test actual cleanup
        removed = backup_service.cleanup_old_backups(temp_dir, dry_run=False)
        assert len(removed) == 1
        assert old_backup in removed[0]
        
        # Old backup should be removed, others should remain
        assert not os.path.exists(old_backup)
        assert os.path.exists(recent_backup)
        assert os.path.exists(invalid_backup)


def test_get_backup_count():
    """Test counting backup directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # No backups initially
        assert backup_service.get_backup_count(temp_dir) == 0
        
        # Create backup directory
        backup_root = os.path.join(temp_dir, ".backup")
        os.makedirs(backup_root)
        
        # Create some backup directories
        os.makedirs(os.path.join(backup_root, "v0_1_2024_01_01"))
        os.makedirs(os.path.join(backup_root, "v0_2_2024_01_02"))
        
        # Create a file (should not be counted)
        with open(os.path.join(backup_root, "not-a-backup.txt"), 'w') as f:
            f.write("not a backup")
        
        assert backup_service.get_backup_count(temp_dir) == 2


def test_backup_integration_with_transformations():
    """Test that backup is created before transformations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a quote file with old version
        quote_file = os.path.join(temp_dir, "test.md")
        with open(quote_file, 'w') as f:
            f.write("""---
delete: false
favorite: false
source_path: "test.md"
version: "V0.0"
---

> Test quote

**Source:** [test](link)
""")
        
        from quote_vault_manager.services.transformation_manager import TransformationManager, default_transformations
        from quote_vault_manager import VERSION
        transformation_manager = TransformationManager(VERSION, default_transformations)
        
        # Apply transformations (should create backup)
        files_updated = transformation_manager.apply_transformations_to_all_quotes(temp_dir, dry_run=False)
        
        assert files_updated == 1
        
        # Should have created backup
        backup_root = os.path.join(temp_dir, ".backup")
        assert os.path.exists(backup_root)
        assert backup_service.get_backup_count(temp_dir) == 1
        
        # Backup should contain the original file
        backup_dirs = os.listdir(backup_root)
        assert len(backup_dirs) == 1
        backup_dir = os.path.join(backup_root, backup_dirs[0])
        backup_file = os.path.join(backup_dir, "test.md")
        assert os.path.exists(backup_file)
        
        # Original file should be updated
        from quote_vault_manager import VERSION
        with open(quote_file, 'r') as f:
            content = f.read()
        assert f'version: {VERSION}' in content or f'version: "{VERSION}"' in content 