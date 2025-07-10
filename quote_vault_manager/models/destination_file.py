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

    @property
    def is_edited(self) -> bool:
        """Return True if this file is marked as edited."""
        return self.frontmatter.get('edited') is True

    @property
    def is_marked_for_deletion(self) -> bool:
        """Return True if this file is marked for deletion."""
        return self.frontmatter.get('delete') is True

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
            filename = os.path.basename(path)
            block_id = DestinationFile.extract_block_id_from_filename(filename)
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

    @staticmethod
    def is_edited_quote_file(file_path: str) -> bool:
        """Return True if file is a markdown file with edited: true in frontmatter."""
        if not file_path.endswith('.md'):
            return False
        from quote_vault_manager.quote_writer import read_quote_file_content, frontmatter_str_to_dict
        frontmatter, _ = read_quote_file_content(file_path)
        if not frontmatter:
            return False
        fm = frontmatter_str_to_dict(frontmatter)
        return fm.get('edited') is True

    @staticmethod
    def extract_source_path_from_content(content: str) -> str:
        """Extract the source file path from the Obsidian URI in the quote file content."""
        import re
        from urllib.parse import unquote
        # Look for a line like: **Source:** [Book](obsidian://open?vault=Notes&file=...%23^QuoteNNN)
        match = re.search(r'\(obsidian://open\?vault=[^&]+&file=([^%#)]+)', content)
        if match:
            encoded_path = match.group(2)
            return unquote(encoded_path)
        return ""

    @staticmethod
    def get_edited_quote_info(file_path: str, filename: str) -> tuple:
        """Extract source_path (from URI), block_id (from filename), new_quote_text, and frontmatter dict from file."""
        from quote_vault_manager.quote_writer import read_quote_file_content, frontmatter_str_to_dict, extract_quote_text_from_content
        frontmatter, content = read_quote_file_content(file_path)
        fm = frontmatter_str_to_dict(frontmatter) if frontmatter else {}
        content_str = str(content or "")
        source_path = DestinationFile.extract_source_path_from_content(content_str)
        block_id = DestinationFile.extract_block_id_from_filename(filename)
        new_quote_text = extract_quote_text_from_content(content_str)
        return source_path, block_id, new_quote_text, fm

    def update_frontmatter(self, updates: dict):
        """Update the frontmatter in the destination file with the given updates."""
        self.frontmatter.update(updates)
        from quote_vault_manager.quote_writer import frontmatter_dict_to_str
        new_frontmatter = frontmatter_dict_to_str(self.frontmatter)
        with open(self.path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        parts = file_content.split('---', 2)
        if len(parts) >= 3:
            new_content = f"---\n{new_frontmatter}\n---\n{parts[2]}"
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(new_content) 

    @staticmethod
    def extract_block_id_from_filename(filename: str) -> str:
        """Extract block ID from filename if possible."""
        if ' - Quote' in filename:
            parts = filename.split(' - Quote')
            if len(parts) >= 2:
                block_id_part = parts[1].split(' - ')[0]
                return f"^Quote{block_id_part}"
        return "" 