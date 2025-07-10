from .destination_file import DestinationFile
from typing import List
import os

class DestinationVault:
    """Represents a collection of destination (quote) files in a vault."""
    def __init__(self, directory: str):
        self.directory = directory
        self.destination_files: List[DestinationFile] = self._load_destination_files()

    def _load_destination_files(self) -> List[DestinationFile]:
        """Loads all markdown destination files from the directory."""
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.md'):
                    path = os.path.join(root, filename)
                    files.append(DestinationFile.from_file(path))
        return files

    def transform_all(self, transform_fn):
        """Applies a transformation function to all destination files."""
        for dest in self.destination_files:
            transform_fn(dest)

    def save_all(self):
        """Saves all destination files."""
        for dest in self.destination_files:
            if dest.path:
                dest.save(dest.path)

    def delete_flagged(self, source_vault_path: str, dry_run: bool = False) -> dict:
        """Deletes all quote files with a delete flag. Returns a results dict."""
        from .source_file import SourceFile
        results = {
            'quotes_unwrapped': 0,
            'errors': []
        }
        for dest in self.destination_files:
            if not dest.is_marked_for_deletion:
                continue
            frontmatter = dest.frontmatter
            source_file = frontmatter.get('source_path')
            if not source_file:
                continue
            import os
            source_file_path = os.path.join(source_vault_path, source_file) if source_vault_path else source_file
            if not os.path.exists(source_file_path):
                error_msg = f"Could not find source file {source_file} in {source_vault_path} for quote file {dest.path}"
                results['errors'].append(error_msg)
                continue
            block_id = frontmatter.get('block_id') or dest.quote.block_id
            if not block_id:
                continue
            source = SourceFile.from_file(source_file_path)
            unwrapped = source.unwrap_quote(block_id)
            if unwrapped:
                if not dry_run:
                    source.save()
                results['quotes_unwrapped'] += 1
            if not dry_run and dest.path:
                DestinationFile.delete(dest.path)
        return results

    def sync_edited_back(self, source_vault_path: str, dry_run: bool = False) -> int:
        """Syncs all edited quotes back to their source files. Returns the count synced."""
        from quote_vault_manager.source_sync import sync_edited_quotes
        return sync_edited_quotes(self.directory, dry_run=dry_run, source_vault_path=source_vault_path) 