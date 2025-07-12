#!/usr/bin/env python3

import tempfile
import os
from quote_vault_manager.models.source_file import SourceFile

# Create a test file with multi-line quote
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    content = """# Header

Some intro text.

> This is a multi-line quote
> that spans multiple lines
> to test unwrapping functionality
^Quote001

Some middle text.

> Another quote
^Quote002

Footer text."""
    f.write(content)
    file_path = f.name

print("Original content:")
print("=" * 50)
with open(file_path, 'r') as f:
    print(f.read())

print("\nAfter unwrapping:")
print("=" * 50)
source = SourceFile.from_file(file_path)
q1 = source.quotes[0]
source.unwrap_quote(q1)
source.save()

with open(file_path, 'r') as f:
    print(f.read())

# Clean up
os.unlink(file_path) 