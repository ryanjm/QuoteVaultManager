"""
Quote synchronization service using improved SourceQuote and DestinationQuote classes.
"""

from typing import Dict, Any, List, Optional
import os
from ..models.source_quote import SourceQuote
from ..models.destination_quote import DestinationQuote
from ..models.source_file import SourceFile
from ..models.destination_file import DestinationFile
from ..models.destination_vault import DestinationVault
from ..file_utils import get_book_title_from_path, get_vault_name_from_path
from quote_vault_manager import VERSION


class QuoteSyncService:
    """
    Service for synchronizing quotes between source and destination vaults
    using improved SourceQuote and DestinationQuote classes.
    """
    
    def __init__(self, source_vault_path: str, destination_vault_path: str):
        self.source_vault_path = source_vault_path
        self.destination_vault_path = destination_vault_path
        self.source_vault_name = get_vault_name_from_path(source_vault_path)
        self.destination_vault_name = get_vault_name_from_path(destination_vault_path)
        
        # Load existing destination vault to get current state
        self.destination_vault = DestinationVault(destination_vault_path)
        
        # Track quote relationships
        self._source_quotes: Dict[str, SourceQuote] = {}  # block_id -> SourceQuote
        self._destination_quotes: Dict[str, DestinationQuote] = {}  # block_id -> DestinationQuote
        
        # Load existing destination quotes
        self._load_existing_destination_quotes()
    
    def _load_existing_destination_quotes(self) -> None:
        """Load existing destination quotes from the vault."""
        for dest_file in self.destination_vault.files:
            if dest_file.quote.block_id and dest_file.quote.text:
                # Convert existing Quote to DestinationQuote
                dest_quote = DestinationQuote(
                    dest_file.quote.text,
                    dest_file.quote.block_id,
                    frontmatter=dest_file.frontmatter.copy()
                )
                self._destination_quotes[dest_file.quote.block_id] = dest_quote
                print(f"Loaded existing destination quote: {dest_quote.block_id} -> {dest_quote.text[:50]}... (edited: {dest_quote.is_edited})")
    
    def sync_source_file(self, source_file_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Sync a single source file to the destination vault.
        Returns sync results.
        """
        results = {
            'quotes_processed': 0,
            'quotes_created': 0,
            'quotes_updated': 0,
            'quotes_synced_back': 0,
            'errors': []
        }
        
        # Load source file
        source_file = SourceFile.from_file(source_file_path)
        
        # Convert existing Quote objects to SourceQuote objects
        self._convert_source_quotes(source_file)
        
        # Link destination quotes to the correct SourceQuote objects
        for block_id, dest_quote in self._destination_quotes.items():
            source_quote = self._source_quotes.get(block_id)
            if source_quote:
                dest_quote.source_quote = source_quote
        
        # First, sync any edited quotes back to source
        self._sync_edited_quotes_back(source_file, dry_run, results)
        
        # Then sync from source to destination
        self._sync_source_to_destination(source_file, source_file_path, dry_run, results)
        
        # Save changes
        if not dry_run:
            source_file.save()
            self.destination_vault.save_all()
        
        return results
    
    def _convert_source_quotes(self, source_file: SourceFile) -> None:
        """Convert Quote objects in SourceFile to SourceQuote objects."""
        for i, quote in enumerate(source_file.quotes):
            if quote.block_id and quote.text:
                # Create SourceQuote with the same data
                source_quote = SourceQuote(quote.text, quote.block_id)
                
                # Replace the Quote object with SourceQuote in the source file
                source_file.quotes[i] = source_quote
                
                # Store in our tracking dict
                self._source_quotes[quote.block_id] = source_quote
                
                print(f"Converted source quote: {quote.block_id} -> {quote.text[:50]}...")
    
    def _sync_edited_quotes_back(self, source_file: SourceFile, dry_run: bool, results: Dict[str, Any]) -> None:
        """Sync any edited destination quotes back to the source file."""
        print(f"Checking for edited quotes to sync back... (found {len(self._destination_quotes)} destination quotes)")
        
        for quote in source_file.quotes:
            if not quote or not quote.block_id:
                continue
            
            # Find corresponding destination quote
            dest_quote = self._destination_quotes.get(quote.block_id)
            if dest_quote and dest_quote.is_edited:
                print(f"Found edited destination quote for {quote.block_id}: {dest_quote.text[:50]}...")
                # Sync the edit back to source
                if dest_quote.sync_to_source(dry_run):
                    results['quotes_synced_back'] += 1
                    print(f"Synced edit back to source for {quote.block_id}")
                    # Save the destination file to persist the edit flag reset
                    if not dry_run:
                        self._save_destination_quote(dest_quote, get_book_title_from_path(source_file.path))
    
    def _sync_source_to_destination(self, source_file: SourceFile, source_file_path: str, 
                                  dry_run: bool, results: Dict[str, Any]) -> None:
        """Sync quotes from source to destination."""
        book_title = get_book_title_from_path(source_file_path)
        
        for quote in source_file.quotes:
            results['quotes_processed'] += 1
            
            if not quote.block_id:
                results['errors'].append(f"Quote has no block ID: {quote.text[:50]}...")
                continue
            
            # Use the existing SourceQuote from the source file
            if isinstance(quote, SourceQuote):
                source_quote = quote
            else:
                # Fallback: create SourceQuote if conversion didn't happen
                source_quote = self._get_or_create_source_quote(quote)
            
            # Find or create destination quote
            dest_quote = self._get_or_create_destination_quote(source_quote, book_title, source_file_path)
            
            # Sync from source to destination
            if dest_quote.sync_from_source(source_quote):
                results['quotes_updated'] += 1
                if not dry_run:
                    self._save_destination_quote(dest_quote, book_title)
            elif dest_quote not in self._destination_quotes.values():
                results['quotes_created'] += 1
                if not dry_run:
                    self._save_destination_quote(dest_quote, book_title)
    
    def _get_or_create_source_quote(self, quote) -> SourceQuote:
        """Get or create a SourceQuote for the given quote."""
        if not quote.block_id:
            raise ValueError("Quote must have a block_id")
        
        if quote.block_id in self._source_quotes:
            return self._source_quotes[quote.block_id]
        
        source_quote = SourceQuote(quote.text, quote.block_id)
        self._source_quotes[quote.block_id] = source_quote
        return source_quote
    
    def _get_or_create_destination_quote(self, source_quote: SourceQuote, book_title: str, 
                                       source_file_path: str) -> DestinationQuote:
        """Get or create a DestinationQuote for the given source quote."""
        block_id = source_quote.block_id
        if not block_id:
            raise ValueError("SourceQuote must have a block_id")
        
        if block_id in self._destination_quotes:
            dest_quote = self._destination_quotes[block_id]
            # Establish bidirectional relationship
            source_quote.add_destination_quote(dest_quote)
            return dest_quote
        
        # Create new destination quote
        frontmatter = {
            'delete': False,
            'favorite': False,
            'edited': False,
            'version': VERSION
        }
        
        dest_quote = DestinationQuote(
            source_quote.text, 
            block_id,
            frontmatter=frontmatter,
            source_quote=source_quote
        )
        
        # Establish bidirectional relationship
        source_quote.add_destination_quote(dest_quote)
        self._destination_quotes[block_id] = dest_quote
        
        return dest_quote
    
    def _save_destination_quote(self, dest_quote: DestinationQuote, book_title: str) -> None:
        """Save a destination quote to disk."""
        if not dest_quote.block_id:
            raise ValueError("DestinationQuote must have a block_id")
        
        filename = DestinationFile.create_quote_filename(book_title, dest_quote.block_id, dest_quote.text)
        quote_file_path = os.path.join(self.destination_vault.directory, book_title, filename)
        
        # Try to find the existing DestinationFile in the vault
        existing_files = [f for f in self.destination_vault.files if f.path == quote_file_path]
        if existing_files:
            dest_file = existing_files[0]
            dest_file.frontmatter = dest_quote.frontmatter.copy()
            dest_file.quote = dest_quote
            # Ensure frontmatter is up to date before saving
            dest_file.frontmatter = dest_quote.frontmatter.copy()
        else:
            # Check if there's an existing file with the same block_id but different path
            # This happens when quote text changes and filename changes
            old_files = [f for f in self.destination_vault.files 
                        if f.quote.block_id == dest_quote.block_id and f.path != quote_file_path]
            
            if old_files:
                # Delete the old file since filename has changed
                old_file = old_files[0]
                if old_file.path:
                    print(f"Deleting old file due to filename change: {old_file.path}")
                    DestinationFile.delete(old_file.path)
                self.destination_vault.files.remove(old_file)
            
            # Create destination file
            dest_file = DestinationFile(
                dest_quote.frontmatter,
                dest_quote,
                path=quote_file_path,
                destination_vault=self.destination_vault
            )
            self.destination_vault.files.append(dest_file)
        
        # Save to disk
        dest_file.save(quote_file_path)
    
    def sync_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Sync all source files to destination vault.
        Returns overall sync results.
        """
        results = {
            'source_files_processed': 0,
            'total_quotes_processed': 0,
            'total_quotes_created': 0,
            'total_quotes_updated': 0,
            'total_quotes_synced_back': 0,
            'errors': []
        }
        
        # Get all markdown files in source vault
        from ..file_utils import get_markdown_files, has_sync_quotes_flag
        
        markdown_files = get_markdown_files(self.source_vault_path)
        
        for file_path in markdown_files:
            if has_sync_quotes_flag(file_path):
                file_results = self.sync_source_file(file_path, dry_run)
                results['source_files_processed'] += 1
                results['total_quotes_processed'] += file_results['quotes_processed']
                results['total_quotes_created'] += file_results['quotes_created']
                results['total_quotes_updated'] += file_results['quotes_updated']
                results['total_quotes_synced_back'] += file_results['quotes_synced_back']
                results['errors'].extend(file_results['errors'])
        
        return results 