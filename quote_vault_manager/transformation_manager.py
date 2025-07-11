"""
Transformation manager for applying versioned transformations to quote files.
"""

import os
import glob
from typing import Dict, Any
from .models.destination_file import DestinationFile
from .backup_utils import create_backup, cleanup_old_backups
from . import VERSION


def apply_transformations_to_quote_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Applies all necessary transformations to a quote file and updates it if needed.
    Returns True if the file was (or would be) updated, False otherwise.
    """
    dest = DestinationFile.from_file(file_path)
    frontmatter = dest.frontmatter
    content = dest.quote.text
    file_version = frontmatter.get('version', 'V0.0')
    if file_version == VERSION:
        return False
    note = {'frontmatter': frontmatter, 'content': content}
    # Apply transformations in sequence
    if file_version < 'V0.1':
        from .transformations import v0_1_add_version
        note = v0_1_add_version.transform(note)
    if file_version < 'V0.2':
        from .transformations import v0_2_add_random_note_link
        note = v0_2_add_random_note_link.transform(note)
    if file_version < 'V0.3':
        from .transformations import v0_3_add_edited_flag
        note = v0_3_add_edited_flag.transform(note)
    changed = (note['frontmatter'] != frontmatter) or (note['content'] != content)
    if changed and not dry_run:
        dest.frontmatter = note['frontmatter']
        dest.quote.text = note['content']
        dest.save(file_path)
        return True
    return changed


def apply_transformations_to_all_quotes(destination_vault_path: str, dry_run: bool = False) -> int:
    """
    Applies transformations to all quote files in the destination vault.
    Creates backup before destructive changes and cleans up old backups.
    Returns the number of files that were (or would be) updated.
    """
    import glob
    import os
    from .models.destination_file import DestinationFile
    from . import VERSION
    if not os.path.exists(destination_vault_path):
        return 0
    quote_files = glob.glob(os.path.join(destination_vault_path, '**', '*.md'), recursive=True)
    # Check if any files need updating
    files_needing_update = 0
    for file_path in quote_files:
        dest = DestinationFile.from_file(file_path)
        file_version = dest.frontmatter.get('version', 'V0.0')
        if file_version != VERSION:
            files_needing_update += 1
    # Create backup before destructive changes if any files need updating
    if files_needing_update > 0 and not dry_run:
        from .backup_utils import create_backup, cleanup_old_backups
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