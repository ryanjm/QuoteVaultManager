import tempfile
import os
from quote_vault_manager.sync import (
    has_sync_quotes_flag,
    get_markdown_files,
    get_book_title_from_path,
    sync_source_file,
    process_delete_flags,
    sync_vaults
)

def test_has_sync_quotes_flag():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file with sync_quotes: true
        file1 = os.path.join(temp_dir, "test1.md")
        content1 = """---
sync_quotes: true
---

> Some quote
"""
        with open(file1, 'w') as f:
            f.write(content1)
        
        assert has_sync_quotes_flag(file1)
        
        # Create file with sync_quotes: false
        file2 = os.path.join(temp_dir, "test2.md")
        content2 = """---
sync_quotes: false
---

> Some quote
"""
        with open(file2, 'w') as f:
            f.write(content2)
        
        assert not has_sync_quotes_flag(file2)
        
        # Create file without frontmatter
        file3 = os.path.join(temp_dir, "test3.md")
        content3 = "> Some quote"
        with open(file3, 'w') as f:
            f.write(content3)
        
        assert not has_sync_quotes_flag(file3)
        
        print("Sync quotes flag detection tests passed.")

def test_get_markdown_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        os.makedirs(os.path.join(temp_dir, "subdir"), exist_ok=True)
        
        file1 = os.path.join(temp_dir, "test1.md")
        file2 = os.path.join(temp_dir, "subdir", "test2.md")
        file3 = os.path.join(temp_dir, "test3.txt")
        
        for file_path in [file1, file2, file3]:
            with open(file_path, 'w') as f:
                f.write("test content")
        
        markdown_files = get_markdown_files(temp_dir)
        
        assert len(markdown_files) == 2
        assert file1 in markdown_files
        assert file2 in markdown_files
        assert file3 not in markdown_files
        
        print("Markdown file discovery tests passed.")

def test_get_book_title_from_path():
    assert get_book_title_from_path("/path/to/Deep Work.md") == "Deep Work"
    assert get_book_title_from_path("test.md") == "test"
    assert get_book_title_from_path("/path/to/file with spaces.md") == "file with spaces"
    
    print("Book title extraction tests passed.")

def test_sync_source_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source file
        source_file = os.path.join(temp_dir, "test_source.md")
        source_content = """---
sync_quotes: true
---

> First quote
^Quote001

> Second quote without ID

> Third quote
^Quote003
"""
        with open(source_file, 'w') as f:
            f.write(source_content)
        
        # Create destination directory
        dest_dir = os.path.join(temp_dir, "quotes")
        os.makedirs(dest_dir, exist_ok=True)
        
        # Test sync (dry run)
        results = sync_source_file(source_file, dest_dir, dry_run=True)
        
        assert results['quotes_processed'] == 3
        assert results['quotes_created'] == 3  # All three quotes are new
        assert results['block_ids_added'] == 1  # Second quote needs block ID
        assert results['quotes_updated'] == 0  # No changes in dry run
        
        # In dry run, files shouldn't actually be created
        book_dir = os.path.join(dest_dir, "test_source")
        assert not os.path.exists(book_dir)
        
        # Test actual sync
        results = sync_source_file(source_file, dest_dir, dry_run=False)
        
        assert results['quotes_processed'] == 3
        assert results['quotes_created'] == 3
        assert results['block_ids_added'] == 1
        
        # Check that files were created
        quote_files = [f for f in os.listdir(dest_dir) if f.endswith('.md')]
        assert len(quote_files) == 0  # No direct files in dest_dir
        
        book_dir = os.path.join(dest_dir, "test_source")
        assert os.path.exists(book_dir)
        
        book_files = [f for f in os.listdir(book_dir) if f.endswith('.md')]
        assert len(book_files) == 3  # All three quotes should be present (second quote gets block ID assigned)
        
        print("Source file sync tests passed.")

def test_process_delete_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source file
        source_file = os.path.join(temp_dir, "test_source.md")
        source_content = """---
sync_quotes: true
---

> Quote to be deleted
^Quote001

> Another quote
^Quote002
"""
        with open(source_file, 'w') as f:
            f.write(source_content)
        
        # Create quote file with delete: true
        quote_dir = os.path.join(temp_dir, "quotes", "test_source")
        os.makedirs(quote_dir, exist_ok=True)
        
        quote_file = os.path.join(quote_dir, "test_source - Quote001 - Quote to be deleted.md")
        quote_content = """---
delete: true
favorite: false
source_path: "test_source.md"
---

> Quote to be deleted

**Source:** [test_source](obsidian://open?vault=Notes&file=test_source.md%23%5EQuote001)
"""
        with open(quote_file, 'w') as f:
            f.write(quote_content)
        
        # Test processing delete flags (dry run)
        results = process_delete_flags(os.path.join(temp_dir, "quotes"), temp_dir, dry_run=True)
        
        assert results['quotes_unwrapped'] == 1
        
        # Check that source file wasn't actually modified in dry run
        with open(source_file, 'r') as f:
            content = f.read()
            assert "^Quote001" in content
            assert "> Quote to be deleted" in content
        
        # Test actual processing
        results = process_delete_flags(os.path.join(temp_dir, "quotes"), temp_dir, dry_run=False)
        
        assert results['quotes_unwrapped'] == 1
        
        # Check that source file was modified
        with open(source_file, 'r') as f:
            content = f.read()
            assert "^Quote001" not in content
            assert '"Quote to be deleted"' in content
        
        # Check that quote file was deleted
        assert not os.path.exists(quote_file)
        
        print("Delete flag processing tests passed.")

def test_sync_vaults():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source vault structure
        source_vault = os.path.join(temp_dir, "source")
        os.makedirs(source_vault, exist_ok=True)
        
        source_file = os.path.join(source_vault, "test_book.md")
        source_content = """---
sync_quotes: true
---

> Test quote
^Quote001
"""
        with open(source_file, 'w') as f:
            f.write(source_content)
        
        # Create destination vault
        dest_vault = os.path.join(temp_dir, "dest")
        os.makedirs(dest_vault, exist_ok=True)
        
        # Test sync
        config = {
            'source_vault_path': source_vault,
            'destination_vault_path': dest_vault
        }
        
        results = sync_vaults(config, dry_run=True)
        
        assert results['source_files_processed'] == 1
        assert results['total_quotes_processed'] == 1
        assert results['total_quotes_created'] == 1  # Quote file would be created in dry run
        
        print("Full vault sync tests passed.")

def test_skip_files_without_sync_quotes_flag():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source vault with multiple files
        source_vault = os.path.join(temp_dir, "source")
        os.makedirs(source_vault, exist_ok=True)
        
        # File with sync_quotes: true
        file1 = os.path.join(source_vault, "book1.md")
        content1 = """---
sync_quotes: true
---

> Quote from book 1
^Quote001
"""
        with open(file1, 'w') as f:
            f.write(content1)
        
        # File with sync_quotes: false
        file2 = os.path.join(source_vault, "book2.md")
        content2 = """---
sync_quotes: false
---

> Quote from book 2
^Quote001
"""
        with open(file2, 'w') as f:
            f.write(content2)
        
        # File without frontmatter
        file3 = os.path.join(source_vault, "book3.md")
        content3 = "> Quote from book 3"
        with open(file3, 'w') as f:
            f.write(content3)
        
        # Create destination vault
        dest_vault = os.path.join(temp_dir, "dest")
        os.makedirs(dest_vault, exist_ok=True)
        
        # Test sync
        config = {
            'source_vault_path': source_vault,
            'destination_vault_path': dest_vault
        }
        
        results = sync_vaults(config, dry_run=True)
        
        # Should only process 1 file (the one with sync_quotes: true)
        assert results['source_files_processed'] == 1
        assert results['total_quotes_processed'] == 1
        
        print("Skip files without sync_quotes flag tests passed.")

def test_orphaned_quote_detection_and_removal():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source file
        source_file = os.path.join(temp_dir, "test_source.md")
        source_filename = "test_source.md"
        source_content = """---
sync_quotes: true
---

> First quote
^Quote001

> Second quote
^Quote002
"""
        with open(source_file, 'w') as f:
            f.write(source_content)
        
        # Create destination directory with an orphaned quote file
        dest_dir = os.path.join(temp_dir, "quotes")
        book_dir = os.path.join(dest_dir, "test_source")
        os.makedirs(book_dir, exist_ok=True)
        
        # Create an orphaned quote file with a unique block ID that doesn't exist in source
        orphaned_file = os.path.join(book_dir, "test_source - Quote999 - Orphaned quote.md")
        orphaned_content = f"""---
delete: false
favorite: false
source_path: "{source_filename}"
---

> Orphaned quote

**Source:** [test_source](obsidian://open?vault=Notes&file=test_source.md%23%5EQuote999)
"""
        with open(orphaned_file, 'w') as f:
            f.write(orphaned_content)
        
        # Test sync (dry run)
        results = sync_source_file(source_file, dest_dir, dry_run=True)
        assert results['quotes_processed'] == 2
        assert results['quotes_created'] == 2  # Two quotes from source
        assert results.get('quotes_deleted', 0) == 1  # One orphaned quote detected
        
        # In dry run, orphaned file should still exist
        assert os.path.exists(orphaned_file)
        
        # Test actual sync
        results = sync_source_file(source_file, dest_dir, dry_run=False)
        
        assert results['quotes_processed'] == 2
        assert results['quotes_created'] == 2
        assert results.get('quotes_deleted', 0) == 1
        
        # Orphaned file should be deleted
        assert not os.path.exists(orphaned_file)
        
        # Check that valid quote files still exist
        book_files = [f for f in os.listdir(book_dir) if f.endswith('.md')]
        assert len(book_files) == 2  # Only the two valid quotes should remain
        
        print("Orphaned quote detection and removal tests passed.")

if __name__ == "__main__":
    test_has_sync_quotes_flag()
    test_get_markdown_files()
    test_get_book_title_from_path()
    test_sync_source_file()
    test_process_delete_flags()
    test_sync_vaults()
    test_skip_files_without_sync_quotes_flag()
    test_orphaned_quote_detection_and_removal()
    print("All sync tests passed!") 