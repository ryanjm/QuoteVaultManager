"""
Transformation for V0.3: Add 'edited: false' to the note's frontmatter if not present.
"""
VERSION_INTRODUCED = "V0.3"

def transform(note: dict) -> dict:
    """Adds 'edited: false' to the note's frontmatter if not present, then updates to current version."""
    if 'edited' not in note.get('frontmatter', {}):
        note.setdefault('frontmatter', {})['edited'] = False
    # Always update to latest version at the end
    from .v0_x_update_version import transform as update_version
    note = update_version(note)
    return note 