from .quote import Quote

class SourceFile:
    """Represents a source file containing multiple quotes."""
    def __init__(self, path: str, quotes: list[Quote]):
        self.path = path
        self.quotes = quotes

    def __repr__(self):
        return f"SourceFile(path={self.path!r}, quotes={self.quotes!r})" 