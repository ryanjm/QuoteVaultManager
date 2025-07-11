from .destination_file import DestinationFile
from typing import List, Optional, Dict, Any
import os
from .base_vault import BaseVault
from ..file_utils import get_book_title_from_path

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

    def sync_quotes_from_source(self, source_file: str, quotes_with_ids: list, block_id_map: dict, 
                               dry_run: bool = False, vault_name: str = "Notes", 
                               source_vault_path: Optional[str] = None) -> Dict[str, Any]:
        """Sync quotes from a source file to this destination vault."""
        results = {
            'quotes_processed': 0,
            'quotes_created': 0,
            'quotes_updated': 0,
            'errors': []
        }
        
        book_title = get_book_title_from_path(source_file)
        for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
            results['quotes_processed'] += 1
            if block_id is None:
                results['errors'].append(f"Quote at index {idx} has no block ID after assignment")
                continue
            filename = DestinationFile.create_quote_filename(book_title, block_id, quote_text)
            quote_file_path = os.path.join(self.directory, book_title, filename)
            if os.path.exists(quote_file_path):
                dest = DestinationFile.from_file(quote_file_path)
                updated = False
                if dest.quote.text != quote_text:
                    dest.quote.text = quote_text
                    updated = True
                if dest.quote.block_id != block_id:
                    dest.quote.block_id = block_id
                    updated = True
                if updated and not dry_run:
                    dest.save(quote_file_path)
                    results['quotes_updated'] += 1
            else:
                # Create new DestinationFile and save
                from .quote import Quote
                frontmatter = {
                    'block_id': block_id,
                    'vault': vault_name,
                    'delete': False,
                    'favorite': False,
                    'edited': False
                }
                dest = DestinationFile(frontmatter, Quote(quote_text, block_id))
                if not dry_run:
                    os.makedirs(os.path.dirname(quote_file_path), exist_ok=True)
                    dest.save(quote_file_path)
                results['quotes_created'] += 1
        
        return results

    def remove_orphaned_quotes_for_source(self, source_file: str, block_id_map: dict, 
                                        dry_run: bool = False) -> Dict[str, Any]:
        """Remove quote files that no longer have a corresponding blockquote in the source file."""
        results = {
            'quotes_deleted': 0,
            'errors': []
        }
        
        existing_block_ids = set(block_id_map.values())
        existing_quote_files = self.find_quote_files_for_source(source_file)
        for quote_file in existing_quote_files:
            filename = os.path.basename(quote_file)
            block_id = DestinationFile.extract_block_id_from_filename(filename)
            if block_id and block_id not in existing_block_ids:
                results['quotes_deleted'] += 1
                if not dry_run:
                    DestinationFile.delete(quote_file)
        
        return results

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