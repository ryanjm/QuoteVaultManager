from .quote import Quote
from typing import Dict, Any

class DestinationFile:
    """Represents a destination file with frontmatter and a single quote."""
    def __init__(self, frontmatter: Dict[str, Any], quote: Quote, path: str = None):
        self.frontmatter = frontmatter
        self.quote = quote
        self.path = path

    def __repr__(self):
        return f"DestinationFile(frontmatter={self.frontmatter!r}, quote={self.quote!r}, path={self.path!r})"

    @classmethod
    def from_file(cls, path: str) -> 'DestinationFile':
        """Parses the file at path and returns a DestinationFile with frontmatter and quote."""
        from quote_vault_manager.quote_writer import read_quote_file_content, frontmatter_str_to_dict, extract_quote_text_from_content
        import os
        frontmatter_str, content = read_quote_file_content(path)
        frontmatter = frontmatter_str_to_dict(frontmatter_str) if frontmatter_str else {}
        quote_text = extract_quote_text_from_content(content)
        # Try to get block_id from frontmatter first, then from filename
        block_id = frontmatter.get('block_id') if isinstance(frontmatter.get('block_id'), str) else None
        if not block_id:
            # Extract from filename
            filename = os.path.basename(path)
            if ' - Quote' in filename:
                parts = filename.split(' - Quote')
                if len(parts) >= 2:
                    block_id_part = parts[1].split(' - ')[0]
                    block_id = f"^Quote{block_id_part}"
        quote = Quote(quote_text, block_id)
        return cls(frontmatter, quote, path=path)

    def save(self, path: str):
        """Saves the current frontmatter and quote to the file at the given path."""
        from quote_vault_manager.quote_writer import frontmatter_dict_to_str
        frontmatter_str = frontmatter_dict_to_str(self.frontmatter)
        quote_text = self.quote.text or ''
        # Format quote as blockquote
        quote_lines = [f'> {line}' for line in quote_text.split('\n') if line.strip()]
        if self.quote.block_id:
            quote_lines.append(self.quote.block_id)
        content = f"---\n{frontmatter_str}\n---\n\n" + '\n'.join(quote_lines) + '\n'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def delete(path: str):
        """Deletes the destination file at the given path."""
        import os
        if os.path.exists(path):
            os.remove(path) 