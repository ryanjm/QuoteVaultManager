from .destination_file import DestinationFile
from typing import List
import os

class DestinationVault:
    """Represents a collection of destination (quote) files in a vault."""
    def __init__(self, directory: str):
        self.directory = directory
        self.destination_files: List[DestinationFile] = self._load_destination_files()

    def _load_destination_files(self) -> List[DestinationFile]:
        """Loads all markdown destination files from the directory."""
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.md'):
                    path = os.path.join(root, filename)
                    files.append(DestinationFile.from_file(path))
        return files

    def transform_all(self, transform_fn):
        """Applies a transformation function to all destination files."""
        for dest in self.destination_files:
            transform_fn(dest)

    def save_all(self):
        """Saves all destination files."""
        for dest in self.destination_files:
            if dest.path:
                dest.save(dest.path) 