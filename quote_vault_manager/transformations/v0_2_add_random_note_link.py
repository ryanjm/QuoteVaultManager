"""
Transformation for V0.2: Add a blank line and a Random Note link at the bottom of the quote file content, if not already present.
"""

VERSION_INTRODUCED = "V0.2"
RANDOM_NOTE_LINK = "[Random Note](obsidian://adv-uri?vault=ReferenceQuotes&commandid=random-note)"

def transform(note: dict) -> dict:
    """Adds a blank line and a Random Note link at the bottom of the note content if not already present, then updates to current version."""
    content = note.get('content', '')
    if RANDOM_NOTE_LINK not in content:
        # Ensure there is a blank line before the link
        if not content.endswith('\n\n'):
            if not content.endswith('\n'):
                content += '\n'
            content += '\n'
        content += f"{RANDOM_NOTE_LINK}\n"
        note['content'] = content
    # Always update to latest version at the end
    from .v0_x_update_version import transform as update_version
    note = update_version(note)
    return note 