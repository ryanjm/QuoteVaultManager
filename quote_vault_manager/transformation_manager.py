"""
Transformation manager for applying versioned transformations to quote files.
"""

import os
import glob
from typing import Dict, Any
from .quote_writer import (
    read_quote_file_content, frontmatter_str_to_dict, frontmatter_dict_to_str
)
from .backup_utils import create_backup, cleanup_old_backups
from . import VERSION


def apply_transformations_to_quote_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Applies all necessary transformations to a quote file and updates it if needed.
    Returns True if the file was (or would be) updated, False otherwise.
    """
    frontmatter, content = read_quote_file_content(file_path)
    if frontmatter is None:
        return False
    
    fm_dict = frontmatter_str_to_dict(frontmatter)
    file_version = fm_dict.get('version', 'V0.0')
    
    if file_version == VERSION:
        return False
    
    note = {'frontmatter': fm_dict, 'content': content}
    
    # Apply transformations in sequence
    if file_version < 'V0.1':
        from .transformations import v0_1_add_version
        note = v0_1_add_version.transform(note)
    
    if file_version < 'V0.2':
        from .transformations import v0_2_add_random_note_link
        note = v0_2_add_random_note_link.transform(note)
    
    new_frontmatter = frontmatter_dict_to_str(note['frontmatter'])
    
    if new_frontmatter != frontmatter or note['content'] != content:
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"---\n{new_frontmatter}\n---\n\n{note['content']}")
        return True
    
    return False


def apply_transformations_to_all_quotes(destination_vault_path: str, dry_run: bool = False) -> int:
    """
    Applies transformations to all quote files in the destination vault.
    Creates backup before destructive changes and cleans up old backups.
    Returns the number of files that were (or would be) updated.
    """
    if not os.path.exists(destination_vault_path):
        return 0
    
    quote_files = glob.glob(os.path.join(destination_vault_path, '**', '*.md'), recursive=True)
    
    # Check if any files need updating
    files_needing_update = 0
    for file_path in quote_files:
        frontmatter, _ = read_quote_file_content(file_path)
        if frontmatter is None:
            continue
        
        fm_dict = frontmatter_str_to_dict(frontmatter)
        file_version = fm_dict.get('version', 'V0.0')
        
        if file_version != VERSION:
            files_needing_update += 1
    
    # Create backup before destructive changes if any files need updating
    if files_needing_update > 0 and not dry_run:
        backup_path = create_backup(destination_vault_path, VERSION, dry_run=False)
        print(f"📦 Created backup at: {backup_path}")
        
        # Clean up old backups
        removed_backups = cleanup_old_backups(destination_vault_path, dry_run=False)
        if removed_backups:
            print(f"🗑️  Removed {len(removed_backups)} old backup(s)")
    
    # Apply transformations
    files_updated = 0
    for file_path in quote_files:
        if apply_transformations_to_quote_file(file_path, dry_run=dry_run):
            files_updated += 1
    
    return files_updated 