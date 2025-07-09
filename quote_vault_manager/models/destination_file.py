from .quote import Quote
from typing import Dict, Any

class DestinationFile:
    """Represents a destination file with frontmatter and a single quote."""
    def __init__(self, frontmatter: Dict[str, Any], quote: Quote):
        self.frontmatter = frontmatter
        self.quote = quote

    def __repr__(self):
        return f"DestinationFile(frontmatter={self.frontmatter!r}, quote={self.quote!r})"

    @classmethod
    def from_file(cls, path: str) -> 'DestinationFile':
        """Parses the file at path and returns a DestinationFile with frontmatter and quote."""
        from quote_vault_manager.quote_writer import read_quote_file_content, frontmatter_str_to_dict, extract_quote_text_from_content
        frontmatter_str, content = read_quote_file_content(path)
        frontmatter = frontmatter_str_to_dict(frontmatter_str) if frontmatter_str else {}
        quote_text = extract_quote_text_from_content(content)
        block_id = frontmatter.get('block_id') if isinstance(frontmatter.get('block_id'), str) else None
        quote = Quote(quote_text, block_id)
        return cls(frontmatter, quote) 