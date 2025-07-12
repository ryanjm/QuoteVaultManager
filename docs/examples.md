# Examples

This document provides practical examples of how to use the Quote Vault Manager.

## Basic Usage

### Initial Setup

1. **Create configuration file** (`config.yaml`):
```yaml
source_vault_path: "/Users/username/Documents/Notes"
destination_vault_path: "/Users/username/Documents/QuoteVault"
std_log_path: "./sync.log"
err_log_path: "./sync.err.log"
```

2. **Add sync flag to source files**:
```markdown
---
sync_quotes: true
---

> This quote will be synced to the quote vault.
^Quote001

> This quote will also be synced.
^Quote002

Regular text that won't be synced.
```

3. **Run initial sync**:
```bash
# Dry run first
python -m quote_vault_manager --config config.yaml --dry-run

# Real sync
python -m quote_vault_manager --config config.yaml
```

## Common Workflows

### Adding New Quotes

1. **Add blockquotes to source file**:
```markdown
---
sync_quotes: true
---

> Focus without distraction is the key to producing great work.
^Quote001

> The ability to perform deep work is becoming increasingly rare.
^Quote002
```

2. **Run sync**:
```bash
python -m quote_vault_manager --config config.yaml
```

3. **Result**: Quote files are created in destination vault:
```
QuoteVault/
└── Deep Work/
    ├── Deep Work - Quote001 - Focus without distraction.md
    └── Deep Work - Quote002 - The ability to perform.md
```

### Editing Quotes

1. **Edit quote in destination file**:
```markdown
---
delete: false
favorite: false
edited: true
version: V0.3
---

> Focus without distraction is the key to producing great work.

**Source:** [Deep Work](obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote001)

[Random Note](obsidian://adv-uri?vault=ReferenceQuotes&commandid=random-note)
```

2. **Run sync**:
```bash
python -m quote_vault_manager --config config.yaml
```

3. **Result**: Source file is updated with edited quote.

### Deleting Quotes

1. **Mark quote for deletion**:
```markdown
---
delete: true
favorite: false
edited: false
version: V0.3
---

> Quote to be deleted

**Source:** [Book](obsidian://open?vault=Notes&file=Book%23%5EQuote001)

[Random Note](obsidian://adv-uri?vault=ReferenceQuotes&commandid=random-note)
```

2. **Run sync**:
```bash
python -m quote_vault_manager --config config.yaml
```

3. **Result**: Quote is unwrapped in source file and quote file is deleted.

### Removing Quotes from Source

1. **Delete blockquote from source file**:
```markdown
---
sync_quotes: true
---

> This quote remains.
^Quote001

# Quote below was removed
# > This quote was deleted.
# ^Quote002
```

2. **Run sync**:
```bash
python -m quote_vault_manager --config config.yaml
```

3. **Result**: Orphaned quote file is deleted from destination vault.

## Advanced Scenarios

### Multiple Source Files

**Source vault structure**:
```
Notes/
├── Books/
│   ├── Deep Work.md
│   └── Atomic Habits.md
└── Articles/
    └── Productivity Tips.md
```

**Destination vault structure** (after sync):
```
QuoteVault/
├── Deep Work/
│   ├── Deep Work - Quote001 - Focus without distraction.md
│   └── Deep Work - Quote002 - The ability to perform.md
├── Atomic Habits/
│   ├── Atomic Habits - Quote001 - Tiny changes remarkable results.md
│   └── Atomic Habits - Quote002 - Compound effect.md
└── Productivity Tips/
    └── Productivity Tips - Quote001 - Time blocking technique.md
```

### Handling Special Characters

**Source file with special characters**:
```markdown
---
sync_quotes: true
---

> This quote has "quotes" and 'apostrophes'.
^Quote001

> This quote has /slashes\ and :colons:.
^Quote002
```

**Generated filename**:
```
Book - Quote001 - This quote has quotes and apostrophes.md
Book - Quote002 - This quote has -slashes- and -colons-.md
```

### Multiline Quotes

**Source file**:
```markdown
---
sync_quotes: true
---

> This is a multiline quote
> that spans multiple lines
> for better readability.
^Quote001
```

**Destination file**:
```markdown
---
delete: false
favorite: false
edited: false
version: "0.3"
---

> This is a multiline quote
> that spans multiple lines
> for better readability.

**Source:** [Book](obsidian://open?vault=Notes&file=Book%23%5EQuote001)

[Random Note](obsidian://adv-uri?vault=ReferenceQuotes&commandid=random-note)
```

## Troubleshooting

### Common Issues

#### 1. Quotes Not Syncing

**Problem**: Quotes aren't being extracted from source files.

**Check**:
- Source file has `sync_quotes: true` in frontmatter
- Quotes are properly formatted with `>` prefix
- File has `.md` extension

**Solution**:
```markdown
---
sync_quotes: true
---

> This quote will sync properly.
^Quote001
```

#### 2. Duplicate Block IDs

**Problem**: Multiple quotes have the same block ID.

**Check**:
- Each quote has a unique `^QuoteNNN` ID
- No duplicate IDs in the same file

**Solution**:
```markdown
> First quote
^Quote001

> Second quote
^Quote002

> Third quote
^Quote003
```

#### 3. Orphaned Quote Files

**Problem**: Quote files exist but source quotes were deleted.

**Solution**:
- Run sync to automatically remove orphaned files
- Orphaned files are detected and deleted automatically

#### 4. URI Links Not Working

**Problem**: Obsidian URIs in quote files don't open source files.

**Check**:
- Vault name in URI matches actual vault name
- File path is correctly URL-encoded
- Block ID is properly formatted

**Example of correct URI**:
```
obsidian://open?vault=Notes&file=Deep%20Work%23%5EQuote001
```

### Log Analysis

Check log files for detailed information:

```bash
# Check standard log
cat sync.log

# Check error log
cat sync.err.log
```

## Best Practices

### File Organization

1. **Use descriptive book titles** for better organization
2. **Keep source files focused** on specific topics
3. **Use consistent naming** for easier management

### Quote Management

1. **Assign block IDs immediately** when adding quotes
2. **Use meaningful quote text** for better filenames
3. **Review orphaned files** before deletion

### Backup Strategy

1. **Backup source vault** before major syncs
2. **Use dry-run mode** for testing
3. **Keep log files** for troubleshooting

### Performance Tips

1. **Sync regularly** to avoid large batches
2. **Use dry-run** to preview changes
3. **Monitor log files** for performance issues 