from .source_file import SourceFile
from typing import List
import os

class SourceVault:
    """Represents a collection of source files in a vault."""
    def __init__(self, directory: str):
        self.directory = directory
        self.source_files: List[SourceFile] = self._load_source_files()

    def _load_source_files(self) -> List[SourceFile]:
        """Loads all markdown source files from the directory."""
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.md'):
                    path = os.path.join(root, filename)
                    files.append(SourceFile.from_file(path))
        return files

    def validate_all(self) -> List[str]:
        """Validates block IDs in all source files and returns a list of errors."""
        errors = []
        for source in self.source_files:
            errors.extend(source.validate_block_ids())
        return errors

    def assign_block_ids_all(self) -> int:
        """Assigns missing block IDs in all source files. Returns total block IDs added."""
        total = 0
        for source in self.source_files:
            total += source.assign_missing_block_ids()
        return total

    def save_all(self):
        """Saves all source files."""
        for source in self.source_files:
            source.save() 