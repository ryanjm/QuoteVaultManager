from .source_file import SourceFile
from typing import List
import os

class SourceVault:
    """Represents a collection of source files in a vault."""
    def __init__(self, directory: str):
        self.directory = directory
        self.source_files: List[SourceFile] = self._load_source_files()

    def _load_source_files(self) -> List[SourceFile]:
        """Loads all markdown source files from the directory."""
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.md'):
                    path = os.path.join(root, filename)
                    files.append(SourceFile.from_file(path))
        return files

    def validate_all(self) -> List[str]:
        """Validates block IDs in all source files and returns a list of errors."""
        errors = []
        for source in self.source_files:
            errors.extend(source.validate_block_ids())
        return errors

    def assign_block_ids_all(self) -> int:
        """Assigns missing block IDs in all source files. Returns total block IDs added."""
        total = 0
        for source in self.source_files:
            total += source.assign_missing_block_ids()
        return total

    def save_all(self):
        """Saves all source files."""
        for source in self.source_files:
            source.save()

    def sync_to_destination(self, destination_vault, dry_run: bool = False) -> dict:
        """Syncs all source files to the destination vault. Returns a results dict."""
        from quote_vault_manager.source_sync import sync_source_file
        results = {
            'source_files_processed': 0,
            'total_quotes_processed': 0,
            'total_quotes_created': 0,
            'total_quotes_updated': 0,
            'total_block_ids_added': 0,
            'total_quotes_deleted': 0,
            'errors': []
        }
        for source in self.source_files:
            file_results = sync_source_file(source.path, destination_vault.directory, dry_run, self.directory)
            results['source_files_processed'] += 1
            results['total_quotes_processed'] += file_results['quotes_processed']
            results['total_quotes_created'] += file_results['quotes_created']
            results['total_quotes_updated'] += file_results['quotes_updated']
            results['total_block_ids_added'] += file_results['block_ids_added']
            results['total_quotes_deleted'] += file_results.get('quotes_deleted', 0)
            results['errors'].extend(file_results['errors'])
        return results 