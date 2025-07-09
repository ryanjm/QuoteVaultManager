"""
Transformation: Update the version field in the note's frontmatter to the current script version.
"""
from .. import VERSION

def transform(note: dict) -> dict:
    """Set the version in frontmatter to the current script version."""
    note.setdefault('frontmatter', {})['version'] = VERSION
    return note 