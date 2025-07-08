"""
Transformation for V0.1: Add version number to note frontmatter if missing.
"""

VERSION_INTRODUCED = "V0.1"

def transform(note):
    """
    Adds version number to the note's frontmatter if not present.
    Expects note as a dict with a 'frontmatter' key (dict).
    Returns updated note dict.
    """
    if 'version' not in note.get('frontmatter', {}):
        note.setdefault('frontmatter', {})['version'] = VERSION_INTRODUCED
    return note 