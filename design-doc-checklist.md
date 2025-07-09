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

- [x] Support versioning
  - [x] Create a version number in the code as a constant. Start with `V0.1`.
  - [x] The frontmatter of the quotes should include the version number.
  - [x] When the version number in the frontmatter is not the same as the constant in the script, apply all transformations (from `transformations/` directory) with a version greater than the note’s version, in order.
  - [x] If a note is missing a version, assume `V0.0` and apply the `V0.1` transformation to add the version.
  - [x] After all transformations for a version, update the note’s version in frontmatter.
  - [x] Notify the user (stdout and logs) of how many files were updated.
  - [x] Each transformation lives in its own file under `quote_vault_manager/transformations/`, tagged with the version it was introduced in.
  - [ ] There should be a separate transformation for updating the version number in the note.
  - [ ] Before destructive changes, create a backup in `.backup/VERSION-DATE/` in the quote vault, and delete backups older than a week.

- [x] Create a transformation file for `V0.2` to update notes to include a new link at the bottom of the page (there should be a blank line between the link back to the original vault and this one)
  - [x] The link will use Command URI's random URL link: [Random Note](obsidian://adv-uri?vault=ReferenceQuotes&commandid=random-note). It will be the same link for all notes.
  - [x] Increment version of the script to `V0.2` so that this patch will be applied.

- [ ] Support editing quotes
  - [ ] Create a transformation file for `V0.3` to add `edited: false` to the quote's frontmatter.
  - [ ] As part of the sync, check for edited quotes:
    - [ ] In quotes vault, check frontmatter for edited status (`edited: true`)
    - [ ] Overwrite the original blockquote in the source file with the updated quote.
  - [ ] Increment version of the script to `V0.3`.


> Tip: As you complete each item, mark it `[x]` to track progress.