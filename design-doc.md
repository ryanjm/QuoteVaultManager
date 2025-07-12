# 🛠 Engineering Design Document: `quote-vault-manager`

## Overview

This Python script manages quote synchronization between a source Obsidian vault (`Notes`) and a destination quote vault (`ReferenceQuotes`). It scans markdown files in the source vault, extracts all blockquotes, and ensures corresponding quote files exist and are properly linked. It supports syncing, deletions, updates, and orphan cleanup. This document outlines the architecture, data structures, logic, and error handling for a robust and idempotent implementation.

## ✨ Features

- Parse YAML config
- Extract multiline blockquotes
- Assign and track stable block IDs (`^QuoteNNN`)
- Create individual quote files in a subfolder per book
- Maintain bidirectional links using Obsidian URI
- Sync updates from source to quote vault (source is the ground truth)
- Handle quote deletions via `delete: true` in frontmatter
- Dry-run mode for safe test execution
- Structured logging for stdout and errors

## 🧱 Architecture

### Main Modules

```
quote_vault_manager/
├── __main__.py         # CLI entry point
├── config.py           # YAML config loader and validation
├── quote_parser.py     # Parse blockquotes and assign IDs
├── quote_writer.py     # Create/update/delete quote files
├── sync.py             # Main sync logic controller
├── utils.py            # Helpers for URI encoding, file ops, etc.
└── logger.py           # Logging setup (stdout and error log)
```

## 📁 Directory Layouts

### Notes Vault (Source)

```
Notes/
└── References/Book Notes/
    └── Deep Work.md
```

### Quote Vault (Destination)

```
ReferenceQuotes/
└── Deep Work/
    └── Deep Work - Quote003 - Focus without distraction.md
```

## 📄 Quote File Format (Example)

```markdown
---
delete: false
favorite: false
source_path: "Deep Work.md"
---

> Focus without distraction is the key to producing great work.

**Source:** [Deep Work](obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote003)
```

## 🧩 Functional Logic

### Config Loader

- Parses YAML using `pyyaml`
- Validates 4 keys:
  - `source_vault_path`
  - `destination_vault_path`
  - `std_log_path`
  - `err_log_path`

### Quote Extraction

- Uses regex or markdown parsing to find multiline blockquotes.
- Groups consecutive lines starting with `>` as one quote.
- Detects existing IDs using the `^QuoteNNN` block ID syntax.
- Tracks the next available ID (`QuoteNNN`) by scanning existing blocks.

### Block ID Handling

- New quotes are assigned `^QuoteNNN` based on the next available index.
- IDs are scoped per file.
- Quote file name is built using:
  ```
  [Book Title] - QuoteNNN - [First Few Words].md
  ```

### Quote File Management

- If a quote file doesn’t exist → create it.
- If it exists and quote has changed → update contents (leave YAML unchanged).
- If quote was deleted in source → delete quote file.
- If quote has `delete: true` in quote file → unwrap the quote in the source file (remove `>` and block ID).
- If quote file is orphaned (ID no longer in source) → delete it.

### Obsidian URI Generation

Use:

```python
urllib.parse.quote("Deep Work")  # Deep%20Work
```

Final URI pattern:

```
obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote003
```

### Bidirectional Linking

- **Quote file** links to **source file** via URI.
- **Source file** links to **quote file** via block ID.

## 🔄 Sync Workflow

```python
for source_file in get_markdown_files(source_vault_path):
    if not has_sync_quotes_true(source_file):
        continue

    quotes = extract_blockquotes(source_file)

    for quote in quotes:
        ensure_block_id(quote)
        ensure_quote_file_exists_or_update(quote)

    remove_deleted_or_orphaned_quotes(source_file)
```

## ⚙️ Dry Run

- Add a `--dry-run` CLI flag.
- All file writes/deletes are skipped in dry run mode.
- Log actions it *would* take.

## 🪵 Logging

- `std_log_path`: for sync success messages
- `err_log_path`: for:
  - File read/write errors
  - Invalid config
  - YAML format issues
  - Duplicate block IDs
  - Orphaned quote inconsistencies

## 🔒 Error Handling Strategy

| Case                          | Action                                                     |
|------------------------------|-------------------------------------------------------------|
| Missing config keys          | Exit and log error                                          |
| Missing vault paths          | Exit and log error                                          |
| Invalid markdown format      | Skip file and log warning                                   |
| Duplicate block IDs          | Log error with file and line number                         |
| File permissions issue       | Log error, continue to next file                            |
| Unexpected YAML keys         | Ignore unless it’s critical (`delete`, `favorite`)          |

## 🧪 Testing Plan

- Unit tests for:
  - Markdown parsing
  - ID assignment logic
  - File generation and naming
  - URI generation
- Manual testing in dry-run mode with test vaults
- End-to-end run on real data with backups enabled

## 🧼 Idempotency

- Quote ID assignment is deterministic
- Redundant runs result in no change unless the source quote content has changed
- No global state maintained between runs

## 🧰 CLI Usage Example

```bash
python3 quote_vault_manager/main.py --config config.yaml
python3 quote_vault_manager/main.py --config config.yaml --dry-run
```