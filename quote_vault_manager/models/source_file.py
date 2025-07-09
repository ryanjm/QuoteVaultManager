from .quote import Quote
from typing import List, Optional

class SourceFile:
    """Represents a source file containing multiple quotes."""
    def __init__(self, path: str, quotes: List[Quote]):
        self.path = path
        self.quotes = quotes

    def __repr__(self):
        return f"SourceFile(path={self.path!r}, quotes={self.quotes!r})"

    @classmethod
    def from_file(cls, path: str) -> 'SourceFile':
        """Parses the file at path and returns a SourceFile with all quotes."""
        from quote_vault_manager.quote_parser import extract_blockquotes_with_ids
        quotes = []
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for quote_text, block_id in extract_blockquotes_with_ids(content):
            quotes.append(Quote(quote_text, block_id))
        return cls(path, quotes)

    def validate_block_ids(self) -> List[str]:
        """Validates block IDs in the source file and returns a list of errors."""
        from quote_vault_manager.quote_parser import validate_block_ids
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
        return validate_block_ids(content)

    def assign_missing_block_ids(self) -> int:
        """Assigns missing block IDs to quotes and updates the file. Returns the number of block IDs added."""
        from quote_vault_manager.quote_parser import get_next_block_id
        from quote_vault_manager.quote_writer import ensure_block_id_in_source
        block_ids_added = 0
        # Find the next available block ID
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
        next_block_id = get_next_block_id(content)
        used_ids = set(q.block_id for q in self.quotes if q.block_id)
        for quote in self.quotes:
            if not quote.block_id and quote.text:
                # Assign a new block ID
                while next_block_id in used_ids:
                    num = int(next_block_id.replace('^Quote', '')) + 1
                    next_block_id = f'^Quote{num:03d}'
                ensure_block_id_in_source(self.path, quote.text, next_block_id, dry_run=False)
                quote.block_id = next_block_id
                used_ids.add(next_block_id)
                block_ids_added += 1
                # Update next_block_id for the next missing one
                num = int(next_block_id.replace('^Quote', '')) + 1
                next_block_id = f'^Quote{num:03d}'
        return block_ids_added

    def add_quote(self, text: Optional[str], block_id: Optional[str] = None):
        """Adds a new quote to the source file object."""
        self.quotes.append(Quote(text, block_id))

    def remove_quote(self, block_id: str) -> bool:
        """Removes a quote by block ID. Returns True if removed, False if not found."""
        for i, quote in enumerate(self.quotes):
            if quote.block_id == block_id:
                del self.quotes[i]
                return True
        return False

    def update_quote(self, block_id: str, new_text: Optional[str]) -> bool:
        """Updates the text of a quote by block ID. Returns True if updated, False if not found."""
        for quote in self.quotes:
            if quote.block_id == block_id:
                quote.text = new_text
                return True
        return False

    def save(self):
        """Saves the current quotes (with block IDs) back to the source file."""
        lines = []
        for quote in self.quotes:
            if quote.text:
                for line in quote.text.split('\n'):
                    lines.append(f'> {line}')
                if quote.block_id:
                    lines.append(quote.block_id)
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n') 