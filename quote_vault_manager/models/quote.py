from typing import Optional

class Quote:
    """Represents a quote with text, block_id, and change flags.
    Args:
        text: The quote text.
        block_id: The block ID.
        needs_edit: If True, quote needs to be edited in source file.
        needs_unwrap: If True, quote needs to be unwrapped in source file.
        needs_unwrap_block_id: Block ID to unwrap.
        needs_block_id_assignment: If True, block ID needs to be written to file.
    """
    def __init__(self, text: Optional[str], block_id: Optional[str], needs_edit: bool = False, needs_unwrap: bool = False, needs_unwrap_block_id: Optional[str] = None, needs_block_id_assignment: bool = False):
        self.text = text
        self.block_id = block_id
        self.needs_edit = needs_edit
        self.needs_unwrap = needs_unwrap
        self.needs_unwrap_block_id = needs_unwrap_block_id
        self.needs_block_id_assignment = needs_block_id_assignment

    def __repr__(self):
        return f"Quote(text={self.text!r}, block_id={self.block_id!r}, needs_edit={self.needs_edit!r}, needs_unwrap={self.needs_unwrap!r}, needs_unwrap_block_id={self.needs_unwrap_block_id!r}, needs_block_id_assignment={self.needs_block_id_assignment!r})"

    def __eq__(self, other):
        if not isinstance(other, Quote):
            return NotImplemented
        return self.text == other.text and self.block_id == other.block_id

    def differs_from(self, other: 'Quote') -> bool:
        """Checks if this quote differs from another quote."""
        return self.text != other.text or self.block_id != other.block_id 

    @staticmethod
    def _format_quote_text(quote_text: str) -> str:
        """Format quote text with proper blockquote formatting."""
        quote_lines = quote_text.split('\n')
        return '\n'.join(f'> {line}' for line in quote_lines) 