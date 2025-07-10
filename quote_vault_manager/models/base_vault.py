from abc import ABC, abstractmethod

class BaseVault(ABC):
    def __init__(self, directory: str):
        self.directory = directory
        self.files = self._load_files()

    @abstractmethod
    def _load_files(self):
        pass

    def save_all(self):
        for file in self.files:
            if hasattr(file, 'save') and file.path:
                file.save(file.path) 