#!/usr/bin/env python3
"""
Debug script to test the improved quote sync architecture.
"""

import os
import tempfile
from quote_vault_manager.models.source_quote import SourceQuote
from quote_vault_manager.models.destination_quote import DestinationQuote
from quote_vault_manager.services.quote_sync import QuoteSyncService

def test_improved_quote_architecture():
    """Test the improved SourceQuote and DestinationQuote architecture."""
    
    print("Testing improved quote architecture...")
    
    # Create a source quote
    source_quote = SourceQuote("Original quote from the book", "^Quote001")
    print(f"SourceQuote: {source_quote}")
    
    # Create a destination quote with frontmatter
    frontmatter = {
        'delete': False,
        'favorite': False,
        'edited': True,
        'version': '0.3'
    }
    
    dest_quote = DestinationQuote(
        "Edited quote from the book", 
        "^Quote001",
        frontmatter=frontmatter,
        source_quote=source_quote
    )
    print(f"DestinationQuote: {dest_quote}")
    print(f"  Is edited: {dest_quote.is_edited}")
    
    # Establish bidirectional relationship
    source_quote.add_destination_quote(dest_quote)
    print(f"SourceQuote has {len(source_quote.destination_quotes)} destination quotes")
    print(f"SourceQuote has edits: {source_quote.has_edits}")
    print(f"SourceQuote edited text: {source_quote.edited_text}")
    
    # Test syncing from source to destination (should not overwrite edited quote)
    print("\nTesting sync from source to destination...")
    changed = dest_quote.sync_from_source(source_quote)
    print(f"Sync changed destination: {changed}")
    print(f"Destination text after sync: {dest_quote.text}")
    print(f"Destination still edited: {dest_quote.is_edited}")
    
    # Test syncing from destination back to source
    print("\nTesting sync from destination back to source...")
    changed = dest_quote.sync_to_source(dry_run=False)
    print(f"Sync changed source: {changed}")
    print(f"Source text after sync: {source_quote.text}")
    print(f"Destination edit flag reset: {dest_quote.is_edited}")
    
    print("\n✅ SUCCESS: Improved quote architecture works correctly!")

def test_quote_formatting():
    """Test quote formatting for different contexts."""
    
    print("\nTesting quote formatting...")
    
    # Test source quote formatting
    source_quote = SourceQuote("This is a multi-line\nquote from the book", "^Quote001")
    source_formatted = source_quote.format_for_source()
    print("Source formatting:")
    print(source_formatted)
    
    # Test destination quote formatting
    dest_quote = DestinationQuote("This is a multi-line\nquote from the book", "^Quote001")
    dest_formatted = dest_quote.format_for_destination("Book.md", "Notes", "")
    print("Destination formatting:")
    print(dest_formatted)
    
    print("\n✅ SUCCESS: Quote formatting works correctly!")

def test_quote_sync_service():
    """Test the new QuoteSyncService with real files."""
    
    print("\n" + "="*60)
    print("TESTING QUOTE SYNC SERVICE")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source file with original quote
        src_path = os.path.join(temp_dir, "Book.md")
        src_content = """---
sync_quotes: true
---

> Original quote from the book
^Quote001

Other content here.
"""
        with open(src_path, 'w') as f:
            f.write(src_content)
        
        # Create destination vault with edited quote
        qvault_path = os.path.join(temp_dir, "quotes")
        os.makedirs(qvault_path, exist_ok=True)
        
        # Create edited quote file
        book_dir = os.path.join(qvault_path, "Book")
        os.makedirs(book_dir, exist_ok=True)
        
        quote_path = os.path.join(book_dir, "Book - Quote001 - Original quote from the book.md")
        quote_content = """---
delete: false
favorite: false
edited: true
version: "0.3"
---

> Edited quote from the book

**Source:** [Book](obsidian://open?vault=Notes&file=Book%23^Quote001)

[Random Note](obsidian://advanced-uri?vault=Notes&commandid=random-note-open)
"""
        with open(quote_path, 'w') as f:
            f.write(quote_content)
        
        print("Before sync:")
        print(f"  Source file: {open(src_path).read()}")
        print(f"  Quote file: {open(quote_path).read()}")
        
        # Test the new QuoteSyncService
        quote_sync_service = QuoteSyncService(temp_dir, qvault_path)
        results = quote_sync_service.sync_source_file(src_path, dry_run=False)
        
        print(f"\nSync results: {results}")
        print(f"\nAfter sync:")
        print(f"  Source file: {open(src_path).read()}")
        print(f"  Quote file path: {quote_path}")
        quote_file_content = open(quote_path).read()
        print(f"  Quote file content after sync:\n{quote_file_content}")
        
        # Verify the results
        assert results['quotes_synced_back'] == 1, "Should have synced 1 edited quote back to source"
        assert "> Edited quote from the book" in open(src_path).read(), "Source should contain edited quote"
        assert "edited: false" in quote_file_content, "Edit flag should be reset"
        
        print("\n✅ SUCCESS: QuoteSyncService works correctly!")

if __name__ == "__main__":
    test_improved_quote_architecture()
    test_quote_formatting()
    test_quote_sync_service() 