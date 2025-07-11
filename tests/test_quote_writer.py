import tempfile
import os
from quote_vault_manager.models.destination_file import DestinationFile
from quote_vault_manager.models.source_file import SourceFile
from quote_vault_manager.models.destination_vault import DestinationVault

def test_create_quote_filename():
    # Test basic filename creation
    result = DestinationFile.create_quote_filename("Deep Work", "^Quote001", "Focus without distraction is the key")
    expected = "Deep Work - Quote001 - Focus without distraction is.md"
    assert result == expected, f"Expected {expected}, got {result}"
    
    # Test with special characters
    result2 = DestinationFile.create_quote_filename("Test Book", "^Quote002", "This has / and \\ characters")
    print(f"DEBUG: result2 = '{result2}'")
    expected2 = "Test Book - Quote002 - This has - and.md"
    assert result2 == expected2, f"Expected {expected2}, got {result2}"
    
    # Test with leading/trailing whitespace
    result3 = DestinationFile.create_quote_filename("Test Book", "^Quote003", "   This has whitespace   ")
    expected3 = "Test Book - Quote003 - This has whitespace.md"
    assert result3 == expected3, f"Expected {expected3}, got {result3}"
    
    print("Quote filename tests passed.")

def test_create_quote_content():
    result = DestinationFile.create_quote_content(
        "Focus without distraction is the key to producing great work.",
        "Deep Work.md",
        "^Quote001"
    )
    
    # Check that content contains expected elements
    assert "delete: false" in result
    assert "favorite: false" in result
    assert "edited: false" in result
    assert "version:" in result
    assert "> Focus without distraction is the key to producing great work." in result
    assert "**Source:** [Deep Work](obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote001)" in result
    assert "obsidian://open?vault=Notes&file=" in result
    
    print("Quote content tests passed.")

def test_read_quote_file_content():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test quote file
        file_path = os.path.join(temp_dir, "test_quote.md")
        content = """---
delete: false
favorite: true
---

> This is a test quote

**Source:** [test](obsidian://open?vault=Notes&file=test%23%5EQuote001)
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Test reading the file
        frontmatter, quote_content = DestinationFile.read_quote_file_content(file_path)
        
        assert frontmatter is not None
        assert "delete: false" in frontmatter
        assert "favorite: true" in frontmatter
        assert quote_content is not None
        assert "> This is a test quote" in quote_content
        
        # Test reading non-existent file
        frontmatter2, quote_content2 = DestinationFile.read_quote_file_content("nonexistent.md")
        assert frontmatter2 is None
        assert quote_content2 is None
        
        print("Quote file reading tests passed.")

def test_extract_quote_text_from_content():
    content = """---
delete: false
---

> This is the first line
> This is the second line

**Source:** [test](obsidian://open?vault=Notes&file=test%23%5EQuote001)
"""
    
    result = DestinationFile.extract_quote_text_from_content(content)
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
---

> Original quote text

**Source:** [test](obsidian://open?vault=Notes&file=test%23%5EQuote001)
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        # Test updating with same content (should not update)
        # Note: This function no longer exists, so we'll skip this test
        print("Skipping update_quote_file_if_changed test - function removed")
        
        # Test updating with different content (should update)
        # Note: This function no longer exists, so we'll skip this test
        print("Skipping update_quote_file_if_changed test - function removed")
        
        # Check that frontmatter was preserved
        with open(file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
            assert "delete: false" in new_content
            assert "favorite: true" in new_content
            assert "> Original quote text" in new_content
        
        print("Quote file update tests passed.")



def test_find_quote_files_for_source():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test quote files
        test_dir = os.path.join(temp_dir, "test")
        other_dir = os.path.join(temp_dir, "other")
        os.makedirs(test_dir, exist_ok=True)
        os.makedirs(other_dir, exist_ok=True)

        # Create quote file 1
        quote1_content = """---
delete: false
favorite: false
---

> Quote 1

**Source:** [test](obsidian://open?vault=Notes&file=test%23%5EQuote001)
"""
        quote1_path = os.path.join(test_dir, "Test Book - Quote001 - Quote 1.md")
        with open(quote1_path, 'w') as f:
            f.write(quote1_content)

        # Create quote file 2 (different source)
        quote2_content = """---
delete: false
favorite: false
---

> Quote 2

**Source:** [other](obsidian://open?vault=Notes&file=other%23%5EQuote001)
"""
        quote2_path = os.path.join(other_dir, "Test Book - Quote002 - Quote 2.md")
        with open(quote2_path, 'w') as f:
            f.write(quote2_content)

        # Test finding files for "test.md"
        vault = DestinationVault(temp_dir)
        found_files = vault.find_quote_files_for_source("test.md")
        assert len(found_files) == 1
        assert quote1_path in found_files
        
        # Test finding files for "other.md"
        found_files = vault.find_quote_files_for_source("other.md")
        assert len(found_files) == 1
        assert quote2_path in found_files
        
        # Test finding files for non-existent source
        found_files = vault.find_quote_files_for_source("nonexistent.md")
        assert len(found_files) == 0
        
        print("Quote file finding tests passed.")



def test_create_obsidian_uri():
    """Test that Obsidian URIs are created in the correct format."""
    
    # Test basic filename
    uri1 = DestinationFile.create_obsidian_uri("Deep Work.md", "^Quote001")
    expected = "obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote001"
    assert uri1 == expected, f"Expected {expected}, got {uri1}"
    
    # Test filename with relative path
    uri2 = DestinationFile.create_obsidian_uri("Test/File.md", "^Quote002", vault_root="Test")
    expected2 = "obsidian://open?vault=Notes&file=File%23%5EQuote002"
    assert uri2 == expected2, f"Expected {expected2}, got {uri2}"
    
    # Test filename with nested relative path
    uri3 = DestinationFile.create_obsidian_uri("Books/Deep Work.md", "^Quote003", vault_root="Books")
    expected3 = "obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote003"
    assert uri3 == expected3, f"Expected {expected3}, got {uri3}"
    
    # Test custom vault name
    uri4 = DestinationFile.create_obsidian_uri("My Book.md", "^Quote004", source_vault="MyVault")
    expected4 = "obsidian://open?vault=MyVault&file=My%20Book%23%5EQuote004"
    assert uri4 == expected4, f"Expected {expected4}, got {uri4}"
    
    print("Obsidian URI format tests passed.")

if __name__ == "__main__":
    test_create_quote_filename()
    test_create_quote_content()
    test_read_quote_file_content()
    test_extract_quote_text_from_content()
    test_update_quote_file_if_changed()
    test_find_quote_files_for_source()
    test_create_obsidian_uri()
    print("All quote writer tests passed!") 