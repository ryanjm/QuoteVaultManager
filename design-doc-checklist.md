## ✅ Execution Checklist for Implementation

### 🔧 Config & Setup
- [x] Create `config.yaml` format and example file
- [x] Implement `config.py` to load and validate YAML keys:
  - `source_vault_path`
  - `destination_vault_path`
  - `std_log_path`
  - `err_log_path`

### 🧠 Parsing & Extraction
- [x] Implement markdown parser to extract multiline blockquotes
- [x] Handle grouping of consecutive `>` lines
- [x] Detect and parse block IDs (`^QuoteNNN`)
- [x] Track and increment next available ID per file

### 📁 Quote File Management
- [x] Create individual quote files per extracted blockquote
- [x] Apply naming convention: `[Book Title] - QuoteNNN - [First Few Words].md`
- [x] Check and update existing quote files if source content has changed
- [x] Skip updating frontmatter fields (`delete`, `favorite`, `source_path`)
- [x] Handle deletions:
  - [x] From source: delete quote file
  - [x] From quote file (`delete: true`): unwrap in source file

### 🔗 Linking & URIs
- [x] Generate Obsidian URI for source file and block ID
- [x] Insert URI into quote file `**Source:**` section
- [x] Ensure source file links to block ID for bidirectional linking

### 🔁 Sync Logic
- [x] Implement sync controller in `sync.py`
- [x] Skip files without `sync_quotes: true`
- [x] Implement orphaned quote detection and removal

### 🚫 Dry Run Support
- [x] Add CLI `--dry-run` flag
- [x] Implement dry-run checks across all write/delete actions
- [x] Log simulated actions

### 🪵 Logging
- [x] Set up logging to `std_log_path` and `err_log_path`
- [x] Log key events: file actions, errors, config issues, etc.

### 🚫 Error Handling
- [x] Handle and log missing config keys
- [x] Handle unreadable files and invalid markdown
- [x] Detect and log duplicate block IDs
- [x] Catch unexpected YAML fields (warn only unless critical)

### 🧪 Testing
- [x] Unit tests:
  - [x] Markdown parsing
  - [x] Block ID generation
  - [x] Quote file generation
  - [x] URI creation
- [x] Manual test with sample vaults (dry-run and real)
- [x] End-to-end test with backups enabled

### 🚀 CLI Interface
- [x] Create CLI interface in `__main__.py`
- [x] Parse flags and run main sync logic

### New Features
- [ ] Create a version number so that every time there is a new version of the script it can burn everything down and rebuild it
- [ ] Check for edited quotes:
  - [ ] In quotes vault, check frontmatter for edited status (edited: true)
  - [ ] Update the source file with the update blockquote
- [ ] Add an extra link in the quote files for Command URI's random URL link - [Random Note](obsidian://adv-uri?vault=ReferenceQuotes&commandid=random-note)

---

> Tip: As you complete each item, mark it `[x]` to track progress.