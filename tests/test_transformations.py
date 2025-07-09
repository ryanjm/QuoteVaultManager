import pytest
from quote_vault_manager.transformations import v0_1_add_version
from quote_vault_manager.transformations import v0_2_add_random_note_link
from quote_vault_manager.transformations import v0_3_add_edited_flag
from quote_vault_manager.transformation_manager import apply_transformations_to_quote_file
from quote_vault_manager import VERSION
import tempfile
import os

def test_adds_version_if_missing():
    note = {'frontmatter': {}}
    updated = v0_1_add_version.transform(note.copy())
    from quote_vault_manager import VERSION
    assert updated['frontmatter']['version'] == VERSION

def test_does_not_overwrite_existing_version():
    note = {'frontmatter': {'version': 'V0.0'}}
    updated = v0_1_add_version.transform(note.copy())
    from quote_vault_manager import VERSION
    assert updated['frontmatter']['version'] == VERSION

def test_handles_missing_frontmatter():
    note = {}
    updated = v0_1_add_version.transform(note.copy())
    from quote_vault_manager import VERSION
    assert updated['frontmatter']['version'] == VERSION

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

def test_adds_edited_flag_if_missing():
    note = {'frontmatter': {}}
    updated = v0_3_add_edited_flag.transform(note.copy())
    from quote_vault_manager import VERSION
    assert updated['frontmatter']['edited'] is False
    assert updated['frontmatter']['version'] == VERSION

def test_does_not_overwrite_existing_edited_flag():
    note = {'frontmatter': {'edited': True}}
    updated = v0_3_add_edited_flag.transform(note.copy())
    from quote_vault_manager import VERSION
    assert updated['frontmatter']['edited'] is True
    assert updated['frontmatter']['version'] == VERSION

def test_transformation_manager_updates_version_to_latest():
    """Test that transformation manager updates version to latest after applying transformations."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        # Create a quote file with V0.0 version
        f.write(f"""---
delete: false
favorite: false
source_path: "test.md"
version: "V0.0"
---

> Test quote

**Source:** [test](link)
""")
        file_path = f.name
    
    try:
        # Apply transformations
        was_updated = apply_transformations_to_quote_file(file_path, dry_run=False)
        assert was_updated == True
        
        # Read the file back and check version
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have latest version (with or without quotes)
        assert f'version: {VERSION}' in content or f'version: "{VERSION}"' in content
        # Should have random note link
        assert v0_2_add_random_note_link.RANDOM_NOTE_LINK in content
        
    finally:
        os.unlink(file_path)

def test_transformation_manager_updates_version_to_latest_dry_run():
    """Test that transformation manager would update version to latest in dry run."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        # Create a quote file with V0.0 version
        f.write(f"""---
delete: false
favorite: false
source_path: "test.md"
version: "V0.0"
---

> Test quote

**Source:** [test](link)
""")
        file_path = f.name
    
    try:
        # Apply transformations in dry run
        was_updated = apply_transformations_to_quote_file(file_path, dry_run=True)
        assert was_updated == True
        
        # Read the file back - should be unchanged in dry run
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should still have V0.0 version (no changes in dry run)
        assert 'version: V0.0' in content or 'version: "V0.0"' in content
        # Should not have random note link (no changes in dry run)
        assert v0_2_add_random_note_link.RANDOM_NOTE_LINK not in content
        
    finally:
        os.unlink(file_path)

def test_transformation_manager_skips_already_updated_files():
    """Test that transformation manager skips files that already have latest version."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        # Create a quote file with latest version
        f.write(f"""---
delete: false
favorite: false
source_path: "test.md"
version: "{VERSION}"
---

> Test quote

**Source:** [test](link)

{v0_2_add_random_note_link.RANDOM_NOTE_LINK}
""")
        file_path = f.name
    
    try:
        # Apply transformations
        was_updated = apply_transformations_to_quote_file(file_path, dry_run=False)
        assert was_updated == False
        
        # Read the file back - should be unchanged
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should still have latest version (with or without quotes)
        assert f'version: {VERSION}' in content or f'version: "{VERSION}"' in content
        
    finally:
        os.unlink(file_path) 