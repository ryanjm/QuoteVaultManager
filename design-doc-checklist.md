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
- [ ] Generate Obsidian URI for source file and block ID
- [ ] Insert URI into quote file `**Source:**` section
- [ ] Ensure source file links to block ID for bidirectional linking

### 🔁 Sync Logic
- [ ] Implement sync controller in `sync.py`
- [ ] Skip files without `sync_quotes: true`
- [ ] Implement orphaned quote detection and removal

### 🚫 Dry Run Support
- [ ] Add CLI `--dry-run` flag
- [ ] Implement dry-run checks across all write/delete actions
- [ ] Log simulated actions

### 🪵 Logging
- [ ] Set up logging to `std_log_path` and `err_log_path`
- [ ] Log key events: file actions, errors, config issues, etc.

### 🛑 Error Handling
- [ ] Handle and log missing config keys
- [ ] Handle unreadable files and invalid markdown
- [ ] Detect and log duplicate block IDs
- [ ] Catch unexpected YAML fields (warn only unless critical)

### 🧪 Testing
- [ ] Unit tests:
  - [ ] Markdown parsing
  - [ ] Block ID generation
  - [ ] Quote file generation
  - [ ] URI creation
- [ ] Manual test with sample vaults (dry-run and real)
- [ ] End-to-end test with backups enabled

### 🚀 CLI Interface
- [ ] Create CLI interface in `__main__.py`
- [ ] Parse flags and run main sync logic

---

> Tip: As you complete each item, mark it `[x]` to track progress.