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

    def assign_missing_block_ids(self, dry_run: bool = False) -> int:
        """Assigns missing block IDs to quotes and updates the file. Returns the number of block IDs added."""
        from quote_vault_manager.quote_parser import get_next_block_id
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
                # Inline logic for ensuring block ID in source
                import os
                if not os.path.exists(self.path):
                    continue
                with open(self.path, 'r', encoding='utf-8') as f:
                    content = f.read()
                lines = content.splitlines()
                modified = False
                new_lines = []
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if SourceFile._is_blockquote_line(line):
                        processed_lines, new_i, needs_block_id = SourceFile._process_blockquote_for_id_assignment(lines, i, quote.text)
                        new_lines.extend(processed_lines)
                        i = new_i
                        if needs_block_id:
                            new_lines.append(next_block_id)
                            modified = True
                    else:
                        new_lines.append(line)
                        i += 1
                if modified and not dry_run:
                    with open(self.path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
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

    def unwrap_quote(self, block_id: str) -> bool:
        """Unwraps a quote by converting it to regular text (wrapped in quotes). Returns True if unwrapped, False if not found."""
        for quote in self.quotes:
            if quote.block_id == block_id:
                # Convert to regular text by wrapping in quotes
                quote.text = f'"{quote.text}"'
                quote.block_id = None  # Remove the block ID
                return True
        return False

    def save(self):
        """Saves the current quotes (with block IDs) back to the source file, preserving frontmatter."""
        from quote_vault_manager.quote_writer import read_quote_file_content, frontmatter_str_to_dict
        # Read existing content to preserve frontmatter
        frontmatter_str, _ = read_quote_file_content(self.path)
        frontmatter = frontmatter_str_to_dict(frontmatter_str) if frontmatter_str else {}
        
        # Build new content with preserved frontmatter
        lines = []
        if frontmatter:
            from quote_vault_manager.quote_writer import frontmatter_dict_to_str
            frontmatter_str = frontmatter_dict_to_str(frontmatter)
            lines.append('---')
            lines.append(frontmatter_str)
            lines.append('---')
            lines.append('')
        
        # Add quotes and block IDs
        for quote in self.quotes:
            if quote.text:
                for line in quote.text.split('\n'):
                    lines.append(f'> {line}')
                if quote.block_id:
                    lines.append(quote.block_id)
        
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n') 

    @staticmethod
    def build_source_file_path(source_path: str, source_vault_path: str) -> Optional[str]:
        """Build full path to source file."""
        import os
        if not isinstance(source_path, str) or not source_path:
            return None
        if source_vault_path and isinstance(source_vault_path, str):
            return os.path.join(source_vault_path, source_path)
        return source_path

    @staticmethod
    def overwrite_quote_in_source(source_file_path: str, block_id: str, new_quote_text: str, dry_run: bool = False) -> bool:
        """Overwrite a quote in the source file (by block ID) with new text, preserving blockquote formatting and block ID. Only the relevant blockquote section is updated."""
        import os
        if not os.path.exists(source_file_path):
            return False
        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.splitlines()
            def _is_blockquote_line(line):
                return line.strip().startswith('>')
            def _find_blockquote_with_id(lines, block_id):
                i = 0
                while i < len(lines):
                    if _is_blockquote_line(lines[i]):
                        start = i
                        while i < len(lines) and _is_blockquote_line(lines[i]):
                            i += 1
                        if i < len(lines) and lines[i].strip() == block_id:
                            end = i
                            return start, end
                    i += 1
                return None, None
            def _format_quote_text(quote_text):
                quote_lines = quote_text.split('\n')
                return [f'> {line}' for line in quote_lines]
            start, end = _find_blockquote_with_id(lines, block_id)
            if start is None or end is None:
                return False
            formatted_new = _format_quote_text(new_quote_text)
            old_blockquote = lines[start:end]
            new_blockquote = formatted_new
            if old_blockquote == new_blockquote:
                return False
            new_lines = lines[:start] + new_blockquote + [block_id] + lines[end+1:]
            if not dry_run:
                with open(source_file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
            return True
        except Exception:
            return False

    @classmethod
    def process_edited_quote(
        cls,
        file_path: str,
        source_path: Optional[str],
        block_id: Optional[str],
        new_quote_text: Optional[str],
        fm: dict,
        dry_run: bool,
        source_vault_path: str
    ) -> bool:
        if not (source_path and block_id and new_quote_text):
            return False
        source_file_path = cls.build_source_file_path(source_path, source_vault_path)
        if not isinstance(source_file_path, str) or not source_file_path:
            return False
        updated = cls.overwrite_quote_in_source(source_file_path, block_id, new_quote_text, dry_run)
        if updated and not dry_run:
            from quote_vault_manager.models.destination_file import DestinationFile
            dest = DestinationFile.from_file(file_path)
            dest.update_frontmatter({'edited': False})
        return updated 

    @staticmethod
    def _is_blockquote_line(line: str) -> bool:
        return line.strip().startswith('>')

    @staticmethod
    def _collect_blockquote_lines(lines: list, start_index: int) -> tuple:
        quote_lines = []
        i = start_index
        while i < len(lines) and SourceFile._is_blockquote_line(lines[i]):
            quote_lines.append(lines[i].lstrip('> ').rstrip())
            i += 1
        return quote_lines, i

    @staticmethod
    def _process_blockquote_section(lines: list, i: int, target_block_id: str) -> tuple:
        quote_lines, i = SourceFile._collect_blockquote_lines(lines, i)
        if i < len(lines) and lines[i].strip() == target_block_id:
            quote_text = ' '.join(quote_lines)
            return [f'"{quote_text}"'], i + 1, True
        else:
            original_lines = []
            for j in range(i - len(quote_lines), i):
                original_lines.append(lines[j])
            return original_lines, i, False

    @staticmethod
    def _has_block_id_at_index(lines: list, index: int) -> bool:
        return index < len(lines) and lines[index].strip().startswith('^Quote')

    @staticmethod
    def _process_blockquote_for_id_assignment(lines: list, i: int, target_quote_text: str) -> tuple:
        quote_lines, i = SourceFile._collect_blockquote_lines(lines, i)
        has_block_id = SourceFile._has_block_id_at_index(lines, i)
        current_quote_text = '\n'.join(quote_lines).strip()
        target_quote_text = target_quote_text.strip()
        if current_quote_text == target_quote_text and not has_block_id:
            original_lines = []
            for j in range(i - len(quote_lines), i):
                original_lines.append(lines[j])
            return original_lines, i, True
        else:
            original_lines = []
            for j in range(i - len(quote_lines), i):
                original_lines.append(lines[j])
            if has_block_id:
                original_lines.append(lines[i])
                i += 1
            return original_lines, i, False

    @staticmethod
    def _find_blockquote_with_id(lines: list, block_id: str):
        i = 0
        while i < len(lines):
            if SourceFile._is_blockquote_line(lines[i]):
                start = i
                while i < len(lines) and SourceFile._is_blockquote_line(lines[i]):
                    i += 1
                if i < len(lines) and lines[i].strip() == block_id:
                    end = i
                    return start, end
            i += 1
        return None, None

    @staticmethod
    def _replace_blockquote(lines: list, start: int, end: int, new_quote_text: str, block_id: str):
        formatted_new = SourceFile._format_quote_text(new_quote_text).split('\n')
        return lines[:start] + formatted_new + [block_id] + lines[end+1:]

    @staticmethod
    def unwrap_quote_in_source(source_file_path: str, block_id: str, dry_run: bool = False) -> bool:
        import os
        if not os.path.exists(source_file_path):
            return False
        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.splitlines()
            modified = False
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if SourceFile._is_blockquote_line(line):
                    processed_lines, new_i, was_unwrapped = SourceFile._process_blockquote_section(lines, i, block_id)
                    new_lines.extend(processed_lines)
                    i = new_i
                    if was_unwrapped:
                        modified = True
                else:
                    new_lines.append(line)
                    i += 1
            if modified and not dry_run:
                with open(source_file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
            return modified
        except Exception:
            return False 