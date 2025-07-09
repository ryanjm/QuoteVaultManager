"""
Transformation for V0.1: Add version number to note frontmatter if missing.
"""
VERSION_INTRODUCED = "V0.1"

def transform(note: dict) -> dict:
    """Adds version number to the note's frontmatter if not present, then updates to current version."""
    if 'version' not in note.get('frontmatter', {}):
        note.setdefault('frontmatter', {})['version'] = VERSION_INTRODUCED
    # Always update to latest version at the end
    from .v0_x_update_version import transform as update_version
    note = update_version(note)
    return note 