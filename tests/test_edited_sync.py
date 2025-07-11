import os
import shutil
import pytest
from quote_vault_manager.models.destination_vault import DestinationVault
from quote_vault_manager.models.destination_file import DestinationFile

def make_source_file(tmp_path, content, name="Book.md"):
    src = tmp_path / name
    src.write_text(content, encoding="utf-8")
    return str(src)

def make_quote_file(tmp_path, frontmatter, quote_text, name="Book - Quote001 - Test.md"):
    qf = tmp_path / name
    fm_str = DestinationFile.frontmatter_dict_to_str(frontmatter)
    # Prefix every line of quote_text with '>'
    quote_lines = quote_text.split('\n')
    formatted_quote = '\n'.join(f'> {line}' for line in quote_lines)
    # Always use 'Book.md' for the source file in the URI
    source_file = 'Book.md'
    source_name = source_file.replace('.md', '')
    qf.write_text(f"---\n{fm_str}\n---\n{formatted_quote}\n\n**Source:** [{source_name}](obsidian://open?vault=Notes&file={source_name}%23^Quote001)", encoding="utf-8")
    return str(qf)

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def test_edited_quote_updates_source_and_resets_flag(tmp_path):
    # Setup source file with original quote
    orig = "> Old quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    
    # Setup quote file with edited: true and new quote
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True, "source_path": os.path.basename(src_path)}
    quote_path = make_quote_file(qvault, frontmatter, "New quote")
    
    # Run sync
    vault = DestinationVault(str(qvault))
    updated = vault.sync_edited_back(str(tmp_path), dry_run=False)
    
    # Source file updated
    src_content = read_file(src_path)
    assert "> New quote" in src_content
    assert "^Quote001" in src_content
    # Quote file edited flag reset
    q_content = read_file(quote_path)
    assert "edited: false" in q_content
    assert updated == 1

def test_non_edited_quote_is_ignored(tmp_path):
    src_path = make_source_file(tmp_path, "> Old\n^Quote001")
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": False, "source_path": os.path.basename(src_path)}
    quote_path = make_quote_file(qvault, frontmatter, "New")
    vault = DestinationVault(str(qvault))
    updated = vault.sync_edited_back(str(tmp_path), dry_run=False)
    assert updated == 0
    assert "> Old" in read_file(src_path)

def test_missing_source_path_is_ignored(tmp_path):
    src_path = make_source_file(tmp_path, "> Old\n^Quote001")
    qvault = tmp_path / "vault"
    qvault.mkdir()
    # No source_path in frontmatter, but URI is present, so update should occur
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "New", name="Book - Quote001 - Test2.md")
    vault = DestinationVault(str(qvault))
    updated = vault.sync_edited_back(str(tmp_path), dry_run=False)
    assert updated == 1

def test_dry_run_does_not_modify_files(tmp_path):
    orig = "> Old\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True, "source_path": os.path.basename(src_path)}
    quote_path = make_quote_file(qvault, frontmatter, "New quote")
    vault = DestinationVault(str(qvault))
    updated = vault.sync_edited_back(str(tmp_path), dry_run=True)
    # Source file not updated
    assert read_file(src_path) == orig
    # Quote file edited flag not reset
    assert "edited: true" in read_file(quote_path)
    assert updated == 1 

def test_edit_single_line_to_multiline(tmp_path):
    # Setup source file with original single-line quote
    orig = "> Old quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    # Setup quote file with edited: true and multiline new quote
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True, "source_path": os.path.basename(src_path)}
    quote_path = make_quote_file(qvault, frontmatter, "Line one\nLine two")
    # Run sync
    vault = DestinationVault(str(qvault))
    updated = vault.sync_edited_back(str(tmp_path), dry_run=False)
    # Source file updated to multiline
    src_content = read_file(src_path)
    assert "> Line one" in src_content
    assert "> Line two" in src_content
    assert "^Quote001" in src_content
    # Quote file edited flag reset
    q_content = read_file(quote_path)
    assert "edited: false" in q_content
    assert updated == 1

def test_edit_single_line_to_single_line(tmp_path):
    # Setup source file with original single-line quote
    orig = "> Old quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    # Setup quote file with edited: true and new single-line quote
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True, "source_path": os.path.basename(src_path)}
    quote_path = make_quote_file(qvault, frontmatter, "New single line")
    # Run sync
    vault = DestinationVault(str(qvault))
    updated = vault.sync_edited_back(str(tmp_path), dry_run=False)
    # Source file updated to new single line
    src_content = read_file(src_path)
    assert "> New single line" in src_content
    assert "^Quote001" in src_content
    # Quote file edited flag reset
    q_content = read_file(quote_path)
    assert "edited: false" in q_content
    assert updated == 1 