from .destination_file import DestinationFile
from .source_vault import SourceVault
from typing import List, Optional, Dict, Any
import os
from .base_vault import BaseVault
from ..file_utils import get_book_title_from_path

class DestinationVault(BaseVault):
    files: List[DestinationFile]  # type: ignore
    
    """Represents a collection of destination (quote) files in a vault."""
    def __init__(self, directory: str, vault_name: str = "", source_vault: Optional['SourceVault'] = None):
        super().__init__(directory, vault_name)
        self.source_vault = source_vault

    def _load_files(self) -> List[DestinationFile]:
        """Loads all markdown destination files from the directory."""
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.md'):
                    path = os.path.join(root, filename)
                    files.append(DestinationFile.from_file(path, destination_vault=self))
        return files

    def transform_all(self, transform_fn):
        """Applies a transformation function to all destination files."""
        for dest in self.files:
            transform_fn(dest)

    def commit_changes(self, dry_run: bool = False):
        """Apply all in-memory changes: save new/updated files, delete marked files. Honors dry_run."""
        for dest in self.files:
            if dest.marked_for_deletion:
                if not dry_run and dest.path:
                    DestinationFile.delete(dest.path)
                dest.marked_for_deletion = False
            elif dest.needs_update or dest.is_new:
                if not dry_run:
                    if dest.path:
                        dest.save(dest.path)
                dest.needs_update = False
                dest.is_new = False

    def save_all(self):
        """Commits all in-memory changes to disk."""
        self.commit_changes(dry_run=False)

    def sync_quotes_from_source(self, source_file: str, quotes_with_ids: list, block_id_map: dict, 
                               dry_run: bool = False, vault_name: str = "Notes", 
                               source_vault_path: Optional[str] = None) -> Dict[str, Any]:
        """Sync quotes from a source file to this destination vault in memory, marking for update or creation."""
        results = {
            'quotes_processed': 0,
            'quotes_created': 0,
            'quotes_updated': 0,
            'errors': []
        }
        book_title = get_book_title_from_path(source_file)
        # Build a lookup for existing files by (block_id)
        existing_by_block = {(dest.quote.block_id, dest.path): dest for dest in self.files}
        for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
            results['quotes_processed'] += 1
            if block_id is None:
                results['errors'].append(f"Quote at index {idx} has no block ID after assignment")
                continue
            filename = DestinationFile.create_quote_filename(book_title, block_id, quote_text)
            quote_file_path = os.path.join(self.directory, book_title, filename)
            # Try to find in-memory file
            found = None
            for dest in self.files:
                if dest.path == quote_file_path:
                    found = dest
                    break
            if found:
                updated = False
                # Don't update quote text if the file is marked as edited
                if found.quote.text != quote_text and not found.is_edited:
                    found.quote.text = quote_text
                    updated = True
                if found.quote.block_id != block_id:
                    found.quote.block_id = block_id
                    updated = True
                if updated:
                    found.needs_update = True
                    results['quotes_updated'] += 1
            else:
                from .quote import Quote
                from quote_vault_manager import VERSION
                frontmatter = {
                    'delete': False,
                    'favorite': False,
                    'edited': False,
                    'version': VERSION
                }
                new_dest = DestinationFile.new(frontmatter, Quote(quote_text, block_id), path=quote_file_path, source_path=source_file, destination_vault=self)
                self.files.append(new_dest)
                results['quotes_created'] += 1
        if not dry_run:
            self.commit_changes(dry_run=False)
        return results

    def remove_orphaned_quotes_for_source(self, source_file: str, block_id_map: dict, dry_run: bool = False) -> Dict[str, Any]:
        """Mark quote files that no longer have a corresponding blockquote in the source file for deletion."""
        results = {
            'quotes_deleted': 0,
            'errors': []
        }
        existing_block_ids = set(block_id_map.values())
        for dest in self.files:
            block_id = dest.quote.block_id
            if block_id and block_id not in existing_block_ids:
                dest.marked_for_deletion = True
                results['quotes_deleted'] += 1
        if not dry_run:
            self.commit_changes(dry_run=False)
        return results

    def delete_flagged(self, source_vault_path: str, dry_run: bool = False) -> dict:
        """Mark all quote files with a delete flag for deletion. Unwrap quotes in source if needed."""
        from .source_file import SourceFile
        results = {
            'quotes_unwrapped': 0,
            'errors': []
        }
        for dest in self.files:
            if not dest.is_marked_for_deletion:
                continue
            if not dest.source_path:
                continue
            source_path = dest.source_path
            if source_path and not source_path.endswith('.md'):
                source_path = source_path + '.md'
            source_file_path = os.path.join(source_vault_path, source_path) if source_vault_path else source_path
            if not os.path.exists(source_file_path):
                error_msg = f"Could not find source file {dest.source_path} in {source_vault_path} for quote file {dest.path}"
                results['errors'].append(error_msg)
                continue
            block_id = dest.quote.block_id
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
            dest.marked_for_deletion = True
        if not dry_run:
            self.commit_changes(dry_run=False)
        return results

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