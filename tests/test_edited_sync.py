import os
import shutil
import pytest
from quote_vault_manager.models.destination_vault import DestinationVault
from quote_vault_manager.models.destination_file import DestinationFile
from quote_vault_manager.services.quote_sync import QuoteSyncService

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
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "New quote")
    
    # Run sync using QuoteSyncService
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=False)
    
    # Source file updated
    src_content = read_file(src_path)
    assert "> New quote" in src_content
    assert "^Quote001" in src_content
    # Find the new quote file with the updated filename
    book_dir = qvault / "Book"
    if book_dir.exists():
        new_files = list(book_dir.glob("*.md"))
        assert len(new_files) == 1, f"Expected 1 new file, found {len(new_files)}"
        new_quote_path = str(new_files[0])
        # Check that the new file has the edit flag reset
        q_content = read_file(new_quote_path)
        assert "edited: false" in q_content
        assert "New quote" in q_content
    assert results['quotes_synced_back'] == 1

def test_non_edited_quote_is_ignored(tmp_path):
    src_path = make_source_file(tmp_path, "> Old\n^Quote001")
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": False}
    quote_path = make_quote_file(qvault, frontmatter, "New")
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=False)
    assert results['quotes_synced_back'] == 0
    assert "> Old" in read_file(src_path)

def test_missing_source_path_is_ignored(tmp_path):
    src_path = make_source_file(tmp_path, "> Old\n^Quote001")
    qvault = tmp_path / "vault"
    qvault.mkdir()
    # No source_path in frontmatter, but URI is present, so update should occur
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "New", name="Book - Quote001 - Test2.md")
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=False)
    assert results['quotes_synced_back'] == 1

def test_dry_run_does_not_modify_files(tmp_path):
    orig = "> Old\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "New quote")
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=True)
    # Source file not updated
    assert read_file(src_path) == orig
    # Quote file edited flag not reset
    assert "edited: true" in read_file(quote_path)
    assert results['quotes_synced_back'] == 1

def test_edit_single_line_to_multiline(tmp_path):
    # Setup source file with original single-line quote
    orig = "> Old quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    # Setup quote file with edited: true and multiline new quote
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "Line one\nLine two")
    # Run sync using QuoteSyncService
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=False)
    # Source file updated to multiline
    src_content = read_file(src_path)
    assert "> Line one" in src_content
    assert "> Line two" in src_content
    assert "^Quote001" in src_content
    # Find the new quote file with the updated filename
    book_dir = qvault / "Book"
    if book_dir.exists():
        new_files = list(book_dir.glob("*.md"))
        assert len(new_files) == 1, f"Expected 1 new file, found {len(new_files)}"
        new_quote_path = str(new_files[0])
        # Check that the new file has the edit flag reset
        q_content = read_file(new_quote_path)
        assert "edited: false" in q_content
        assert "Line one" in q_content
        assert "Line two" in q_content
    assert results['quotes_synced_back'] == 1

def test_edit_single_line_to_single_line(tmp_path):
    # Setup source file with original single-line quote
    orig = "> Old quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    # Setup quote file with edited: true and new single-line quote
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "New single line")
    # Run sync using QuoteSyncService
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=False)
    # Source file updated to new single line
    src_content = read_file(src_path)
    assert "> New single line" in src_content
    assert "^Quote001" in src_content
    # Find the new quote file with the updated filename
    book_dir = qvault / "Book"
    if book_dir.exists():
        new_files = list(book_dir.glob("*.md"))
        assert len(new_files) == 1, f"Expected 1 new file, found {len(new_files)}"
        new_quote_path = str(new_files[0])
        # Check that the new file has the edit flag reset
        q_content = read_file(new_quote_path)
        assert "edited: false" in q_content
        assert "New single line" in q_content
    assert results['quotes_synced_back'] == 1

def test_edited_quote_not_overwritten_during_sync(tmp_path):
    """Test that edited quotes are not overwritten when syncing from source to destination."""
    # Setup source file with original quote
    orig = "> Original quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    
    # Setup quote file with edited: true and modified quote
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "Edited quote")
    
    # Create destination vault and load the edited quote
    vault = DestinationVault(str(qvault))
    
    # Verify the quote is marked as edited
    assert len(vault.files) == 1
    dest_file = vault.files[0]
    assert dest_file.is_edited
    assert dest_file.quote.text == "Edited quote"
    
    # Now sync from source to destination (this should NOT overwrite the edited quote)
    from quote_vault_manager.services.source_sync import sync_source_file
    results = sync_source_file(src_path, vault, dry_run=False)
    
    # The edited quote should still have the edited text, not the original
    assert dest_file.quote.text == "Edited quote"
    assert dest_file.is_edited
    assert "edited: true" in read_file(quote_path)
    
    # The source file should still have the original quote
    src_content = read_file(src_path)
    assert "> Original quote" in src_content
    assert "^Quote001" in src_content

def test_edit_flag_reset_with_filename_change(tmp_path):
    """Test that edit flag is properly reset and file is renamed when quote text changes and filename changes using QuoteSyncService."""
    # Setup source file with original quote
    orig = "> Original quote\n^Quote001\nOther text"
    src_path = make_source_file(tmp_path, orig)
    
    # Setup quote file with edited: true and significantly different quote text
    # This will cause the filename to change when synced
    qvault = tmp_path / "vault"
    qvault.mkdir()
    frontmatter = {"edited": True}
    quote_path = make_quote_file(qvault, frontmatter, "Completely different quote text that will change filename")
    
    # Run sync using QuoteSyncService
    service = QuoteSyncService(str(tmp_path), str(qvault))
    results = service.sync_source_file(src_path, dry_run=False)
    
    # Source file should be updated
    src_content = read_file(src_path)
    assert "> Completely different quote text that will change filename" in src_content
    assert "^Quote001" in src_content
    
    # The old quote file should no longer exist (since filename changed)
    assert not os.path.exists(quote_path)
    
    # Find the new quote file with the updated filename
    book_dir = qvault / "Book"
    if book_dir.exists():
        new_files = list(book_dir.glob("*.md"))
        assert len(new_files) == 1, f"Expected 1 new file, found {len(new_files)}"
        new_quote_path = str(new_files[0])
        
        # Check that the new file has the edit flag reset and updated content
        new_content = read_file(new_quote_path)
        assert "edited: false" in new_content
        assert "Completely different quote text that will change filename" in new_content
    
    assert results['quotes_synced_back'] == 1 