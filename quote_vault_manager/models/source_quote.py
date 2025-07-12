"""
SourceQuote represents a quote found in a source markdown file.
"""

from typing import Optional, List, TYPE_CHECKING
from .quote import Quote

if TYPE_CHECKING:
    from .destination_quote import DestinationQuote


class SourceQuote(Quote):
    """
    Represents a quote in a source file with relationships to destination quotes.
    
    A SourceQuote contains the original quote text and block ID, and can track
    whether it has been edited in the destination vault.
    """
    
    def __init__(self, text: str, block_id: Optional[str] = None, *, 
                 needs_block_id_assignment: bool = False, needs_edit: bool = False, 
                 needs_unwrap: bool = False):
        super().__init__(text, block_id)
        self.needs_block_id_assignment = needs_block_id_assignment
        self.needs_edit = needs_edit
        self.needs_unwrap = needs_unwrap
        self._destination_quotes: List['DestinationQuote'] = []
    
    @property
    def destination_quotes(self) -> List['DestinationQuote']:
        """Get all destination quotes that reference this source quote."""
        return self._destination_quotes
    
    def add_destination_quote(self, dest_quote: 'DestinationQuote') -> None:
        """Add a destination quote that references this source quote."""
        if dest_quote not in self._destination_quotes:
            self._destination_quotes.append(dest_quote)
            dest_quote.source_quote = self
    
    def remove_destination_quote(self, dest_quote: 'DestinationQuote') -> None:
        """Remove a destination quote reference."""
        if dest_quote in self._destination_quotes:
            self._destination_quotes.remove(dest_quote)
            if dest_quote.source_quote == self:
                dest_quote.source_quote = None
    
    @property
    def has_edits(self) -> bool:
        """Check if any destination quotes have been edited."""
        return any(dq.is_edited for dq in self._destination_quotes)
    
    @property
    def edited_text(self) -> Optional[str]:
        """Get the edited text from the first edited destination quote."""
        for dq in self._destination_quotes:
            if dq.is_edited:
                return dq.text
        return None
    
    def sync_edits_to_source(self, dry_run: bool = False) -> bool:
        """
        Sync any edits from destination quotes back to this source quote.
        Returns True if any changes were made.
        """
        if not self.has_edits:
            return False
        
        edited_text = self.edited_text
        if edited_text and edited_text != self.text:
            self.text = edited_text
            self.needs_edit = True
            return True
        
        return False
    
    def format_for_source(self) -> str:
        """Format this quote for display in a source file."""
        lines = self.text.split('\n')
        formatted_lines = [f'> {line}' for line in lines]
        result = '\n'.join(formatted_lines)
        if self.block_id:
            result += f'\n{self.block_id}'
        return result
    
    def __repr__(self):
        return f"SourceQuote(text={self.text!r}, block_id={self.block_id!r}, has_edits={self.has_edits})" 