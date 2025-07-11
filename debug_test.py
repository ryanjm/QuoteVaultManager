#!/usr/bin/env python3

import os
import tempfile
import sys

# Add the project root to the Python path
sys.path.insert(0, '/Users/ryanjm/code/quote_vault_manager')

from quote_vault_manager.services.source_sync import sync_source_file

def debug_test():
    """Simple debug test to see what's happening with quote creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temp directory: {temp_dir}")
        
        # Create source file with multiple quotes without block IDs
        source_file = os.path.join(temp_dir, "test_source.md")
        source_content = """---
sync_quotes: true
---

> First quote without ID

> Second quote without ID

> Third quote without ID
"""
        with open(source_file, 'w') as f:
            f.write(source_content)
        
        print(f"Created source file: {source_file}")
        print(f"Source content:\n{source_content}")
        
        # Create destination directory
        dest_dir = os.path.join(temp_dir, "quotes")
        os.makedirs(dest_dir, exist_ok=True)
        print(f"Created dest directory: {dest_dir}")
        
        # Test sync (dry run first)
        print("\n--- DRY RUN ---")
        results = sync_source_file(source_file, dest_dir, dry_run=True)
        print(f"Dry run results: {results}")
        
        # Check what files exist after dry run
        print(f"\nFiles in dest_dir after dry run:")
        if os.path.exists(dest_dir):
            for root, dirs, files in os.walk(dest_dir):
                print(f"  {root}: {dirs} {files}")
        else:
            print("  dest_dir doesn't exist!")
        
        # Test actual sync
        print("\n--- REAL SYNC ---")
        results = sync_source_file(source_file, dest_dir, dry_run=False)
        print(f"Real sync results: {results}")
        
        # Check what files exist after real sync
        print(f"\nFiles in dest_dir after real sync:")
        if os.path.exists(dest_dir):
            for root, dirs, files in os.walk(dest_dir):
                print(f"  {root}: {dirs} {files}")
        else:
            print("  dest_dir doesn't exist!")
        
        # Check source file content after sync
        print(f"\nSource file content after sync:")
        with open(source_file, 'r') as f:
            print(f.read())

if __name__ == "__main__":
    debug_test() 