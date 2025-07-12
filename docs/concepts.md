# Core Concepts

This document explains the fundamental concepts and data structures used in the Quote Vault Manager.

## Block IDs (`^QuoteNNN`)

A block ID is a **reference identifier** that uniquely identifies a section of text in a source file, regardless of its formatting.

### Key Properties:
- **Reference, not formatting**: Block IDs identify text blocks, not blockquotes specifically
- **Persistent**: Once assigned, a block ID remains valid even if the text is reformatted
- **File-scoped**: Block IDs are unique within a single source file
- **Stable**: Block IDs don't change unless the text block is deleted

### Usage:
- **Source files**: Block IDs appear after blockquotes: `> Quote text\n^Quote001`
- **Quote files**: Block IDs are embedded in filenames and URIs
- **Unwrapping**: When quotes are unwrapped, the block ID is removed from the source file, but the Quote object retains the block_id reference for the unwrap operation

### Implementation:
- Block IDs are stored in `Quote.block_id` throughout the object's lifecycle
- During unwrapping, `block_id` remains set (it's a reference, not a formatting property)
- The `needs_unwrap_block_id` field was removed as redundant

## Quote Objects

A `Quote` object represents a piece of text that can be synced between source and destination files.

### Properties:
- `text`: The actual quote content
- `block_id`: Reference to the block in the source file
- `needs_edit`: Flag indicating the quote needs to be updated in the source
- `needs_unwrap`: Flag indicating the quote should be unwrapped (removed from blockquote format)
- `needs_block_id_assignment`: Flag indicating a new block ID needs to be written to the file

### Lifecycle:
1. **Extraction**: Quote is parsed from source file
2. **Processing**: Quote may be edited, unwrapped, or assigned a block ID
3. **Sync**: Changes are propagated to source/destination files
4. **Cleanup**: Flags are reset after successful sync

## Source vs Destination Files

### Source Files
- **Location**: User's main Obsidian vault (e.g., Notes)
- **Content**: Original markdown files with blockquotes
- **Control**: Source files are the "ground truth"
- **Sync flag**: Only files with `sync_quotes: true` in frontmatter are processed

### Destination Files
- **Location**: Dedicated quote vault
- **Content**: Individual quote files with frontmatter and Obsidian URIs
- **Structure**: Organized by book title in subdirectories
- **Naming**: `[Book Title] - QuoteNNN - [First Few Words].md`

## Obsidian URIs

Obsidian URIs provide bidirectional linking between source and destination files.

### Format:
```
obsidian://open?vault=Notes&file=Book%20Title%23%5EQuote001
```

### Components:
- `vault`: The source vault name
- `file`: URL-encoded source file name
- `#`: Separator between file and block ID
- `^Quote001`: The specific block ID

### Usage:
- **Quote files**: Include URI in `**Source:**` link
- **Source files**: Block IDs provide implicit links to quote files

## File Formats

### Source File Format
```markdown
---
sync_quotes: true
---

> This is a quote that will be synced.
^Quote001

> Another quote with a different block ID.
^Quote002

Regular text that won't be synced.
```

### Destination File Format
```markdown
---
delete: false
favorite: false
edited: false
version: "0.3"
---

> This is a quote that will be synced.

**Source:** [Book Title](obsidian://open?vault=Notes&file=Book%20Title%23%5EQuote001)

[Random Note](obsidian://advanced-uri?vault=Notes&commandid=random-note-open)
```

## Sync Operations

### Forward Sync (Source → Destination)
1. Extract blockquotes from source files
2. Assign block IDs to quotes that don't have them
3. Create/update quote files in destination
4. Remove orphaned quote files

### Reverse Sync (Destination → Source)
1. Process edited quotes back to source files
2. Unwrap quotes marked for deletion
3. Update source file content

### Flags and States
- **`needs_edit`**: Quote text has been modified
- **`needs_unwrap`**: Quote should be converted from blockquote to regular text
- **`needs_block_id_assignment`**: New block ID needs to be written to file
- **`marked_for_deletion`**: Quote file should be deleted
- **`needs_update`**: Quote file content has changed 