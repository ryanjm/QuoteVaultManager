import tempfile
import os
from quote_vault_manager.quote_writer import (
    create_quote_filename, 
    create_quote_content, 
    write_quote_file,
    read_quote_file_content,
    extract_quote_text_from_content,
    update_quote_file_if_changed,
    delete_quote_file,
    find_quote_files_for_source,
    has_delete_flag,
    unwrap_quote_in_source
)

def test_create_quote_filename():
    # Test basic filename creation
    result = create_quote_filename("Deep Work", "^Quote001", "Focus without distraction is the key")
    expected = "Deep Work - Quote001 - Focus without distraction is.md"
    assert result == expected, f"Expected {expected}, got {result}"
    
    # Test with special characters
    result2 = create_quote_filename("Test Book", "^Quote002", "This has / and \\ characters")
    print(f"DEBUG: result2 = '{result2}'")
    expected2 = "Test Book - Quote002 - This has - and.md"
    assert result2 == expected2, f"Expected {expected2}, got {result2}"
    
    # Test with leading/trailing whitespace
    result3 = create_quote_filename("Test Book", "^Quote003", "   This has whitespace   ")
    expected3 = "Test Book - Quote003 - This has whitespace.md"
    assert result3 == expected3, f"Expected {expected3}, got {result3}"
    
    print("Quote filename tests passed.")

def test_create_quote_content():
    result = create_quote_content(
        "Focus without distraction is the key to producing great work.",
        "Deep Work.md",
        "^Quote001"
    )
    
    # Check that content contains expected elements
    assert "delete: false" in result
    assert "favorite: false" in result
    assert 'source_path: "Deep Work.md"' in result
    assert "> Focus without distraction is the key to producing great work." in result
    assert "**Source:** [Deep Work](obsidian://open?vault=Notes&file=Deep%20Work.md%23%5EQuote001)" in result
    assert "obsidian://open?vault=Notes&file=" in result
    
    print("Quote content tests passed.")

def test_read_quote_file_content():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test quote file
        file_path = os.path.join(temp_dir, "test_quote.md")
        content = """---
delete: false
favorite: true
source_path: "test.md"
---

> This is a test quote

**Source:** [test](obsidian://open?vault=Notes&file=test.md%23%5EQuote001)
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Test reading the file
        frontmatter, quote_content = read_quote_file_content(file_path)
        
        assert frontmatter is not None
        assert "delete: false" in frontmatter
        assert "favorite: true" in frontmatter
        assert quote_content is not None
        assert "> This is a test quote" in quote_content
        
        # Test reading non-existent file
        frontmatter2, quote_content2 = read_quote_file_content("nonexistent.md")
        assert frontmatter2 is None
        assert quote_content2 is None
        
        print("Quote file reading tests passed.")

def test_extract_quote_text_from_content():
    content = """---
delete: false
---

> This is the first line
> This is the second line

**Source:** [test](obsidian://open?vault=Notes&file=test.md%23%5EQuote001)
"""
    
    result = extract_quote_text_from_content(content)
    expected = "This is the first line\nThis is the second line"
    assert result == expected, f"Expected {expected}, got {result}"
    
    print("Quote text extraction tests passed.")

def test_update_quote_file_if_changed():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test_quote.md")
        
        # Create initial quote file
        initial_content = """---
delete: false
favorite: true
source_path: "test.md"
---

> Original quote text

**Source:** [test](obsidian://open?vault=Notes&file=test.md%23%5EQuote001)
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        # Test updating with same content (should not update)
        updated = update_quote_file_if_changed(file_path, "Original quote text", "test.md", "^Quote001", dry_run=False)
        assert not updated
        
        # Test updating with different content (should update)
        updated = update_quote_file_if_changed(file_path, "Updated quote text", "test.md", "^Quote001", dry_run=False)
        assert updated
        
        # Check that frontmatter was preserved
        with open(file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
            assert "delete: false" in new_content
            assert "favorite: true" in new_content
            assert "> Updated quote text" in new_content
        
        print("Quote file update tests passed.")

def test_write_quote_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test dry run (should not create actual file)
        file_path = write_quote_file(
            temp_dir, 
            "Test Book", 
            "^Quote001", 
            "Test quote content", 
            "test.md", 
            dry_run=True
        )
        
        expected_path = os.path.join(temp_dir, "Test Book", "Test Book - Quote001 - Test quote content.md")
        assert file_path == expected_path
        
        # Check that file was not actually created in dry run
        assert not os.path.exists(file_path)
        
        # Test actual file creation
        file_path = write_quote_file(
            temp_dir, 
            "Test Book", 
            "^Quote001", 
            "Test quote content", 
            "test.md", 
            dry_run=False
        )
        
        # Check that file was created
        assert os.path.exists(file_path)
        
        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test quote content" in content
            assert "delete: false" in content
        
        print("Quote file writing tests passed.")

def test_delete_quote_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        file_path = os.path.join(temp_dir, "test_quote.md")
        with open(file_path, 'w') as f:
            f.write("test content")
        
        # Test dry run deletion (should not actually delete)
        deleted = delete_quote_file(file_path, dry_run=True)
        assert deleted
        assert os.path.exists(file_path)  # File should still exist
        
        # Test actual deletion
        deleted = delete_quote_file(file_path, dry_run=False)
        assert deleted
        assert not os.path.exists(file_path)  # File should be deleted
        
        # Test deleting non-existent file
        deleted = delete_quote_file("nonexistent.md", dry_run=False)
        assert not deleted
        
        print("Quote file deletion tests passed.")

def test_find_quote_files_for_source():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test quote files
        book_dir = os.path.join(temp_dir, "Test Book")
        os.makedirs(book_dir, exist_ok=True)
        
        # Create quote file 1
        quote1_content = """---
delete: false
favorite: false
source_path: "test.md"
---

> Quote 1

**Source:** [test](obsidian://open?vault=Notes&file=test.md%23%5EQuote001)
"""
        quote1_path = os.path.join(book_dir, "Test Book - Quote001 - Quote 1.md")
        with open(quote1_path, 'w') as f:
            f.write(quote1_content)
        
        # Create quote file 2 (different source)
        quote2_content = """---
delete: false
favorite: false
source_path: "other.md"
---

> Quote 2

**Source:** [other](obsidian://open?vault=Notes&file=other.md%23%5EQuote001)
"""
        quote2_path = os.path.join(book_dir, "Test Book - Quote002 - Quote 2.md")
        with open(quote2_path, 'w') as f:
            f.write(quote2_content)
        
        # Test finding files for "test.md"
        found_files = find_quote_files_for_source(temp_dir, "test.md")
        assert len(found_files) == 1
        assert quote1_path in found_files
        
        # Test finding files for "other.md"
        found_files = find_quote_files_for_source(temp_dir, "other.md")
        assert len(found_files) == 1
        assert quote2_path in found_files
        
        # Test finding files for non-existent source
        found_files = find_quote_files_for_source(temp_dir, "nonexistent.md")
        assert len(found_files) == 0
        
        print("Quote file finding tests passed.")

def test_has_delete_flag():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create quote file with delete: true
        file_path = os.path.join(temp_dir, "test_quote.md")
        content = """---
delete: true
favorite: false
source_path: "test.md"
---

> Test quote

**Source:** [test](obsidian://open?vault=Notes&file=test.md%23%5EQuote001)
"""
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Test with delete: true
        assert has_delete_flag(file_path)
        
        # Create quote file with delete: false
        file_path2 = os.path.join(temp_dir, "test_quote2.md")
        content2 = """---
delete: false
favorite: false
source_path: "test.md"
---

> Test quote

**Source:** [test](obsidian://open?vault=Notes&file=test.md%23%5EQuote001)
"""
        with open(file_path2, 'w') as f:
            f.write(content2)
        
        # Test with delete: false
        assert not has_delete_flag(file_path2)
        
        # Test with non-existent file
        assert not has_delete_flag("nonexistent.md")
        
        print("Delete flag detection tests passed.")

def test_unwrap_quote_in_source():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test source file
        source_file = os.path.join(temp_dir, "test_source.md")
        source_content = """# Test Document

Some text before.

> This is a quote that should be unwrapped
> It has multiple lines
^Quote001

Some text after.

> This is another quote that should stay
> It also has multiple lines
^Quote002

More text.
"""
        with open(source_file, 'w') as f:
            f.write(source_content)
        
        # Test unwrapping Quote001 (dry run)
        modified = unwrap_quote_in_source(source_file, "^Quote001", dry_run=True)
        assert modified
        
        # Check that file wasn't actually modified in dry run
        with open(source_file, 'r') as f:
            content = f.read()
            assert "> This is a quote that should be unwrapped" in content
            assert "^Quote001" in content
        
        # Test actual unwrapping
        modified = unwrap_quote_in_source(source_file, "^Quote001", dry_run=False)
        assert modified
        
        # Check that the quote was unwrapped
        with open(source_file, 'r') as f:
            content = f.read()
            assert '"This is a quote that should be unwrapped It has multiple lines"' in content
            assert "^Quote001" not in content
            assert "> This is another quote that should stay" in content  # Other quote should remain
        
        # Test unwrapping non-existent block ID
        modified = unwrap_quote_in_source(source_file, "^Quote999", dry_run=False)
        assert not modified
        
        print("Quote unwrapping tests passed.")

if __name__ == "__main__":
    test_create_quote_filename()
    test_create_quote_content()
    test_read_quote_file_content()
    test_extract_quote_text_from_content()
    test_update_quote_file_if_changed()
    test_write_quote_file()
    test_delete_quote_file()
    test_find_quote_files_for_source()
    test_has_delete_flag()
    test_unwrap_quote_in_source()
    print("All quote writer tests passed!") 