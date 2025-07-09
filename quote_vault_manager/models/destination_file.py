from .quote import Quote

class DestinationFile:
    """Represents a destination file with frontmatter and a single quote."""
    def __init__(self, frontmatter: dict, quote: Quote):
        self.frontmatter = frontmatter
        self.quote = quote

    def __repr__(self):
        return f"DestinationFile(frontmatter={self.frontmatter!r}, quote={self.quote!r})" 