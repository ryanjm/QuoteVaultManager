"""
Backup utilities for creating and managing backups before destructive changes.
"""

import os
import shutil
import glob
from datetime import datetime, timedelta
from typing import List


def create_backup_path(destination_vault_path: str, version: str) -> str:
    """Create backup directory path in format v0_2_YYYY_MM_DD/."""
    # Convert version like V0.2 to v0_2
    version_folder = version.lower().replace('.', '_')
    date_str = datetime.now().strftime("%Y_%m_%d")
    backup_dir = os.path.join(destination_vault_path, ".backup", f"{version_folder}_{date_str}")
    return backup_dir


def create_backup(destination_vault_path: str, version: str, dry_run: bool = False) -> str:
    """
    Create a backup of the destination vault before destructive changes.
    Returns the path to the backup directory.
    """
    backup_path = create_backup_path(destination_vault_path, version)
    
    if not dry_run:
        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)
        
        # Copy all markdown files to backup
        for root, dirs, files in os.walk(destination_vault_path):
            # Skip .backup directory itself
            if '.backup' in root:
                continue
                
            for file in files:
                if file.endswith('.md'):
                    # Get relative path from destination vault
                    rel_path = os.path.relpath(root, destination_vault_path)
                    backup_file_dir = os.path.join(backup_path, rel_path)
                    os.makedirs(backup_file_dir, exist_ok=True)
                    
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(backup_file_dir, file)
                    shutil.copy2(src_file, dst_file)
    
    return backup_path


def cleanup_old_backups(destination_vault_path: str, dry_run: bool = False) -> List[str]:
    """
    Remove backup directories older than a week.
    Returns list of removed backup directories.
    """
    backup_root = os.path.join(destination_vault_path, ".backup")
    if not os.path.exists(backup_root):
        return []
    
    cutoff_date = datetime.now() - timedelta(days=7)
    removed_backups = []
    
    for backup_dir in os.listdir(backup_root):
        backup_path = os.path.join(backup_root, backup_dir)
        if not os.path.isdir(backup_path):
            continue
            
        # Try to parse date from directory name (v0_2_YYYY_MM_DD format)
        try:
            date_part = backup_dir.split('_', 2)[-1]  # Get the YYYY_MM_DD part
            backup_date = datetime.strptime(date_part, "%Y_%m_%d")
            
            if backup_date < cutoff_date:
                if not dry_run:
                    shutil.rmtree(backup_path)
                removed_backups.append(backup_path)
        except (ValueError, IndexError):
            # Skip directories that don't match expected format
            continue
    
    return removed_backups


def get_backup_count(destination_vault_path: str) -> int:
    """Get the number of backup directories."""
    backup_root = os.path.join(destination_vault_path, ".backup")
    if not os.path.exists(backup_root):
        return 0
    
    count = 0
    for item in os.listdir(backup_root):
        item_path = os.path.join(backup_root, item)
        if os.path.isdir(item_path):
            count += 1
    
    return count 