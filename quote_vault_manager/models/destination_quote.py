"""
DestinationQuote represents a quote in a destination file with frontmatter.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from .quote import Quote

if TYPE_CHECKING:
    from .source_quote import SourceQuote


class DestinationQuote(Quote):
    """
    Represents a quote in a destination file with frontmatter and source relationships.
    
    A DestinationQuote contains the quote text, block ID, and frontmatter metadata,
    and maintains a reference to its source quote.
    """
    
    def __init__(self, text: str, block_id: Optional[str] = None, *, 
                 frontmatter: Optional[Dict[str, Any]] = None, 
                 source_quote: Optional['SourceQuote'] = None):
        super().__init__(text, block_id)
        self.frontmatter = frontmatter or {}
        self.source_quote = source_quote
        self._destination_file = None
    
    @property
    def is_edited(self) -> bool:
        """Return True if this quote is marked as edited."""
        return self.frontmatter.get('edited') is True
    
    @property
    def is_marked_for_deletion(self) -> bool:
        """Return True if this quote is marked for deletion."""
        return self.frontmatter.get('delete') is True
    
    @property
    def is_favorite(self) -> bool:
        """Return True if this quote is marked as favorite."""
        return self.frontmatter.get('favorite') is True
    
    @property
    def version(self) -> str:
        """Get the version of this quote."""
        return self.frontmatter.get('version', '0.1')
    
    def mark_edited(self, edited: bool = True) -> None:
        """Mark this quote as edited or not edited."""
        self.frontmatter['edited'] = edited
    
    def mark_for_deletion(self, delete: bool = True) -> None:
        """Mark this quote for deletion."""
        self.frontmatter['delete'] = delete
    
    def mark_favorite(self, favorite: bool = True) -> None:
        """Mark this quote as favorite."""
        self.frontmatter['favorite'] = favorite
    
    def set_version(self, version: str) -> None:
        """Set the version of this quote."""
        self.frontmatter['version'] = version
    
    def sync_from_source(self, source_quote: 'SourceQuote', force: bool = False) -> bool:
        """
        Sync this destination quote from a source quote.
        Returns True if changes were made.
        
        Args:
            source_quote: The source quote to sync from
            force: If True, overwrite even if this quote is edited
        """
        if not force and self.is_edited:
            return False
        
        changed = False
        if self.text != source_quote.text:
            self.text = source_quote.text
            changed = True
        
        if self.block_id != source_quote.block_id:
            self.block_id = source_quote.block_id
            changed = True
        
        if changed:
            # Reset edit flag when syncing from source
            self.mark_edited(False)
        
        return changed
    
    def sync_to_source(self, dry_run: bool = False) -> bool:
        """
        Sync this destination quote back to its source quote.
        Returns True if changes were made.
        """
        print(f"  sync_to_source called: is_edited={self.is_edited}, source_quote={self.source_quote is not None}")
        if not self.is_edited or not self.source_quote:
            print(f"  sync_to_source returning False: is_edited={self.is_edited}, has_source_quote={self.source_quote is not None}")
            return False
        
        print(f"  Comparing texts: dest='{self.text}' vs source='{self.source_quote.text}'")
        if self.text != self.source_quote.text:
            print(f"  Updating source quote text from '{self.source_quote.text}' to '{self.text}'")
            self.source_quote.text = self.text
            self.source_quote.needs_edit = True
            if not dry_run:
                self.mark_edited(False)
            print(f"  sync_to_source returning True")
            return True
        
        print(f"  sync_to_source returning False: texts are the same")
        return False
    
    def format_for_destination(self, source_file: str, vault_name: str = "Notes", 
                             vault_root: str = "") -> str:
        """Format this quote for display in a destination file."""
        from .destination_file import DestinationFile
        
        # Create the Obsidian URI
        uri = DestinationFile.create_obsidian_uri(source_file, self.block_id or '', vault_name, vault_root)
        
        # Format the quote text with blockquotes
        lines = self.text.split('\n')
        formatted_lines = [f'> {line}' for line in lines]
        quote_text = '\n'.join(formatted_lines)
        
        # Create the source link
        import os
        link_text = os.path.basename(source_file).replace('.md', '')
        source_link = f"**Source:** [{link_text}]({uri})"
        
        # Add random note link
        from quote_vault_manager.transformations.v0_2_add_random_note_link import RANDOM_NOTE_LINK
        
        return f"{quote_text}\n\n{source_link}\n\n{RANDOM_NOTE_LINK}\n"
    
    def __repr__(self):
        return f"DestinationQuote(text={self.text!r}, block_id={self.block_id!r}, edited={self.is_edited})" 