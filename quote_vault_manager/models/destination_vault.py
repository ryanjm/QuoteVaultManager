from .destination_file import DestinationFile
from typing import List, Optional
import os
from .base_vault import BaseVault

class DestinationVault(BaseVault):
    """Represents a collection of destination (quote) files in a vault."""
    def __init__(self, directory: str):
        super().__init__(directory)

    def _load_files(self) -> List[DestinationFile]:
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
        for dest in self.files:
            transform_fn(dest)

    def save_all(self):
        """Saves all destination files."""
        for dest in self.files:
            if dest.path:
                dest.save(dest.path)

    def delete_flagged(self, source_vault_path: str, dry_run: bool = False) -> dict:
        """Deletes all quote files with a delete flag. Returns a results dict."""
        from .source_file import SourceFile
        results = {
            'quotes_unwrapped': 0,
            'errors': []
        }
        for dest in self.files:
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
            # Find the Quote object by block_id
            quote_obj = None
            for q in source.quotes:
                if q.block_id == block_id:
                    quote_obj = q
                    break
            if quote_obj is None:
                continue
            unwrapped = source.unwrap_quote(quote_obj)
            if unwrapped:
                if not dry_run:
                    source.save()
                results['quotes_unwrapped'] += 1
            if not dry_run and dest.path:
                DestinationFile.delete(dest.path)
        return results

    def sync_edited_back(self, source_vault_path: str, dry_run: bool = False) -> int:
        """Syncs all edited quotes back to their source files. Returns the count synced."""
        return self._sync_edited_quotes(dry_run, source_vault_path)

    def _sync_edited_quotes(self, dry_run: bool = False, source_vault_path: Optional[str] = None) -> int:
        """Sync edited quotes back to source files."""
        from .source_file import SourceFile
        if not isinstance(self.directory, str) or not self.directory:
            return 0
        updated_count = 0
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                if not DestinationFile.is_edited_quote_file(file_path):
                    continue
                source_path, block_id, new_quote_text, fm = DestinationFile.get_edited_quote_info(file_path, file)
                if source_path is None or block_id is None or new_quote_text is None:
                    continue
                if SourceFile.process_edited_quote(file_path, source_path, block_id, new_quote_text, fm, dry_run, source_vault_path or ""):
                    updated_count += 1
        return updated_count

    def find_quote_files_for_source(self, source_file: str) -> list:
        import os
        quote_files = []
        source_filename = os.path.basename(source_file)
        source_name = source_filename.replace('.md', '')
        
        # Look for quote files in the subdirectory named after the source file
        source_dir = os.path.join(self.directory, source_name)
        if os.path.exists(source_dir):
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.endswith('.md'):
                        quote_files.append(os.path.join(root, file))
        
        return quote_files 