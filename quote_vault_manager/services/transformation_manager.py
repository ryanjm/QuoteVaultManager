"""
Transformation manager for applying versioned transformations to quote files.
"""

import os
import glob
from typing import Dict, Any
from quote_vault_manager.models.destination_file import DestinationFile
from quote_vault_manager.backup_utils import create_backup, cleanup_old_backups
from quote_vault_manager import VERSION
from quote_vault_manager.transformations import v0_1_add_version, v0_2_add_random_note_link, v0_3_add_edited_flag


class TransformationManager:
    def __init__(self, version, backup_utils, transformations):
        self.version = version
        self.backup_utils = backup_utils
        self.transformations = transformations  # List of (version, transform_fn)

    def apply_transformations_to_quote_file(self, file_path: str, dry_run: bool = False) -> bool:
        """Applies all necessary transformations to a quote file and updates it if needed."""
        dest = DestinationFile.from_file(file_path)
        frontmatter = dest.frontmatter
        content = dest.quote.text
        file_version = frontmatter.get('version', 'V0.0')
        if file_version == self.version:
            return False
        note = {'frontmatter': frontmatter, 'content': content}
        # Apply transformations in sequence
        for version, transform_fn in self.transformations:
            if file_version < version:
                note = transform_fn(note)
        changed = (note['frontmatter'] != frontmatter) or (note['content'] != content)
        if changed and not dry_run:
            dest.frontmatter = note['frontmatter']
            dest.quote.text = note['content']
            dest.save(file_path)
            return True
        return changed

    def apply_transformations_to_all_quotes(self, destination_vault_path: str, dry_run: bool = False) -> int:
        """Applies transformations to all quote files in the destination vault."""
        if not os.path.exists(destination_vault_path):
            return 0
        quote_files = glob.glob(os.path.join(destination_vault_path, '**', '*.md'), recursive=True)
        files_needing_update = 0
        for file_path in quote_files:
            dest = DestinationFile.from_file(file_path)
            file_version = dest.frontmatter.get('version', 'V0.0')
            if file_version != self.version:
                files_needing_update += 1
        # Create backup before destructive changes if any files need updating
        if files_needing_update > 0 and not dry_run:
            backup_path = self.backup_utils['create_backup'](destination_vault_path, self.version, dry_run=False)
            print(f"📦 Created backup at: {backup_path}")
            removed_backups = self.backup_utils['cleanup_old_backups'](destination_vault_path, dry_run=False)
            if removed_backups:
                print(f"🗑️  Removed {len(removed_backups)} old backup(s)")
        files_updated = 0
        for file_path in quote_files:
            if self.apply_transformations_to_quote_file(file_path, dry_run=dry_run):
                files_updated += 1
        return files_updated

# Default instantiation for current usage
default_transformations = [
    ("V0.1", v0_1_add_version.transform),
    ("V0.2", v0_2_add_random_note_link.transform),
    ("V0.3", v0_3_add_edited_flag.transform),
]
default_backup_utils = {
    'create_backup': create_backup,
    'cleanup_old_backups': cleanup_old_backups,
}

transformation_manager = TransformationManager(
    VERSION,
    default_backup_utils,
    default_transformations
) 