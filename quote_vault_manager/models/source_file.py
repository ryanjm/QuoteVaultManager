from .quote import Quote
from typing import List, Optional, Tuple, Set
import re

class SourceFile:
    """Represents a source file containing multiple quotes."""
    
    # Block ID pattern for source files
    BLOCK_ID_PATTERN = re.compile(r'^\^Quote(\d{3})$', re.MULTILINE)
    
    def __init__(self, path: str, quotes: List[Quote]):
        self.path = path
        self.quotes = quotes

    def __repr__(self):
        return f"SourceFile(path={self.path!r}, quotes={self.quotes!r})"

    @classmethod
    def from_file(cls, path: str) -> 'SourceFile':
        """Parses the file at path and returns a SourceFile with all quotes."""
        quotes = []
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for quote_text, block_id in cls.extract_blockquotes_with_ids(content):
            quotes.append(Quote(quote_text, block_id))
        return cls(path, quotes)

    def validate_block_ids(self) -> List[str]:
        """Validates block IDs in the source file and returns a list of errors."""
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.validate_block_ids_from_content(content)

    def assign_missing_block_ids(self, dry_run: bool = False) -> int:
        """Assigns missing block IDs to quotes. Returns the number of block IDs added. Only sets flags; file update is deferred to save()."""
        block_ids_added = 0
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
        next_block_id = self.get_next_block_id(content)
        used_ids = set(q.block_id for q in self.quotes if q.block_id)
        for quote in self.quotes:
            if not quote.block_id and quote.text:
                # Assign a new block ID
                while next_block_id in used_ids:
                    num = int(next_block_id.replace('^Quote', '')) + 1
                    next_block_id = f'^Quote{num:03d}'
                quote.block_id = next_block_id
                quote.needs_block_id_assignment = True
                used_ids.add(next_block_id)
                block_ids_added += 1
                num = int(next_block_id.replace('^Quote', '')) + 1
                next_block_id = f'^Quote{num:03d}'
        return block_ids_added



    @staticmethod
    def extract_blockquotes_with_ids(markdown: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extracts blockquotes and their associated block IDs (^QuoteNNN) from markdown text.
        Returns a list of (quote_text, block_id or None) tuples.
        """
        blockquotes = []
        lines = markdown.splitlines()
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('>'):
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith('>'):
                    quote_lines.append(lines[i].lstrip('> ').rstrip())
                    i += 1
                # Look ahead for block ID
                block_id = None
                if i < len(lines) and SourceFile.BLOCK_ID_PATTERN.match(lines[i].strip()):
                    block_id = lines[i].strip()
                    i += 1
                blockquotes.append(('\n'.join(quote_lines).strip(), block_id))
            else:
                i += 1
        return blockquotes

    @staticmethod
    def validate_block_ids_from_content(markdown: str) -> List[str]:
        """
        Validates block IDs in markdown text and returns a list of errors.
        Checks for duplicate block IDs and invalid formats.
        """
        errors = []
        seen_ids: Set[str] = set()
        line_number = 0
        
        for line in markdown.splitlines():
            line_number += 1
            stripped_line = line.strip()
            
            if SourceFile.BLOCK_ID_PATTERN.match(stripped_line):
                block_id = stripped_line
                if block_id in seen_ids:
                    errors.append(f"Duplicate block ID '{block_id}' found at line {line_number}")
                else:
                    seen_ids.add(block_id)
            elif stripped_line.startswith('^Quote') and not SourceFile.BLOCK_ID_PATTERN.match(stripped_line):
                errors.append(f"Invalid block ID format '{stripped_line}' at line {line_number}. Expected format: ^QuoteNNN (where NNN is 3 digits)")
        
        return errors

    @staticmethod
    def get_next_block_id(markdown: str) -> str:
        """
        Finds the highest existing block ID in the markdown and returns the next sequential ID.
        If no block IDs exist, returns '^Quote001'.
        """
        existing_ids = []
        for line in markdown.splitlines():
            match = SourceFile.BLOCK_ID_PATTERN.match(line.strip())
            if match:
                existing_ids.append(int(match.group(1)))
        
        if not existing_ids:
            return '^Quote001'
        
        next_num = max(existing_ids) + 1
        return f'^Quote{next_num:03d}'

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

    def unwrap_quote(self, quote: Quote) -> bool:
        """Unwraps a quote and marks it for unwrapping."""
        if quote:
            quote.text = f'"{quote.text}"'
            quote.needs_unwrap = True
            return True
        return False

    def save(self, dry_run: bool = False):
        """Propagates edits, unwrapping, and block ID assignments for quotes with flags set, using in-place file updates only."""
        for quote in self.quotes:
            if getattr(quote, "needs_edit", False):
                if quote.block_id is not None and quote.text is not None:
                    self.overwrite_quote_in_source(self.path, quote.block_id, quote.text, dry_run)
                quote.needs_edit = False
            if getattr(quote, "needs_unwrap", False):
                if quote.block_id is not None:
                    self.unwrap_quote_in_source(self.path, quote.block_id, dry_run)
                quote.needs_unwrap = False
            if getattr(quote, "needs_block_id_assignment", False):
                # Write the block ID to the file (unless dry_run)
                self._write_block_id_to_file(quote, dry_run)
                quote.needs_block_id_assignment = False

    @staticmethod
    def build_source_file_path(source_path: str, source_vault_path: str) -> Optional[str]:
        """Build full path to source file, ensuring .md extension."""
        import os
        if not isinstance(source_path, str) or not source_path:
            return None
        # Ensure .md extension
        if not source_path.endswith('.md'):
            source_path = source_path + '.md'
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
            quote_text = '\n'.join(quote_lines)
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
    def _format_quote_text(quote_text: str) -> str:
        """Format quote text with proper blockquote formatting."""
        quote_lines = quote_text.split('\n')
        return '\n'.join(f'> {line}' for line in quote_lines)

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

    def _write_block_id_to_file(self, quote: Quote, dry_run: bool = False):
        """Helper to write the assigned block ID to the correct place in the file."""
        if not quote.block_id:
            return
        import os
        if not os.path.exists(self.path):
            return
        with open(self.path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        # Find the blockquote matching the quote text, and insert the block ID after it if not present
        i = 0
        while i < len(lines):
            if self._is_blockquote_line(lines[i]):
                quote_lines, next_i = self._collect_blockquote_lines(lines, i)
                current_quote_text = '\n'.join(quote_lines).strip()
                if current_quote_text == (quote.text or '').strip():
                    # Check if next line is a block ID
                    if next_i < len(lines) and self.BLOCK_ID_PATTERN.match(lines[next_i].strip()):
                        # Already has a block ID, skip
                        return
                    # Insert block ID after quote
                    new_lines = lines[:next_i] + [quote.block_id] + lines[next_i:]
                    if not dry_run:
                        with open(self.path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(new_lines))
                    return
                i = next_i
            else:
                i += 1 