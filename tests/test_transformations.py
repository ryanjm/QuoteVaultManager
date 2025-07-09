import pytest
from quote_vault_manager.transformations import v0_1_add_version
from quote_vault_manager.transformations import v0_2_add_random_note_link

def test_adds_version_if_missing():
    note = {'frontmatter': {}}
    updated = v0_1_add_version.transform(note.copy())
    assert updated['frontmatter']['version'] == v0_1_add_version.VERSION_INTRODUCED

def test_does_not_overwrite_existing_version():
    note = {'frontmatter': {'version': 'V0.0'}}
    updated = v0_1_add_version.transform(note.copy())
    assert updated['frontmatter']['version'] == 'V0.0'

def test_handles_missing_frontmatter():
    note = {}
    updated = v0_1_add_version.transform(note.copy())
    assert updated['frontmatter']['version'] == v0_1_add_version.VERSION_INTRODUCED 

def test_adds_random_note_link_if_missing():
    note = {'frontmatter': {}, 'content': 'Some quote content\n\n**Source:** [Book](link)'}
    updated = v0_2_add_random_note_link.transform(note.copy())
    assert v0_2_add_random_note_link.RANDOM_NOTE_LINK in updated['content']
    # Should be a blank line before the link
    assert updated['content'].splitlines()[-2] == ''

def test_does_not_duplicate_random_note_link():
    content = f"Some quote content\n\n**Source:** [Book](link)\n\n{v0_2_add_random_note_link.RANDOM_NOTE_LINK}\n"
    note = {'frontmatter': {}, 'content': content}
    updated = v0_2_add_random_note_link.transform(note.copy())
    # Should only be one instance of the link
    assert updated['content'].count(v0_2_add_random_note_link.RANDOM_NOTE_LINK) == 1 