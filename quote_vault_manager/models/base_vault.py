from abc import ABC, abstractmethod
from typing import List

class BaseVault(ABC):
    def __init__(self, directory: str):
        self.directory = directory
        self.files: List = self._load_files()

    @abstractmethod
    def _load_files(self) -> List:
        pass

    def save_all(self):
        for file in self.files:
            if hasattr(file, 'save') and file.path:
                file.save(file.path) 