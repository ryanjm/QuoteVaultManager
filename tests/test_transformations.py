import pytest
from quote_vault_manager.transformations import v0_1_add_version

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