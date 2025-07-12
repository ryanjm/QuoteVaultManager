from abc import ABC, abstractmethod
from typing import List, Optional

class BaseVault(ABC):
    def __init__(self, directory: str, vault_name: str = ""):
        self.directory = directory
        self.vault_name = vault_name
        self.files: List = self._load_files()

    @abstractmethod
    def _load_files(self) -> List:
        pass

    def save_all(self):
        for file in self.files:
            if hasattr(file, 'save') and file.path:
                file.save(file.path) 