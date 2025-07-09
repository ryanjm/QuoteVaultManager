class Quote:
    """Represents a quote with text and block_id."""
    def __init__(self, text: str, block_id: str):
        self.text = text
        self.block_id = block_id

    def __repr__(self):
        return f"Quote(text={self.text!r}, block_id={self.block_id!r})"

    def __eq__(self, other):
        if not isinstance(other, Quote):
            return NotImplemented
        return self.text == other.text and self.block_id == other.block_id

    def differs_from(self, other: 'Quote') -> bool:
        """Checks if this quote differs from another quote."""
        return self.text != other.text or self.block_id != other.block_id 