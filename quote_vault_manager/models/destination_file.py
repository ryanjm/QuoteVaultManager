from .quote import Quote
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .destination_vault import DestinationVault

class DestinationFile:
    """
    Represents a destination file with frontmatter and a single quote.

    Example Destination File Format:
    ---
    favorite: false
    delete: false
    edited: false
    version: "0.3"
    ---

    > This is a quote from the book.

    **Source:** [Book Title](obsidian://open?vault=Notes&file=Book%20Title%23%5EQuote001)

    [Random Note](obsidian://advanced-uri?vault=Notes&commandid=random-note-open)
    """
    def __init__(self, frontmatter: Dict[str, Any], quote: Quote, path: Optional[str] = None, *, marked_for_deletion: bool = False, needs_update: bool = False, is_new: bool = False, destination_vault: Optional['DestinationVault'] = None):
        """
        Initialize a DestinationFile.
        Args:
            frontmatter: Frontmatter dict.
            quote: Quote object.
            path: File path.
            marked_for_deletion: If True, file will be deleted on commit.
            needs_update: If True, file will be updated on commit.
            is_new: If True, file is new and will be created on commit.
            destination_vault: Reference to the DestinationVault this file belongs to.
        """
        self.frontmatter = frontmatter
        self.quote = quote
        self.path = path
        self.marked_for_deletion = marked_for_deletion
        self.needs_update = needs_update
        self.is_new = is_new
        self.destination_vault = destination_vault
        import os
        self.filename = os.path.basename(path) if path else None
        self.source_path = None
        if path:
            try:
                frontmatter_str, content = self.read_quote_file_content(path)
                self.source_path = self.extract_source_path_from_content(content)
            except Exception:
                self.source_path = None

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
    def from_file(cls, path: str, destination_vault: Optional['DestinationVault'] = None) -> 'DestinationFile':
        """Parses the file at path and returns a DestinationFile with frontmatter and quote."""
        import os
        frontmatter_str, content = cls.read_quote_file_content(path)
        frontmatter = cls.frontmatter_str_to_dict(frontmatter_str) if frontmatter_str else {}
        quote_text = cls.extract_quote_text_from_content(content)
        filename = os.path.basename(path)
        block_id = cls.extract_block_id_from_filename(filename)
        quote = Quote(quote_text, block_id)
        obj = cls(frontmatter, quote, path=path, marked_for_deletion=False, needs_update=False, is_new=False, destination_vault=destination_vault)
        obj.filename = filename
        obj.source_path = cls.extract_source_path_from_content(content)
        return obj

    def save(self, path: str):
        """Saves the current frontmatter and quote to the file at the given path."""
        if not path:
            raise ValueError("Path must not be None when saving a DestinationFile.")
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Use the existing template to create proper content with source links
        frontmatter_str = self.frontmatter_dict_to_str(self.frontmatter)
        quote_text = self.quote.text or ''
        block_id = self.quote.block_id or ''
        
        print(f"  DestinationFile.save: frontmatter={self.frontmatter}")
        print(f"  DestinationFile.save: frontmatter_str={frontmatter_str}")
        
        # Use source_path if available, otherwise extract from filename
        source_file = self.source_path or ''
        if not source_file and self.filename:
            # Extract book title from filename as fallback
            if ' - Quote' in self.filename:
                source_file = self.filename.split(' - Quote')[0] + '.md'
        
        # Get vault name from object hierarchy
        vault_name = "Notes"  # Default fallback
        if self.destination_vault and self.destination_vault.source_vault:
            vault_name = self.destination_vault.source_vault.vault_name
        
        # Get source vault path for proper URI generation
        vault_root = ""
        if self.destination_vault and self.destination_vault.source_vault:
            vault_root = self.destination_vault.source_vault.directory
        
        content = self._create_quote_content_template(
            quote_text, source_file, block_id, frontmatter_str, vault_name, vault_root
        )
        
        print(f"  DestinationFile.save: Writing content to {path}")
        print(f"  DestinationFile.save: Content starts with: {content[:200]}...")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.is_new = False
        self.needs_update = False

    @staticmethod
    def delete(path: str):
        """Deletes the destination file at the given path."""
        import os
        if path and os.path.exists(path):
            os.remove(path)

    @staticmethod
    def is_edited_quote_file(file_path: str) -> bool:
        """Return True if file is a markdown file with edited: true in frontmatter."""
        if not isinstance(file_path, str) or not file_path.endswith('.md'):
            return False
        frontmatter, _ = DestinationFile.read_quote_file_content(file_path)
        if not frontmatter:
            return False
        fm = DestinationFile.frontmatter_str_to_dict(frontmatter)
        return fm.get('edited') is True

    @staticmethod
    def extract_source_path_from_content(content: str) -> str:
        """Extract the source file path from the Obsidian URI in the quote file content."""
        import re
        from urllib.parse import unquote
        # Look for a line like: **Source:** [Book](obsidian://open?vault=Notes&file=...%23^QuoteNNN)
        match = re.search(r'\(obsidian://open\?vault=[^&]+&file=([^%#)]+)', content)
        if match:
            encoded_path = match.group(1)
            return unquote(encoded_path)
        return ""

    @staticmethod
    def get_edited_quote_info(file_path: str, filename: str) -> tuple:
        """Extract source_path (from URI only), block_id (from filename), new_quote_text, and frontmatter dict from file."""
        if not isinstance(file_path, str):
            return "", "", "", {}
        frontmatter, content = DestinationFile.read_quote_file_content(file_path)
        fm = DestinationFile.frontmatter_str_to_dict(frontmatter) if frontmatter else {}
        content_str = str(content or "")
        source_path = DestinationFile.extract_source_path_from_content(content_str) or ""
        block_id = DestinationFile.extract_block_id_from_filename(filename)
        new_quote_text = DestinationFile.extract_quote_text_from_content(content_str)
        return source_path, block_id, new_quote_text, fm

    def update_frontmatter(self, updates: dict):
        """Update the frontmatter in the destination file with the given updates."""
        if not self.path:
            raise ValueError("Path must not be None when updating frontmatter.")
        self.frontmatter.update(updates)
        new_frontmatter = self.frontmatter_dict_to_str(self.frontmatter)
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

    @staticmethod
    def create_obsidian_uri(source_file: str, block_id: str, source_vault: str = "Notes", vault_root: str = "") -> str:
        """Creates an Obsidian URI in the correct format."""
        from urllib.parse import quote
        import os
        if source_file.endswith('.md'):
            source_file = source_file[:-3]
        if vault_root:
            rel_path = os.path.relpath(source_file, vault_root)
        else:
            rel_path = source_file
        rel_path = rel_path.replace(os.sep, '/')
        encoded_file = quote(rel_path)
        encoded_block = quote(block_id)
        return f"obsidian://open?vault={source_vault}&file={encoded_file}%23{encoded_block}"

    @staticmethod
    def _truncate_words_to_length(text: str, max_length: int = 30) -> str:
        if len(text) <= max_length:
            return text
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space]
        return truncated

    @staticmethod
    def _clean_filename_text(text: str) -> str:
        import re
        cleaned = text.replace('\\', '-').replace('/', '-').replace(':', '-')
        cleaned = re.sub(r'-+', '-', cleaned)
        return cleaned.strip('- ')

    @staticmethod
    def create_quote_filename(book_title: str, block_id: str, quote_text: str) -> str:
        clean_block_id = block_id.lstrip('^')
        clean_quote_text = quote_text.strip()
        words = clean_quote_text.split()[:5]
        first_words = ' '.join(words)
        first_words = DestinationFile._truncate_words_to_length(first_words, 30)
        first_words = DestinationFile._clean_filename_text(first_words)
        return f"{book_title} - {clean_block_id} - {first_words}.md"

    @staticmethod
    def _format_quote_text(quote_text: str) -> str:
        quote_lines = quote_text.split('\n')
        return '\n'.join(f'> {line}' for line in quote_lines)

    @staticmethod
    def _create_quote_content_template(quote_text: str, source_file: str, block_id: str, frontmatter: str, vault_name: str, vault_root: str) -> str:
        """Create quote content with the given frontmatter and quote text."""
        from quote_vault_manager import VERSION
        from quote_vault_manager.transformations.v0_2_add_random_note_link import RANDOM_NOTE_LINK
        uri = DestinationFile.create_obsidian_uri(source_file, block_id, vault_name, vault_root)
        import os
        link_text = os.path.basename(source_file).replace('.md', '')
        formatted_quote = DestinationFile._format_quote_text(quote_text)
        return f"""---\n{frontmatter}\n---\n\n{formatted_quote}\n\n**Source:** [{link_text}]({uri})\n\n{RANDOM_NOTE_LINK}\n"""

    @staticmethod
    def create_quote_content(quote_text: str, source_file: str, block_id: str, vault_name: str = "Notes", vault_root: str = "") -> str:
        from quote_vault_manager import VERSION
        default_frontmatter = f"""delete: false\nfavorite: false\nedited: false\nversion: \"{VERSION}\"\n"""
        return DestinationFile._create_quote_content_template(quote_text, source_file, block_id, default_frontmatter, vault_name, vault_root)

    @staticmethod
    def read_quote_file_content(path: str) -> tuple:
        """Reads the file and returns (frontmatter, content) tuple."""
        from quote_vault_manager.file_utils import split_frontmatter_from_file
        return split_frontmatter_from_file(path)

    @classmethod
    def extract_quote_text_from_content(cls, content: str) -> str:
        if content is None:
            return ""
        lines = content.split('\n')
        quote_lines = []
        for line in lines:
            if line.strip().startswith('>'):
                quote_lines.append(line.lstrip('> ').rstrip())
            elif line.strip().startswith('**Source:'):
                break
        return '\n'.join(quote_lines) if quote_lines else ""

    @classmethod
    def frontmatter_str_to_dict(cls, frontmatter: str) -> dict:
        import yaml
        try:
            return yaml.safe_load(frontmatter) or {}
        except Exception:
            return {}

    @classmethod
    def frontmatter_dict_to_str(cls, frontmatter_dict: dict) -> str:
        import yaml
        if not frontmatter_dict:
            return ""
        try:
            return yaml.safe_dump(frontmatter_dict, sort_keys=False).strip()
        except Exception:
            return ""

    @classmethod
    def new(cls, frontmatter: Dict[str, Any], quote: Quote, path: Optional[str] = None, source_path: Optional[str] = None, destination_vault: Optional['DestinationVault'] = None) -> 'DestinationFile':
        """Create a new DestinationFile with is_new=True."""
        obj = cls(frontmatter, quote, path=path, marked_for_deletion=False, needs_update=False, is_new=True, destination_vault=destination_vault)
        import os
        obj.filename = os.path.basename(path) if path else None
        obj.source_path = source_path
        return obj 