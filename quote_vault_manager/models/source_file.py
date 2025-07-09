from .quote import Quote
from typing import List

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